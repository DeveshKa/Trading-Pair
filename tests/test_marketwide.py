from dataclasses import replace
import json
import numpy as np
import pandas as pd
import pytest
from nifty_pairs.catalog import catalog_from_exports
from nifty_pairs.data import Dataset,make_demo
from nifty_pairs.marketwide import DistanceConfig,discover,exact_neighbours,forward_convergence,distance_study
from nifty_pairs.config import Config


@pytest.fixture
def sample(tmp_path):
    p=tmp_path/'data';make_demo(p,500)
    d=Dataset.load(p)
    symbols=sorted(d.bars.symbol.unique())
    master=pd.DataFrame({'symbol':symbols,'exchange':'SYNTHETIC',
                         'isin':['TEST'+str(i) for i in range(len(symbols))],'security_type':'EQUITY'}).set_index('symbol',drop=False)
    return d,master


def test_blocked_search_matches_brute_force():
    rng=np.random.default_rng(8);x=np.exp(rng.normal(0,.1,(37,70)));x/=x[:,[0]]
    names=[f'S{i:03}' for i in range(len(x))]
    expected=sorted((float(np.mean((x[i]-x[j])**2)),names[i],names[j])
                    for i in range(len(x)) for j in range(i+1,len(x)))[:20]
    for block in (1,8,128):
        assert exact_neighbours(x,names,20,block)==expected


def test_discovery_has_no_correlation_or_sector_gate(sample):
    d,m=sample
    r=discover(d,m,DistanceConfig(min_median_turnover_inr=0))
    assert r['eligible_distinct_securities']==6
    assert r['candidate_pair_count']==15
    assert len(r['pairs'])==15
    assert not any('correlation' in k or 'pvalue' in k for p in r['pairs'] for k in p)


def test_same_security_two_venues_never_forms_pair(sample):
    d,m=sample
    duplicate=d.bars.loc[d.bars.symbol=='DEMO00'].copy();duplicate['symbol']='BSE_ALIAS';duplicate['volume']*=2
    bars=pd.concat([d.bars,duplicate],ignore_index=True)
    alias=m.loc[['DEMO00']].copy();alias['symbol']='BSE_ALIAS';alias['exchange']='BSE';alias.index=['BSE_ALIAS']
    r=discover(replace(d,bars=bars),pd.concat([m,alias]),DistanceConfig(min_median_turnover_inr=0))
    assert r['eligible_distinct_securities']==6
    assert any(x['symbol']=='DEMO00' and x['reason']=='DUPLICATE_SECURITY_OTHER_VENUE' for x in r['security_audit'])
    assert all(p['isin_a'] != p['isin_b'] for p in r['pairs'])
    assert all('DEMO00' not in (p['a'],p['b']) for p in r['pairs'])


def test_future_data_cannot_change_discovery(sample):
    d,m=sample;date=sorted(d.bars.date.unique())[300]
    a=discover(d,m,as_of=date)
    changed=d.bars.copy();changed.loc[changed.date>date,'adj_close']*=100
    assert discover(replace(d,bars=changed),m,as_of=date)==a


def test_missing_or_untraded_prices_are_not_filled(sample):
    d,m=sample;bars=d.bars.copy();bars.loc[(bars.symbol=='DEMO00') & (bars.date==bars.date.max()),'volume']=0
    r=discover(replace(d,bars=bars),m)
    assert r['eligible_distinct_securities']==5
    assert any(x['symbol']=='DEMO00' and x['reason']=='INCOMPLETE_OR_UNTRADED_FORMATION' for x in r['security_audit'])


def test_old_cohorts_do_not_require_future_survival(sample):
    d,m=sample;cutoff=sorted(d.bars.date.unique())[300]
    # A listing disappears after formation: still forms then; its later window is not invented.
    bars=d.bars.loc[~((d.bars.symbol=='DEMO00') & (d.bars.date>cutoff))]
    r=discover(replace(d,bars=bars),m,as_of=cutoff)
    assert r['eligible_distinct_securities']==6
    outcomes=forward_convergence(replace(d,bars=bars),r)
    assert any(o['status']=='INCOMPLETE_FORWARD_WINDOW' for o in outcomes if 'DEMO00' in (o['a'],o['b']))


def test_study_is_formation_before_forward_period(sample):
    d,m=sample
    r=distance_study(d,m,DistanceConfig(252,126,5,16,0))
    assert r['cohorts']>0
    assert all(o['forward_sessions']==126 for o in r['outcomes'])
    assert all(o['converged']<=o['opened'] for o in r['outcomes'])
    assert all(o['window_complete'] for o in r['outcomes'])


def test_zero_volume_forward_window_is_not_claimed_complete(sample):
    d,m=sample;dates=sorted(d.bars.date.unique())
    result=discover(d,m,DistanceConfig(min_median_turnover_inr=0),dates[300])
    changed=d.bars.copy();changed.loc[changed.date==dates[320],'volume']=0
    outcomes=forward_convergence(replace(d,bars=changed),result)
    assert all(o['status']=='INVALID_FORWARD_OBSERVATIONS' for o in outcomes)
    assert all(not o['window_complete'] and o['opened']==0 for o in outcomes)


def test_current_nse_and_bse_exports_normalize_without_name_matching(tmp_path):
    n=tmp_path/'n.csv';b=tmp_path/'b.csv'
    pd.DataFrame({'SYMBOL':['A'],'NAME OF COMPANY':['Company'],' SERIES':['EQ'],' ISIN NUMBER':['INE000000001']}).to_csv(n,index=False)
    pd.DataFrame({'Security Code':['500000'],'Security Name':['Different name'],'ISIN No':['INE000000001']}).to_csv(b,index=False)
    r=catalog_from_exports(n,b)
    assert set(r.symbol)=={'A.NS','500000.BO'}
    assert r['isin'].nunique()==1


def test_identical_paths_are_not_an_automatic_trade():
    x=np.ones((3,60))
    result=exact_neighbours(x,['A','B','C'],3)
    assert result==[(0.,'A','B'),(0.,'A','C'),(0.,'B','C')]


def test_active_defaults_return_to_distance_without_sector_gate():
    assert Config().strategy=='distance'
    assert Config().same_sector is False
