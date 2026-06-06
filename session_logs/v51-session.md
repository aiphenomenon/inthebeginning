# V51 Session — Wire `deploy/` to GitHub Pages from this repo

**Date**: 2026-06-05 19:00 CT (2026-06-06 00:00 UTC)
**Branch**: `claude/develop-branch-setup-GflwB` (based on `origin/develop`)
**Previous version**: v50

---

## Requested

1. Confirm the working branch is hooked up to develop's progress.
2. Make the Cosmic Runner game UI available on GitHub Pages **directly from
   this repo** instead of manually copying `deploy/` into a separate gh-pages
   repo.

## Done

### Branch setup
- Confirmed the new branch `claude/develop-branch-setup-GflwB` was forked from
  `main` (45 commits behind `develop`), reset it onto `origin/develop`
  (`d0baada`), set commit identity to `Claude <noreply@anthropic.com>` for new
  commits, and pushed it to origin with upstream tracking. The 44 inherited
  develop commits were intentionally **not** rewritten (they are upstream
  history, not commits from this session).

### GitHub Pages auto-deploy
Confirmed choices with the user: **GitHub Actions** method, root **redirects**
to the latest game, publish **everything** in `deploy/`.

- **`.github/workflows/pages.yml`** (new): build + deploy jobs using
  `actions/upload-pages-artifact@v3` and `actions/deploy-pages@v4`. Triggers on
  push to `develop` and `claude/develop-branch-setup-GflwB`, path-filtered to
  `deploy/**` and the workflow file, plus `workflow_dispatch`. Least-privilege
  permissions (`pages: write`, `id-token: write`). `concurrency: pages` with
  `cancel-in-progress: false` serializes deploys.
- **`deploy/index.html`** (new): root landing that redirects to
  `v13/inthebeginning-bounce/` via meta-refresh + JS + anchor fallback. The
  relative URL resolves under the `/inthebeginning/` project-site subpath.
- **LFS SoundFont handling**: `deploy/shared/audio/soundfonts/FluidR3_GM.sf2`
  is Git LFS-tracked (~142 MB real binary, 134-byte pointer in tree). That
  exceeds the GitHub Pages **100 MB per-file hard limit**, so the workflow
  checks out without LFS and strips `*.sf2`/`*.sf3` pointers before upload, with
  a guard step that fails the build if any file exceeds 100 MB. HiFi mode
  degrades gracefully to Synth (per the v50 client fixes); MP3 / MIDI / Synth
  modes are unaffected.
- **`RELEASE_HISTORY.md`** / **`WORKLOG.md`**: recorded the v0.51.0 change and
  added WORKLOG items D4 (done) and D5 (open — host the SoundFont externally so
  HiFi works on Pages).

## One-time manual step (user)

Set the Pages source to GitHub Actions — this cannot be done from git:

> Repo → **Settings → Pages → Build and deployment → Source → GitHub Actions**

After that, the first push touching `deploy/**` (or a manual
`workflow_dispatch`) publishes to `https://aiphenomenon.github.io/inthebeginning/`.

## Test results

- Reference suite (`python -m pytest tests/`): **not run** — `pytest` is not
  installed in this environment. No simulator code was touched this session
  (changes are a workflow, an HTML redirect, and markdown docs), so the suite
  is unaffected.
- `pages.yml`: validated as well-formed YAML (`yaml.safe_load`).
- `deploy/index.html`: parsed without errors; redirect target
  `deploy/v13/inthebeginning-bounce/index.html` confirmed to exist.
- `session_logs/v51-journal.json`: passes `.claude/hooks/validate-journal.py`.

## Files created / modified

- created: `.github/workflows/pages.yml`
- created: `deploy/index.html`
- created: `future_memories/v51-plan.md`
- created: `session_logs/v51-session.md`, `session_logs/v51-journal.json`
- modified: `RELEASE_HISTORY.md`, `WORKLOG.md`

## Follow-ups

- D5: host the 142 MB SoundFont on a CDN or GitHub Release asset and point the
  HiFi client at it, so HiFi works on Pages.
- D2: end-to-end verification on the live Pages site once the source setting is
  enabled.
- Once `develop` is the settled deploy source, drop
  `claude/develop-branch-setup-GflwB` from the workflow's trigger list.
