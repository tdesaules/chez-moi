# fzf.nu
export-env {
    $env.FZF_DEFAULT_COMMAND = "fd --type f --hidden --exclude .git --strip-cwd-prefix --color=always"
    $env.FZF_DEFAULT_OPTS = "--ansi --color=bg+:#3B4252,bg:#2E3440,spinner:#81A1C1,hl:#616E88 --color=fg:#D8DEE9,header:#616E88,info:#81A1C1,pointer:#81A1C1 --color=marker:#81A1C1,fg+:#D8DEE9,prompt:#81A1C1,hl+:#81A1C1"
}

export def --env fcd [...args: string] {
    if ($args | is-empty) {
        let dir = (fd --type d --hidden --exclude .git | fzf --prompt="Search   " | decode utf-8 | str trim)
        if ($dir != "") { cd $dir }
        return
    }
    let query = ($args | str join ' ')
    let matches = (fd --type d --hidden --exclude .git -g $"*($query)*" | lines)
    let match_count = ($matches | length)
    if $match_count == 0 {
        print $"No directory found : ($query)"
    } else if $match_count == 1 {
        cd ($matches | first)
    } else {
        let selected = ($matches | str join (char nl) | fzf --prompt="Search   " --query $query | decode utf-8 | str trim)
        if ($selected != "") { cd $selected }
    }
}

export def --env fvi [...args: string] {
    if ($args | is-empty) {
        let file = (fzf --prompt="Search   " | decode utf-8 | str trim)
        if ($file != "") { vi $file }
        return
    }
    let query = ($args | str join ' ')
    let matches = (fd --type f --hidden --exclude .git -g $"*($query)*" | lines)
    let match_count = ($matches | length)
    if $match_count == 0 {
        print $"No file found : ($query)"
    } else if $match_count == 1 {
        vi ($matches | first)
    } else {
        let selected = ($matches | str join (char nl) | fzf --prompt="Search   " --query $query | decode utf-8 | str trim)
        if ($selected != "") { vi $selected }
    }
}

export def --env fkill [...args: string] {
    if ($args | is-empty) {
        let target = (ps | each { |row| $"($row.pid) ($row.name)" } | str join (char nl) | fzf --prompt="Search   " | split row " " | first)
        if ($target != "") { kill -f ($target | into int) }
        return
    }
    let query = ($args | str join ' ')
    let matches = (ps | where name =~ $query)
    let match_count = ($matches | length)
    if $match_count == 0 {
        print $"No process found : ($query)"
    } else if $match_count == 1 {
        let target_pid = ($matches | first | get pid)
        kill -f ($target_pid | into int)
    } else {
        let selected = ($matches | each { |row| $"($row.pid) ($row.name)" } | str join (char nl) | fzf --prompt="Search   " --query $query | split row " " | first)
        if ($selected != "") { kill -f ($selected | into int) }
    }
}

export def --env fls [...args: string] {
    if ($args | is-empty) {
        let selected = (fd --hidden --exclude .git | fzf --prompt="Search   " | decode utf-8 | str trim)
        if ($selected != "") {
            let result = ($selected | path expand)
            $result | wl-copy
            return $result
        }
        return
    }
    let query = ($args | str join ' ')
    let matches = (fd --hidden --exclude .git -g $"*($query)*" | lines)
    let match_count = ($matches | length)
    if $match_count == 0 {
        print $"No item found : ($query)"
    } else if $match_count == 1 {
        let result = (($matches | first) | path expand)
        $result | wl-copy
        return $result
    } else {
        let selected = ($matches | str join (char nl) | fzf --prompt="Search   " --query $query | decode utf-8 | str trim)
        if ($selected != "") {
            let result = ($selected | path expand)
            $result | wl-copy
            return $result
        }
    }
}

export def --env fcat [...args: string] {
    if ($args | is-empty) {
        let selected = (fd --type f --hidden --exclude .git | fzf --prompt="Search   " --preview 'bat --style=plain --color=always {}' --preview-window=right:60% | decode utf-8 | str trim)
        if ($selected != "") {
            let content = (open --raw $selected | into string)
            $content | wl-copy
            print $"Content of ($selected) copied to clipboard."
        }
        return
    }
    let query = ($args | str join ' ')
    let matches = (fd --type f --hidden --exclude .git -g $"*($query)*" | lines)
    if ($matches | length) == 0 {
        print $"No files found matching: ($query)"
    } else {
        let selected = ($matches | str join (char nl) | fzf --prompt="Search   " --query $query --preview 'bat --style=plain --color=always {}' --preview-window=right:60% | decode utf-8 | str trim)
        if ($selected != "") {
            let content = (open --raw $selected | into string)
            $content | wl-copy
            print $"Content of ($selected) copied to clipboard."
        }
    }
}

