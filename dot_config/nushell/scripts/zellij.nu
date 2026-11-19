# Name the tab once, from the shell's starting directory.
export def setup-zellij-tab [] {
    if ($env.ZELLIJ_PANE_ID? == null) { return }
    try {
        let pane_id = ($env.ZELLIJ_PANE_ID | into int)
        let tab_id = (^zellij action list-panes --tab --json | from json
            | where { |p| not $p.is_plugin and $p.id == $pane_id }
            | first | get tab_id)
        let name = ($env.PWD | path basename)
        ^zellij action rename-tab --tab-id $tab_id -- (if $name == "" { "/" } else { $name })
    } catch { }
}
