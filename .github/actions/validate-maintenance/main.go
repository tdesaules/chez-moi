package main

import (
	"fmt"
	"os"
)

func valid(ref, event string) bool {
	return ref == "refs/heads/main" && (event == "schedule" || event == "workflow_dispatch")
}

func main() {
	if len(os.Args) != 1 || !valid(os.Getenv("GITHUB_REF"), os.Getenv("GITHUB_EVENT_NAME")) {
		fmt.Fprintln(os.Stderr, "maintenance requires schedule or dispatch on main")
		os.Exit(1)
	}
}
