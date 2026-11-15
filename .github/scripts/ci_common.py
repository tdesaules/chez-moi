"""Shared IO for fixed-operation CI actions; no runtime operation dispatcher."""
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
STABLE = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


def git(*args, strip=True):
    result = subprocess.check_output(
        ["git", "-c", f"safe.directory={ROOT}", *args],
        cwd=ROOT, text=True)
    return result.strip() if strip else result


def output(name, value):
    if isinstance(value, (dict, list)):
        value = json.dumps(value, separators=(",", ":"))
    elif isinstance(value, bool):
        value = str(value).lower()
    with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
        stream.write(f"{name}={value}\n")


def write_json(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def api(path, payload=None, method=None):
    repository = os.environ["GITHUB_REPOSITORY"]
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
        raise ValueError("Invalid repository")
    request = Request(f"https://api.github.com/repos/{repository}/{path}",
                      data=json.dumps(payload).encode() if payload is not None else None,
                      method=method, headers={
                          "Authorization": f"Bearer {os.environ['CI_TOKEN']}",
                          "Accept": "application/vnd.github+json",
                          "X-GitHub-Api-Version": "2022-11-28",
                      })
    with urlopen(request, timeout=30) as response:
        data = response.read()
        return json.loads(data) if data else None


def previous_version():
    tags = [tag for tag in git("tag", "--merged", "HEAD").splitlines() if STABLE.fullmatch(tag)]
    return max(tags, key=lambda tag: tuple(map(int, tag.split("."))), default="")


def increment(messages, previous):
    """Select intent independently of changelog filtering; breaking always wins."""
    rank = 0
    for message in messages:
        subject = message.splitlines()[0] if message else ""
        if re.match(r"^[A-Za-z]+(?:\([^)]*\))?!:", subject) or re.search(
                r"(?m)^BREAKING[ -]CHANGE:\s*\S", message):
            rank = max(rank, 3)
        elif re.match(r"(?i)^feat(?:\([^)]*\))?:", subject):
            rank = max(rank, 2)
        elif re.match(r"(?i)^(fix|perf)(?:\([^)]*\))?:", subject):
            rank = max(rank, 1)
    if rank == 3 and previous.startswith("0."):
        rank = 2
    return {0: "", 1: "patch", 2: "minor", 3: "major"}[rank]


def require_main():
    if os.environ["GITHUB_REF"] != "refs/heads/main":
        raise ValueError("Manual preparation and maintenance require main")


def validate_receipts(plan, directory):
    records = [json.loads(path.read_text()) for path in Path(directory).glob("*.json")]
    expected = {entry["arch"] for entry in plan["test_matrix"]["include"]}
    actual = [record.get("arch") for record in records]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError("Missing or duplicate qualification receipts")
    for record in records:
        if (record.get("source_sha") != plan["source_sha"]
                or record.get("run_id") != os.environ["GITHUB_RUN_ID"]
                or record.get("tested") is not True):
            raise ValueError("Unqualified or mismatched source receipt")
