"""Official raw daily archives: ingestion evidence, not adjusted trading snapshots."""
import hashlib
import io
import json
from pathlib import Path
import zipfile
import pandas as pd
import numpy as np


def read_csv_archive(path):
    path=Path(path);data=path.read_bytes()
    if zipfile.is_zipfile(io.BytesIO(data)):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names=[n for n in z.namelist() if n.lower().endswith('.csv')]
            if len(names)!=1:raise ValueError("Expected one CSV per archive")
            frame=pd.read_csv(io.BytesIO(z.read(names[0])))
    else:frame=pd.read_csv(io.BytesIO(data))
    frame.columns=frame.columns.str.strip()
    return frame


def parse_bhavcopy(path,exchange):
    raw=read_csv_archive(path)
    if {'TckrSymb','TradDt','SctySrs','ClsPric','TtlTradgVol'} <= set(raw):
        mapping={'TckrSymb':'exchange_symbol','TradDt':'date','SctySrs':'series','ISIN':'isin',
                 'OpnPric':'open','HghPric':'high','LwPric':'low','ClsPric':'close',
                 'TtlTradgVol':'volume','TtlTrfVal':'turnover','FinInstrmId':'instrument_id'}
        frame=raw.rename(columns=mapping)
        if exchange=='BSE':
            if 'instrument_id' not in frame:raise ValueError("BSE UDiFF needs its exchange instrument code")
            frame['symbol']=frame.instrument_id.astype(str).str.replace(r'\.0$','',regex=True)+'.BO'
        elif exchange=='NSE':frame['symbol']=frame.exchange_symbol.astype(str)+'.NS'
        else:raise ValueError("Exchange must be NSE or BSE")
    elif exchange=='NSE' and {'SYMBOL','SERIES','TIMESTAMP','ISIN','OPEN','CLOSE','TOTTRDQTY'} <= set(raw):
        frame=raw.rename(columns={'SYMBOL':'exchange_symbol','SERIES':'series','TIMESTAMP':'date','ISIN':'isin',
                                 'OPEN':'open','HIGH':'high','LOW':'low','CLOSE':'close','TOTTRDQTY':'volume','TOTTRDVAL':'turnover'})
        frame['symbol']=frame.exchange_symbol+'.NS'
    else:
        raise ValueError("Unrecognized archive schema. Legacy BSE without ISIN requires a dated security-master join.")
    required=['date','symbol','isin','open','high','low','close','volume','turnover','series']
    if not set(required)<=set(frame):raise ValueError("Archive lacks required fields")
    frame=frame[required].copy();frame['exchange']=exchange
    frame['date']=pd.to_datetime(frame.date,errors='raise',format='mixed').dt.normalize()
    if frame.date.nunique()!=1:raise ValueError("Expected one session per official archive")
    for column in ['open','high','low','close','volume','turnover']:
        frame[column]=pd.to_numeric(frame[column],errors='raise')
    return frame


def repair_zero_volumes(dataset, archive_paths, output):
    """Replace zero library quantity only when official date/symbol/close agree.

    No row is dropped; unverified records remain zero and fail formation eligibility.
    """
    from .data import write_dataset
    bars=dataset.bars.copy();repairs=[];unresolved=[];sources=[]
    for path in archive_paths:
        official=parse_bhavcopy(path,'NSE')
        official=official.loc[official.series=='EQ'].set_index(['date','symbol'])
        if official.index.duplicated().any():raise ValueError("Duplicate official date/symbol")
        sources.append({'file':Path(path).name,'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()})
        day=official.index.get_level_values('date')[0]
        for i,row in bars.loc[(bars.date==day) & (bars.volume<=0)].iterrows():
            key=(row.date,row.symbol)
            if key not in official.index:
                unresolved.append({'date':str(day.date()),'symbol':row.symbol,'reason':'NO_OFFICIAL_EQ_RECORD'});continue
            record=official.loc[key]
            # Match reporting/float precision, not a loose percentage of a daily move.
            if record.volume<=0 or not np.isclose(record.close,row.close,rtol=1e-6,atol=.005):
                unresolved.append({'date':str(day.date()),'symbol':row.symbol,'reason':'PRICE_OR_VOLUME_MISMATCH'});continue
            bars.loc[i,'volume']=record.volume
            repairs.append({'date':str(day.date()),'symbol':row.symbol,'field':'volume','old':float(row.volume),'new':float(record.volume)})
    manifest={**dataset.manifest,'source':dataset.manifest['source']+'+official_nse_volume_overlay',
              'volume_overlay_sources':sources,'volume_repairs':repairs,'unresolved_volume_cases':unresolved}
    manifest.pop('file_hashes',None)
    write_dataset(output,bars,dataset.benchmark,manifest,dataset.membership)
    return {'repaired':len(repairs),'unresolved':len(unresolved),'snapshot':str(output)}
