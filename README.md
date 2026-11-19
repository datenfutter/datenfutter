# Datenfutter

Source-backed statistical charts for Datenfutter (German) and Datafodder (English).

The repository is being migrated from the [working Drive folder](https://drive.google.com/drive/folders/1K-NwNYx3TcyCWFCtuaCVljVi-bqEXizs). See [PLAN.md](PLAN.md) for current migration status and the next atomic steps.

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
