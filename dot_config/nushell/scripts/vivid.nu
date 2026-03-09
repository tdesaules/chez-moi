# vivid.nu

export-env {
    $env.LS_COLORS = (vivid generate ($nu.home-dir | path join ".config" "vivid" "nord.yml") | str trim)
}
