# CHEZ-MOI

Dotfiles for a Fedora Atomic (rpm-ostree) desktop — Kinoite, nushell + mise + gopass + niri.

## Prerequisites

- `mise` on `$PATH`
- AGE USB key (`/dev/disk/by-label/AGE`) with gopass age identity

## Bootstrap

```bash
ujust update
rpm-ostree install chezmoi
```

Reboot to apply the rpm-ostree layer.

## Init

```bash
chezmoi init --apply https://github.com/tdesaules/chez-moi.git
```

**Interactive** — generates SSH key, does GitHub OAuth (QR code), mounts AGE USB
key, asks for gopass age passphrase, clones gopass store, installs mise tools,
and sets up systemd services + containers. Some scripts need **sudo**.

## Update

Pull and apply from the remote:

```bash
chezmoi update
```

Or apply changes from the repo clone:

```bash
chezmoi apply --source ~/repository/github.com/tdesaules/chez-moi
```

Applies that read secrets need the age agent unlocked:

```bash
gopass age agent unlock
```

The agent caches the unlocked identity for 2h idle (`age.agent-timeout`); the
cache is purged at boot, on AGE USB key removal, and on agent restart. See
`AGENTS.md` for the full caching lifecycle.

Externals hit GitHub's rate limit — use an authenticated token:

```bash
GITHUB_TOKEN=$(gopass show -o perso/token/github.com/5fc4238e-6370-4187-bbd7-f8f05c5dfff5) chezmoi apply --source ~/repository/github.com/tdesaules/chez-moi
```

## Steam

### Launch options

Pour les jeux clavier/souris (gamescope active le fullscreen + cursor grab) :

```bash
gamescope -f -w 2880 -h 1800 -W 2880 -H 1800 --force-grab-cursor -- mangohud %command%
```

Pour les jeux à la manette — **ne pas utiliser gamescope** (bug connu :
ValveSoftware/gamescope#1180, #1687, #2080 — gamescope en mode nested ne
forward pas les events gamepad via Steam Input) :

```bash
mangohud %command%
```
