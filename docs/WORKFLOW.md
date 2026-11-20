# Acquire, prepare, render, review and deliver

## Acquire evidence

For the current fresh-source rebuilds, use the Google Drive plugin to identify
an existing plot topic, then research its authoritative sources again. Do not
copy Drive data, specifications, code or finished plots. Work on one selected
plot at a time and use GitHub's shared renderer and brand.

Define the metric, countries, units and period. Use authoritative sources;
preserve uncertainty, gaps, revisions and series breaks. Keep exact source
responses and their original retrieval receipts, including failed attempts.
Acquisition may require network access; rebuilding a selected snapshot does
not. A new retrieval is a new receipt, never a new timestamp on old bytes.
Keep acquisition in the project's separate `acquire.py`; do not perform network
requests from `prepare.py` or rendering.

## Prepare the current selection

Select evidence in the source register and keep substantive assumptions linked
to their sources. Implement topic calculations in `prepare.py`, with current
outputs under `data/processed/`. Rebuild from raw evidence without reading old
processed tables, specifications or plot revisions. Validate observation keys,
coverage, baselines, units and reconciliation before writing derived files.

Use the shared renderer and brand; do not embed country-specific calculations
in rendering code. Reuse data across languages only when definitions and
selected vintages agree.

## Render and compare

Use canonical language/post specifications. Run:

```bash
python -m datenfutter build TOPIC
python -m datenfutter check TOPIC
python -m datenfutter layout
```

The fresh unemployment pilot adds a project-specific production gate:

```bash
python projects/unemployment-de-ch-dk-no/verify.py
```

`build` writes only disposable previews under ignored `build/`. `check` compares
complete current output sets without replacing them; it requires current posts
to compare. `layout` permits draft projects and reports counts, so a passing
layout check alone is not a reproduction result. The project verifier
excludes existing processed data from its preparation workspace, compares all
derived files, and then compares current posts. Keep preparation and rendering
offline, and check that verification leaves source inputs and current outputs
unchanged. There is no generic `scripts/check_production.py` in the repository.
Report CI network isolation or production verification only when the actual
workflow and results for the exact commit demonstrate it.

## Inspect and record review

Inspect every image at 1080 px and about 360 px width, with the complete caption
and alt text. Preserve cream backgrounds, navy accents, black text, DejaVu Sans,
the supplied df circle, bold pagination, one descriptive block and the localized
date footer. Captions retain complete literal public source URLs. Resolve
clipping or misleading values before promotion.

Retain exactly one current generated set per topic/language/post. Record its
hashes and checks in the current review record. An internally checked preview
is not user approval; a successful build is not social publication. Present
the images and full caption for the requested review before final delivery.
Use the existing task authorization once its review requirements are met.

## Commit and continue

Make one bounded change per commit. Inspect the diff, run its acceptance gate,
stage explicit paths, commit, push normally, and verify that exact remote SHA
and CI before the next integrated step. Never force-push to simplify history.
If a new operation is blocked, record its exact scope and continue independent
work. The current fresh-source instruction takes priority over the paused
historical fuel-import queue; PLAN retains that history without making it the
next task.

GitHub main owns current code, instructions, specifications and outputs. The user
handles old-branch deletion and Drive cleanup; those are not execution gates.
Do not create extra task branches, recovery bundles or duplicate delivery sets.
Read PLAN for the next executable task and its exact acceptance gate. Check the
remote ref before a write and use a non-forced conditional update. On a timeout,
read back the ref before retrying; do not create duplicate commits blindly.
After the first fresh plot is completed, let the user select the next plot.

Drive delivery is optional and requires a specific request. Social publication
and sharing changes remain separate actions. Retain actual review status; the
merge authorization does not invent editorial approval or social publication.
