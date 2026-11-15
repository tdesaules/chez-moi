# CI and source releases

## Events and qualification

- `main.yml`: branch pushes; `check`, `lint`, empty `build`, `test`.
- `release.yml`: manual preparation on `main`, or stable annotated tag pushes;
  independent `check`, `lint`, empty `build`, `test`, `release`.
- `maintenance.yml`: daily at 04:00 UTC, or manual on `main`; only `maintenance`.

The repository distributes chezmoi sources, not application binaries or images.
`has_images` is always false. Native development tests run on AMD64; preparation
and tag publication qualify the complete source on AMD64 and ARM64. Template
fixtures additionally exercise both architectures, absent tools and path handling.
No development artifact is reused as release qualification.

After successful development qualification on `main`, version-changing history
requests a separate `release.yml` dispatch using the job's `actions: write`
permission. GitHub permits workflow dispatch with `GITHUB_TOKEN` to start another
run. This is the intentional automatic-preparation extension to the shared
three-workflow contract; manual preparation remains available.

Preparation verifies source-bound native receipts, updates `CHANGELOG.md`, and
atomically pushes the changelog commit and a new annotated tag using a bot App
installation token. A lease rejects concurrent changes to `main`. The resulting
tag run requalifies the full source and publishes the GitHub Release. Releases
are never inferred from a green development run or skipped selected tests.
Tag publication never rebuilds a distributed artifact.

## Version policy

Initial development does not publish automatically. Dispatch `release.yml` on
`main` with `first_release=true` to explicitly publish the first `1.0.0`.
Subsequent releases are automatic:

- `feat`: minor;
- `fix` or `perf`: patch;
- `!` or `BREAKING CHANGE:` on any commit type: major after 1.0.0, minor before it;
- other changes alone: no release.

The selector determines the strongest intent before changelog filtering.
Pinned git-cliff 2.14.2 computes the increment and Keep a Changelog notes.
Tags have no `v` prefix. Deployment from a branch versus a release tag remains a
separate chezmoi operational choice.

## Credentials and activation

Use the existing `BOT_APP_ID` variable and `BOT_APP_PRIVATE_KEY` secret.
Install the shared App on this repository with Contents, Pull requests, Issues
and Workflows write access and Actions read access, plus Renovate's documented
platform permissions. Each preparation/maintenance job creates its own
repository-scoped token. No personal access token is used.

Disable duplicate execution by the hosted Renovate App before enabling this
self-hosted schedule. Presence of App credentials alone does not prove installation
or permissions. Confirm those in the first hosted execution.

Only the CI preparation action pushes release metadata. Local development agents
still never push. Branches may be pushed directly to `main`; force-push protection
is configured in repository settings.

## Native chezmoi tests

Run with chezmoi 2.73.0, Python, jq and git-cliff 2.14.2 available:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 .github/scripts/qualify_dotfiles.py
```

The fixtures create a separate source, destination, config, cache and persistent
state. They substitute a fake gopass and never read real credentials. External
archives are omitted from offline round trips and checked separately through
bounded HTTP requests. Native `apply --exclude=scripts`, `verify` and `diff`
check convergence and detect deliberate target drift.

The rendering linter also checks the bootstrap/external TOML templates, Nushell
0.117.0, Niri 26.04, desktop entries and offline-generated Quadlet/systemd units.
The distro's older Nushell is not used: the upstream native archives are pinned
by checksum for both architectures.

Lifecycle tests use a separate minimal source. Regression tests mock commands
for systemd, Beszel, AGE locking and Hugging Face. They do not start desktop
services. Actual graphical, USB and privileged service integration still requires
qualification on the target host or a dedicated VM.

Functional reports and receipts live under `.build/`. Source SBOMs and Grype
reports are advisory, including tool failures. They do not qualify or scan the
host's installed Quadlet images. GitHub artifact retention uses the repository
default; receipts from expired runs cannot authorize publication.

## Temporary source-action bridge

Published catalog actions are pinned to commit
`727e561c44b938c184dd51eea33b816fe99c37ac` (1.6.3), with their own image digests.
The dotfiles-specific operations do not yet have published catalog interfaces.
Their dedicated Docker actions currently live in `.github/actions/`, each with
a fixed Go entrypoint, adjacent Containerfile and an operation-specific helper
under `.github/scripts/`. `Dockerfile` is a symlink for GitHub's source-action
loader. These unreleased images are built at invocation.

This is a bootstrap bridge, **not completed catalog activation**. Removal requires:

1. Port each required operation into `tdesaules/github-actions` with its tests.
2. Qualify the exact native AMD64/ARM64 images, runtime dependencies and licenses.
3. Publish those exact candidates and record their verified digests.
4. Replace every local action reference here with a named released catalog action.
5. Observe the complete hosted main, preparation, tag and maintenance paths.

No placeholder registry digests or unqualified remote action paths are used.
Runtime bases are Fedora 45 (Python, Git, chezmoi and distro runtime dependencies)
and scratch for the static maintenance event validator. Renovate validation
inherits the verified Fedora-based catalog runtime used by maintenance.
The git-cliff donor is build-only; the resulting runtime is Fedora.

Validate base references against the registry, including the AMD64/ARM64 index,
before updating a pin. For local build verification use `podman build
--pull=always --no-cache`: a cached image can still build after its manifest
becomes unavailable to a fresh GitHub runner.

## Adding checks

Keep repository-only helpers under `.github/scripts/` and tests named `test_*.py`.
Declare new operations as explicit `uses:` steps. Do not add host-script or
generic operation-dispatch steps. Extend the planner's known static selections
and tests together. A skipped selected phase must never authorize release.
