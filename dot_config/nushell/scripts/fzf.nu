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

def get-system-commands [include_history: bool] {
    let env_cmds = (scope commands | where type == "custom" or type == "alias" | get name | str trim)
    let path_bins = ($env.PATH
        | split row (char esep)
        | where { |it| $it | path exists }
        | each { |it|
            try {
                glob ($it | path join "*")
                | where { |f| (try { ($f | path type) in ["file", "symlink"] } catch { false }) and ($f !~ '\.(so|dll|dylib|a|lib|pdb)(?:\.[0-9]+)*$') }
                | path basename
            } catch { [] }
        } | flatten)
    let system_cmds = ([$env_cmds, $path_bins] | flatten | uniq | sort)
    if $include_history {
        let history_lines = (history | get command | reverse | str trim | where { |it| ($it | is-not-empty) })
        return ([$system_cmds, $history_lines] | flatten | uniq)
    } else {
        return $system_cmds
    }
}

def path-explorer [current_arg: string, cmd: string, is_cd: bool] {
    mut active_path = ""
    if ($current_arg | is-empty) {
        $active_path = ""
    } else if (try { ($current_arg | path expand | path type) == "dir" } catch { false }) {
        $active_path = (if ($current_arg | str ends-with "/") { $current_arg } else { $"($current_arg)/" })
    } else {
        let d = ($current_arg | path dirname)
        $active_path = (if $d == "." or $d == "" { "" } else if $d == "/" { "/" } else { $"($d)/" })
    }
    mut is_first_run = true
    loop {
        let search_path = if ($active_path | is-empty) { "" } else { $active_path }
        let normal_files = (try { glob $"($search_path)*" } catch { [] })
        let hidden_files = (try { glob $"($search_path).*" } catch { [] })
        mut candidates = ($normal_files | append $hidden_files | uniq | where { |it| let b = ($it | path basename); $b != "." and $b != ".." }
            | each { |it|
                let type = (try { $it | path expand | path type } catch { "file" })
                if $is_cd and $type != "dir" { return null }
                if $type == "dir" { $"(ansi light_blue)($it)/(ansi reset)" } else { $"(ansi white)($it)(ansi reset)" }
            } | where { $in != null })
        if ($active_path | is-not-empty) { $candidates = ($candidates | prepend $"(ansi green)($active_path)(ansi reset)(char tab)__current__") }
        let query = (if $is_first_run { $is_first_run = false; if ($current_arg | str ends-with "/") { "" } else { $current_arg | path basename } } else { "" })
        let fzf_out = ($candidates | str join (char nl) | fzf --height 30% --layout reverse --border --delimiter (char tab) --with-nth 1 --prompt $"($cmd) ($active_path) > " --ansi --expect "tab,right,left" --query $query --select-1 --exit-0 --exact)
        if ($fzf_out | is-empty) { return "" }
        let fzf_lines = ($fzf_out | lines)
        let key = ($fzf_lines | get 0)
        let selection_raw = ($fzf_lines | get -o 1 | default "")
        let picked = ($selection_raw | ansi strip | split row (char tab) | first)
        if $key == "left" {
            let parent = (if ($active_path | is-empty) { "../" } else { let d = ($active_path | str replace -r '/$' '' | path dirname); if $d == "." { "" } else if $d == "/" { "/" } else { $"($d)/" } })
            $active_path = $parent
            continue
        }
        if ($selection_raw | str contains "__current__") { return $active_path }
        if $key == "" { return $picked }
        if $key in ["tab", "right"] { if ($picked | str ends-with "/") { $active_path = $picked } else { return $picked } }
    }
}

