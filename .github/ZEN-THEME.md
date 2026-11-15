# Zen Nord Dark

Original shared CSS theme for Perso, Devoteam and Thales, verified in Zen 1.23b.
The built-in theme can still appear as “System theme — auto” in the Add-ons
manager: Nord is applied through userChrome/userContent, not an extension.

## Visual roles

| Role | Colors |
| --- | --- |
| Main surfaces | Nord1 `#3b4252` |
| Fields, cards, menus, dialogs | Nord2 `#434c5e` |
| Hover and selected surfaces | Nord3 `#4c566a` |
| Secondary, normal and heading text | `#d8dee9`, `#e5e9f0`, `#eceff4` |
| Icons, focus, borders, selection tint, scrollbars | Frost `#8fbcbb`, `#88c0d0`, `#81a1c1`, `#5e81ac` |
| Perso accent | Aurora green `#a3be8c` |
| Devoteam accent (`work` directory) | Aurora orange `#d08770` |
| Thales accent | Aurora purple `#b48ead` |
| Errors/close hover and warnings | Aurora red `#bf616a`, yellow `#ebcb8b` |

Aurora is a small profile signature: selected-tab edge, workspace indicator and
internal-page heading underline. It does not flood toolbars or selected tabs.
Frost is shared across profiles. Nord0 is reserved for shadows and color mixing.
Snow Storm text on all three main surfaces has a minimum contrast ratio of about
5.46:1. Links use Snow Storm text with Frost decoration; pale Frost fills do not
receive low-contrast white labels.

The theme covers chrome, sidebar/workspaces, tabs/folders, URL suggestions,
toolbars/bookmarks, menus, permission panels, downloads, notifications, findbar,
Library trees, Glance/split-view controls and internal pages (settings, Add-ons,
new tab, home, configuration, etc.). Native geometry and compact mode remain
under Zen's control. Favicons, emoji and contextual-identity colors are retained.

## Fonts

- **Geist Sans**: controls and normal text. Its installed family name is **Geist**.
  The CSS fallback order is `"Geist", "Geist Sans", sans-serif`.
- **Geist Mono**: URL bar, address suggestions, status URLs, code and preference data.
- **Comfortaa 600**: workspace/folder labels and internal-page headings, matching
  DankMaterialShell's configured display family and weight.

All three families were found under `/usr/local/share/fonts` inside
`zen-distrobox`, and the actual glyph faces were verified in Gecko using
`InspectorUtils.getUsedFontFaces`. No remote font import or duplicate font install
is needed on this machine. Other hosts need these fonts installed; fallbacks apply.

## Source and deployment

- `.chezmoidata/zen.yaml`: palette, fonts, profile accents and persistent preferences.
- `.chezmoitemplates/zen/`: shared token, chrome, internal-page and preference templates.
- `dot_zen/{perso,work,thales}/`: thin wrappers retaining the existing profile paths.

The dark inputs are `zen.view.window.scheme=0`, `ui.systemUsesDarkTheme=1` and
`layout.css.prefers-color-scheme.content-override=0`. Firefox's derived
`browser.theme.toolbar-theme`/`content-theme` preferences are not managed.
Default dark canvas/text colors also use Nord; authored website colors still win.

Internal-page CSS excludes `about:blank` and `about:srcdoc`: websites use those
URLs for editors and embedded frames. HTTP(S) pages, their fonts and their
authored colors are not restyled. They receive the normal dark-mode preference.

Preview and apply only the three managed profiles:

```sh
chezmoi diff --source ~/repository/github.com/tdesaules/chez-moi --exclude=scripts \
  ~/.zen/perso ~/.zen/work ~/.zen/thales
chezmoi apply --source ~/repository/github.com/tdesaules/chez-moi --exclude=scripts \
  ~/.zen/perso ~/.zen/work ~/.zen/thales
```

Fully close and reopen each profile afterward: CSS and `user.js` are loaded at
startup. Browsing data, sessions, extensions and generated Zen workspace files
are not managed by this theme.

## Verification

The generic CI suite renders all profiles and checks distinct Aurora accents,
persistent dark inputs and text contrast. For real-browser integration on the
desktop with `zen-distrobox` already running:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 .github/scripts/verify_zen_theme.py
```

This creates disposable profiles under `.build/zen-theme`, launches separate
headless processes and enables automation only there. It verifies actual chrome,
selected-tab colors, fonts/glyph faces, workspace typography, popup state/colors,
settings/Add-ons/new-tab backgrounds, CSS parsing and website/frame isolation.
Only those test processes are closed; the temporary profiles are removed.
Reports and chrome/settings screenshots remain under `.build/zen-theme`.
Native popup windows are checked through computed styles, not screenshots.

## Research references

- [Official Nord palette and semantic roles](https://www.nordtheme.com/docs/colors-and-palettes)
- [Zen's official userChrome guide](https://docs.zen-browser.app/guides/live-editing)
- [Zen 1.23b theme variables and dark-scheme preference](https://github.com/zen-browser/desktop/blob/1.23b/src/zen/common/styles/zen-theme.css)
- [Zen workspace styling](https://github.com/zen-browser/desktop/blob/1.23b/src/zen/spaces/zen-workspaces.css)
- [Vercel Geist families and licensing](https://vercel.com/font)
- [Comfortaa description from Google Fonts](https://github.com/google/fonts/blob/main/ofl/comfortaa/DESCRIPTION.en_us.html)
- [Mozilla content color-scheme preference](https://developer.mozilla.org/en-US/docs/Mozilla/Add-ons/WebExtensions/API/browserSettings/overrideContentColorScheme)
- [Mozilla default dark canvas colors](https://github.com/mozilla-firefox/firefox/blob/main/modules/libpref/init/StaticPrefList.yaml)
