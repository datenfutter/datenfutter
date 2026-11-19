# One current project state

| Path | Responsibility |
| --- | --- |
| `datenfutter/`, `brand/` | One shared implementation and visual system. |
| `projects/<topic>/README.md` | Scope, selected vintage, method and limitations. |
| `projects/<topic>/sources/source-register.json` | Current source selection, definitions, exact public URLs and source-linked calculation parameters. |
| `projects/<topic>/sources/raw/` | Immutable source responses; dated snapshots and source ZIPs are valid evidence. |
| Original source receipt logs | Original paths, timestamps, hashes, sizes and failed attempts, preserved without rewriting. |
| `projects/<topic>/prepare.py` | Offline transformation of selected evidence into current tables. |
| `projects/<topic>/data/processed/` | One current derived-data set and deterministic validation results. |
| `projects/<topic>/specs/<language>/<post>.json` | One active chart/copy specification per post; `de` or `en`. |
| `projects/<topic>/posts/<language>/<post>/` | Numbered PNG/SVG pairs, `caption.md`, `alt-text.md`, `manifest.json`. |
| `projects/<topic>/review.json` | Actual inspection and user-review state tied to exact file/input hashes. |
| Current `delivery.json` | Verified external delivery receipt; private destination identifiers remain with that delivery. |
| Ignored `build/` | Disposable preparation, previews, phone-size checks and requested temporary exports. |

Project/post discovery comes from specifications. Do not maintain another
parallel output inventory. Manifests own the generated file set; review and
delivery records describe what was actually inspected and saved.

Do not create maintained plot revision folders, output backups, dated exports,
contact sheets or duplicate delivery ZIPs. Ordinary Git history retains earlier
code/content revisions. Evidence history is different: keep the immutable raw
responses and original receipts needed to explain the selected data.

Keep one language-independent preparation path when source selections agree.
Language-specific copy belongs in specifications, not a duplicated renderer.
Unmigrated English topics may still be under `datafodder/projects/`; migrate
them individually rather than treating an old location as a second canonical
target. Reconcile any source-vintage differences before sharing inputs.

The user handles old remote branches and Drive cleanup manually. Agents do not
create replacement archive hierarchies or make those operations prerequisites
for implementation. Unmigrated topics still need their original evidence; a
successful fuel import does not make unrelated Drive packages disposable.