export def bin-completion [] {
    let context = (commandline)
    let clean_context = ($context | str trim -r)
    let is_arg_mode = ($context =~ '\s')
    let quote_if_needed = { |val| if ($val | str contains " ") and not ($val | str starts-with '"') and not ($val | str starts-with "'") { $"\"($val)\"" } else { $val } }
    if not $is_arg_mode {
        if ($context | str starts-with "/") or ($context | str starts-with "./") or ($context | str starts-with "~/") {
            let selection = (path-explorer $context "Cmd" false)
            if ($selection | is-empty) { return }
            commandline edit --replace $"((do $quote_if_needed $selection)) "
        } else {
            let system_cmds = (get-system-commands false | str join (char nl))
            let selection = ($system_cmds | fzf --height 30% --layout reverse --border --query $context --prompt "Cmd > " --no-info --ansi --tiebreak=index --select-1 --exit-0 --exact | str trim)
            if ($selection | is-empty) { return }
            commandline edit --replace $"($selection) "
        }
        return
    }
    let parts = ($clean_context | split row -r ' +(?=(?:[^"]*"[^"]*")*[^"]*$)')
    let cmd = ($parts | first)
    let current_arg = (if ($context | str ends-with " ") { "" } else { $parts | last | str replace -a '"' '' | str replace -a "'" '' })
    let spec_path = ($nu.home-dir | path join ".config" "usage" "specs" $"($cmd).usage.kdl")
    if ($spec_path | path exists) {
        try {
            let spec = (usage generate json --file $spec_path | from json)
            let base_args = (if ($context | str ends-with " ") { $parts } else { $parts | drop 1 })
            let target_node = ($base_args | skip 1 | reduce -f ($spec.cmd? | default {}) { |arg, acc|
                let clean = ($arg | str replace -a '"' '' | str replace -a "'" '')
                let next = ($acc.subcommands? | default {} | get -o $clean)
                if ($next | is-empty) { $acc } else { $next }
            })
            let to_b64 = { |data| $data | to json --raw | encode base64 | str replace -a "\n" "" }
            let sub_cmds = ($target_node.subcommands? | default {} | transpose name data | each { |it| { value: $it.name, payload: (do $to_b64 $it.data) } })
            let flags = ($target_node.flags? | default [] | each { |f| let b64 = (do $to_b64 $f); ($f.long? | default [] | each { |l| { value: $"--($l)", payload: $b64 } }) | append ($f.short? | default [] | each { |s| { value: $"-($s)", payload: $b64 } }) } | flatten)
            let options = ($sub_cmds | append $flags | each { |it| $"($it.value)(char tab)($it.payload)" })
            if ($options | is-not-empty) {
                let preview_cmd = "B64={2} nu -c '$env.B64 | decode base64 | decode utf-8 | from json | to yaml' | bat --style=plain --color=always --language yaml"
                let selection = ($options | str join (char nl) | fzf --height 30% --layout reverse --border --delimiter (char tab) --with-nth 1 --ansi --preview $preview_cmd --preview-window "right:75%:wrap" --bind "alt-up:preview-up,alt-down:preview-down" --prompt $"($cmd) > " --query $current_arg --select-1 --exit-0 --exact)
                if ($selection | is-empty) { return }
                let val = (do $quote_if_needed ($selection | str trim | split row (char tab) | first))
                let suffix = (if ($val | str ends-with "/") { "" } else { " " })
                let new_line = (if ($context | str ends-with " ") { $"($context | str trim -r) ($val)" } else { $"($parts | drop 1 | str join ' ') ($val)" })
                commandline edit --replace $"($new_line | str trim)($suffix)"
                return
            }
        } catch { return }
    }
    let selection = (path-explorer $current_arg $cmd ($cmd == "cd"))
    if ($selection | is-not-empty) {
        let val = (do $quote_if_needed $selection)
        let suffix = (if ($val | str ends-with "/") { "" } else { " " })
        let new_line = (if ($context | str ends-with " ") { $"($context | str trim -r) ($val)" } else { $"($parts | drop 1 | str join ' ') ($val)" })
        commandline edit --replace $"($new_line | str trim)($suffix)"
    }
}

export def file-completion [] {
    let context = (commandline)
    let clean_context = ($context | str trim -r)
    let is_arg_mode = ($context =~ '\s')
    let quote_if_needed = { |val| if ($val | str contains " ") and not ($val | str starts-with '"') and not ($val | str starts-with "'") { $"\"($val)\"" } else { $val } }
    if not $is_arg_mode {
        if ($context | str starts-with "/") or ($context | str starts-with "./") or ($context | str starts-with "~/") {
            let selection = (path-explorer $context "Run" false)
            if ($selection | is-empty) { return }
            commandline edit --replace $"((do $quote_if_needed $selection)) "
        } else {
            let combined = (get-system-commands true | str join (char nl))
            let selection = ($combined | fzf --height 30% --layout reverse --border --query $context --prompt "Run > " --no-info --ansi --tiebreak=index --select-1 --exit-0 --exact | str trim)
            if ($selection | is-empty) { return }
            commandline edit --replace $"($selection) "
        }
        return
    }
    let parts = ($clean_context | split row -r ' +(?=(?:[^"]*"[^"]*")*[^"]*$)')
    let cmd = ($parts | first)
    let current_arg = (if ($context | str ends-with " ") { "" } else { $parts | last | str replace -a '"' '' | str replace -a "'" '' })
    let selection = (path-explorer $current_arg $cmd ($cmd == "cd"))
    if ($selection | is-not-empty) {
        let val = (do $quote_if_needed $selection)
        let suffix = (if ($val | str ends-with "/") { "" } else { " " })
        let new_line = (if ($context | str ends-with " ") { $"($context | str trim -r) ($val)" } else { $"($parts | drop 1 | str join ' ') ($val)" })
        commandline edit --replace $"($new_line | str trim)($suffix)"
    }
}
