# Erwerbslosigkeit in Deutschland, Schweiz, Dänemark und Norwegen

One German trend plot of annual unemployment rates from 2016 to 2025. This is
the first fresh-source rebuild of an existing Datenfutter topic. Drive was used
only to identify the topic; no old data, specifications, code or plots were
copied. The shared renderer and visual assets come from GitHub.

The current plot passes the 96-test suite, project build/check, layout validation
and raw-only offline reproduction (six derived files and five post files).
See the root [PLAN](../../PLAN.md) and the current review record for check scope
and review status. A repository
commit does not imply user approval or social publication.

## Measure and evidence

Eurostat dataset `une_rt_a`, **Unemployment by sex and age - annual data**:

- Geography: Germany (`DE`), Switzerland (`CH`), Denmark (`DK`), Norway (`NO`).
- Annual frequency (`A`), ages 15–74 (`Y15-74`), total sexes (`T`).
- Unit: percent of the labour force (`PC_ACT`), not percent of the population.
- Selected observations: 2016–2025; 40 country-year values with no missing data.
- Source response includes 2015–2025; the additional 2015 observations are
  retained as original evidence and excluded from the plot selection.
- Fresh retrieval: 20 November 2026. Provider update: 6 November 2026.

Exact acquisition query:

https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/une_rt_a?lang=en&freq=A&age=Y15-74&unit=PC_ACT&sex=T&geo=DE&geo=CH&geo=DK&geo=NO&sinceTimePeriod=2015&untilTimePeriod=2025

Dataset DOI:

https://doi.org/10.2908/UNE_RT_A

The source register records the selection, public source URLs, definitions and
reuse policy. Immutable raw bytes and the retrieval receipt preserve the
response timestamp, size and SHA-256 hash. Future acquisitions are new evidence;
do not relabel or replace this snapshot's receipt.

## Method and limitations

Preparation decodes the response's JSON-stat dimension indexes, selects the
four countries and ten years, and retains values and observation flags. It
does not average monthly unemployment rates or interpolate missing values.
The year is represented by 1 January only for positioning annual observations
on a date axis; these are annual results, not January measurements.

The labour force consists of employed and unemployed people. The Eurostat/ILO
definition requires no employment in the reference week, availability for work
and active job search, with a provision for a job starting within three months.
Registered unemployment is a different measure. Annual rates are published
from LFS population estimates; use the published annual figures directly.

Eurostat flags time-series breaks (`b`) for Denmark in 2016, 2017 and 2023 and
Germany in 2020. Preserve all points and omit incoming line segments at breaks;
Denmark's 2016 flag is at the first displayed observation. Comparisons crossing
these breaks are limited. Germany's 2020 result also uses a broader integrated
household-survey sample because of survey-system technical issues. No extra
break is invented for 2021 when it is absent from this selected data vintage.

In the selected vintage, rates rise in each country from 2023 to 2024 and from
2024 to 2025. The 2025 figures are Germany 3.8%, Switzerland 4.9%, Denmark 6.4%
and Norway 4.5%. This descriptive comparison does not establish a cause.
2025 is the latest annual period in the source response; no partial 2026 result
is joined to the annual series.

Methodology and definition:

https://ec.europa.eu/eurostat/cache/metadata/en/lfsi_esms.htm

https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Glossary:Unemployment

Reuse policy:

https://ec.europa.eu/eurostat/help/copyright-notice

Eurostat permits reuse of these EU/EFTA statistical data with source
acknowledgement. Selection and visualization are by Datenfutter; Eurostat is
not responsible for this presentation.

## Files and commands

| Path | Purpose |
| --- | --- |
| `acquire.py` | Separate online retrieval and receipt creation |
| `sources/source-register.json` | Current source selection, definitions and public links |
| `sources/raw/` | Immutable official response bytes |
| `prepare.py` | Offline decoding, validation and derived-table preparation |
| `data/processed/` | Current derived data and validation results |
| `specs/de/` | One current German post specification |
| `posts/de/` | Current PNG/SVG, caption, alt text and manifest |
| `verify.py` | Raw-only preparation and exact derived/post reproduction |
| `review.json` | Actual review status tied to file hashes |

From the repository root:

```bash
python -m datenfutter build unemployment-de-ch-dk-no
python -m datenfutter check unemployment-de-ch-dk-no
python -m datenfutter layout
python projects/unemployment-de-ch-dk-no/verify.py
python -m unittest discover -s tests -v
```

`build` produces disposable previews under ignored `build/`. `check` compares
them with the current posts without overwriting those posts. The project
verifier removes saved processed tables from its disposable input copy,
prepares offline from raw evidence, then compares complete derived-data and
post file sets and bytes. It must not repair current outputs or modify source
evidence. A layout pass alone is not proof of raw-to-output reproduction.

Inspect the complete caption and alt text together with the image at 1080 px
and around 360 px width before final delivery. Record internal inspection,
user review, exact-commit CI and social publication as separate states.
