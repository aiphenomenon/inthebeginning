# V51 Plan — Wire `deploy/` to GitHub Pages from this repo

## Date
2026-06-06

## Context
The user has been publishing the Cosmic Runner game UI to GitHub Pages by
**manually copying** the `deploy/` tree into a separate `gh-pages` repo on
every release. That is cumbersome. They want the site served **directly from
this repository** so a push updates the live site with no copying.

Decisions (confirmed with user via AskUserQuestion):
- **Method**: GitHub Actions workflow (not a `gh-pages` branch).
- **Site root**: redirect `/` to the latest game (`v13/inthebeginning-bounce/`).
- **Scope**: publish the entire `deploy/` tree (all versions v4–v13 + shared
  assets, ~358 MB committed). Old version URLs stay alive.

Branch context: work is on `claude/develop-branch-setup-GflwB`, which was reset
onto `origin/develop` (the branch with the most progress, 45 commits ahead of
`main`). The deployable content (`deploy/v13/`) lives here.

## Key constraint discovered: LFS SoundFont vs Pages 100 MB limit
`deploy/shared/audio/soundfonts/FluidR3_GM.sf2` is **Git LFS-tracked** and is a
134-byte pointer in the working tree; the real binary is ~142 MB. Two problems
for Pages:
1. GitHub Pages has a **hard 100 MB per-file limit** — a resolved 142 MB `.sf2`
   would be rejected and could fail the whole deploy.
2. Serving the LFS *pointer text* is exactly the v50 "vers" bug.

**Resolution**: the workflow checks out **without** LFS and **removes** the
`*.sf2`/`*.sf3` pointer files from the artifact before upload. HiFi mode then
degrades gracefully — the v13 client (v50 fixes) detects the missing SoundFont,
shows a visible error, and falls back to Synth. MP3 / MIDI / Synth modes work
fully. No file in the published artifact exceeds 9 MB.

## Deliverables
1. **`future_memories/v51-plan.md`** — this file.
2. **`deploy/index.html`** — root landing that redirects to
   `v13/inthebeginning-bounce/` (meta-refresh + JS + anchor fallback). Works
   under the `/inthebeginning/` project-site subpath because the redirect is
   relative.
3. **`.github/workflows/pages.yml`** — Pages deploy workflow:
   - `on: push` to `develop` and `claude/develop-branch-setup-GflwB`
     (immediate verification pre-merge), plus `workflow_dispatch`. Path-filtered
     to `deploy/**` and the workflow file.
   - `permissions: { contents: read, pages: write, id-token: write }`.
   - `concurrency: { group: pages, cancel-in-progress: false }` — serialize
     deploys, let in-flight ones finish (prevents multi-branch races).
   - build job: checkout (no LFS) → strip `*.sf2`/`*.sf3` pointers → ensure
     `.nojekyll` → `actions/upload-pages-artifact` with `path: deploy`.
   - deploy job: `actions/deploy-pages`.
4. **`RELEASE_HISTORY.md`** — v0.51.0 entry.
5. **`WORKLOG.md`** — note Pages auto-deploy wired up.
6. **`session_logs/v51-session.md`** + **`session_logs/v51-journal.json`**.

## One-time manual step (user)
Pages source must be set to **GitHub Actions**:
Repo → Settings → Pages → Build and deployment → Source → **GitHub Actions**.
This cannot be done from git; documented in the session log and chat.

## Non-goals
- Hosting the 142 MB SoundFont anywhere (HiFi stays degraded on Pages for now).
  Follow-up option: host the `.sf2` on a CDN / Releases asset and point the
  client at it.
- Changing the game code, simulator, or other `apps/` implementations.
- Setting up a custom domain.

## Verification
- `python -m pytest tests/ -v --tb=short` — reference suite unaffected (no
  simulator change), sanity only.
- YAML lint of the workflow (`python -c yaml.safe_load`).
- After merge to `develop` (or push of this branch) + user enabling Pages:
  confirm the Actions run is green and `aiphenomenon.github.io/inthebeginning/`
  redirects to the v13 game.

## Rollback
Delete `.github/workflows/pages.yml` and `deploy/index.html`. No other files
depend on them; the manual copy workflow still works as before.
