# Check rendered assets

Fixed Go entrypoint for `.github/scripts/check_release_assets.py`.
Takes a read-only GitHub token through the action environment. Resolves URLs
from actual templates and derives coverage from dependency annotations.
Requests have timeouts and bounded retries; GitHub release metadata is reused.
Coverage regression: `.github/scripts/test_ci.py`.
Reports: `.build/reports/assets.json`.
See [bridge lifecycle](../../CI.md#temporary-source-action-bridge).
