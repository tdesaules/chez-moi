# zellij.nu - short tab names: last 2 path components, bounded width

export def --env setup-zellij-tab [] {
    if ($env.ZELLIJ_TAB_HOOK_SETUP? | default false) { return }
    $env.ZELLIJ_TAB_HOOK_SETUP = true
    _zellij_add_hook hooks.pre_prompt { condition: { "ZELLIJ" in $env }, code: { _zellij_rename_tab } }
    _zellij_add_hook hooks.env_change.PWD { condition: { "ZELLIJ" in $env }, code: { _zellij_rename_tab } }
}

def --env _zellij_add_hook [field: cell-path, new_hook: record] {
    let cell = ($field | split cell-path | update optional true | into cell-path)
    let old_hooks = ($env.config | get $cell | default [])
    $env.config = ($env.config | upsert $cell ($old_hooks ++ [$new_hook]))
}

def _zellij_rename_tab [] {
    let max_len = 15
    let ellipsis = "[...]"
    let keep = $max_len - ($ellipsis | str length -g)
    let home = $nu.home-dir
    let dir = if ($env.PWD == $home) {
        "~"
    } else {
        let rel = ($env.PWD | str replace $home "~")
        let parts = ($rel | path split | where {|x| $x != "/" and $x != "~" })
        let short = if ($rel | str starts-with "~") {
            ["~"] ++ ($parts | last 1)
        } else {
            $parts | last 2
        }
        if ($short | is-empty) { "/" } else { $short | path join }
    }
    let truncated = if (($dir | str length -g) > $max_len) {
        $ellipsis + ($dir | str reverse | str substring 0..($keep - 1) | str reverse)
    } else {
        $dir
    }
    let name = ($truncated | fill -a left -c ' ' -w $max_len)
    try { ^zellij action rename-tab $name } catch { }
}
