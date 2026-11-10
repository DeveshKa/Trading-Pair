"""As-of research gap cards. Never claims that a historical gap is trade-ready."""
import json
from pathlib import Path
import pandas as pd
from .alerts import AlertStore
from .selection import select_pairs


def scan(dataset, config, as_of=None):
    date = pd.Timestamp(as_of) if as_of else dataset.bars.date.max()
    available = sorted(dataset.bars.loc[dataset.bars.date <= date, "date"].unique())
    if not available:
        raise ValueError("No observations at or before requested date")
    date = available[-1]
    models, audit = select_pairs(dataset, date, config)
    bars = dataset.bars.loc[dataset.bars.date == date].set_index("symbol")
    prior = dataset.bars.loc[dataset.bars.date == available[-2]].set_index("symbol") if len(available)>1 else None
    cards = []
    for model in models:
        z = model.zscore(bars.loc[model.a, "adj_close"], bars.loc[model.b, "adj_close"])
        old = model.zscore(prior.loc[model.a, "adj_close"], prior.loc[model.b, "adj_close"]) if prior is not None else z
        crossing = old < config.entry_z <= z or old > -config.entry_z >= z
        state = ("BLOCKED_CATASTROPHIC_GAP" if abs(z) >= config.stop_z else
                 "RESEARCH_CROSSING" if crossing else
                 "RESEARCH_DIVERGENCE" if abs(z) >= config.entry_z else "WATCHING")
        cards.append({**model.to_dict(), "as_of": str(pd.Timestamp(date).date()), "z": z,
                      "prior_z_under_same_model": old, "state": state,
                      "direction_if_qualified": "SHORT_A_LONG_B" if z > 0 else "LONG_A_SHORT_B",
                      "execution_ready": False,
                      "blocked_reasons": ["NO_LIVE_QUOTE_VALIDATION", "NO_CONFIRMED_BORROW_OR_FUTURES",
                                          "RESEARCH_SCAN_REFITS_AS_OF_DATE_NOT_MONTHLY_REPLAY"]})
    return {"as_of": str(pd.Timestamp(date).date()), "snapshot": dataset.digest,
            "source": dataset.manifest["source"], "synthetic": dataset.manifest.get("synthetic", False),
            "status": "RESEARCH_ONLY" if cards else "NO_QUALIFIED_PAIRS",
            "pairs": cards, "selection_audit": audit}


def save_scan(result, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "gaps.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    store = AlertStore(folder / "alerts.sqlite")
    for card in result["pairs"]:
        store.put(f"{result['snapshot']}:{card['model_id']}:{card['as_of']}:{card['state']}",
                  card["as_of"], card["state"], card)
