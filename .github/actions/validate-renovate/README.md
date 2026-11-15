# Validate Renovate configuration

Fixed Go entrypoint invoking the strict validator from the exact immutable
Renovate image used by maintenance. Requires `renovate.json` in the workspace;
needs no token or Docker socket.
The final runtime inherits Fedora 45 from catalogue release 1.6.3.
See [bridge lifecycle](../../CI.md#temporary-source-action-bridge).
