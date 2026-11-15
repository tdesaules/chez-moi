import json
import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from check_release_assets import targets
from ci_common import increment, validate_receipts
from plan_ci import changed_files
import ci_common
import plan_ci
from publish_source_release import is_latest
import publish_source_release
import dispatch_release


class ReleaseContractTests(unittest.TestCase):
    def test_dispatch_rejects_wrong_ref_before_network(self):
        with patch.dict(os.environ, GITHUB_REF="refs/heads/other", GITHUB_EVENT_NAME="push"), \
                patch("dispatch_release.api") as api:
            with self.assertRaises(ValueError):
                dispatch_release.main()
            api.assert_not_called()

    def test_old_release_cannot_replace_latest(self):
        releases = [{"tag_name": "2.0.0", "draft": False, "prerelease": False},
                    {"tag_name": "3.0.0", "draft": True, "prerelease": False}]
        self.assertFalse(is_latest("1.5.1", releases))
        self.assertTrue(is_latest("2.0.0", releases))

    def test_publication_paginates_and_updates_idempotently(self):
        version = "1.5.1"
        records = [{"tag_name": "1.0.0", "draft": False, "prerelease": False}] * 100
        newer = {"tag_name": "2.0.0", "draft": False, "prerelease": False}
        for exists in (True, False):
            with self.subTest(exists=exists), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / ".build").mkdir()
                (root / ".build/plan.json").write_text(json.dumps({
                    "mode": "publish", "version": version, "source_sha": "abc"}))
                responses = [
                    {"object": {"type": "tag", "sha": "tag"}},
                    {"object": {"type": "commit", "sha": "abc"}},
                    records, [newer],
                    {"id": 7} if exists else HTTPError("url", 404, "missing", {}, None),
                    {"html_url": "https://github.com/owner/repo/releases/tag/1.5.1"},
                ]
                with patch.object(publish_source_release, "ROOT", root), \
                        patch("publish_source_release.git", return_value="abc"), \
                        patch("publish_source_release.validate_receipts"), \
                        patch("publish_source_release.write_json"), \
                        patch("publish_source_release.subprocess.check_output", return_value="## [1.5.1]"), \
                        patch("publish_source_release.api", side_effect=responses) as api, \
                        contextlib.redirect_stdout(io.StringIO()):
                    publish_source_release.main()
                self.assertEqual(api.call_args_list[3].args[0], "releases?per_page=100&page=2")
                self.assertEqual(api.call_args.kwargs["method"], "PATCH" if exists else "POST")
                self.assertEqual(api.call_args.args[1]["make_latest"], "false")

    def test_bump_policy(self):
        for messages, previous, expected in [
            (["feat: feature"], "1.2.3", "minor"),
            (["fix: bug"], "1.2.3", "patch"),
            (["perf: faster"], "1.2.3", "patch"),
            (["docs: wording", "ci: jobs"], "1.2.3", ""),
            (["docs!: change"], "1.2.3", "major"),
            (["chore: migrate\n\nBREAKING CHANGE: configuration moved"], "1.2.3", "major"),
            (["fix: bug", "feat: feature"], "1.2.3", "minor"),
            (["feat!: change"], "0.2.3", "minor"),
        ]:
            with self.subTest(messages=messages):
                self.assertEqual(increment(messages, previous), expected)

    def test_asset_coverage_is_derived_not_counted(self):
        url = "https://github.com/owner/tool/releases/download/1.2.3/a.tar.gz"
        assets, _, _ = targets(url, {"owner/tool"})
        self.assertEqual(len(assets), 1)
        with self.assertRaises(ValueError):
            targets(url, {"owner/tool", "owner/missing"})

    def test_diff_preserves_spaces_and_deleted_paths(self):
        with patch("plan_ci.git", side_effect=["", "old name\0new name\0deleted\0"]):
            self.assertEqual(changed_files("a" * 40, "b" * 40),
                             ["old name", "new name", "deleted", ""])

    def test_missing_history_fails(self):
        with patch("plan_ci.git", side_effect=ValueError("missing history")):
            with self.assertRaises(ValueError):
                changed_files("a" * 40, "b" * 40)

    def test_receipts_require_complete_matching_success(self):
        plan = {"source_sha": "abc", "test_matrix": {"include": [
            {"arch": "amd64"}, {"arch": "arm64"}]}}
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, GITHUB_RUN_ID="42"):
            for arch in ("amd64", "arm64"):
                Path(directory, f"{arch}.json").write_text(json.dumps({
                    "arch": arch, "source_sha": "abc", "run_id": "42", "tested": True}))
            validate_receipts(plan, directory)
            Path(directory, "arm64.json").unlink()
            with self.assertRaises(ValueError):
                validate_receipts(plan, directory)
            Path(directory, "arm64.json").write_text(json.dumps({
                "arch": "arm64", "source_sha": "other", "run_id": "42", "tested": True}))
            with self.assertRaises(ValueError):
                validate_receipts(plan, directory)
            Path(directory, "arm64.json").write_text(json.dumps({
                "arch": "arm64", "source_sha": "abc", "run_id": "42", "tested": False}))
            with self.assertRaises(ValueError):
                validate_receipts(plan, directory)


class PlanEventTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.original_root = ci_common.ROOT
        shutil.copyfile(self.original_root / "cliff.toml", self.root / "cliff.toml")
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null",
                        GIT_AUTHOR_NAME="test", GIT_AUTHOR_EMAIL="test@example.invalid",
                        GIT_COMMITTER_NAME="test", GIT_COMMITTER_EMAIL="test@example.invalid")
        self.run_git("init", "-b", "main")
        (self.root / "README.md").write_text("# Fixture\n")
        self.run_git("add", ".")
        self.run_git("-c", "commit.gpgsign=false", "commit", "-m", "docs: initial")
        self.source = self.run_git("rev-parse", "HEAD")

    def run_git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, env=self.env,
                                       stderr=subprocess.DEVNULL, text=True).strip()

    def plan(self, mode, ref="refs/heads/main", inputs=None, before="0" * 40):
        event = self.root / "event.json"
        event.write_text(json.dumps({"inputs": inputs or {}, "before": before}))
        event_name = "workflow_dispatch" if mode == "prepare" else "push"
        with patch.object(ci_common, "ROOT", self.root), patch.object(plan_ci, "ROOT", self.root), \
                patch.dict(os.environ, dict(self.env, INPUT_MODE=mode, GITHUB_REF=ref,
                           GITHUB_EVENT_NAME=event_name, GITHUB_EVENT_PATH=str(event),
                           GITHUB_OUTPUT=str(self.root / "outputs"), GITHUB_RUN_ID="42")):
            with contextlib.redirect_stdout(io.StringIO()):
                plan_ci.main()
        return json.loads((self.root / ".build/plan.json").read_text())

    def test_initial_preparation_is_explicit(self):
        plan = self.plan("prepare")
        self.assertFalse(plan["has_release"])
        self.assertFalse(plan["has_tests"])
        plan = self.plan("prepare", inputs={"first_release": "true"})
        self.assertEqual(plan["version"], "1.0.0")
        self.assertEqual(len(plan["test_matrix"]["include"]), 2)

    def test_wrong_ref_and_stale_source_fail(self):
        with self.assertRaises(ValueError):
            self.plan("prepare", ref="refs/heads/other")
        with self.assertRaises(ValueError):
            self.plan("prepare", inputs={"source_sha": "f" * 40})
        with self.assertRaises(ValueError):
            self.plan("publish", ref="refs/tags/v1.0.0")

    def test_empty_development_plan(self):
        plan = self.plan("development", before=self.source)
        self.assertFalse(plan["has_lint"])
        self.assertFalse(plan["has_tests"])
        self.assertFalse(plan["has_images"])

    def test_git_cliff_bump_and_changelog(self):
        self.run_git("-c", "tag.gpgsign=false", "tag", "-a", "1.0.0", "-m", "initial")
        for subject, expected in [
            ("perf: improve startup", "1.0.1"),
            ("feat: new profile", "1.1.0"),
            ("docs!: change setup\n\nBREAKING CHANGE: migrate setup", "2.0.0"),
        ]:
            self.run_git("-c", "commit.gpgsign=false", "commit", "--allow-empty", "-m", subject)
            plan = self.plan("prepare")
            self.assertEqual(plan["version"], expected)
        notes = subprocess.check_output([
            "git-cliff", "--config", "cliff.toml", "--tag", "2.0.0"],
            cwd=self.root, env=self.env, text=True)
        self.assertIn("BREAKING", notes)
        self.assertIn("### Added", notes)
        self.assertIn("### Changed", notes)
        self.assertIn("/compare/1.0.0...2.0.0", notes)


if __name__ == "__main__":
    unittest.main()
