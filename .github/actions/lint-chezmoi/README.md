# Lint rendered chezmoi files

Fixed Go entrypoint for `.github/scripts/lint_dotfiles.py`.
Renders isolated profiles, checks generated formats, Bash syntax and error-level
ShellCheck findings. Emits `.build/reports/lint.json`, including failures.
Also checks Nushell 0.117.0, Niri 26.04 and desktop entries, generates Quadlet
units offline and runs systemd's verifier without starting any service.
Fixtures and convergence regressions live in `.github/scripts/test_dotfiles.py`.
See [bridge lifecycle](../../CI.md#temporary-source-action-bridge).
