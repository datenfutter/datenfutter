# Datenfutter

Source-backed statistical charts for Datenfutter (German) and Datafodder (English).

**GitHub main is canonical.** Read [PLAN.md](PLAN.md) for the next executable task and verified progress. The [working Drive folder](https://drive.google.com/drive/folders/1K-NwNYx3TcyCWFCtuaCVljVi-bqEXizs) supplies unmigrated source material; its older instructions and output copies are not authoritative. The user handles old-branch deletion and Drive cleanup manually.

Each project will retain one current set of plots under `projects/<topic>/posts/<language>/<post>/`. Raw source evidence and retrieval receipts remain available; Git records later revisions. Temporary previews belong in ignored `build/`. Shared code and brand assets are maintained once at the root.

The first pilot is the DE/CH/LU fuel snapshot retrieved on 18 November 2026, covering January 2019–October 2026. No social publication is implied by a repository commit.

## Local checks

Use Python 3.12. Install `requirements.txt`, then run `python -m unittest discover -s tests -v`. The CI workflow runs the same suite. The small legacy input fixture preserves behavioral coverage during migration; historical plot outputs are not included.

## Offline project builds

Run `python -m datenfutter build TOPIC` for one canonical project, or
`python -m datenfutter build --all`. Projects are discovered from
`projects/<topic>/specs/<language>/<post>.json`. Each specification must use
schema 0.4 (0.3 alias supported) and match its language directory.

The command copies inputs into a disposable workspace under ignored `build/`,
runs the project's `prepare.py` there when present, and renders with the shared
brand. Preparation scripts use their own project directory for inputs and
outputs; acquisition is a separate command. Projects without preparation use
their saved tables. Successful previews are placed under
`build/projects/<topic>/posts/<language>/<post>/`. Current posts and input files
are never the build destination. Rendering/preparation errors preserve previous
previews; output promotion retains the renderer's per-file replacement behavior.

An empty project selection is an error. Production inputs are awaiting migration;
the public CI baseline currently exercises synthetic fixtures and retained small
legacy inputs, not a complete production rebuild.

Run `python -m datenfutter check TOPIC` or `python -m datenfutter check --all`
to rebuild and compare the complete file sets and bytes against current posts.
Checks report missing, extra and changed files; they never repair or overwrite
current posts. `--all` reports and skips projects with no current outputs. A
comparison with no current outputs fails, so an empty tree cannot masquerade
as a successful production rebuild.

Run `python -m datenfutter layout` to validate canonical paths and complete
managed output sets. It reports project and current-post counts separately.
A valid layout with zero current posts is not a production reproduction check.

## Small verified changes

Continue this consolidation in small verified commits to main. Inspect the diff,
run the acceptance gate, then update the expected remote head without force and
verify CI for that exact commit. Do not create extra branches or recovery bundles.
Manual branch deletion and Drive cleanup do not block the next executable task.

During migration, rendering from saved tables and rebuilding those tables from
raw evidence are separate gates. Production verification must exclude existing
processed tables from its disposable preparation workspace, compare complete
file sets and bytes, and run preparation/rendering offline. The current public
CI does not yet include that production gate. See [PLAN.md](PLAN.md) for the
remaining sequence.
