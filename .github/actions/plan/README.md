# Plan dotfiles qualification

Fixed Go entrypoint for `.github/scripts/plan_ci.py`.
Input: `mode` (`development`, `prepare`, `publish`). Produces `.build/plan.json`
and the scalar/matrix outputs declared in `action.yml`.
Tests: `PlanEventTests` and `ReleaseContractTests` in `.github/scripts/test_ci.py`.
Rejects missing history, wrong events/refs, invalid tags and stale source requests.
See [bridge lifecycle](../../CI.md#temporary-source-action-bridge).
