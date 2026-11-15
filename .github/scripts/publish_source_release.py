"""Reconcile tag qualification and publish idempotent, correctly ranked notes."""
import json
import subprocess
from urllib.error import HTTPError
from ci_common import ROOT, STABLE, api, git, validate_receipts, write_json


def is_latest(version, releases):
    stable = [record["tag_name"] for record in releases if not record["draft"]
              and not record["prerelease"] and STABLE.fullmatch(record["tag_name"])]
    key = lambda tag: tuple(map(int, tag.split(".")))
    return key(version) >= max(map(key, stable), default=(0, 0, 0))


def main():
    plan = json.loads((ROOT / ".build/plan.json").read_text())
    if plan["mode"] != "publish" or plan["source_sha"] != git("rev-parse", "HEAD"):
        raise ValueError("Expected a source-bound tag publication plan")
    validate_receipts(plan, ROOT / ".build/qualified")
    version = plan["version"]
    if not STABLE.fullmatch(version):
        raise ValueError("Expected stable SemVer")
    remote_ref = api(f"git/ref/tags/{version}")["object"]
    if remote_ref["type"] != "tag":
        raise ValueError("Remote release tag is not annotated")
    remote_tag = api(f"git/tags/{remote_ref['sha']}")["object"]
    if remote_tag["type"] != "commit" or remote_tag["sha"] != plan["source_sha"]:
        raise ValueError("Remote tag changed since qualification")
    notes = subprocess.check_output(
        ["git-cliff", "--config", "cliff.toml", "--current", "--strip", "header"],
        cwd=ROOT, text=True)
    if f"[{version}]" not in notes:
        raise ValueError("Release notes do not match tag")
    releases = []
    page = 1
    while True:
        records = api(f"releases?per_page=100&page={page}")
        releases.extend(records)
        if len(records) < 100:
            break
        page += 1
    payload = {"tag_name": version, "name": version, "body": notes,
               "draft": False, "prerelease": False,
               "make_latest": "true" if is_latest(version, releases) else "false"}
    try:
        existing = api(f"releases/tags/{version}")
    except HTTPError as error:
        if error.code != 404:
            raise
        existing = None
    release = api(f"releases/{existing['id']}" if existing else "releases",
                  payload, method="PATCH" if existing else "POST")
    write_json(".build/release.json", {
        "mode": "publish", "source_sha": plan["source_sha"], "version": version,
        "url": release["html_url"], "latest": payload["make_latest"] == "true",
    })
    print(release["html_url"])


if __name__ == "__main__":
    main()
