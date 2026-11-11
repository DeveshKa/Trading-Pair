"""Normalize official listing exports; no guessed ticker or company-name joins."""
import json
from pathlib import Path
import pandas as pd


def catalog_from_exports(nse_path=None,bse_path=None):
    rows=[]
    if nse_path:
        nse=pd.read_csv(nse_path,dtype=str).fillna("")
        nse.columns=nse.columns.str.strip()
        if not {"SYMBOL","ISIN NUMBER","NAME OF COMPANY","SERIES"} <= set(nse):
            raise ValueError("Unrecognized NSE equity-list export")
        for r in nse.to_dict("records"):
            rows.append({"symbol":r["SYMBOL"]+".NS","exchange":"NSE","isin":r["ISIN NUMBER"].strip(),
                         "name":r["NAME OF COMPANY"],"security_type":"EQUITY","series":r["SERIES"],
                         "listed_at":r.get("DATE OF LISTING","")})
    if bse_path:
        bse=pd.read_csv(bse_path,dtype=str).fillna("");bse.columns=bse.columns.str.strip()
        # Both official exported names and the canonical import contract are accepted.
        aliases={"Security Code":"code","SCRIP_CD":"code","scrip_cd":"code",
                 "ISIN No":"isin","ISIN_NUMBER":"isin","ISIN":"isin",
                 "Security Name":"name","Scrip_Name":"name"}
        bse=bse.rename(columns={k:v for k,v in aliases.items() if k in bse})
        if not {"code","isin","name"} <= set(bse):
            raise ValueError("BSE export needs Security Code/ISIN No/Security Name or code/isin/name")
        for r in bse.to_dict("records"):
            if not r["code"].isdigit():
                raise ValueError("Invalid BSE security code")
            rows.append({"symbol":r["code"]+".BO","exchange":"BSE","isin":r["isin"].strip(),
                         "name":r["name"],"security_type":r.get("security_type","EQUITY"),
                         "series":r.get("Group",""),"listed_at":r.get("listed_at","")})
    if not rows:raise ValueError("Supply an official NSE or BSE export")
    result=pd.DataFrame(rows)
    if result.symbol.duplicated().any():raise ValueError("Duplicate exchange symbols")
    return result


def bulk_library_download(catalog_path,start,end,destination,limit=100,symbols_path=None):
    """Resumable library pilot. Failed instruments remain in the acquisition ledger.

    Defaults are a bounded pilot, never an assertion of all-exchange historical coverage.
    """
    from .data import YFinanceProvider, Dataset, write_dataset
    from .marketwide import load_master
    master=load_master(catalog_path)
    if pd.Timestamp(start) >= pd.Timestamp(end):raise ValueError("start must precede exclusive end")
    if limit < 1:raise ValueError("limit must be positive")
    if symbols_path:
        requested=[s.strip() for s in Path(symbols_path).read_text().splitlines() if s.strip()]
        if len(set(requested)) != len(requested) or any(s not in master.index for s in requested):
            raise ValueError("Symbol file must contain unique symbols present in the catalog")
    else:
        requested=sorted(master.index)
    requested=requested[:limit]
    root=Path(destination);root.mkdir(parents=True,exist_ok=True)
    request={"start":start,"end":end,"symbols":requested}
    spec=root/"request.json"
    if spec.exists() and json.loads(spec.read_text()) != request:
        raise ValueError("Resume request differs; use a new acquisition directory")
    spec.write_text(json.dumps(request,indent=2))
    chunks=root/"chunks";chunks.mkdir(exist_ok=True)
    ledger=[];frames=[];benchmark=None;provider=YFinanceProvider()
    for number,symbol in enumerate(requested):
        path=chunks/str(number)
        try:
            if not path.exists():
                provider.download([symbol],start,end,path,diagnostics_only=True)
            d=Dataset.load(path)
            if d.manifest.get("symbols") != [symbol]:raise ValueError("Cached symbol mismatch")
            frames.append(d.bars);benchmark=d.benchmark if benchmark is None else benchmark
            ledger.append({"symbol":symbol,"status":"OK","rows":len(d.bars),"digest":d.digest})
        except Exception as exc:
            ledger.append({"symbol":symbol,"status":"FAILED","error":f"{type(exc).__name__}: {exc}"})
        (root/"acquisition.json").write_text(json.dumps(ledger,indent=2))
        if ledger[-1]["status"] == "FAILED" and ("429" in ledger[-1]["error"] or "RateLimit" in ledger[-1]["error"]):
            break # Stop on provider throttling; do not hammer or hide skipped requests.
    attempted={r["symbol"] for r in ledger}
    ledger.extend({"symbol":s,"status":"NOT_ATTEMPTED"} for s in requested if s not in attempted)
    (root/"acquisition.json").write_text(json.dumps(ledger,indent=2))
    if len(frames)<2:raise ValueError("Fewer than two successful instruments; see acquisition.json")
    combined=pd.concat(frames,ignore_index=True)
    successful={r["symbol"] for r in ledger if r["status"] == "OK"}
    (root/"security_master.csv").write_text(master.loc[sorted(successful)].to_csv(index=False))
    snapshot=root/"snapshot"
    if snapshot.exists():
        raise ValueError("Merged snapshot already exists; cached acquisition can be inspected without overwriting it")
    write_dataset(snapshot,combined,benchmark,
                  {"source":"yfinance_bulk_current_listing_pilot","price_basis":"raw_execution",
                   "benchmark_kind":"PRICE_INDEX","usage":"relationship_diagnostics_only",
                   "actions_complete":False,"membership_audited":False,"universe_kind":"CURRENT_SURVIVORS_ONLY",
                   "start":start,"end_exclusive":end,"requested":len(requested),"successful":len(successful),
                   "failures_and_skips":len(requested)-len(successful),
                   "note":"No delisted-coverage or all-NSE/BSE completeness claim"})
    return {"requested":len(requested),"successful":len(successful),"snapshot":str(snapshot),
            "security_master":str(root/"security_master.csv"),"ledger":str(root/"acquisition.json")}
