"""Promote a fully qualified source revision to an annotated SemVer tag."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

from ci_common import ROOT, STABLE, git, require_main, validate_receipts, write_json


def main():
    require_main()
    plan = json.loads((ROOT / ".build/plan.json").read_text())
    version, source = plan["version"], plan["source_sha"]
    if plan["mode"] != "prepare" or not STABLE.fullmatch(version):
        raise ValueError("Invalid preparation plan")
    if source != git("rev-parse", "HEAD"):
        raise ValueError("Checkout differs from qualified source")
    validate_receipts(plan, ROOT / ".build/qualified")
    if git("status", "--porcelain", "--untracked-files=no"):
        raise ValueError("Release requires a clean checkout")
    # No credentials are persisted to the remote or repository configuration.
    with tempfile.TemporaryDirectory(prefix="release-auth-") as directory:
        askpass = Path(directory) / "askpass"
        askpass.write_text('#!/bin/sh\ncase "$1" in *Username*) echo x-access-token ;; *) printf "%s\\n" "$CI_TOKEN" ;; esac\n')
        askpass.chmod(0o700)
        env = dict(os.environ, GIT_ASKPASS=str(askpass), GIT_TERMINAL_PROMPT="0")
        repository = os.environ["GITHUB_REPOSITORY"]
        remote = f"https://github.com/{repository}.git"

        def authenticated(*args):
            return subprocess.check_output(
                ["git", "-c", f"safe.directory={ROOT}", "-c", "credential.helper=", *args],
                cwd=ROOT, env=env, text=True).strip()

        if authenticated("ls-remote", remote, "refs/heads/main").split()[0] != source:
            raise ValueError("main advanced; refusing stale release")
        if authenticated("ls-remote", remote, f"refs/tags/{version}"):
            raise ValueError("Tag already exists; refusing to move it")
        subprocess.run(["git-cliff", "--config", "cliff.toml", "--tag", version,
                        "--output", "CHANGELOG.md"], cwd=ROOT, check=True)
        git("add", "--", "CHANGELOG.md")
        if git("diff", "--cached", "--name-only") != "CHANGELOG.md":
            raise ValueError("Unexpected staged release changes")
        git("-c", "user.name=chez-moi release bot", "-c", "user.email=release@users.noreply.github.com",
            "-c", "commit.gpgsign=false", "commit", "-m", f"chore(release): prepare {version}",
            "-m", f"Record the qualified source {source} and its user-facing release notes.")
        git("-c", "user.name=chez-moi release bot", "-c", "user.email=release@users.noreply.github.com",
            "-c", "tag.gpgsign=false", "tag", "-a", version, "-m", f"Release {version}\n\nQualified source: {source}")
        # Lease on main plus an atomic new-tag push closes the external-writer race.
        authenticated("push", "--atomic", f"--force-with-lease=refs/heads/main:{source}",
                      remote, "HEAD:refs/heads/main", f"refs/tags/{version}:refs/tags/{version}")
        write_json(".build/release.json", {
            "mode": "prepare", "source_sha": source,
            "final_sha": git("rev-parse", "HEAD"), "version": version,
        })
        print(f"Prepared {version}; the tag workflow owns publication")


if __name__ == "__main__":
    main()
