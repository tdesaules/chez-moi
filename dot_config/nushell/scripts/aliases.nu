# aliases.nu

export def --env home [] {
    cd $env.HOME
}

export def wlc [...args: string] {
    wl-copy ...$args
}

export def wlp [...args: string] {
    wl-paste ...$args
}

export def book [...args: string] {
    bookokrat ...$args
}

export def cat [...args: string] {
    bat --style=plain ...$args
}

export def df [...args: string] {
    dust ...$args
}

export def du [...args: string] {
    duf ...$args --json | from json
}

export def la [...args: string] {
    eza -a --icons=always --color=always --group-directories-first ...$args
}

export def ll [...args: string] {
    eza -l --icons=always --color=always --git --group-directories-first ...$args
}

export def lla [...args: string] {
    eza -la --icons=always --color=always --git --group-directories-first ...$args
}

export def ls [...args: string] {
    eza --icons=always --color=always ...$args
}

export def lzg [...args: string] {
    lazygit ...$args
}

export def pass [...args: string] {
    gopass ...$args
}

export def ping [...args: string] {
    gping ...$args
}

export def top [...args: string] {
    btop ...$args
}

export def tree [...args: string] {
    eza --tree --icons=always --color=always ...$args
}
