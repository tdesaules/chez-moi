# Changelog

All notable changes are documented using [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

## [1.1.0] - 2026-11-21

### Added

- Adopt the validated Fedora 45 Files runtime

- Contrast the tab sidebar with a Snow Storm page canvas

- Install Helm alongside kubectl

- Install OpenTofu and Terraform

### Changed

- List fuzzy path candidates in one pass

### Fixed

- Opencode config

- Hide unwanted OpenAI models

- Bind the path explorer to the builtin ls

- Expose only the Steam launcher

- Name the owning tab from its starting directory

- Remove the page shadow from the bottom gutter

- Qualify the full tree after a branch rewrite

- Skip Terra bootstrap on subsequent starts

- Launch Big Picture windowed at the display scale

- Keep Fedora 45 usable across Quay manifest rotations

- Recognize the hosted Ubuntu 26.04 runner in actionlint

[1.1.0]: https://github.com/tdesaules/chez-moi/compare/1.0.0...1.1.0

## [1.0.0] - 2026-11-15

### Added

- Init repository and first chezmoi tasks

- Update niri external screen location

- Add auto pull lemonade service

- Update method pull models

- Add lemonade models to download

- Add antigravity google ai agent and install hugging face cli to download models

- Try a custom local folder directory

- Replace downloader service to use buildin script to retrieve huggingface models

- Remove gemma models

- Split topgrade configuration

- Add z.ai chat web app

- Disable some app visibility in launcher and remove z.ai icon border

- Add danklinux vault plugin to add integration with dank launcher and gopass

- Add gopass-jsonapi

- Add new gopass-dank plugin

- Add gopass and opencode configuration and adapt niri app rules to handle gopass-dank plugin

- Change gopass dank shell plugin windows size

- Configure gopass git helper

- Add 24h cache

- Add lemonade local provider to opencode

- Clean some AI models and add new one

- Add delete function and hf token with gopass in hf download script

- Add opencode token

- Try to set a cache on gopass

- Tempo add pinentry-tty to unlock gopass secret store

- Change the way to retrieve gopass-dank archive

- Add github token for mise and update gopassDank plugin name to gopassDms

- Add pinentry-dms plugin and refresh external config

- Update fastfetch configuration

- Auto refresh plugins

- Add umans ai provider

- Configure external screen

- Add usb key with secret identities to unlock gopass

- Add qrcode to log into github

- Add OpenRouter opencode provider

- Add butane cli

- Add beszel podman quadlet service to host hub

- Add beszel login setup

- Configure qemu

- Change qemu bridge subnet

- Update llm models list

- Add beszel agent and change publish to register internal vms

- Export Beszel secrets in gopass and expose it for the system

- Add passgen alias

- Add poolside provider and local laguna models

- Remap variant cycle keybind to alt+t

- Enable lemonade auto_evict for dynamic VRAM management

- Add scaleway provider via built-in + auth.json

- Add floating window rule for gopass view secret

- Configure new opencode provider

- Try bypass anthro limitation

- Add mise package

- Remove anthropic

- Remove old models from downloader

- Enable gemini in opencode

- Add llmgateway provider

- Add Omnissa Horizon Client container

- Remove some models

- Add opencode git workflkow skill

- Enable models in opencode

- Clean some models

- Grant steam controller access in distrobox

- Enable steam-streaming + lan-transfer services

- Add -pipewire flag for wayland screen capture

- Add orcaslicer, freecad, librecad appimage containers

- Add thales identity override for gitlab.thalesdigital.io remotes

- Update opencode llmgateway models

- Clean opencode provider

- Insert dash in middle of passgen output

- Switch local HF models to Muse-Glimmer-30B Q8_0

- Test provider

- Enable opencode ne provider

- Short bounded zellij tab names and pre-0.45 pane frames

- Fix zellij tab name width to 24 chars

- Fix zellij tab width to 15 with [...] ellipsis

- Widen zellij tab width to 20

- Enable new opencode models

- Add claude-fable and remove fugu models in opencode

- Add OpenSCAD snapshot in distrobox

- Prototype a modular 5U SBC rack

- Update model list

- Open Big Picture from the application launcher

- Add craft-distrobox container and pin app versions in apps.yaml

- Recolor Craft app SVGs with Nord palette

- Enable 1M context and upgrade to GPT-6.1 Sol

- Add on-demand Ornith server and Dank launcher

- Add Nord system tray indicator for Dank

- Show health popup on tray click

- Add Qwen and Unsloth Muse servers with tray launchers

- Enable vision with the BF16 projector

- Integrate LibrePCB with a Nord icon

- Scope identities and gopass tokens by target

- Integrate Niri Tonic Files

- Add Devoteam organization identity

- Enable submodule recursion for GitHub repositories

- Replace local models with DealignAI Q4_K_M builds

- Separate Devoteam and Thales browser profiles

- Unify Nord Dark styling and profile accents

### Fixed

- Lemonde server volume mounted

- Pull models

- Chez moi refresh systemd service

- Fcitx issue switching keyboard

- Antigravity github repo

- Kcl extract command

- Adapt chezmoi file extension

- Delete old chezmoi script

- Remove systemd dependency file

- Topgrade configuration

- Small bugs

- Small bugs notification timeout and dedicated class to isolate gemini web

- Add dedicated class to "chromium" web app

- Webapp status icon

- Assh configuration

- Try to add an age daemon cache

- Gopass age agent fix

- Resume download

- Enable gopassDank plugin by default

- Remove usless provider in opencode

- Bracket issue

- Second try on escape

- Double quote

- Github sugnature issue with mise and update ai agent informations

- Try to fix gopass passphrase cache

- Restore age agent systemd service

- Restart gopass agent when usb key is inserted

- Add an include and change chezmoi scripts order

- Distrobox container burst log issue

- Openrouter token api

- Same

- Script refacto issue during mise init tools install

- Fix; gh auth

- Auto start quadlet containers feature

- Inline local password

- Allow mdns

- Allow vm to access beszel hub

- Old beszel socket

- Beszel agent status

- Firewall beszel hub activation

- Nushell warning depression

- Gihub auth

- Gopass init issue

- Also add beszel key in env var

- Plugin path

- Wrong llm models name

- Gopass handler loop

- Tolerate Omnissa RPM post-script failures

- Add Omnissa Horizon runtime dependencies

- Reliable USB removal lock + 2h idle cache

- Workaround gopass age agent re-prompt loop (gopass#3488/#3509)

- Self-heal age agent stuck unlocked-but-empty

- List new models in opencode

- Grant raw USB access for Steam Controller firmware update

- Grant serial port access for Steam Controller bootloader

- Grant uinput + valve event devices access for steam input

- Trigger input+misc subsystems for uinput and event devices

- Replace non-nord colors in svg logos

- Add missing opengl and webkitgtk deps for orcaslicer

- Opencode json file

- Clean models list

- Migrate settings to schema 18

- Harden bootstrap and local services

- Scope secrets and restore bootstrap

- Remove desktop system monitor

- Repair automatic tab naming

- Hide unused spotlight actions

- Keep password fields on French layout

- Share Bibata with distroboxes

- Restore French keyboard via niri xkb fallback and fcitx5 defaults

- Drop trailing-space padding from tab names

- Full PWD tab names left-truncated to 16 chars

- Json formating

- Force software GL for orcaslicer

- Preserve hardware streaming support across rebuilds

- Validate app updates and track pinned DMS plugins

- Delegate Quadlet updates to Podman

- Disable automatic Podman updates

- Use the OpenCode 2 distribution backend

- Disable the standalone Zed update step

- Disable rustup updates

- Disable unused package update steps

- Use GTK file chooser under Niri

- Size GTK portal dialogs as floating windows

- Load DMS colors for application dialogs

- Soften Nord dialog borders and text states

- Remove unused mistral-vibe tool

- Use Vulkan shared memory for KV cache

- Expose local server on port 50501

- Query health once when opening tray menu

- Show connection address instead of health status

- Deploy skills from the flattened repository

- Correct desktop launcher executable

- Update author names and moved token paths

- Limit credential caching to 15 minutes

- Configure credentials for Devoteam account repositories

- Propagate service failures and recover secrets safely

- Retain working downloads until replacements succeed

- Preserve shell paths and resolve home directories

- Migrate V2 settings without losing UI preferences

- Correct invalid application launcher metadata

- Avoid repeating OAuth after bootstrap script updates

[1.0.0]: https://github.com/tdesaules/chez-moi/releases/tag/1.0.0
