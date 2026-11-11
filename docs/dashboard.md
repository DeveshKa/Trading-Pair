# Pairwise dashboard

An interactive frontend for the minimum-distance research system. Its assets are packaged with the Python distribution under `nifty_pairs/web`; no frontend build tool or browser runtime dependency is needed to use it.

Private hosted dashboard: https://pairwise-nse-research.rusticagave1.chatgpt.site

## Offline demonstration

```bash
python -m pip install -e '.[test]'
nifty-pairs dashboard-demo --out runs/dashboard-demo
nifty-pairs serve --run runs/dashboard-demo
```

Open `http://127.0.0.1:8765/report.html`; it redirects to the dashboard. The demo uses invented assets and clearly displays its synthetic status.

## Export your research snapshot

```bash
nifty-pairs dashboard \
  --data data/broad-distance-300-verified-volume \
  --security-master data/broad-distance-300/security_master.csv \
  --discoveries runs/distance-300-2024/results.json runs/distance-300-2024-three-year/results.json \
  --study runs/distance-300-forward-final/results.json \
  --out runs/my-dashboard
nifty-pairs serve --run runs/my-dashboard
```

The exporter verifies matching dataset hashes, security-master identity and formation dates. Price paths stay within the displayed formation window. Historical outcome windows attach only if they finished by the displayed snapshot date, preventing future outcomes from appearing as contemporaneous evidence. A three-year pair screen does not inherit a one-year strategy's historical results.

The output is static HTML/CSS/JavaScript plus `bundle.json`; serve it over HTTP rather than opening the HTML using a file URL. An exported bundle can also be opened using **Import snapshot** in the existing dashboard. Import processing stays in the browser, validates schema and size, and does not upload data to a service.

## Features

- Company names, symbols, exchange identities and recognizable pair cards.
- Search, exchange filter, divergence filter, maximum distance, sorting, pagination, grid/list layouts and formation-window selection.
- Pair spotlight with normalized paths, hover inspection, range controls, formation-spread chart and distance/gap statistics.
- Historical cohort observations and source/identity information per pair.
- Watchlist persisted in browser storage, independent of notification delivery.
- Filtered CSV export with cell quoting and spreadsheet-formula protection.
- Research-history and data-health views with exclusions and clear empty states.
- Responsive layouts, labeled controls, keyboard tab navigation, visible focus and reduced-motion support.

Displayed divergences are historical formation diagnostics, not confirmed live signals. Crossings are not profits. The UI has no order-submission facility, no connected Kite feed and no external messaging activation.

## Hosting and data separation

The private hosted dashboard uses the actual historical research export, with 1Y and 3Y screens dated 31 December 2024. The source research dataset covers 2005–2025. Do not interpret that screen as a current market scan.

The reusable frontend and exporter are in the public project repository. Actual vendor-derived bundle and price history remain in ignored local outputs and the owner-private Site source. No real market-data bundle is committed to the public repository. `.openai/hosting.json` records the retained Site identity and static deployment directory; changing the repository does not automatically refresh the hosted snapshot.

To update the dashboard, export a fresh bundle and publish the matching frontend and bundle as a new version of the existing Site, preserving access. Refresh the dataset through the research pipeline first; the static UI does not scrape market data or silently recompute pair qualification in the browser.

## Verification

Python tests cover identity/snapshot matching, chart chronology, outcome-availability timing, horizon separation and static packaging. Node tests cover search, composed filters, sorting, CSV safety, input validation, charts, watchlists, pagination, empty states, detail selection, tabs, keyboard behavior and data-health navigation.

```bash
python -m pytest -q
cd src/nifty_pairs/web
npm ci --ignore-scripts --no-audit --no-fund
npm test
```

The current managed environment lacks the `cua_repl.js` browser-control tool, so these are automated DOM/logic checks rather than a rendered-browser visual certification. Responsive rules were implemented but still warrant visual review on real devices. No substitute browser infrastructure was installed.
