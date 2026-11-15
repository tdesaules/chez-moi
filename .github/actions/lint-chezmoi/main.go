package main

import (
	"fmt"
	"os"
	"os/exec"
	"syscall"
)

func main() {
	if len(os.Args) != 1 {
		fmt.Fprintln(os.Stderr, "unexpected arguments")
		os.Exit(2)
	}
	if info, err := os.Stat("."); err == nil && os.Getuid() == 0 {
		stat := info.Sys().(*syscall.Stat_t)
		if err := syscall.Setgid(int(stat.Gid)); err != nil {
			panic(err)
		}
		if err := syscall.Setuid(int(stat.Uid)); err != nil {
			panic(err)
		}
	}
	cmd := exec.Command("python3", ".github/scripts/lint_dotfiles.py")
	cmd.Stdout, cmd.Stderr = os.Stdout, os.Stderr
	if err := cmd.Run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
