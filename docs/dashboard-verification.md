# Dashboard verification and release

Prepared 11 November 2026. The new frontend is a static research explorer connected through a validated Python export; it does not submit orders or stream live prices.

## Actual data wiring

The private hosted export uses snapshot `17359245afbd18dacadca14b663e80f5433f4183f810fa3248eb6bad6353bb51` and the matching security master. It contains twenty ranked pairs for each of the 252- and 756-session formation windows, both ending 31 December 2024. The broader data source contains 285 stocks and 2005–2025 observations; those coverage dates do not turn the dated formation screens into current signals.

Only fully elapsed outcome windows available by the displayed snapshot date are attached. The 252-session screen has 222 completed formation cohorts available as of that date; the 756-session screen has no matching forward study attached. The UI does not use the one-year study to imply that the three-year selector has been tested.

The exporter rejects mismatched dataset or master hashes and incomplete chart series. The original model's distance ranking and source eligibility are preserved. The frontend computes filters, views and chart geometry, not pair qualification or orders.

## Automated checks actually run

- **53 Python tests passed**, including dashboard provenance, chart chronology, outcome timing, horizon separation and export packaging, alongside the existing research tests.
- **14 Node logic/DOM tests passed**, exercising search, filters, distance controls, sorting, pagination, grid/list view, selected details, charts, watchlists, CSV export, local JSON import, rejected imports, tabs, keyboard navigation, data-health and history views.
- Actual real-data bundle passed frontend schema validation, with forty pair cards across the two formation windows.
- The new offline `dashboard-demo` command generated a separately labeled synthetic dashboard with fifteen pairs per formation window; its bundle passed frontend validation.
- Dependency consistency and JavaScript syntax checks passed.

The managed browser-control tool was unavailable, so no rendered-browser visual or responsive-device certification is claimed. DOM tests establish interaction behavior, not pixel-level layout. The CSS provides responsive layouts and reduced-motion support for device review.

## Publishing

Published owner-private with the Sites workflow at:

https://pairwise-nse-research.rusticagave1.chatgpt.site

The native deployment returned `succeeded`. The source was pushed before the matching static archive was published. The short-lived source credential stayed in process memory/stdin and was not committed. The real market-data bundle is stored only in ignored local outputs and private Site source; reusable frontend files and tests are tracked in the public project repository.

Public source changes do not automatically refresh the private hosted snapshot. Future updates must export and publish a matching bundle while retaining the same Site identity and audience. See `dashboard.md` for local use and import instructions.
