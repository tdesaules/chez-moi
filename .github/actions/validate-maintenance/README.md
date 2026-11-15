# Validate maintenance event

Static Go executable with a scratch runtime. Accepts only schedule or manual
dispatch on `main`. No inputs, filesystem writes or network access.
`main_test.go` exercises valid/invalid event/ref combinations.
See [bridge lifecycle](../../CI.md#temporary-source-action-bridge).
