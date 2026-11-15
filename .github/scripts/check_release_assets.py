"""Check annotated release dependencies against rendered download URLs."""
import json
import os
from pathlib import Path
import re
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]


def fetch(url, api=False):
    headers = {"Accept": "application/vnd.github+json"} if api else {}
    if api and (token := os.environ.get("GITHUB_TOKEN")):
        headers["Authorization"] = f"Bearer {token}"
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers=headers, method="GET" if api else "HEAD"),
                         timeout=30) as response:
                return json.load(response) if api else None
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(2 ** attempt)


def render(name):
    return subprocess.run([
        "chezmoi", "execute-template", "--source", str(ROOT), "--config", "/dev/null",
        "--config-format", "toml", "--override-data",
        '{"chezmoi":{"arch":"amd64","osRelease":{"id":"fedora","versionID":"44"}}}',
    ], input=(ROOT / name).read_text(), text=True, capture_output=True,
        check=True, timeout=30).stdout


def targets(text, declared):
    assets = re.findall(
        r"https://github.com/([^/]+/[^/]+)/releases/download/([^/]+)/([^\s\"']+)", text)
    archives = re.findall(r"https://github.com/([^/]+/[^/]+)/archive/([^/\s]+)\.tar\.gz", text)
    observed = {repo for repo, _, _ in assets} | {repo for repo, _ in archives}
    official = re.findall(r"https://(?:download\.librepcb\.org|files\.openscad\.org)/[^\s\"']+", text)
    if any("download.librepcb.org/" in url for url in official):
        observed.add("LibrePCB/LibrePCB")
    if missing := declared - observed:
        raise ValueError(f"Dependencies absent from rendered URLs: {sorted(missing)}")
    if not assets:
        raise ValueError("No rendered release assets")
    return sorted(set(assets)), sorted(set(archives)), sorted(set(official))


def main():
    declared = set()
    for path in ("apps.yaml", "plugins.yaml"):
        declared.update(re.findall(r"# renovate: depName=(\S+)",
                                  (ROOT / ".chezmoidata" / path).read_text()))
    assets, archives, official = targets(
        render("dot_config/distrobox/distrobox.ini.tmpl") + render(".chezmoiexternal.toml"),
        declared)
    results, releases = [], {}

    def check(label, operation):
        try:
            operation()
            results.append({"target": label, "status": "passed"})
            print(f"OK {label}", flush=True)
        except Exception as error:
            results.append({"target": label, "status": "failed", "error": str(error)})
            print(f"FAIL {label}: {error}", flush=True)

    def asset(repo, tag, filename):
        key = (repo, tag)
        if key not in releases:
            releases[key] = fetch(
                f"https://api.github.com/repos/{repo}/releases/tags/{quote(tag, safe='')}", api=True)
        if filename not in {entry["name"] for entry in releases[key]["assets"]}:
            raise ValueError(f"Missing asset {filename}")

    for repo, tag, filename in assets:
        check(f"{repo}@{tag}/{filename}", lambda r=repo, t=tag, f=filename: asset(r, t, f))
    for repo, ref in archives:
        check(f"{repo}@{ref}", lambda r=repo, t=ref: fetch(
            f"https://api.github.com/repos/{r}/commits/{quote(t, safe='')}", api=True))
    for url in official:
        check(url, lambda u=url: fetch(u))
    report = ROOT / ".build/reports/assets.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(results, indent=2) + "\n")
    if any(result["status"] != "passed" for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
