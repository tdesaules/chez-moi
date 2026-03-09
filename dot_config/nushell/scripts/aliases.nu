# aliases.nu

export def --env home [] {
    cd $env.HOME
}

export def --wrapped wlc [...args: string] {
    wl-copy ...$args
}

export def --wrapped wlp [...args: string] {
    wl-paste ...$args
}

export def --wrapped book [...args: string] {
    bookokrat ...$args
}

export def --wrapped cat [...args: string] {
    bat --style=plain ...$args
}

export def --wrapped la [...args: string] {
    eza -a --icons=always --color=always --group-directories-first ...$args
}

export def --wrapped ll [...args: string] {
    eza -l --icons=always --color=always --group-directories-first ...$args
}

export def --wrapped lla [...args: string] {
    eza -la --icons=always --color=always --group-directories-first ...$args
}

export def --wrapped ls [...args: string] {
    eza --icons=always --color=always --group-directories-first ...$args
}

export def --wrapped lzg [...args: string] {
    lazygit ...$args
}

export def --wrapped pass [...args: string] {
    gopass ...$args
}

export def --wrapped top [...args: string] {
    btop ...$args
}

export def --wrapped tree [...args: string] {
    eza --tree --icons=always --color=always ...$args
}

export def --wrapped lemonade [...args: string] {
    podman exec -it lemonade-server /opt/lemonade/lemonade ...$args
}
