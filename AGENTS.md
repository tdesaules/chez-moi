# AGENTS.md

Chezmoi dotfiles source repo for a Fedora Atomic (rpm-ostree) desktop.
Target machine: Kinoite, nushell + mise + gopass + niri.

## Response style

- Keep responses **short and concise**. Only essential information, no fluff.
- No preamble, no postamble, no unnecessary explanations.

## Where to edit

- **Edit only files in this project repo** (`~/repository/github.com/tdesaules/chez-moi`).
  `chezmoi source-path` returns `~/.local/share/chezmoi`, a *separate clone* with the
  same remote — editing there is lost work. To apply changes from this repo:
  `chezmoi apply --source ~/repository/github.com/tdesaules/chez-moi`
- Paths map `dot_<X>` → `~/.<X>` (e.g. `dot_config/mise/...` → `~/.config/mise/...`).
- `README.md`, `AGENTS.md`, `LICENSE`, `.chezmoiversion`, `.chezmoitemplates` are in
  `.chezmoiignore` and never deployed.
- If a deployed file was modified outside chezmoi (e.g. `mise settings set`), apply with
  `--force` to overwrite: `chezmoi apply --force --source <repo> <path>`.

## Git workflow

- **Commit changes locally** using [conventional commits](https://www.conventionalcommits.org/)
  (e.g. `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`).
- **Never push** — pushing to the remote is done manually by the user.

## Chezmoi template facts

- chezmoi 2.70.0. Functions and `{{ }}` syntax are chezmoi's, not mise's.
- **Two data sources for templates:**
  - `.chezmoi.toml.tmpl` computes runtime booleans: `is_linux`, `is_fedora`,
    `is_mise`, `is_nushell`, `is_ssh`, `is_systemd`, and `is_distrobox`. Use
    `.chezmoi.osRelease.versionID` directly for the Fedora release and these
    booleans for OS/tool gating: `{{ if .is_linux }} ... {{ end }}`.
  - `.chezmoidata/*.yaml` provides structured config (paths, ports, key names, etc.)
    accessed as `{{ .systemd.user_dir }}`, `{{ .gopass.age.device }}`,
    `{{ .dms.service }}`, etc. Add new config values here, not inline in templates.
- Scripts in `.chezmoiscripts/` use lifecycle prefixes with numeric ordering:
  - `run_once_before_*` — bootstrap (runs once on first init, before everything else).
  - `run_once_after_*` — runs once, after bootstrap.
  - `run_onchange_*` — re-runs only when one of its `{{ include "<path>" | sha256sum }}`
    comment-hashes changes. Add a hash line for every file that should trigger it.
- `run_after_99-bootstrap-complete.sh.tmpl` writes the success marker consumed by
  the image's Topgrade service. Keep it last and idempotent.
- **DMS plugins are chezmoi externals**. Their release tags are pinned in
  `.chezmoidata/plugins.yaml` and updated together by Renovate. The externals and
  `run_onchange_after_03-dms-plugins.sh.tmpl` both use these tags. The pinentry
  binary remains on mise `latest`; check binary/plugin compatibility on upgrades.
- Shared logging helper: every script does
  `{{ include ".chezmoitemplates/functions.tmpl" }}`
  then calls `_log "<level>" "<msg>"` (levels: info/success/error/warning/...).
  Use it for consistency; do not hand-roll `echo`.

## Secrets (gopass)

- **Never hardcode tokens.** Use the chezmoi `gopass` template function:
  `{{ gopass "perso/token/<host>/<uuid>" | trim }}`
  (path examples live in `dot_local/share/opencode/auth.json.tmpl` and
  `dot_config/mise/private_config.toml.tmpl`).
- For paths needing special chars, use backtick strings:
  `` {{ gopass `perso/token/.../uuid` | trim }} ``
- gopass store layout: `perso/<category>/<host>/<uuid>` (token UUIDs are real entries;
  see `gopass ls` on the host).
- gopass uses the **age backend**. The age identity lives on a USB key
  (`/dev/disk/by-label/AGE`), symlinked to `~/.config/gopass/age/identities`.
  The store is a git repo cloned from `git@github.com:tdesaules/gopass.git` to
  `~/.local/share/gopass/stores/root`.
- The age agent is **not** locked at boot anymore: a fresh agent holds no
  identities, so the former `ExecStartPost` lock was a no-op security-wise, and
  any pre-insertion `gopass` call would unlock-and-fail during recovery,
  leaving the agent stuck unlocked-but-empty. Note `gopass age agent unlock`
  on ≤ 1.16.1 is itself buggy (sets `locked=false` without loading identities,
  gopasspw/gopass#3430) — avoid calling it. On AGE key insertion the
  `gopass-age-usb-handler` runs `~/.local/bin/gopass-age-selfheal`, which
  locks the agent if it is unlocked-but-empty so the next access takes the
  working recovery path. If prompts repeat on every call, run
  `gopass-age-selfheal` (or `gopass age agent lock`) once.
- **Passphrase caching**: the agent caches the *unlocked identity* in memory
  (not the passphrase). `age.agent-timeout` (in `dot_config/gopass/config`,
  7200s = 2h) is an **idle** timeout — each successful `gopass show` resets the
  timer, so regular use keeps the cache alive indefinitely. The cache is purged
  by: **AGE USB key removal** (the `gopass-age-usb-handler` polls the device
  in-process and locks the agent + removes the identity symlink), the idle
  timeout, and agent restart / host shutdown (a fresh agent starts empty).
  Screen
  lock and suspend do **not** purge the cache in this setup. Do **not** enable
  `age.usekeychain` (would persist the passphrase across reboots via the OS
  keyring).
- Changing `agent-timeout` takes effect on the next agent unlock (the value is
  pushed to the running agent via `set-timeout`); run `gopass age agent lock`
  once after the change to activate it immediately.
- **Expected cache behavior (spec)**: one pinentry prompt after each lock, then
  the agent serves every decrypt until the idle timeout or a lock event.
  Prompts on *every* `gopass` call = bug, not design.
- **gopass ≤ 1.16.1 is buggy** (fixed upstream, unreleased): gopasspw/gopass#3509
  (SSH identities from `~/.ssh` are included in `SendIdentities`, can't be
  re-parsed by the agent, and Go map iteration order makes it a coin flip) +
  #3488 (an empty-but-unlocked agent never self-heals → prompt on every call,
  even with the correct passphrase). **Workaround 1**: `GOPASS_SSH_DIR` in mise
  `[env]` points to `~/.config/gopass/no-ssh` (contains an empty `.ssh/`, see
  `dot_config/gopass/no-ssh/`) so gopass scans zero SSH identities and only the
  native identity reaches the agent. **Workaround 2**: `gopass-age-selfheal`
  (`dot_local/bin/executable_gopass-age-selfheal.tmpl`) probes the agent and
  locks it when it is unlocked-but-empty, so the next access recovers; it is
  invoked by the USB handler on key insertion. **Remove both once a gopass
  release ships #3488 + #3509** (check release notes > v1.16.1 / v1.17.0-rc.2).
- gopass binaries run through mise shims:
  `~/.local/share/mise/shims/gopass`. All systemd unit `ExecStart` lines use this path.

## GitHub API rate limits

- DMS externals use pinned tags, so applying them no longer resolves latest
  releases through the GitHub API. CI checks release assets with a GitHub token.
- The `GITHUB_TOKEN` env var (provisioned by mise via gopass) also covers
  `mise ls-remote` and any `github:` backend calls.
- Other externals (`usage-specs`, `nvim`/LazyVim) use static archive URLs and don't hit
  the rate limit.

## mise

- Global tool list: `dot_config/mise/private_config.toml.tmpl`. Almost every CLI is a `github:*`
  backend tool. Add new tools there (version `"latest"` unless pinning).
- `[settings.github]` has `github_attestations = false` — disables GitHub artifact
  attestation verification (sigstore TSA bug in mise, causes install failures for `github:*` tools).
- `minimum_release_age_excludes = ["github:tdesaules/pinentry-dms"]` — exempts that tool
  from the minimum release age gate.
- Scripts to run after tool changes:
  - `run_once_after_01-mise.sh.tmpl` — runs `mise install --yes` once.
  - If a tool needs systemd/shim refresh, add a `run_onchange_*` script with the file hash.
- Env vars for mise live under `[env]` in the same config. Use `redact = true` on secrets
  so `mise env` doesn't leak them. Example pattern (already in repo):
  `GITHUB_TOKEN = { value = "{{ gopass \"...\" | trim }}", redact = true }`

## systemd / containers

- User units: `dot_config/systemd/user/*.service.tmpl` → `~/.config/systemd/user/`.
  `run_onchange_after_01-systemd.sh.tmpl` reloads and enables/disables based on presence.
- **The onchange script scans `*.service`, `*.socket`, and `*.path`** (line 31 `find`).
  If you add `.timer` or `.mount` units, extend the `find` command accordingly.
- Quadlet containers: `dot_config/containers/systemd/*.container.tmpl` + `ai.network`.
  Containers with an `[Install]` section are explicitly enabled (symlinked into
  `default.target.wants` and restarted). Those without `[Install]` get daemon-reload only.
- Any new unit must add a `# {{ include "<path>" | sha256sum }}` line to the
  systemd onchange script.
- Quadlet images follow `latest` and are pulled by Topgrade using Podman.
  Restart their services manually to use new images. No `AutoUpdate=registry`:
  the systemd onchange script disables the previously managed
  `podman-auto-update.timer` on apply.

## Renovate

- Nine Distrobox apps and two DMS plugins are pinned in `.chezmoidata/apps.yaml`
  and `plugins.yaml`. Preserve the `# renovate: depName=...` annotations.
- `.github/renovate-config.cjs` is runner config; `renovate.json` is repo config.
- The nightly workflow needs the GitHub secret `RENOVATE_TOKEN`, with repository
  contents, PR, issues (dependency dashboard), and workflow write access. No
  automerge. Never store its value in this repo.
- PR CI validates Renovate and checks assets using rendered chezmoi templates.
  If upstream changes an asset naming convention, update the template too.
- Mise stays on `latest`. DNF/OS, OpenSCAD snapshots, branch externals and models
  retain their existing update strategies.

## distrobox

- `dot_config/distrobox/distrobox.ini.tmpl` assembles containers via
  `distrobox assemble create --file ...` in `run_onchange_after_04-distrobox.sh.tmpl`.
  Add a hash line in that script for every new `.desktop.tmpl`, `distrobox.ini.tmpl`,
  or `dot_config/containers/containers.conf`.

## Scripts needing sudo or interaction

- `run_once_before_01-ssh-keygen.sh.tmpl` — generates ed25519 SSH key (gated on `is_ssh`).
- `run_once_before_02-gopass-bootstrap.sh.tmpl` — **interactive**: installs gopass+gh via
  mise, does GitHub OAuth (QR code on terminal), mounts AGE USB key, clones gopass store,
  unlocks age agent. Reads passphrase from `/dev/tty`. Runs only on first init.
- `run_onchange_after_02-age-usb.sh.tmpl` — deploys udisks2 mount_options.conf to system
  path (**needs sudo**).
- `run_onchange_after_05-qemu-bridge.sh.tmpl` — deploys QEMU bridge network config +
  firewall rules (**needs sudo**).
- `run_onchange_after_06-beszel-agent.sh.tmpl` — sets up Beszel monitoring agent via API
  calls to local hub (`localhost:8090`).
- `run_onchange_after_09-orcaslicer-udev.sh.tmpl` — deploys the 3D-printer serial udev
  rule (`90-orcaslicer-3dprinter.rules`, `/dev/ttyACM*` + `/dev/ttyUSB*` access) to
  `/etc/udev/rules.d/` and reloads udev (**needs sudo**). Driven by
  `dot_config/udev/rules.d/90-orcaslicer-3dprinter.rules` + `.chezmoidata/udev.yaml`.

## opencode

- Provider config: `dot_config/opencode/private_opencode.json.tmpl`. Enabled providers:
  `opencode-go` (OpenCode Go subscription, built-in), `openrouter`, `poolside`,
  `scaleway`, `zai-coding-plan`, `ollama-cloud` (Ollama Cloud API,
  `https://ollama.com/v1`).
- OpenCode Zen (`opencode`) has been replaced by OpenCode Go (`opencode-go`).
- Each provider uses a `whitelist` to show only curated models in `/models`:
  - `opencode-go`: `kimi-k3`, `kimi-k2.7-code`, `deepseek-v4-flash`, `glm-5.2`
  - `ollama-cloud`: same four as `opencode-go`
  - `openrouter`: `moonshotai/kimi-k3`, `moonshotai/kimi-k2.7-code`,
    `deepseek/deepseek-v4-flash`, `z-ai/glm-5.2`
  - `poolside`: `poolside/laguna-s-2.1`, `poolside/laguna-xs-2.1`
  - `scaleway`: `glm-5.2`, `mistral-medium-3.5-128b`
  - `zai-coding-plan`: `glm-5.2`
- `openrouter` and `poolside` are defined inline in `private_opencode.json.tmpl` with
  gopass-backed API keys. `ollama-cloud`, `zai-coding-plan`, and `scaleway` get
  their keys from `dot_local/share/opencode/auth.json.tmpl`. `opencode-go`,
  `ollama-cloud`, `scaleway`, and `zai-coding-plan` are built-in providers
  (models.dev).
- The `opencode-claude-auth` plugin (removed in OpenCode 1.3.0) is no longer
  referenced. Anthropic Pro/Max OAuth routing is not supported per Anthropic ToS.

## Local model downloads

- `dot_local/bin/private_executable_pull-hf-models.tmpl` downloads Hugging Face
  models listed in `dot_config/models/config.kcl.tmpl` to
  `~/.local/share/huggingface/models`, using the mise-provided `hf`, `kcl`, and `jq`.
- Topgrade runs `pull-hf-models`. This downloader is independent of the retired
  Lemonade / Open WebUI / Open Terminal stack.
- `.chezmoiremove` removes the retired stack's deployed configuration and launchers;
  `run_once_before_03-retire-lemonade.sh.tmpl` stops its user services first.
  Existing Podman volumes and downloaded models are preserved.

## llama.cpp

- `.chezmoidata/llama.yaml` configures the Vulkan Quadlet, Ornith Q4_K_M model,
  localhost port 50501, and five slots with 262144 tokens per slot.
- `dot_config/models/config.kcl.tmpl` adds Ornith to the existing downloader;
  keep existing models in the list to prevent its orphan cleanup deleting them.
- `llama-server.container.tmpl` mounts the whole models directory read-only,
  including `.hf-cache` so the downloader's relative symlinks resolve.
- No `[Install]`: start/stop on demand through the Dank launcher entry `Ornith-1.5-35B-A3B`.
  `llama-server-toggle` waits for `/health` silently on startup (errors still notify);
  it does not download models.
- `ornith-tray.service` is wanted by the server and stops with it (`BindsTo`/`PartOf`).
  Left-click opens the Nord health panel in `dot_config/quickshell/ornith-health/`
  on the focused Niri output; it refreshes `/health` every 3 seconds and closes on
  Escape or an outside click. Right-click has only `Open Chat` and `Stop`.
  The tray uses `/usr/bin/python3`, system PyGObject/Gio and GdkPixbuf,
  not mise Python. It re-registers when the tray watcher restarts.
- The Ornith mascot is redrawn as a Nord SVG; its reference URL is in the SVG.
- Context fitting is disabled to prevent silently reducing the requested capacity.
  Vulkan reports about 79 GiB accessible on this Strix Halo host, including shared
  memory (the kernel reports 32 GiB dedicated VRAM). Keep KV offloading enabled;
  the five 256K slots need about 25 GiB of FP16 KV cache in addition to weights.
  Validate memory use and `/props` after changing context, parallelism, or backend.

## Verify before commit

- `chezmoi diff --source <repo>` — preview rendered changes against `$HOME`.
- `GITHUB_TOKEN="$(gopass show -o ...)" chezmoi apply --source <repo>` — apply
  (unlocks gopass+rate limit).
- Do NOT run `gsub`/`sed` over templates expecting rendered output — they contain
  chezmoi `{{ }}` directives that must be preserved.
