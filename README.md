# Datenfutter

Source-backed statistical charts for Datenfutter (German) and Datafodder (English).

**GitHub main is canonical.** Read [PLAN.md](PLAN.md) for the next executable task and verified progress. The current direction is to rebuild one existing plot topic at a time using freshly researched authoritative sources. Use the Google Drive plugin to identify the topic in the working Datenfutter folder; do not copy its data, specifications, code or finished plots. The user handles old-branch deletion and Drive cleanup manually.

Each project retains one current set of plots under `projects/<topic>/posts/<language>/<post>/`. Raw source evidence and retrieval receipts remain available; Git records later revisions. Temporary previews belong in ignored `build/`. Shared code and brand assets are maintained once at the root.

The fresh-source pilot is [annual unemployment in Germany, Switzerland, Denmark and Norway](projects/unemployment-de-ch-dk-no/README.md), covering 2016–2025 in one German trend plot. Its Eurostat evidence was retrieved on 20 November 2026. This task supersedes the previous fuel-import priority; the old import queue is paused. Check PLAN for implementation and verification status. No social publication is implied by a repository commit.

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

An empty project selection is an error. The fresh pilot has its own raw-to-output
verification command; it does not establish that other Drive topics have been
rebuilt. Shared framework tests and layout checks alone do not verify production
reproducibility.

Run `python -m datenfutter check TOPIC` or `python -m datenfutter check --all`
to rebuild and compare the complete file sets and bytes against current posts.
Checks report missing, extra and changed files; they never repair or overwrite
current posts. `--all` reports and skips projects with no current outputs. A
comparison with no current outputs fails, so an empty tree cannot masquerade
as a successful production rebuild.

Run `python -m datenfutter layout` to validate canonical paths and complete
managed output sets. It reports project and current-post counts separately.
A valid layout with zero current posts is not a production reproduction check.

For the unemployment pilot, run:

```bash
python projects/unemployment-de-ch-dk-no/verify.py
```

This project-specific gate prepares from raw evidence in a disposable copy
without existing processed tables, then compares complete derived-data and
post file sets and bytes with the current files. Source acquisition through
the project's `acquire.py` is a separate network operation. Consult the project
README and current CI workflow for the checks actually implemented and run.

## Small verified changes

Continue these fresh-source rebuilds in small verified commits to main. Inspect the diff,
run the acceptance gate, then update the expected remote head without force and
verify CI for that exact commit. Do not create extra branches or recovery bundles.
Manual branch deletion and Drive cleanup do not block the next executable task.

Rendering from saved tables and rebuilding those tables from
raw evidence are separate gates. Production verification must exclude existing
processed tables from its disposable preparation workspace, compare complete
file sets and bytes, and run preparation/rendering offline. There is no generic
`scripts/check_production.py` command in this repository; use the applicable
project verifier. Record local verification and exact-commit CI separately in
[PLAN.md](PLAN.md).
