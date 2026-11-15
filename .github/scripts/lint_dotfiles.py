"""Render before validating: templates are never treated as final config files."""
import ast
import json
import subprocess
import tomllib
import xml.etree.ElementTree as ET

from chezmoi_testlib import Fixture, ROOT
from ci_common import write_json


def main():
    errors, counts = [], {}
    for arch, tools in (("amd64", True), ("arm64", True), ("amd64", False)):
        fixture = Fixture(arch, tools)
        try:
            tomllib.loads(fixture.render(".chezmoi.toml.tmpl"))
            tomllib.loads(fixture.chezmoi(
                "execute-template", input=(ROOT / ".chezmoiexternal.toml").read_text()).stdout)
            for path in sorted(fixture.source.rglob("*")):
                if not path.is_file():
                    continue
                name = path.relative_to(fixture.source).as_posix()
                if name.startswith(".chezmoitemplates/") or name == ".chezmoi.toml.tmpl":
                    continue
                try:
                    text = path.read_text()
                except UnicodeDecodeError:
                    continue
                try:
                    if name.endswith(".tmpl"):
                        text = fixture.render(name)
                    if path.name.startswith("modify_"):
                        ast.parse(text)
                        continue
                    suffix = name.removesuffix(".tmpl")
                    if suffix.endswith(".json"):
                        json.loads(text)
                    elif suffix.endswith(".toml"):
                        tomllib.loads(text)
                    elif suffix.endswith(".svg"):
                        ET.fromstring(text)
                    if text.startswith(("#!/bin/bash", "#!/bin/sh")):
                        subprocess.run(["bash", "-n"], input=text, text=True,
                                       capture_output=True, check=True)
                        # Error-level baseline; stylistic warnings can be tightened
                        # independently without hiding parsing/control-flow errors.
                        subprocess.run(["shellcheck", "--severity=error", "-s", "bash", "-"],
                                       input=text, text=True, capture_output=True, check=True)
                    if text.startswith("#!/usr/bin/python3"):
                        ast.parse(text)
                    counts[f"{arch}:{tools}"] = counts.get(f"{arch}:{tools}", 0) + 1
                except subprocess.CalledProcessError as error:
                    errors.append({"file": name, "profile": f"{arch}:{tools}",
                                   "error": error.stdout + error.stderr})
                except Exception as error:
                    errors.append({"file": name, "profile": f"{arch}:{tools}", "error": str(error)})
            # Native validators inspect deployed names, not chezmoi attributes.
            # apply never executes the desktop scripts in this fixture.
            fixture.chezmoi("apply", "--exclude=scripts")
            for target in fixture.home.rglob("*.json"):
                json.loads(target.read_text())
            commands = [["niri", "validate", "--config", str(fixture.home / ".config/niri/config.kdl")]]
            commands.extend([["desktop-file-validate", str(path)]
                             for path in fixture.home.rglob("*.desktop")])
            for path in fixture.home.rglob("*.nu"):
                result = subprocess.run(
                    ["nu", "--no-config-file", "-c",
                     'if not (nu-check $env.CHECK_FILE) { error make {msg: "invalid Nushell source"} }'],
                    env=dict(fixture.env, CHECK_FILE=str(path)), text=True,
                    capture_output=True, timeout=30)
                if result.returncode:
                    errors.append({"file": str(path.relative_to(fixture.home)),
                                   "profile": f"{arch}:{tools}",
                                   "error": result.stdout + result.stderr})
            generated = fixture.base / "generated"
            generated.mkdir()
            generator = "/usr/lib/systemd/system-generators/podman-system-generator"
            unit_env = dict(fixture.env, QUADLET_UNIT_DIRS=str(
                fixture.home / ".config/containers/systemd"))
            commands.append([generator, "--user", "--no-kmsg-log",
                             str(generated), str(generated), str(generated)])
            for command in commands:
                result = subprocess.run(command, env=unit_env, text=True,
                                        capture_output=True, timeout=30)
                if result.returncode:
                    errors.append({"file": command[-1], "profile": f"{arch}:{tools}",
                                   "error": result.stdout + result.stderr})
            # Executable existence is checked without starting services.
            shims = fixture.home / ".local/share/mise/shims"
            shims.mkdir(parents=True, exist_ok=True)
            for name in ("gopass", "filen-cli"):
                stub = shims / name
                stub.write_text("#!/bin/sh\nexit 0\n")
                stub.chmod(0o755)
            units = fixture.home / ".config/systemd/user"
            unit_env["SYSTEMD_UNIT_PATH"] = f"{units}:{generated}:/usr/lib/systemd/user"
            result = subprocess.run(
                ["systemd-analyze", "--user", "verify", "--man=no", "--recursive-errors=no",
                 *map(str, sorted(units.glob("*.service"))),
                 *map(str, sorted(units.glob("*.path"))),
                 *map(str, sorted(generated.glob("*.service")))],
                env=unit_env, text=True, capture_output=True, timeout=30)
            if result.returncode:
                errors.append({"file": "systemd units", "profile": f"{arch}:{tools}",
                               "error": result.stdout + result.stderr})
        finally:
            fixture.close()
    for path in (ROOT / ".github/scripts").glob("*.py"):
        ast.parse(path.read_text(), filename=str(path))
    write_json(".build/reports/lint.json", {"checked": counts, "errors": errors})
    for error in errors:
        print(json.dumps(error), flush=True)
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
