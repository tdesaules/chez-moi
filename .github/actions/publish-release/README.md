# Publish source release

Fixed Go entrypoint for `.github/scripts/publish_source_release.py`.
Reconciles complete tag-run receipts and the remote annotated tag against the
immutable source plan. Creates or updates matching notes idempotently; only the
newest stable version becomes latest. Paginates the existing release inventory.
The catalog 1.6.3 publisher lacks these update/latest controls.
Receipt/bump/latest regression tests live in `.github/scripts/test_ci.py`.
See [bridge lifecycle](../../CI.md#temporary-source-action-bridge).