export def fbin-discover [] {
    let context = (commandline)
    let clean_context = ($context | str trim -r)
    let is_arg_mode = ($context =~ '\s')
    let quote_if_needed = { |val|
        if ($val | str contains " ") and not ($val | str starts-with '"') { $"\"($val)\"" } else { $val }
    }
    let apply_selection = { |selection, parts, context|
        let val = (do $quote_if_needed $selection)
        let suffix = (if ($val | str ends-with "/") { "" } else { " " })

        let new_line = if ($context | str ends-with " ") {
            $"($context | str trim -r) ($val)"
        } else {
            let base = ($parts | drop 1 | str join " ")
            if ($base | is-empty) { $val } else { $"($base) ($val)" }
        }
        commandline edit --replace $"($new_line | str trim)($suffix)"
    }
    if not $is_arg_mode {
        let env_cmds = (scope commands | where type == "custom" or type == "alias" | get name | str trim)
        let path_bins = ($env.PATH | split row (char esep) | where { |it| $it | path exists } | each { |it| glob ($it | path join "*") | where { |f| ($f | path type) == "file" } | path basename } | flatten | str trim)
        let history_lines = (history | get command | reverse | str trim | where { |it| ($it | is-not-empty) })
        let combined = ($history_lines | append $env_cmds | append $path_bins | uniq | str join (char nl))
        let selection = ($combined | fzf --height 30% --layout reverse --border --query $context --prompt "Run > " --no-info --ansi | str trim)
        if ($selection | is-not-empty) { commandline edit --replace $"($selection) " }
    } else {
        let parts = ($clean_context | split row -r ' +(?=(?:[^"]*"[^"]*")*[^"]*$)')
        if ($parts | is-empty) { return }
        let cmd = ($parts | first)
        let raw_arg = (if ($context | str ends-with " ") { "" } else { $parts | last })
        let current_arg = ($raw_arg | str replace -a '"' '' | str replace -a "'" '')
        let base_args = (if ($context | str ends-with " ") { $parts } else { $parts | drop 1 })
        let spec_path = ($nu.home-dir | path join ".config" "usage" "specs" $"($cmd).usage.kdl")
        let has_spec = ($spec_path | path exists)
        let usage_options = if $has_spec {
            try {
                let spec = (usage generate json --file $spec_path | from json)
                let root_cmd = ($spec.cmd? | default {})
                let target_node = ($base_args | skip 1 | reduce -f $root_cmd { |arg, acc|
                    let clean_arg = ($arg | str replace -a '"' '' | str replace -a "'" '')
                    let next = ($acc.subcommands? | default {} | get -o $clean_arg)
                    if ($next | is-empty) { $acc } else { $next }
                })
                let to_b64 = { |data| $data | to json --raw | encode base64 | str replace -a "\n" "" }
                let sub_cmds = ($target_node.subcommands? | default {} | transpose name data | each { |it| { value: $it.name, payload: (do $to_b64 $it.data) } })
                let flags = ($target_node.flags? | default [] | each { |f|
                    let b64 = (do $to_b64 $f)
                    ($f.long? | default [] | each { |l| { value: $"--($l)", payload: $b64 } })
                    | append ($f.short? | default [] | each { |s| { value: $"-($s)", payload: $b64 } })
                } | flatten)
                $sub_cmds | append $flags | each { |it| $"($it.value)(char tab)($it.payload)" }
            } catch { [] }
        } else { [] }
        if ($usage_options | is-not-empty) {
            let preview_cmd = "B64={2} nu -c '$env.B64 | decode base64 | decode utf-8 | from json | to yaml' | bat --style=plain --color=always --language yaml"
            let selection = ($usage_options | str join (char nl) | fzf --height 30% --layout reverse --border --delimiter (char tab) --with-nth 1 --ansi --preview $preview_cmd --preview-window "right:75%:wrap" --prompt $"($cmd) > " --query $current_arg)
            if ($selection | is-not-empty) {
                let val = ($selection | str trim | split row (char tab) | first)
                do $apply_selection $val $parts $context
            }
        } else {
            let is_cd = ($cmd == "cd")
            mut active_path = if ($current_arg | is-empty) { "" } else if (try { ($current_arg | path type) == "dir" } catch { false }) {
                if ($current_arg | str ends-with "/") { $current_arg } else { $"($current_arg)/" }
            } else {
                let dir = ($current_arg | path dirname | str replace -r '^\.$' '')
                if ($dir | is-empty) { "" } else { $"($dir)/" }
            }
            mut is_first_run = true
            mut final_selection = ""
            loop {
                let search_pattern = if ($active_path | is-empty) { "{*,.*}" } else { $"($active_path){*,.*}" }
                mut candidates = (try {
                    glob $search_pattern
                    | where { |it| let b = ($it | path basename); $b != "." and $b != ".." }
                    | where { |it| if $is_cd { ($it | path type) == "dir" } else { true } }
                    | each { |it|
                        if ($it | path type) == "dir" { $"(ansi light_blue)($it)/(ansi reset)" } else { $"(ansi white)($it)(ansi reset)" }
                    }
                } catch { [] })
                $candidates = ($candidates | prepend $"(ansi yellow)../(ansi reset)")
                let query = (if $is_first_run { $is_first_run = false; $current_arg | path basename } else { "" })
                let fzf_out = ($candidates | str join (char nl) | fzf --height 30% --layout reverse --border --prompt $"($cmd) ($active_path) > " --ansi --expect "tab" --query $query)
                if ($fzf_out | is-empty) { break }
                let fzf_lines = ($fzf_out | lines)
                let key = ($fzf_lines | get 0)
                let selection = ($fzf_lines | get -o 1 | default "")
                let picked = ($selection | ansi strip)
                if $key == "" {
                    $final_selection = (if ($selection | is-empty) or ($picked == "../") { $active_path } else { $picked })
                    break
                }
                if $key == "tab" {
                    if ($selection | is-empty) { continue }
                    if $picked == "../" {
                        $active_path = (if ($active_path | is-empty) or ($active_path | str ends-with "../") { $"($active_path)../" } else { $active_path | str replace -r '[^/]+/?$' '' })
                    } else if ($picked | str ends-with "/") {
                        $active_path = $picked
                    } else {
                        $final_selection = $picked
                        break
                    }
                }
            }
            if ($final_selection | is-not-empty) { do $apply_selection $final_selection $parts $context }
        }
    }
}
