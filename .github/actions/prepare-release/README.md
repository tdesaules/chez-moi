# Prepare source release

Fixed Go entrypoint for `.github/scripts/prepare_source_release.py`.
Requires the check plan, complete native receipts and a repository-scoped bot App
token. Updates release notes, creates an annotated tag and atomically pushes it
with the release commit. Refuses source mismatches, partial evidence and races.
Receipt/bump regression tests live in `.github/scripts/test_ci.py`.
Git mutations are intentionally confined to this CI operation.
See [bridge lifecycle](../../CI.md#temporary-source-action-bridge).
