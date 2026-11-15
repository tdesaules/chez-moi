"""Run the repository's regression suite and emit a source-bound result."""
import os
import platform
import unittest
from ci_common import ROOT, git, write_json

suite = unittest.defaultTestLoader.discover(str(ROOT / ".github/scripts"), pattern="test_*.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
passed = result.wasSuccessful() and result.testsRun > 0 and not result.skipped
arch = {"x86_64": "amd64", "aarch64": "arm64"}[platform.machine()]
receipt = {
    "schema_version": 1, "source_sha": git("rev-parse", "HEAD"), "arch": arch,
    "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
    "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "local"),
    "tested": passed, "tests": result.testsRun,
    "failures": len(result.failures), "errors": len(result.errors),
}
write_json(f".build/qualified/{arch}.json", receipt)
raise SystemExit(0 if passed else 1)
