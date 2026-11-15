"""Isolated chezmoi fixtures. Never load the operator's config or password store."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
FLAGS = ("is_linux", "is_fedora", "is_mise", "is_nushell", "is_ssh",
         "is_systemd", "is_distrobox")


class Fixture:
    def __init__(self, arch="amd64", tools=True, spaced=False):
        self.temp = tempfile.TemporaryDirectory(prefix="chezmoi-test-")
        self.base = Path(self.temp.name)
        self.home = self.base / ("home with spaces" if spaced else "home")
        self.home.mkdir()
        self.source = self.base / "source"
        shutil.copytree(ROOT, self.source, ignore=shutil.ignore_patterns(
            ".git", ".build", "__pycache__", ".github", "repository"))
        # External archive transport is checked separately. An offline fixture
        # must never fetch mutable branches or execute downloaded content.
        (self.source / ".chezmoiexternal.toml").unlink()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.mock("gopass", """#!/bin/sh
case "$*" in
  *username) printf '%s\\n' 'audit@example.invalid' ;;
  *) printf '%s\\n' "$TEST_SECRET" ;;
esac
""")
        self.config = self.base / "chezmoi.json"
        self.config.write_text(json.dumps({"gopass": {"command": str(self.bin / "gopass")}}))
        self.data = {key: tools for key in FLAGS}
        self.data.update(is_linux=True, is_fedora=True)
        self.data["chezmoi"] = {
            "arch": arch, "os": "linux", "homeDir": str(self.home),
            "username": "audit", "osRelease": {"id": "fedora", "versionID": "44"},
        }
        # Do not forward credentials, Git configuration or session integration.
        self.env = {
            "PATH": f"{self.bin}:{os.environ['PATH']}", "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / ".config"),
            "XDG_CACHE_HOME": str(self.home / ".cache"),
            "XDG_DATA_HOME": str(self.home / ".local/share"),
            "XDG_RUNTIME_DIR": str(self.base / "run"),
            "TEST_SECRET": """fake'"\\$() % secret""",
            "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1",
        }
        Path(self.env["XDG_RUNTIME_DIR"]).mkdir()

    def close(self):
        self.temp.cleanup()

    def mock(self, name, text):
        path = self.bin / name
        path.write_text(text)
        path.chmod(0o755)
        return path

    def chezmoi(self, *args, input=None, check=True):
        return subprocess.run([
            "chezmoi", "--source", str(self.source),
            "--destination", str(self.home), "--config", str(self.config),
            "--persistent-state", str(self.base / "state.boltdb"),
            "--cache", str(self.base / "cache"),
            "--override-data", json.dumps(self.data), "--no-tty", *args,
        ], input=input, text=True, capture_output=True, env=self.env,
            check=check, timeout=60)

    def render(self, name):
        return self.chezmoi("execute-template", input=(self.source / name).read_text()).stdout

    def script(self, name):
        path = self.base / "script.sh"
        path.write_text(self.render(name))
        return path

    def run_script(self, name, *args):
        return subprocess.run(["bash", str(self.script(name)), *args],
                              text=True, capture_output=True, env=self.env, timeout=30)
