---
id: release
title: Release and Installation
description: >
  How to install Harness Toolkit CLIs with uv tool and cut GitHub tag releases
  before PyPI publishing is needed.
index:
  - id: install-cli-tools
    keywords: [uv, tool, install, hk, harness-kit, harness-scaffold]
  - id: release-policy
    keywords: [versioning, tags, github-release, pypi]
  - id: docs-site
    keywords: [mkdocs, github-pages, gh-pages, deploy]
  - id: release-checklist
    keywords: [check, build, tag, release]
---

# Release and Installation

Harness Toolkit is currently distributed as a GitHub-sourced Python tool. PyPI
publishing is intentionally deferred until the command contract settles.

## Install CLI tools

Install the latest `main` from GitHub:

```bash
uv tool install git+https://github.com/safurrier/harness-toolkit.git
```

Install a pinned release tag:

```bash
uv tool install git+https://github.com/safurrier/harness-toolkit.git@v0.3.0
```

Install from a local checkout for development:

```bash
git clone https://github.com/safurrier/harness-toolkit.git
uv tool install --editable ./harness-toolkit
```

Verify the installed commands:

```bash
hk --version
harness-kit --version
harness-scaffold --version
```

The installed executables are:

| Command | Use |
|---|---|
| `hk` | Daily portable workflow command for existing repos |
| `harness-kit` | Readable alias for `hk` |
| `harness-scaffold` | Starter-template CLI for initializing new repos |

## Upgrade or reinstall

Upgrade a GitHub-sourced install:

```bash
uv tool upgrade harness-toolkit
```

Reinstall from a specific tag when you want to force the source:

```bash
uv tool install --reinstall git+https://github.com/safurrier/harness-toolkit.git@v0.3.0
```

For editable local installs, pull the checkout and reinstall when entry points or
dependencies change:

```bash
git -C ~/git_repositories/harness-toolkit pull --ff-only
uv tool install --editable ~/git_repositories/harness-toolkit --force
```

## Release policy

Use GitHub tags/releases as the distribution boundary for now.

- Keep `0.x` while CLI contracts and profile semantics are still settling.
- Use patch releases for bug fixes, documentation, and validation hardening.
- Use minor releases for command, profile, or plan-contract changes.
- Defer PyPI until external install-by-name is worth the package maintenance.

## Publish the docs site

Harness Toolkit's own docs deploy from the `gh-pages` branch. The GitHub Actions
workflow builds MkDocs and pushes that branch on changes to `main`, but a new
repo still needs Pages enabled once.

After the first successful `Deploy Documentation` run, enable Pages in GitHub:

1. Go to **Settings → Pages**.
2. Set **Source** to **Deploy from a branch**.
3. Set **Branch** to `gh-pages` and folder to `/ (root)`.
4. Save and wait a minute or two for GitHub to provision the site.

From the CLI, the same setup is:

```bash
gh api repos/safurrier/harness-toolkit/pages \
  --method POST \
  -f 'source[branch]=gh-pages' \
  -f 'source[path]=/'
```

If the deploy action is green and `gh-pages` exists but the site returns 404,
check whether Pages is enabled:

```bash
gh api repos/safurrier/harness-toolkit/pages
git ls-remote --heads origin gh-pages
```

A `404` from the Pages API usually means the branch was pushed but GitHub Pages
has not been configured for the repo yet.

## Release checklist

Before tagging:

```bash
mise run check
uv build
```

Then create release notes, tag, and publish:

```bash
cat > /tmp/harness-toolkit-v0.3.0-notes.md <<'NOTES'
## Summary
- See CHANGELOG.md for the v0.3.0 changes.

## Install
uv tool install git+https://github.com/safurrier/harness-toolkit.git@v0.3.0
NOTES

git tag v0.3.0
git push origin v0.3.0
gh release create v0.3.0 --title "v0.3.0" --notes-file /tmp/harness-toolkit-v0.3.0-notes.md
```

After publishing, verify from a clean environment when possible:

```bash
uv tool install --reinstall git+https://github.com/safurrier/harness-toolkit.git@v0.3.0
hk --version
harness-scaffold --version
```

## PyPI later

Before publishing to PyPI, add or verify:

- project metadata in `pyproject.toml`
- license metadata
- package URLs and classifiers
- GitHub Actions release workflow using trusted publishing
- TestPyPI dry run

Until then, prefer explicit GitHub tag installs so users know exactly what source
they installed.
