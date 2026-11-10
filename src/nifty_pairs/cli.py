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
    serve = sub.add_parser("serve", help="Serve one generated report locally (read-only)")
    serve.add_argument("--run", required=True)
    serve.add_argument("--port", type=int, default=8765)
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
                                       args.allow_calendar_intersection)
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
