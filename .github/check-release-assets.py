"""Check the actual rendered download URLs against GitHub release assets."""
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.request import Request, urlopen

root = Path(__file__).resolve().parents[1]
template = (root / "dot_config/distrobox/distrobox.ini.tmpl").read_text()
rendered = subprocess.run(
    ["chezmoi", "execute-template", "--source", str(root), "--config", "/dev/null", "--config-format", "toml"],
    input=template, text=True, capture_output=True, check=True,
).stdout
external = subprocess.run(
    ["chezmoi", "execute-template", "--source", str(root), "--config", "/dev/null", "--config-format", "toml"],
    input=(root / ".chezmoiexternal.toml").read_text(),
    text=True, capture_output=True, check=True,
).stdout
headers = {"Accept": "application/vnd.github+json"}
if token := os.environ.get("GITHUB_TOKEN"):
    headers["Authorization"] = f"Bearer {token}"

matches = re.findall(
    r"https://github.com/([^/]+/[^/]+)/releases/download/([^/]+)/([^\s\"']+)",
    rendered + external,
)
assert len(matches) == 10, f"Expected nine applications and pinentry plugin, got {len(matches)}"
for repo, tag, filename in matches:
    with urlopen(Request(f"https://api.github.com/repos/{repo}/releases/tags/{tag}", headers=headers)) as response:
        release = json.load(response)
    assert filename in {asset["name"] for asset in release["assets"]}, f"Missing asset: {repo}@{tag}/{filename}"
    print(f"OK {repo}@{tag}/{filename}")

tag = re.search(r"gopass-dms/archive/([^/]+)\.tar\.gz", external).group(1)
with urlopen(Request(f"https://api.github.com/repos/tdesaules/gopass-dms/releases/tags/{tag}", headers=headers)):
    print(f"OK gopass-dms@{tag}")
