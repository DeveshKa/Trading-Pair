import pandas as pd
import pytest
from dataclasses import replace
from nifty_pairs.archives import parse_bhavcopy,repair_zero_volumes
from nifty_pairs.data import Dataset,make_demo


def write_udiff(path,symbol='DEMO00',close=100,volume=10000):
    pd.DataFrame({'TradDt':['2019-05-03'],'TckrSymb':[symbol],'SctySrs':['EQ'],
                  'ISIN':['TEST0'],'OpnPric':[close],'HghPric':[close],'LwPric':[close],
                  'ClsPric':[close],'TtlTradgVol':[volume],'TtlTrfVal':[close*volume],
                  'FinInstrmId':[500000]}).to_csv(path,index=False)


def test_bse_udiff_retains_security_code_and_isin(tmp_path):
    p=tmp_path/'bse.csv';write_udiff(p)
    d=parse_bhavcopy(p,'BSE')
    assert d.iloc[0].symbol=='500000.BO'
    assert d.iloc[0]['isin']=='TEST0'


def test_unsupported_legacy_bse_is_not_given_guessed_identity(tmp_path):
    p=tmp_path/'old.csv';pd.DataFrame({'SC_CODE':[500000],'CLOSE':[100]}).to_csv(p,index=False)
    with pytest.raises(ValueError,match='dated security-master'):
        parse_bhavcopy(p,'BSE')


def test_volume_overlay_requires_price_agreement_and_preserves_other_rows(tmp_path):
    folder=tmp_path/'demo';make_demo(folder,400);d=Dataset.load(folder)
    bars=d.bars.copy();bars.loc[bars.symbol=='DEMO00','symbol']='DEMO00.NS'
    date=pd.Timestamp('2019-05-03');mask=(bars.date==date)&(bars.symbol=='DEMO00.NS')
    close=bars.loc[mask,'close'].iloc[0];bars.loc[mask,'volume']=0
    changed=replace(d,bars=bars)
    wrong=tmp_path/'wrong.csv';write_udiff(wrong,close=close*2)
    result=repair_zero_volumes(changed,[wrong],tmp_path/'wrong_out')
    assert result['repaired']==0 and result['unresolved']==1
    correct=tmp_path/'right.csv';write_udiff(correct,close=close)
    result=repair_zero_volumes(changed,[correct],tmp_path/'right_out')
    out=Dataset.load(tmp_path/'right_out')
    assert result['repaired']==1
    assert len(out.bars)==len(d.bars)
    assert out.bars.loc[(out.bars.date==date)&(out.bars.symbol=='DEMO00.NS'),'volume'].iloc[0]==10000
    assert out.manifest['volume_repairs'][0]['old']==0
