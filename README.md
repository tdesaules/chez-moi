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

Externals hit GitHub's rate limit — use an authenticated token:

```bash
GITHUB_TOKEN=$(gopass show -o perso/token/github.com/5fc4238e-6370-4187-bbd7-f8f05c5dfff5) chezmoi apply --source ~/repository/github.com/tdesaules/chez-moi
```

## Steam

```bash
gamescope -f -W 1920 -H 1200 -w 2880 -h 1800 -- mangohud %command%
```
