"""Export verified research artifacts into a static interactive dashboard bundle."""
import hashlib
import json
from pathlib import Path
import shutil
import pandas as pd


def build_bundle(dataset, master, discoveries, study=None):
    if not discoveries:
        raise ValueError("At least one discovery result required")
    if any(d.get("snapshot") != dataset.digest for d in discoveries):
        raise ValueError("Discovery snapshot does not match dataset")
    if study and study.get("snapshot") != dataset.digest:
        raise ValueError("Study snapshot does not match dataset")
    if len({d["as_of"] for d in discoveries}) != 1:
        raise ValueError("Formation dates must agree across horizon exports")
    expected_master = hashlib.sha256(master.to_csv(index=False).encode()).hexdigest()
    if any(d.get("master_sha256") != expected_master for d in discoveries):
        raise ValueError("Security master does not match discovery identity")
    cutoff = pd.Timestamp(discoveries[0]['as_of'])
    dates = pd.DatetimeIndex(sorted(dataset.bars.date.unique()))
    completed_dates = set()
    if study:
        forward_count = study['config']['trading_sessions']
        for formation in study.get('formations', []):
            first_forward = dates.searchsorted(pd.Timestamp(formation['as_of']),side='right')
            end = first_forward + forward_count - 1
            if end < len(dates) and dates[end] <= cutoff:
                completed_dates.add(formation['as_of'])
    outcomes = [o for o in (study or {}).get('outcomes',[]) if o['formed_at'] in completed_dates]
    horizons=[]
    for discovery in discoveries:
        pairs=[]
        for pair in discovery["pairs"]:
            a,b=pair["a"],pair["b"]
            bars=dataset.bars.loc[(dataset.bars.date>=pair["formation_start"]) &
                                  (dataset.bars.date<=pair["formed_at"]) &
                                  dataset.bars.symbol.isin([a,b])]
            prices=bars.pivot(index="date",columns="symbol",values="adj_close")[[a,b]]
            if prices.isna().any().any() or len(prices)!=discovery["config"]["formation_sessions"]:
                raise ValueError("Incomplete price paths for dashboard")
            normalized=prices/prices.iloc[0]
            spread=normalized[a]-normalized[b]
            sigma=pair["formation_spread_std"]
            z=spread/sigma if sigma>1e-10 else spread*0
            def identity(symbol):
                r=master.loc[symbol]
                return {"symbol":symbol,"ticker":symbol.removesuffix('.NS').removesuffix('.BO'),
                        "name":str(r.get("name",symbol)),"exchange":str(r.exchange),"isin":str(r['isin'])}
            history=[dict(o) for o in outcomes if (o['a'],o['b'])==(a,b)] if study and study['config']['formation_sessions']==discovery['config']['formation_sessions'] else []
            valid=[o for o in history if o.get('window_complete')]
            series=[{"date":str(day.date()),"a":round(float(normalized.loc[day,a])*100,5),
                     "b":round(float(normalized.loc[day,b])*100,5),
                     "spread":round(float(spread.loc[day])*100,5),"z":round(float(z.loc[day]),5)}
                    for day in normalized.index]
            pairs.append({"id":a+'|'+b,"rank":pair['rank'],"a":identity(a),"b":identity(b),
                          "distance":pair['distance_mean_ssd'],"sum_distance":pair['distance_sum_ssd'],
                          "sigma":sigma,"gap_z":float(z.iloc[-1]),"gap_percent":float(spread.iloc[-1])*100,
                          "formation_start":pair['formation_start'],"formed_at":pair['formed_at'],
                          "state":"divergence" if abs(z.iloc[-1])>=2 else "watching",
                          "execution_ready":False,"series":series,"history":history,
                          "cohorts":len(history),"valid_cohorts":len(valid),
                          "openings":sum(o['opened'] for o in valid),"crossings":sum(o['converged'] for o in valid),
                          "unresolved":sum(o['unresolved'] for o in valid)})
        horizons.append({"sessions":discovery['config']['formation_sessions'],
                         "label":f"{discovery['config']['formation_sessions']//252}Y formation",
                         "eligible":discovery['eligible_distinct_securities'],
                         "comparisons":discovery['candidate_pair_count'],"pairs":pairs,
                         "study_cohorts":len(completed_dates) if study and study['config']['formation_sessions']==discovery['config']['formation_sessions'] else 0,
                         "audit":discovery['security_audit'],"config":discovery['config']})
    manifest=dataset.manifest
    bundle={"schema_version":1,"snapshot":dataset.digest,"as_of":discoveries[0]['as_of'],
            "synthetic":manifest.get('synthetic',False),"source":manifest['source'],
            "method":"Minimum distance","historical":True,
            "data_start":str(dataset.bars.date.min().date()),"data_end":str(dataset.bars.date.max().date()),
            "observations":len(dataset.bars),"observed_stocks":dataset.bars.symbol.nunique(),
            "study_cohorts":len(completed_dates),"horizons":horizons,
            "quality":{"membership_audited":manifest.get('membership_audited',False),
                       "actions_complete":manifest.get('actions_complete',False),
                       "unresolved_volume_cases":len(manifest.get('unresolved_volume_cases',[])),
                       "bse_loaded":bool((master.exchange=='BSE').any()),"live_feed_connected":False,
                       "notes":["Historical research snapshot; not live prices or order instructions.",
                                "Distance ranks similar paths; it does not establish future convergence.",
                                "Formation divergence is descriptive, not a confirmed forward-entry signal.",
                                "Crossings are observations, not profitable trades or portfolio returns.",
                                "Current-listing sample and corporate actions require further audit."]}}
    return bundle


def export_dashboard(bundle, destination, assets=None):
    assets=Path(assets) if assets else Path(__file__).parent/'web'
    out=Path(destination)
    if out.exists():raise ValueError("Dashboard output exists; choose a new directory")
    out.mkdir(parents=True)
    for name in ('index.html','styles.css','core.js','app.js'):
        shutil.copy2(assets/name,out/name)
    (out/'bundle.json').write_text(json.dumps(bundle,allow_nan=False,separators=(',',':')))
    (out/'report.html').write_text('<!doctype html><meta http-equiv="refresh" content="0;url=./index.html"><a href="./index.html">Open Pairwise</a>')
    return out
