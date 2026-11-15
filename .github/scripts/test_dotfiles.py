"""Native chezmoi round-trip and regression tests; all side effects are isolated."""
import json
from pathlib import Path
import socket
import subprocess
import unittest

from chezmoi_testlib import Fixture


class DotfilesTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture()
        self.addCleanup(self.fixture.close)

    def test_round_trip_profiles(self):
        for arch, tools in [("amd64", True), ("arm64", True), ("amd64", False)]:
            with self.subTest(arch=arch, tools=tools):
                fixture = Fixture(arch, tools)
                try:
                    fixture.chezmoi("apply", "--exclude=scripts")
                    fixture.chezmoi("verify", "--exclude=scripts")
                    before = fixture.chezmoi("diff", "--exclude=scripts").stdout
                    self.assertEqual(before, "")
                    fixture.chezmoi("apply", "--exclude=scripts")
                    fixture.chezmoi("verify", "--exclude=scripts")
                    self.assertEqual(fixture.chezmoi("diff", "--exclude=scripts").stdout, "")
                    config = fixture.home / ".config/mise/config.toml"
                    self.assertEqual(config.stat().st_mode & 0o077, 0)
                    # verify must actually detect drift, not merely exit green.
                    config.write_text(config.read_text() + "\n# drift\n")
                    result = fixture.chezmoi("verify", "--exclude=scripts", check=False)
                    self.assertNotEqual(result.returncode, 0)
                finally:
                    fixture.close()

    def test_filen_uses_exact_home(self):
        self.fixture.data["chezmoi"]["homeDir"] = "/var/home/user with spaces"
        pairs = json.loads(self.fixture.render("dot_config/filen-cli/syncPairs.json.tmpl"))
        self.assertEqual(pairs[0]["local"], "/var/home/user with spaces/document")

    def test_opencode_preserves_terminal_preferences(self):
        f = self.fixture
        cli = f.home / ".config/opencode/cli.json"
        cli.parent.mkdir(parents=True)
        cli.write_text(json.dumps({
            "theme": {"mode": "system"}, "animations": False,
            "session": {"sidebar": "hide"}, "keybinds": {"app.exit": "ctrl+q"},
        }))
        f.chezmoi("apply", "--exclude=scripts")
        config = json.loads(cli.read_text())
        self.assertEqual(config["theme"], {"mode": "system", "name": "nord"})
        self.assertFalse(config["animations"])
        self.assertEqual(config["session"]["sidebar"], "hide")
        self.assertEqual(config["keybinds"]["app.exit"], "ctrl+q")
        self.assertEqual(config["keybinds"]["variant.cycle"], "alt+t")
        self.assertEqual(cli.stat().st_mode & 0o077, 0)
        f.chezmoi("verify", "--exclude=scripts")

    def test_git_identity_routes_https_and_ssh(self):
        f = self.fixture
        f.chezmoi("apply", "--exclude=scripts")
        data = json.loads(f.chezmoi("execute-template", input="{{ .git | toJson }}").stdout)
        repo = f.home / "repository with spaces"
        repo.mkdir()
        env = dict(f.env, GIT_CONFIG_NOSYSTEM="1")

        def git(*args):
            return subprocess.check_output(["git", "-C", str(repo), *args],
                                           env=env, text=True, stderr=subprocess.DEVNULL).strip()

        git("init", "-b", "main")
        for target in data["targets"].values():
            for pattern in target["urls"]:
                url = pattern.replace("**", "fixture.git").replace("*", "group")
                with self.subTest(url=url):
                    git("config", "--local", "remote.origin.url", url)
                    self.assertEqual(git("config", "user.email"), target["email"])
                    if url.startswith("https://"):
                        self.assertEqual(git("config", "--get-urlmatch", "credential.username", url),
                                         target["username"])
        git("config", "--local", "remote.origin.url", "https://example.invalid/repository.git")
        self.assertEqual(git("config", "user.email"), data["user"]["email"])

    def test_systemd_ignores_unmanaged_units_and_propagates_failure(self):
        f = self.fixture
        f.chezmoi("apply", "--exclude=scripts")
        units = f.home / ".config/systemd/user"
        (units / "personal.service").write_text("[Install]\nWantedBy=default.target\n")
        (f.source / "dot_config/containers/systemd/ignored.container.bak").write_text(
            "[Install]\nWantedBy=default.target\n")
        calls = f.base / "calls"
        f.env["CALLS"] = str(calls)
        f.mock("systemctl", """#!/bin/sh
printf '%s\\n' "$*" >> "$CALLS"
case "$*" in
  *LoadState*) echo not-found ;;
  *'enable filen-sync.service'*) exit 1 ;;
esac
""")
        result = f.run_script(".chezmoiscripts/run_onchange_after_01-systemd.sh.tmpl")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("personal.service", calls.read_text())
        self.assertNotIn("ignored.container", calls.read_text() + result.stdout)
        self.assertIn("enable filen-sync.service", calls.read_text())
        self.assertIn("restart gopass-age-agent.service", calls.read_text())

    def test_beszel_unavailable_is_retryable(self):
        f = self.fixture
        shim = f.home / ".local/share/mise/shims"
        shim.mkdir(parents=True)
        (shim / "gopass").symlink_to(f.bin / "gopass")
        f.mock("curl", "#!/bin/sh\nexit 22\n")
        f.mock("sleep", "#!/bin/sh\nexit 0\n")
        result = f.run_script(".chezmoiscripts/run_onchange_after_06-beszel-agent.sh.tmpl")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("readiness", result.stdout)

    def test_bootstrap_edit_does_not_repeat_oauth(self):
        f = self.fixture
        (f.home / ".local/share/gopass/stores/root/.git").mkdir(parents=True)
        unit = f.home / ".config/systemd/user/gopass-age-agent.service"
        unit.parent.mkdir(parents=True)
        unit.write_text("[Service]\n")
        f.mock("mise", "#!/bin/sh\nexit 17\n")
        result = f.run_script(".chezmoiscripts/run_once_before_02-gopass-bootstrap.sh.tmpl")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("already bootstrapped", result.stdout)

    def test_age_lock_failure_is_reported(self):
        f = self.fixture
        f.data["gopass"] = {"age": {
            "device": str(f.base / "absent-device"), "label": "AGE",
            "identity": ".config/gopass/age/identities",
        }}
        shim = f.home / ".local/share/mise/shims"
        shim.mkdir(parents=True)
        failed = f.mock("gopass-fail", "#!/bin/sh\nexit 1\n")
        (shim / "gopass").symlink_to(failed)
        identity = f.home / ".config/gopass/age/identities"
        identity.parent.mkdir(parents=True)
        identity.symlink_to(f.base / "absent-identity")
        agent_socket = Path(f.env["XDG_RUNTIME_DIR"]) / "gopass/gopass-age-agent.sock"
        agent_socket.parent.mkdir()
        with socket.socket(socket.AF_UNIX) as agent:
            agent.bind(str(agent_socket))
            f.mock("sleep", "#!/bin/sh\nexit 0\n")
            result = f.run_script("dot_local/bin/executable_gopass-age-usb-handler.tmpl", "stop")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unconfirmed", result.stdout)
        self.assertNotIn("secrets purged", result.stdout)
        self.assertFalse(identity.is_symlink())

    def test_distrobox_common_hook_changes_trigger(self):
        name = ".chezmoiscripts/run_onchange_after_04-distrobox.sh.tmpl"
        before = self.fixture.render(name)
        hook = self.fixture.source / ".chezmoitemplates/distrobox/common-hooks.tmpl"
        hook.write_text(hook.read_text() + '\ninit_hooks="true"\n')
        self.assertNotEqual(before, self.fixture.render(name))

    def test_hf_uses_download_result_and_preserves_orphans_on_failure(self):
        for failure in (False, True):
            with self.subTest(failure=failure):
                f = Fixture()
                self.addCleanup(f.close)
                directory = f.home / "models"
                directory.mkdir()
                old = directory / "old.gguf"
                old.write_text("old")
                cache = directory / ".hf-cache/models--owner--model/snapshots"
                for revision in ("aaa-old", "zzz-new"):
                    (cache / revision).mkdir(parents=True)
                    (cache / revision / "new.gguf").write_text(revision)
                f.env["MODEL_CONFIG"] = json.dumps({
                    "download_dir": str(directory),
                    "models": [{"repo": "owner/model", "file": "new.gguf"}],
                })
                f.env["SNAPSHOT"] = str(cache / "zzz-new/new.gguf")
                f.mock("kcl", '#!/bin/sh\nprintf "%s\\n" "$MODEL_CONFIG"\n')
                f.mock("sleep", "#!/bin/sh\nexit 0\n")
                f.mock("hf", "#!/bin/sh\n" + (
                    "exit 1\n" if failure else
                    'if [ "$1" = download ]; then printf "%s\\n" "$SNAPSHOT"; fi\n'))
                result = f.run_script("dot_local/bin/private_executable_pull-hf-models.tmpl")
                self.assertEqual(result.returncode, 1 if failure else 0, result.stderr)
                if failure:
                    self.assertTrue(old.exists())
                else:
                    self.assertEqual((directory / "new.gguf").read_text(), "zzz-new")
                    self.assertFalse(old.exists())

    def test_run_once_and_onchange_lifecycle(self):
        f = self.fixture
        # A tiny real source exercises chezmoi's state semantics, without invoking
        # any deployment script from the desktop configuration.
        import shutil
        shutil.rmtree(f.source)
        f.source.mkdir()
        once = f.source / "run_once_after_01-once.sh"
        change = f.source / "run_onchange_after_02-change.sh"
        log = f.base / "lifecycle"
        once.write_text(f"#!/bin/sh\necho once >> '{log}'\n")
        change.write_text(f"#!/bin/sh\necho change >> '{log}'\n")
        f.chezmoi("apply")
        f.chezmoi("apply")
        self.assertEqual(log.read_text().splitlines(), ["once", "change"])
        change.write_text(change.read_text() + "# new input\n")
        f.chezmoi("apply")
        self.assertEqual(log.read_text().splitlines(), ["once", "change", "change"])
        change.write_text("#!/bin/sh\nexit 1\n")
        self.assertNotEqual(f.chezmoi("apply", check=False).returncode, 0)
        self.assertNotEqual(f.chezmoi("apply", check=False).returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
