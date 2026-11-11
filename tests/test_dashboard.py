from dataclasses import replace
import copy
import json
import pandas as pd
import pytest
from nifty_pairs.data import Dataset,make_demo
from nifty_pairs.marketwide import DistanceConfig,discover,distance_study
from nifty_pairs.dashboard import build_bundle,export_dashboard


@pytest.fixture
def sample(tmp_path):
    p=tmp_path/'data';make_demo(p,650);d=Dataset.load(p)
    symbols=sorted(d.bars.symbol.unique())
    m=pd.DataFrame({'symbol':symbols,'exchange':'SYNTHETIC','name':['Demo '+s for s in symbols],
                    'isin':['TEST'+str(i) for i in range(len(symbols))],'security_type':'EQUITY'}).set_index('symbol',drop=False)
    day=sorted(d.bars.date.unique())[500]
    discovery=discover(d,m,DistanceConfig(min_median_turnover_inr=0),day)
    study=distance_study(d,m,DistanceConfig(min_median_turnover_inr=0))
    return d,m,discovery,study


def test_bundle_has_real_names_paths_and_no_future_charts(sample):
    d,m,discovery,study=sample
    b=build_bundle(d,m,[discovery],study)
    assert b['synthetic']
    assert b['horizons'][0]['pairs']
    for p in b['horizons'][0]['pairs']:
        assert p['a']['name'].startswith('Demo ')
        assert len(p['series'])==252
        assert p['series'][0]['a']==100
        assert p['series'][-1]['date']==b['as_of']
        assert not p['execution_ready']
        # Every attached cohort outcome must end no later than the displayed snapshot.
        dates=pd.DatetimeIndex(sorted(d.bars.date.unique()))
        for o in p['history']:
            end=dates.searchsorted(pd.Timestamp(o['formed_at']),side='right')+125
            assert dates[end]<=pd.Timestamp(b['as_of'])


def test_mismatched_snapshot_or_master_cannot_be_mixed(sample):
    d,m,r,study=sample
    changed=copy.deepcopy(r);changed['snapshot']='wrong'
    with pytest.raises(ValueError,match='snapshot'):build_bundle(d,m,[changed])
    changed_master=m.copy();changed_master.loc[changed_master.index[0],'isin']='DIFFERENT'
    with pytest.raises(ValueError,match='identity'):build_bundle(d,changed_master,[r])


def test_three_year_cards_do_not_claim_one_year_backtests(sample):
    d,m,r,study=sample
    r=copy.deepcopy(r);r['config']['formation_sessions']=756
    # Cannot merely relabel a 252-session discovery as a 756-session series.
    with pytest.raises(ValueError,match='Incomplete'):build_bundle(d,m,[r],study)


def test_export_is_self_contained_and_does_not_overwrite(sample,tmp_path):
    d,m,r,study=sample;b=build_bundle(d,m,[r],study)
    out=tmp_path/'dashboard';export_dashboard(b,out)
    for name in ['index.html','styles.css','app.js','core.js','bundle.json','report.html']:assert (out/name).is_file()
    assert json.loads((out/'bundle.json').read_text())['snapshot']==d.digest
    with pytest.raises(ValueError,match='exists'):export_dashboard(b,out)
