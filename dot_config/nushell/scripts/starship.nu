# starship.nu

export-env {
    if (which starship | is-not-empty) {
        $env.STARSHIP_CONFIG = ($nu.home-dir | path join ".config" "starship" "config.toml")
        $env.STARSHIP_SHELL = "nu"
    }
}
