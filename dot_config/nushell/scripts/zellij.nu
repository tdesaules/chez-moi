# zellij.nu - tab names: full PWD, left-truncated with [...] to 16 chars

export def --env setup-zellij-tab [] {
    _zellij_add_hook hooks.pre_prompt { condition: { "ZELLIJ" in $env }, code: { _zellij_rename_tab } }
    _zellij_add_hook hooks.env_change.PWD { condition: { "ZELLIJ" in $env }, code: { _zellij_rename_tab } }
}

def --env _zellij_add_hook [field: cell-path, new_hook: record] {
    let cell = ($field | split cell-path | update optional true | into cell-path)
    let old_hooks = ($env.config | get $cell | default [])
    $env.config = ($env.config | upsert $cell ($old_hooks ++ [$new_hook]))
}

def _zellij_rename_tab [] {
    let max_len = 16
    let ellipsis = "[...]"
    let keep = $max_len - ($ellipsis | str length -g)
    let dir = $env.PWD
    let truncated = if (($dir | str length -g) > $max_len) {
        $ellipsis + ($dir | str reverse | str substring 0..($keep - 1) | str reverse)
    } else {
        $dir
    }
    try { ^zellij action rename-tab $truncated } catch { }
}
