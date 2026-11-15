"""Request independent release qualification after a successful main chain."""
import os
from ci_common import api, git, require_main

def main():
    require_main()
    if os.environ["GITHUB_EVENT_NAME"] != "push":
        raise ValueError("Automatic preparation requires a main push")
    api("actions/workflows/release.yml/dispatches", {
        "ref": "main", "inputs": {"source_sha": git("rev-parse", "HEAD"), "first_release": "false"},
    })
    print("Requested independent release qualification")


if __name__ == "__main__":
    main()
