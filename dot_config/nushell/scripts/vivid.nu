# vivid.nu

export-env {
    let config_path = ($nu.home-dir | path join ".config" "vivid" "nord.config")
    $env.LS_COLORS = (open $config_path | str trim)
    $env.EZA_COLORS = "sn=38;5;146:sb=38;5;146:da=38;5;109:ur=38;5;109:uw=38;5;174:ux=38;5;150"
}
