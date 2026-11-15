# Qualify chezmoi source

Fixed Go entrypoint for `.github/scripts/qualify_dotfiles.py`.
Runs the repository's `test_*.py` suite. A failed, empty or skipped suite cannot
produce a successful qualification. Emits a native-architecture receipt tied
to the checkout and workflow run under `.build/qualified/`.
See [bridge lifecycle](../../CI.md#temporary-source-action-bridge).
