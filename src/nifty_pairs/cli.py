import argparse
from dataclasses import replace
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from .alerts import AlertStore
from .config import Config
from .data import Dataset, YFinanceProvider, make_demo
from .engine import backtest
from .report import save_run
from .scan import scan, save_scan
from .diagnostics import diagnose, save_diagnostics
from .marketwide import DistanceConfig, discover, distance_study, load_master, save_marketwide
from .catalog import catalog_from_exports, bulk_library_download
from .archives import parse_bhavcopy, repair_zero_volumes
from .dashboard import build_bundle, export_dashboard


def main(argv=None):
    parser = argparse.ArgumentParser(description="Nifty pairs research; no live trading or external messages")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Generate explicitly synthetic daily data")
    demo.add_argument("--out", required=True)
    demo.add_argument("--sessions", type=int, default=1100)
    demo.add_argument("--seed", type=int, default=42)
    download = sub.add_parser("download", help="Exploratory yfinance library history")
    download.add_argument("--symbols", nargs="+", required=True)
    download.add_argument("--start", required=True)
    download.add_argument("--end", required=True, help="Exclusive end date")
    download.add_argument("--benchmark", default="^NSEI")
    download.add_argument("--out", required=True)
    download.add_argument("--allow-calendar-intersection", action="store_true",
                          help="Exploratory only: explicitly drop stock sessions absent from benchmark; log dates")
    download.add_argument("--diagnostics-only", action="store_true",
                          help="Keep every stock session; incomplete benchmark is permitted for diagnostics, never backtesting")
    validate = sub.add_parser("validate", help="Validate CSV contract and print provenance")
    validate.add_argument("--data", required=True)
    run = sub.add_parser("backtest")
    run.add_argument("--data", required=True)
    run.add_argument("--config")
    run.add_argument("--out", required=True)
    run.add_argument("--exploratory", action="store_true", help="Explicitly permit unaudited fixed-symbol membership")
    run.add_argument("--strategy", choices=["distance", "cointegration"])
    alerts = sub.add_parser("alerts", help="Inspect durable local events; does not deliver them")
    alerts.add_argument("--run", required=True)
    watch = sub.add_parser("scan", help="As-of research gap cards and local deduplicated events")
    watch.add_argument("--data", required=True)
    watch.add_argument("--config")
    watch.add_argument("--as-of")
    watch.add_argument("--out", required=True)
    watch.add_argument("--exploratory", action="store_true")
    profile = sub.add_parser("diagnose", help="Long-history correlation and stable-spread evidence")
    profile.add_argument("--data", required=True)
    profile.add_argument("--out", required=True)
    profile.add_argument("--as-of")
    profile.add_argument("--universe", help="JSON with curated sector mapping")
    profile.add_argument("--cross-sector", action="store_true")
    profile.add_argument("--exploratory", action="store_true")
    cat = sub.add_parser("catalog",help="Normalize official NSE/BSE listing exports")
    cat.add_argument("--nse-list")
    cat.add_argument("--bse-list")
    cat.add_argument("--out",required=True)
    bulk = sub.add_parser("bulk-download",help="Bounded resumable library acquisition with failure ledger")
    bulk.add_argument("--catalog",required=True)
    bulk.add_argument("--symbols-file")
    bulk.add_argument("--limit",type=int,default=100)
    bulk.add_argument("--start",required=True)
    bulk.add_argument("--end",required=True)
    bulk.add_argument("--out",required=True)
    parse = sub.add_parser("parse-bhavcopy",help="Normalize official raw daily archives; does not invent adjusted history")
    parse.add_argument("--file",required=True)
    parse.add_argument("--exchange",choices=["NSE","BSE"],required=True)
    parse.add_argument("--out",required=True)
    repair = sub.add_parser("repair-volumes",help="Apply auditable official NSE overlays to zero library volume only")
    repair.add_argument("--data",required=True)
    repair.add_argument("--bhavcopies",nargs='+',required=True)
    repair.add_argument("--out",required=True)
    for command in ("discover","distance-study"):
        p=sub.add_parser(command,help="Original distance matching, without correlation or cointegration gates")
        p.add_argument("--data",required=True)
        p.add_argument("--security-master",required=True)
        p.add_argument("--out",required=True)
        p.add_argument("--formation-sessions",type=int,default=252)
        p.add_argument("--trading-sessions",type=int,default=126)
        p.add_argument("--top-pairs",type=int,default=20)
        p.add_argument("--min-turnover",type=float,default=1_000_000)
        p.add_argument("--as-of")
        p.add_argument("--exploratory",action="store_true")
    serve = sub.add_parser("serve", help="Serve one generated report locally (read-only)")
    serve.add_argument("--run", required=True)
    serve.add_argument("--port", type=int, default=8765)
    dash = sub.add_parser("dashboard",help="Export interactive pair explorer from matching research artifacts")
    dash.add_argument("--data",required=True)
    dash.add_argument("--security-master",required=True)
    dash.add_argument("--discoveries",nargs='+',required=True,help="Discovery results.json paths with matching snapshot/date")
    dash.add_argument("--study",help="Optional forward study results.json")
    dash.add_argument("--out",required=True)
    dash_demo = sub.add_parser("dashboard-demo",help="Generate an offline interactive dashboard with clearly synthetic data")
    dash_demo.add_argument("--out",required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            if args.sessions < 300:
                raise ValueError("Demo requires at least 300 sessions")
            make_demo(args.out, args.sessions, args.seed)
            print(f"Synthetic data written to {args.out}; not real market observations")
        elif args.command == "download":
            if args.start >= args.end or len(set(args.symbols)) != len(args.symbols):
                raise ValueError("Require start < end and unique symbols")
            YFinanceProvider().download(args.symbols, args.start, args.end, Path(args.out), args.benchmark,
                                       args.allow_calendar_intersection, args.diagnostics_only)
            print(f"Library data written to {args.out}; fixed-symbol exploratory sample, not audited Nifty membership")
        elif args.command == "validate":
            d = Dataset.load(args.data)
            print(json.dumps({"rows": len(d.bars), "symbols": sorted(d.bars.symbol.unique()),
                              "snapshot": d.digest, "manifest": d.manifest}, indent=2))
        elif args.command == "backtest":
            d = Dataset.load(args.data)
            c = Config.load(args.config)
            if args.exploratory:
                c = replace(c, require_membership=False)
            if args.strategy:
                c = replace(c, strategy=args.strategy)
            if not args.exploratory and not d.manifest.get("synthetic") and not d.manifest.get("membership_audited"):
                raise ValueError("Membership is unaudited. Audit it or explicitly select --exploratory.")
            result = backtest(d, c)
            out = save_run(result, args.out)
            print(json.dumps(result["summary"], indent=2, allow_nan=False))
            print(f"Report: {out / 'report.html'}")
        elif args.command == "alerts":
            path = Path(args.run) / "alerts.sqlite"
            if not path.exists():
                raise ValueError("No alert database in run")
            print(json.dumps(AlertStore(path).rows(), indent=2))
        elif args.command == "scan":
            d = Dataset.load(args.data)
            c = Config.load(args.config)
            if not args.exploratory and not d.manifest.get("synthetic") and not d.manifest.get("membership_audited"):
                raise ValueError("Unaudited universe: explicitly use --exploratory")
            if c.require_membership and d.membership is None and not args.exploratory:
                raise ValueError("Membership required")
            result = scan(d, c, args.as_of)
            save_scan(result, args.out)
            print(json.dumps({k: v for k, v in result.items() if k != "selection_audit"}, indent=2))
        elif args.command == "parse-bhavcopy":
            path=Path(args.out)
            if path.exists():raise ValueError("Output exists")
            path.parent.mkdir(parents=True,exist_ok=True)
            frame=parse_bhavcopy(args.file,args.exchange);frame.to_csv(path,index=False)
            print(json.dumps({'raw_rows':len(frame),'adjusted':False,'exchange':args.exchange}))
        elif args.command == "repair-volumes":
            print(json.dumps(repair_zero_volumes(Dataset.load(args.data),args.bhavcopies,args.out),indent=2))
        elif args.command == "catalog":
            out=Path(args.out)
            if out.exists():raise ValueError("Output exists")
            out.parent.mkdir(parents=True,exist_ok=True)
            m=catalog_from_exports(args.nse_list,args.bse_list);m.to_csv(out,index=False)
            print(json.dumps({"listings":len(m),"distinct_known_isins":m.loc[m["isin"] != "","isin"].nunique(),"current_snapshot_only":True}))
        elif args.command == "bulk-download":
            print(json.dumps(bulk_library_download(args.catalog,args.start,args.end,args.out,args.limit,args.symbols_file),indent=2))
        elif args.command in ("discover","distance-study"):
            d=Dataset.load(args.data)
            if not args.exploratory and not d.manifest.get("synthetic") and not d.manifest.get("membership_audited"):
                raise ValueError("Unaudited universe: explicitly use --exploratory")
            master=load_master(args.security_master)
            c=DistanceConfig(args.formation_sessions,args.trading_sessions,args.top_pairs,128,args.min_turnover)
            if args.command == "discover":
                result=discover(d,master,c,args.as_of)
                save_marketwide(result,args.out)
                print(json.dumps({k:v for k,v in result.items() if k not in ("security_audit","pairs")},indent=2))
            else:
                if args.as_of:raise ValueError("distance-study uses the entire snapshot; supply a frozen cutoff snapshot instead")
                result=distance_study(d,master,c);save_marketwide(result,args.out)
                print(json.dumps({"cohorts":result["cohorts"],"outcomes":len(result["outcomes"]),"report":args.out},indent=2))
        elif args.command == "diagnose":
            d = Dataset.load(args.data)
            if not args.exploratory and not d.manifest.get("synthetic") and not d.manifest.get("membership_audited"):
                raise ValueError("Unaudited universe: explicitly use --exploratory")
            mapping = json.loads(Path(args.universe).read_text()).get("sectors") if args.universe else None
            result = diagnose(d, as_of=args.as_of, sectors=mapping, same_sector=not args.cross_sector)
            if args.universe:
                result["universe_declaration"] = json.loads(Path(args.universe).read_text())
            save_diagnostics(result, args.out)
            from collections import Counter
            print(json.dumps({"as_of": result["as_of"], "source": result["source"],
                              "pair_count": result["pair_count"],
                              "hypotheses": result["hypotheses_in_joint_holm_family"],
                              "benchmark_missing_sessions": len(result["benchmark_missing_sessions"]),
                              "classifications": dict(Counter(r["classification"] for r in result["pairs"])),
                              "report": str(Path(args.out) / "report.html")}, indent=2))
        elif args.command == "dashboard-demo":
            import tempfile
            import pandas as pd
            with tempfile.TemporaryDirectory() as temp:
                folder=Path(temp)/'demo';make_demo(folder)
                dataset=Dataset.load(folder)
                symbols=sorted(dataset.bars.symbol.unique())
                names=['Demo Aster Bank','Demo Birch Bank','Demo Northstar Digital','Demo Summit Digital','Demo Cedar Health','Demo Willow Health']
                master=pd.DataFrame({'symbol':symbols,'exchange':'SYNTHETIC','name':names,
                                     'isin':['SYNTHETIC'+str(i) for i in range(len(symbols))],
                                     'security_type':'EQUITY'}).set_index('symbol',drop=False)
                configs=[DistanceConfig(252,126,20,128,0),DistanceConfig(756,126,20,128,0)]
                discoveries=[discover(dataset,master,c) for c in configs]
                study=distance_study(dataset,master,configs[0])
                path=export_dashboard(build_bundle(dataset,master,discoveries,study),args.out)
            print(json.dumps({'dashboard':str(path/'index.html'),'synthetic':True,
                              'local_command':f'nifty-pairs serve --run {path}'},indent=2))
        elif args.command == "dashboard":
            dataset=Dataset.load(args.data)
            master=load_master(args.security_master)
            discoveries=[json.loads(Path(p).read_text()) for p in args.discoveries]
            study=json.loads(Path(args.study).read_text()) if args.study else None
            bundle=build_bundle(dataset,master,discoveries,study)
            path=export_dashboard(bundle,args.out)
            print(json.dumps({'dashboard':str(path/'index.html'),'pairs':sum(len(h['pairs']) for h in bundle['horizons']),
                              'as_of':bundle['as_of'],'local_command':f'nifty-pairs serve --run {path}'},indent=2))
        elif args.command == "serve":
            path = Path(args.run).resolve()
            if not (path / "report.html").is_file():
                raise ValueError("Run report not found")
            print(f"Read-only report: http://127.0.0.1:{args.port}/report.html", flush=True)
            ThreadingHTTPServer(("127.0.0.1", args.port), partial(SimpleHTTPRequestHandler, directory=str(path))).serve_forever()
    except (ValueError, OSError, ImportError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
