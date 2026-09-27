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

## OpenSCAD

OpenSCAD runs in `openscad-distrobox` using a pinned official snapshot AppImage
(x86_64), with a desktop launcher and an exported `openscad` command.
The launcher uses XWayland (`QT_QPA_PLATFORM=xcb`): this AppImage bundles Qt
without its Wayland platform plugin. For GUI launches from the terminal, use
`env QT_QPA_PLATFORM=xcb openscad`.

To update, change the version, AppImage URL and SHA256 in
`.chezmoidata/openscad.yaml` using https://openscad.org/downloads.html#snapshots.
The Distrobox onchange script tracks this file. Keep the previous values to
roll back to an earlier snapshot.

After previewing the changes, deploy only the relevant files and assemble OpenSCAD:

```bash
chezmoi apply --source ~/repository/github.com/tdesaules/chez-moi --exclude scripts \
  ~/.config/distrobox/distrobox.ini ~/.config/distrobox/openscad.desktop \
  ~/.local/share/icons/openscad.svg
distrobox assemble create --file ~/.config/distrobox/distrobox.ini --name openscad-distrobox
update-desktop-database ~/.local/share/applications
```

A full `chezmoi apply` runs the shared assembly script for all declared Distroboxes.

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
