# Datenfutter execution plan

Updated 19 November 2026 (Asia/Shanghai). GitHub `main` is the canonical source
for instructions, implementation, current outputs and this ledger.

## Current decision

The user authorized integration of all existing branch work and the recovered
fuel implementation into main, including the original evidence and retrieval
metadata described in the investigation. The previous I03 publication gate is
resolved by that instruction. Preserve exact source bytes and receipts; exclude
private recovery/delivery locators and credentials from public commits.

The user will delete old remote branches and clean Drive manually. Those tasks
are external to agent execution and do not block integration. Do not create
new backup branches, recovery bundles, dated plot versions or delivery copies.
Ordinary Git history and original research evidence remain intact. Unmigrated
Drive topics are still pending; merging existing work does not migrate them.

## Resume protocol

1. Read this file from current main, then the next executable task. Re-read the
   remote head and start with a clean checkout. Reuse the verified final code.
2. Change only that task's paths. Use one coherent commit, explicit staging and
   the stated acceptance command. Inspect exit status and nonzero test count.
3. Update this ledger in the same commit. Publish with a non-forced update
   conditional on the observed remote head. Never overwrite another writer.
4. Verify exact remote SHA and main CI before dependent work. Record that CI in
   the next ordinary task commit; avoid recursive commits chasing their own SHA.
5. After a timeout, read back the expected object/ref before retrying. Stop only
   dependent tasks on failure; keep independent work moving. Do not retry known
   unavailable deletion/authentication operations or reopen resolved approvals.
6. Keep one current output set. Use ignored build/ for disposable previews.
   Source evidence, local tests, remote CI, editorial review and social posting
   are distinct; no merge creates editorial approval or social publication.

## Consolidation tasks

| Task | Scope | State and acceptance evidence |
| --- | --- | --- |
| M00 | Align AGENTS, README, START_HERE, workflow/structure docs and this ledger. | Local-pass: instructions reviewed; diff/layout gates. Remote CI pending this commit. |
| M01 (I03) | Import 49 original raw paths, both receipt logs, current source register, verifier, source tests and project README. | Pending. Require 6 source tests, full suite, verifier and layout; verify every source blob against original receipts. |
| M02 (I04/P07) | Import 24 CSVs, validation report, two German specs, existing prepare.py and preparation tests. | Pending. Require full suite, exact raw-only preparation, both preview builds and unchanged source inputs. |
| M03a (O01) | Import German petrol's nine current files. | Pending. Require full file-set/hash equality to recovered final and preview; layout. |
| M03b (O02) | Import German diesel's nine current files and exact review record. | Pending. Require full file-set/hash equality, project check, 18 managed outputs and layout. |
| M04 (V01/V02) | Import production verifier/tests and network-isolated CI. | Pending. Require full suite, missing/extra/changed/no-op preparation cases, review-scope and input-preservation cases, raw-only production reproduction and exact main CI. |
| M05 | Reconcile instructions/ledger and all branch contents; verify main and clean checkout. | Pending. Record preceding integration CI, confirm no output backups, preserve current review states. |

Next executable task: M01 after M00's exact main CI succeeds.

All eight existing remote branch tips were verified contained in main at
`b22b5fb72df54e7f1602eac4f44909dbc1051338`; no open PRs remained. Seven historical
branches are ancestors; task/c03-public-status equals that main. Recheck fresh
heads before reporting them safe for manual deletion. Existing local recovery
refs contain equivalent implementation, with complementary workflow docs now
being consolidated. Import the final state rather than replaying obsolete code.

## Retained structure and invariants

| Path | Role |
| --- | --- |
| datenfutter/, brand/ | Shared renderer, CLI and visual settings |
| projects/TOPIC/README.md, prepare.py | Scope, selected method, offline preparation |
| projects/TOPIC/sources/ | Exact original evidence, receipts and current selection |
| projects/TOPIC/data/processed/ | One current derived-data set |
| projects/TOPIC/specs/LANGUAGE/POST.json | Current specification |
| projects/TOPIC/posts/LANGUAGE/POST/ | Numbered PNG/SVG pairs, caption, alt text, manifest |
| projects/TOPIC/review.json | Actual review state and exact hashes |
| Ignored build/ | Disposable preparation and previews |

Discover posts from specifications. Preserve fuel's 26+23 original receipt
entries and all 49 raw paths, including failed attempts and retrieval dates.
These are research evidence, not output backups. Keep the frozen selection,
units/currencies and numerical guards. Check authored-file whitespace; original
HTML bytes are validated by hashes and must not be reformatted.

Preserve 1080x1350, cream #FAF8EF, navy #1C2D57 accents, black text, DejaVu Sans,
circle-only df logo, approved A/B/C palettes, bold pagination, one descriptive
block, localized lower-left date, and full literal source URLs in captions.

## Subsequent topic migrations

These tasks have not been implemented by consolidating existing branches.
For each topic, first commit an inventory of exact files/hashes/vintages,
languages/posts, transformations and actual review state. Then add concrete
children to this ledger before coding: evidence; tables/specs; each decoder or
transformation; raw-only verification; one complete post per task; offline CI.
Do not make branch deletion, Drive delivery or Drive cleanup prerequisites.

| Task | Retained scope |
| --- | --- |
| R01 | DK/NO/PL/CZ fuel DE/EN; selected vintages and Norway allocation limitations |
| R02 | Unemployment comparison DE/EN; definitions, vintages and breaks |
| R03 | DE/CH/DK/NO unemployment; comparability, coverage and gaps |
| R04 | DE/NL/PL income; income/survey year, EUR/PPS |
| R05 | German vehicle registrations; full/partial years and actual review state |
| R06 | Retained inflation/ECB; active specs and compatibility users |

After topic inventories, remove one proven-unused compatibility unit per task;
retain units with active users and useful behavioral fixtures. Every shared
change must pass the full suite and reproduce all migrated finals.

## Manual and optional work

- C01: user-owned deletion of already integrated branches. No agent deletion gate.
- D01/D02: Drive delivery/cleanup removed from mandatory agent execution. The user
  owns cleanup; current GitHub outputs are canonical. Delivery occurs only on a
  separate request. Unmigrated evidence remains necessary until its own migration.
- Drive's PLAN is already a pointer to GitHub. Older Drive entry instructions
  are superseded by main and are not a second execution ledger.
- Final verification concerns current main, its CI, canonical file sets and the
  clean checkout. Report remaining topic work honestly; manual cleanup does not
  prevent completion of the consolidation tasks above.
