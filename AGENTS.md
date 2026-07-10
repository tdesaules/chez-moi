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

## Chezmoi template facts

- chezmoi 2.70.0. Functions and `{{ }}` syntax are chezmoi's, not mise's.
- **Two data sources for templates:**
  - `.chezmoi.toml.tmpl` computes runtime booleans: `is_linux`, `is_fedora`,
    `is_mise`, `is_nushell`, `is_ssh`, `is_systemd`, `is_distrobox`, and
    `atomic_version` (rpm-ostree deployment tag). Use for OS/tool gating:
    `{{ if .is_linux }} ... {{ end }}`.
  - `.chezmoidata/*.yaml` provides structured config (paths, ports, key names, etc.)
    accessed as `{{ .systemd.user_dir }}`, `{{ .gopass.age.device }}`,
    `{{ .dms.service }}`, etc. Add new config values here, not inline in templates.
- Scripts in `.chezmoiscripts/` use lifecycle prefixes with numeric ordering:
  - `run_once_before_*` — bootstrap (runs once on first init, before everything else).
  - `run_once_after_*` — runs once, after bootstrap.
  - `run_onchange_*` — re-runs only when one of its `{{ include "<path>" | sha256sum }}`
    comment-hashes changes. Add a hash line for every file that should trigger it.
- **DMS plugins are chezmoi externals** (downloaded archives, not source files), so the
  `include | sha256sum` pattern cannot detect their changes. Instead,
  `run_onchange_after_03-dms-plugins.sh.tmpl` hashes the resolved release tags of both
  `pinentry-dms` and `gopass-dms`:
  `{{ (gitHubLatestRelease "tdesaules/pinentry-dms").TagName }}` and
  `{{ (gitHubLatestRelease "tdesaules/gopass-dms").TagName }}`.
- Shared logging helper: every script does
  `{{ include ".chezmoitemplates/functions.tmpl" }}`
  then calls `_log "<level>" "<msg>"` (levels: info/success/error/warning/...).
  Use it for consistency; do not hand-roll `echo`.

## Secrets (gopass)

- **Never hardcode tokens.** Use the chezmoi `gopass` template function:
  `{{ gopass "perso/token/<host>/<uuid>" | trim }}`
  (path examples live in `dot_local/share/opencode/auth.json.tmpl` and
  `dot_config/mise/config.toml.tmpl`).
- For paths needing special chars, use backtick strings:
  `` {{ gopass `perso/token/.../uuid` | trim }} ``
- gopass store layout: `perso/<category>/<host>/<uuid>` (token UUIDs are real entries;
  see `gopass ls` on the host).
- gopass uses the **age backend**. The age identity lives on a USB key
  (`/dev/disk/by-label/AGE`), symlinked to `~/.config/gopass/age/identities`.
  The store is a git repo cloned from `git@github.com:tdesaules/gopass.git` to
  `~/.local/share/gopass/stores/root`.
- The age agent is **locked at boot** (`gopass-age-agent.service` `ExecStartPost` locks it).
  `chezmoi apply` that reads a secret needs `gopass age agent unlock` first.
- gopass binaries run through mise shims:
  `~/.local/share/mise/shims/gopass`. All systemd unit `ExecStart` lines use this path.

## GitHub API rate limits

- `.chezmoiexternal.toml` calls `(gitHubLatestRelease "<org>/<repo>").TagName` for DMS
  plugins — this hits GitHub's unauthenticated rate limit fast. Run authenticated applies:
  `GITHUB_TOKEN=$(gopass show -o perso/token/github.com/5fc4238e-6370-4187-bbd7-f8f05c5dfff5) chezmoi apply --source <repo>`
- The `GITHUB_TOKEN` env var (provisioned by mise via gopass) also covers
  `mise ls-remote` and any `github:` backend calls.
- Other externals (`usage-specs`, `nvim`/LazyVim) use static archive URLs and don't hit
  the rate limit.

## mise

- Global tool list: `dot_config/mise/config.toml.tmpl`. Almost every CLI is a `github:*`
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

## opencode

- Provider config: `dot_config/opencode/opencode.json.tmpl`. Enabled providers:
  `mistral`, `openrouter`, `zai-coding-plan`, `umans`, `lemonade` (local,
  `http://127.0.0.1:13305/v1`).
- `lemonade`, `umans`, and `openrouter` are defined inline in `opencode.json.tmpl` with
  gopass-backed API keys. `mistral` and `zai-coding-plan` get their keys from
  `dot_local/share/opencode/auth.json.tmpl`.

## Verify before commit

- `chezmoi diff --source <repo>` — preview rendered changes against `$HOME`.
- `GITHUB_TOKEN="$(gopass show -o ...)" chezmoi apply --source <repo>` — apply
  (unlocks gopass+rate limit).
- Do NOT run `gsub`/`sed` over templates expecting rendered output — they contain
  chezmoi `{{ }}` directives that must be preserved.
