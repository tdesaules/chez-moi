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
- `README.md`, `LICENSE`, `.chezmoiversion`, `.chezmoitemplates` are in `.chezmoiignore`
  and never deployed.
- If a deployed file was modified outside chezmoi (e.g. `mise settings set`), apply with
  `--force` to overwrite: `chezmoi apply --force --source <repo> <path>`.

## Chezmoi template facts

- chezmoi 2.70.0. Functions and `{{ }}` syntax are chezmoi's, not mise's.
- `.chezmoi.toml.tmpl` computes booleans exposed as data — use them for OS gating:
  `{{ if .is_linux }} ... {{ end }}`, `{{ if .is_fedora }}`, `{{ if .is_mise }}`,
  `{{ if .is_nushell }}`, and `{{ .atomic_version }}` (rpm-ostree deployment tag).
- Scripts in `.chezmoiscripts/` use lifecycle prefixes:
  - `run_once_*` — runs once, idempotent across applies.
  - `run_onchange_*` — re-runs only when one of its `{{ include "<path>" | sha256sum }}`
    comment-hashes changes. Add a hash line for every file that should trigger it.
- **DMS plugins are chezmoi externals** (downloaded archives, not source files), so the
  `include | sha256sum` pattern cannot detect their changes. Instead,
  `run_onchange_after_dms_plugins.sh.tmpl` hashes the resolved release tag:
  `{{ (gitHubLatestRelease "tdesaules/pinentry-dms").TagName }}`.
- Shared logging helper: every script does
  `source "{{ .chezmoi.sourceDir }}/.chezmoitemplates/functions.sh.tmpl"`
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
- gopass uses the **age backend**. Identity file: `~/.config/gopass/age/identities`
  (scrypt-encrypted keyring). Recipients list: `~/.local/share/gopass/stores/root/.age-recipients`.
  Two recipients: primary (passphrase-protected) + recovery (no passphrase, printed offline).
- The age agent is **locked at boot** (`gopass-age-agent.service` `ExecStartPost` locks it).
  `chezmoi apply` that reads a secret needs `gopass age agent unlock` first.
- gopass binaries run through mise shims:
  `~/.local/share/mise/shims/gopass`. All systemd unit `ExecStart` lines use this path.

## GitHub API rate limits

- `.chezmoiexternal.toml` calls `(gitHubLatestRelease "<org>/<repo>").TagName` — this hits
  GitHub's unauthenticated rate limit fast. Run authenticated applies:
  `GITHUB_TOKEN=$(gopass show -o perso/token/github.com/51fd0064-4366-465d-b741-ab3239cf8271) chezmoi apply --source <repo>`
- The `GITHUB_TOKEN` env var (provisioned by mise via gopass) also covers
  `mise ls-remote` and any `github:` backend calls.

## mise

- Global tool list: `dot_config/mise/config.toml.tmpl`. Almost every CLI is a `github:*`
  backend tool. Add new tools there (version `"latest"` unless pinning).
- `[settings.github]` has `github_attestations = false` — disables GitHub artifact
  attestation verification (sigstore TSA bug in mise, causes install failures for `github:*` tools).
- Scripts to run after tool changes:
  - `run_once_after_mise.sh.tmpl` — runs `mise install --quiet --yes` once.
  - If a tool needs systemd/shim refresh, add a `run_onchange_*` script with the file hash.
- Env vars for mise live under `[env]` in the same config. Use `redact = true` on secrets
  so `mise env` doesn't leak them. Example pattern (already in repo):
  `GITHUB_TOKEN = { value = "{{ gopass \"...\" | trim }}", redact = true }`

## systemd / containers

- User units: `dot_config/systemd/user/*.service.tmpl` → `~/.config/systemd/user/`.
  `run_onchange_after_systemd.sh.tmpl` reloads and enables/disables based on presence.
- **The onchange script only scans `*.service` and `*.socket`** (line 37 `find`). If you
  add `.path`, `.timer`, or `.mount` units, extend the `find` command in
  `run_onchange_after_systemd.sh.tmpl` accordingly.
- Quadlet containers: `dot_config/containers/systemd/*.container.tmpl` + `ai.network`.
  These are handled by `daemon-reload` only (not explicitly enabled).
- Any new unit must add a `# {{ include "<path>" | sha256sum }}` line to the
  systemd onchange script.

## distrobox

- `dot_config/distrobox/distrobox.ini.tmpl` assembles containers via
  `distrobox assemble create --file ...` in `run_onchange_after_distrobox.sh.tmpl`.
  Add a hash line in that script for every new `.desktop.tmpl` or `distrobox.ini.tmpl`.

## opencode

- Provider config: `dot_config/opencode/opencode.json.tmpl`. Enabled providers:
  `mistral`, `opencode-go`, `zai-coding-plan`, `umans`, `lemonade` (local,
  `http://127.0.0.1:13305/v1`).
- Per-provider API keys: `dot_local/share/opencode/auth.json.tmpl` (gopass-backed).

## Verify before commit

- `chezmoi diff --source <repo>` — preview rendered changes against `$HOME`.
- `GITHUB_TOKEN="$(gopass show -o ...)" chezmoi apply --source <repo>` — apply
  (unlocks gopass+rate limit).
- Do NOT run `gsub`/`sed` over templates expecting rendered output — they contain
  chezmoi `{{ }}` directives that must be preserved.
