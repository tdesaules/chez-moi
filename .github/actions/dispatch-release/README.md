# Request release preparation

Fixed Go entrypoint for `.github/scripts/dispatch_release.py`.
Accepts an Actions-write job token and dispatches independent release
qualification for the exact successful main revision. Rejects other refs/events.
The dispatch endpoint is an exception to GitHub's usual job-token event suppression.
See [bridge lifecycle](../../CI.md#temporary-source-action-bridge).
