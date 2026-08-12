---
name: git-workflow
description: Use when committing changes, creating branches, or setting up git hooks and CI/CD pipelines. Enforces Conventional Commits, Trunk-Based Development, local-only commits (never auto-push), pre-push secret scanning, and semantic release automation.
license: GPL-3.0 license
compatibility: opencode
metadata:
  version: 1.1.0
---

## What I do

- Enforce [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) on every commit.
- Apply [Trunk-Based Development](https://trunkbaseddevelopment.com/) with `main` as the default branch.
- Configure pre-push hooks (commit linting + secrets scan) and CI/CD stages (secrets, commit lint, semantic release).

## When to use me

Use this when committing or modifying code, creating branches, initializing a repository, or writing/updating git hooks and CI/CD configuration.

## 1. Commit Guidelines

- **Format**: ALWAYS use [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/).
- **Behavior**: Always commit or provide an adapted commit message when building or modifying things.
- **Pushing**: **NEVER push commits to a remote repository automatically.** You may prepare the commits and instructions, but pushing must be explicitly executed by the user.

## 2. Branching Strategy

- **Default Branch**: The primary branch MUST always be `main`.
- **Methodology**: Follow [Trunk-Based Development](https://trunkbaseddevelopment.com/).
- **Small Repositories**: For small repositories, committing directly to `main` is permitted and encouraged as part of the Trunk-Based approach (the push itself is still done by the user, per §1).

## 3. Git Hooks (Pre-Push)

Whenever initializing or updating a repository's infrastructure, always add a Git Pre-Push hook configured to check for:

- **Conventional Commits format**: Ensure all outgoing commits match the specification.
- **Secrets Leaks**: Scan the code to prevent accidental credential or secret exposure (using tools like `gitleaks` or `trufflehog`).

## 4. CI/CD Pipelines

All repositories MUST be configured with mandatory CI stages (using either GitHub Actions or GitLab CI) that perform the following checks:

- **Secrets Leak Check**: Automated scanning for exposed secrets.
- **Commit Linting**: Verification that all commit messages follow Conventional Commits.
- **Automated Release**: Integration with [semantic-release](https://github.com/semantic-release/semantic-release) and [SemVer](https://semver.org/) for automated versioning and changelog generation.

*When setting up a project, automatically provide the necessary YAML configuration files to implement these stages.*

## 5. Language Configuration

Always use **English** for all comments, commit messages, configuration scripts, and any generated text.
