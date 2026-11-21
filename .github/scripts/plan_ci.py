"""Plan changed dotfiles checks or a complete source release."""
import json
import os
from pathlib import Path
import subprocess

from ci_common import ROOT, STABLE, git, increment, output, previous_version, require_main, write_json


def changed_files(before, after):
    if not before or set(before) == {"0"}:
        # A new branch conservatively qualifies the entire source.
        return git("ls-files", "-z", strip=False).split("\0")
    try:
        git("cat-file", "-e", before + "^{commit}")
    except subprocess.CalledProcessError:
        # Renovate may rewrite a branch: its old tip need not exist in a full clone.
        return git("ls-tree", "-r", "--name-only", "-z", after, strip=False).split("\0")
    return git("diff", "--name-only", "--no-renames", "-z", before, after, "--", strip=False).split("\0")


def main():
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    ref = os.environ["GITHUB_REF"]
    sha = git("rev-parse", "HEAD")
    mode = os.environ["INPUT_MODE"]
    if git("rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("Complete Git history is required")
    previous = previous_version()
    messages = git("log", "--format=%B%x00", f"{previous}..HEAD" if previous else "HEAD").split("\0")
    bump = increment([message.strip() for message in messages if message.strip()], previous)
    version, reason = "", ""
    if mode == "development":
        if os.environ["GITHUB_EVENT_NAME"] != "push" or not ref.startswith("refs/heads/"):
            raise ValueError("Development only accepts branch pushes")
        paths = changed_files(event.get("before", ""), sha)
    elif mode == "prepare":
        require_main()
        if os.environ["GITHUB_EVENT_NAME"] != "workflow_dispatch":
            raise ValueError("Preparation requires manual dispatch on main")
        if event.get("inputs"):
            raise ValueError("Release preparation accepts no version or source overrides")
        if not previous:
            raise ValueError("A reachable stable release tag is required")
        elif bump:
            version = subprocess.check_output(
                ["git-cliff", "--config", "cliff.toml", "--bumped-version"],
                cwd=ROOT, text=True).strip()
            if version == previous:
                raise ValueError("git-cliff did not increment the release version")
        else:
            reason = "No version-changing commits"
        paths = git("ls-files", "-z", strip=False).split("\0") if version else []
    elif mode == "publish":
        if os.environ["GITHUB_EVENT_NAME"] != "push" or not ref.startswith("refs/tags/"):
            raise ValueError("Publication requires a tag push")
        version = ref.removeprefix("refs/tags/")
        if not STABLE.fullmatch(version):
            raise ValueError("Expected stable SemVer without v prefix")
        if git("cat-file", "-t", ref) != "tag":
            raise ValueError("Release tag must be annotated")
        git("merge-base", "--is-ancestor", sha, "origin/main")
        paths = git("ls-files", "-z", strip=False).split("\0")
    else:
        raise ValueError("Unknown planning mode")
    if version and not STABLE.fullmatch(version):
        raise ValueError("Invalid git-cliff version")
    paths = sorted({path for path in paths if path})
    existing = [path for path in paths if (ROOT / path).is_file()]
    lint = []
    groups = {
        "actionlint": [p for p in existing if p.startswith(".github/workflows/") and p.endswith((".yml", ".yaml"))],
        "yaml": [p for p in existing if p.endswith((".yml", ".yaml"))],
        "markdownlint": [p for p in existing if p.endswith(".md")],
        "hadolint": [p for p in existing if p.endswith("/Containerfile")],
    }
    for name, files in groups.items():
        if files:
            lint.append({"id": name, "files": files, "runner": "ubuntu-24.04",
                         "action_path": f"lint/{name}"})
    runtime = bool(paths) and (
        mode != "development" or
        any(not p.endswith(".md") for p in paths))
    if runtime:
        lint.append({"id": "chezmoi", "files": existing, "runner": "ubuntu-24.04",
                     "action_path": ".github/actions/lint-chezmoi"})
    if "renovate.json" in existing:
        lint.append({"id": "renovate", "files": ["renovate.json"], "runner": "ubuntu-24.04",
                     "action_path": ".github/actions/validate-renovate"})
    tests = [{"arch": arch, "runner": runner} for arch, runner in (
        ("amd64", "ubuntu-24.04"), ("arm64", "ubuntu-24.04-arm"))] if runtime else []
    if mode == "development":
        tests = tests[:1]
    plan = {
        "schema_version": 1, "mode": mode, "source_sha": sha,
        "previous": previous, "version": version, "reason": reason,
        "files": paths, "comparison_before": event.get("before", ""),
        "has_lint": bool(lint), "has_images": False, "has_tests": bool(tests),
        "has_release": bool(version),
        "lint_matrix": {"include": lint}, "build_matrix": {"include": []},
        "test_matrix": {"include": tests},
        "plan_artifact": f"plan-{os.environ['GITHUB_RUN_ID']}",
        "has_assets": runtime and (mode != "development" or any(
            p.startswith((".chezmoidata/apps", ".chezmoidata/plugins", ".chezmoidata/openscad",
                          ".chezmoiexternal", ".chezmoitemplates/distrobox",
                          "dot_config/distrobox", ".github/scripts/check_release_assets"))
            for p in paths)),
    }
    write_json(".build/plan.json", plan)
    for key, value in plan.items():
        if key not in ("schema_version", "files", "comparison_before"):
            output(key, value)
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
