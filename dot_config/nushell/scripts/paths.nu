# paths.nu

export-env {
    $env.ENV_CONVERSIONS = {
        "PATH": {
            from_string: { |s| $s | split row (char esep) | path expand --no-symlink }
            to_string: { |v| $v | str join (char esep) }
        }
        "Path": {
            from_string: { |s| $s | split row (char esep) | path expand --no-symlink }
            to_string: { |v| $v | str join (char esep) }
        }
    }
    let current_path = if ($env.PATH | describe) =~ "list" {
        $env.PATH
    } else {
        $env.PATH | split row (char esep)
    }
    $env.PATH = (
        $current_path
        | prepend ($nu.home-dir | path join ".local" "bin")
        | append "/usr/local/bin"
        | append "/usr/local/sbin"
        | append "/usr/bin"
        | append "/usr/sbin"
        | append ($nu.home-dir | path join ".local" "share" "flatpak" "exports" "bin")
        | append "/var/lib/flatpak/exports/bin"
        | uniq
    )
}
