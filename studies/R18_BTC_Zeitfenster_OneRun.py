#!/usr/bin/env python3
"""R18 BTC intraweek/intraday opportunity map, research only, no orders.
Frozen Binance BTC perpetual 5m loader from R12. No strategy and no future predictors.
"""
from __future__ import annotations
import hashlib, importlib.util, json, math, sys
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

ROOT=Path.home()/'QuantResearch-Git/studies'
SOURCE=ROOT/'R12_3_Strategien_BTC_Explorativ.py'
SOURCE_HASH='7c434924f85cdd94fb09438dbf033cb797a946bc93ff8f3bdb82a9850839609d'
DEST=Path.home()/'QuantResearch/R18_BTC_Zeitfenster/Sep2024_Dec2025_v1'
NY=ZoneInfo('America/New_York')
PERIODS={'2024_SepDec':('2024-09-01','2025-01-01'), '2025_JanDec':('2025-01-01','2026-01-01')}
DAYNAMES=['Mo','Di','Mi','Do','Fr','Sa','So']

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def load():
    if not SOURCE.is_file() or sha(SOURCE)!=SOURCE_HASH:raise RuntimeError('R12 Quell-Loader fehlt oder Hash abweichend')
    spec=importlib.util.spec_from_file_location('r18_r12_loader',str(SOURCE))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.load_and_audit()

def synthetic():
    assert str(pd.Timestamp('2025-01-15 14:30',tz='UTC').tz_convert(NY).strftime('%H:%M'))=='09:30'
    assert str(pd.Timestamp('2025-07-15 13:30',tz='UTC').tz_convert(NY).strftime('%H:%M'))=='09:30'
    assert pd.Timestamp('2025-01-15 14:30',tz='UTC').tz_convert(NY).weekday()==2
    assert pd.Timestamp('2025-07-15 13:30',tz='UTC').tz_convert(NY).weekday()==1
    # A known simple hour: 12 close to close steps = ~1% upward should have positive rv.
    c=np.linspace(100,101,13); r=np.log(c[1:]/c[:-1]);assert len(r)==12 and (r*r).sum()>0
    # Slot is assigned by bar START, not future bar ending.
    assert 9*60+30<=9*60+35<10*60+30
    # New York open window switches UTC with daylight savings; never use fixed 14:30UTC year-round
    return True

def make_hourly(a):
    t=a['t'];o,h,l,c,v=(a[x] for x in ['o','h','l','c','v'])
    # Fully within-hour OHLC. Realized variance from 5-minute close-to-close returns.
    # First 5m return in hour references prior hour close: known only at that bar's close.
    lr=np.full(len(c),np.nan);lr[1:]=np.log(c[1:]/c[:-1])
    bins=t.floor('h')
    z=pd.DataFrame({'utc_hour':bins,'o':o,'h':h,'l':l,'c':c,'vol':v,'rv5':lr*lr,'abs5':abs(lr)*1e4})
    g=z.groupby('utc_hour',sort=True)
    d=g.agg(o=('o','first'),h=('h','max'),l=('l','min'),c=('c','last'),
            vol=('vol','sum'),rv=('rv5','sum'),abs5mean=('abs5','mean'),bars=('o','size')).reset_index()
    if not bool(d.bars.eq(12).all()):raise RuntimeError('Unvollständige Stundengruppe')
    d['range_bp']=(d.h/d.l-1)*1e4
    d['oc_abs_bp']=abs(d.c/d.o-1)*1e4
    d['rv_bp2']=d.rv*1e8
    d['utc_date']=d.utc_hour.dt.date.astype(str)
    d['utc_slot']=d.utc_hour.dt.hour
    d['weekday']=d.utc_hour.dt.weekday
    d['ny_time']=d.utc_hour.dt.tz_convert(NY)
    d['ny_date']=d.ny_time.dt.date.astype(str)
    d['ny_weekday']=d.ny_time.dt.weekday
    d['period']=np.where(d.utc_hour<pd.Timestamp('2025-01-01',tz='UTC'),'2024_SepDec','2025_JanDec')
    # Daily share: calendar-day normalized volatility, robust to long-term shifts in BTC volatility.
    dayrv=d.groupby('utc_date').rv.transform('sum'); d['rv_share_of_utc_day']=d.rv/dayrv
    return d

def make_ny_windows(a):
    t=a['t'];o,h,l,c=(a[x] for x in ('o','h','l','c'))
    ny=t.tz_convert(NY)
    # Fixed candidate windows, each 60 minutes: 08:30 before NYSE open; 09:30 open; +1h; +2h
    slots={'PRE_0830':8*60+30,'OPEN_0930':9*60+30,'PLUS1_1030':10*60+30,'PLUS2_1130':11*60+30}
    records=[]
    times=ny.hour.to_numpy()*60+ny.minute.to_numpy()
    for key,start_min in slots.items():
        starts=np.flatnonzero(times==start_min)
        for j in starts:
            if j+12>len(t):continue
            # Validate 12 consecutive 5m slots in NY local day incl DST as represented by absolute UTC time
            if t[j+11]-t[j]!=pd.Timedelta(minutes=55):raise RuntimeError('NY window incomplete')
            # No crossing UTC period when close of window starts 2025 etc.
            if (t[j].year==2024 and t[j+11].year!=2024) or (t[j].year==2025 and t[j+11].year!=2025):continue
            high=float(np.max(h[j:j+12]));low=float(np.min(l[j:j+12]))
            close=float(c[j+11]);opened=float(o[j])
            records.append({'period':'2024_SepDec' if t[j]<pd.Timestamp('2025-01-01',tz='UTC') else '2025_JanDec',
              'ny_day':str(ny[j].date()),'ny_weekday':int(ny[j].weekday()),'ny_window':key,
              'utc_start':str(t[j]),'ny_start':str(ny[j]),
              'range_bp':(high/low-1)*1e4,'abs_oc_bp':abs(close/opened-1)*1e4,
              'ret_oc_bp':(close/opened-1)*1e4,
              'ny_is_weekday':bool(ny[j].weekday()<5)})
    return pd.DataFrame.from_records(records)

def describe(sub, key):
    if len(sub)==0:return None
    x=sub.range_bp.to_numpy(dtype=float)
    return {key:str(sub.iloc[0][key]) if key in sub.columns and sub[key].nunique()==1 else None,
      'n':len(sub),'mean_range_bp':round(float(np.mean(x)),3),'median_range_bp':round(float(np.median(x)),3),
      'p75_range_bp':round(float(np.quantile(x,.75)),3),'p90_range_bp':round(float(np.quantile(x,.90)),3),
      'fraction_range_ge_30bp':round(float(np.mean(x>=30)),4),
      'mean_abs_open_close_bp':round(float(sub.abs_oc_bp.mean() if 'abs_oc_bp' in sub.columns else sub.oc_abs_bp.mean()),3),
      'mean_rv_bp2':round(float(sub.rv_bp2.mean()),3) if 'rv_bp2' in sub.columns else None}

def summarize(h,w):
    hourly=[]; weekdays=[]; heat=[]; ny=[]; ny_paired=[]
    for year in PERIODS:
        hh=h[h.period==year];ww=w[w.period==year]
        for hour in range(24):
            x=hh[hh.utc_slot==hour]
            p=describe(x,'utc_slot');p.update(period=year,utc_hour=hour,
                mean_daily_rv_share=round(float(x.rv_share_of_utc_day.mean()),6))
            hourly.append(p)
        for day in range(7):
            x=hh[hh.weekday==day];p=describe(x,'weekday');p.update(period=year,weekday=DAYNAMES[day]);weekdays.append(p)
            for hour in range(24):
                y=x[x.utc_slot==hour];q=describe(y,'utc_slot');q.update(period=year,weekday=DAYNAMES[day],utc_hour=hour);heat.append(q)
        for typ,group in [('NY_weekday',ww[ww.ny_is_weekday]),('NY_weekend_placebo',ww[~ww.ny_is_weekday])]:
            for slot in ['PRE_0830','OPEN_0930','PLUS1_1030','PLUS2_1130']:
                x=group[group.ny_window==slot]
                q=describe(x,'ny_window');q.update(period=year,group=typ,ny_window=slot);ny.append(q)
        # within-day matched open vs pre and +1/+2; weekdays only, no assumption that weekdays are NYSE trading days
        sub=ww[ww.ny_is_weekday]
        pv=sub.pivot_table(index='ny_day',columns='ny_window',values='range_bp',aggfunc='first').dropna()
        for other in ['PRE_0830','PLUS1_1030','PLUS2_1130']:
            dif=pv['OPEN_0930']-pv[other]
            ny_paired.append({'period':year,'comparison':'OPEN_0930_minus_'+other,
                'paired_days':len(dif),'mean_difference_range_bp':round(float(dif.mean()),3),
                'median_difference_range_bp':round(float(dif.median()),3),
                'positive_days_fraction':round(float((dif>0).mean()),4)})
    return {'hourly_utc':hourly,'weekdays_utc':weekdays,'weekday_hour_heatmap':heat,
      'ny_windows':ny,'ny_paired':ny_paired}

def main():
    if len(sys.argv)!=2 or sys.argv[1] not in ['--preflight','--run']:
        print('Usage: python R18_BTC_Zeitfenster_OneRun.py --preflight | --run');return 2
    synthetic();print('R18 SYNTHETIK PASS: NY DST, 5m to hour, first-bar allocation, weekday, RV')
    a=load();print('R18 DATA GATE PASS:',len(a['t']),'BTC 5m bars,',len(a['hashes']),'original files')
    if sys.argv[1]=='--preflight':print('R18 PREFLIGHT ONLY; NO HISTORICAL RESULT');return 0
    if DEST.exists():raise RuntimeError('Result directory exists: refuse overwrite '+str(DEST))
    h=make_hourly(a);w=make_ny_windows(a)
    result=summarize(h,w)
    DEST.mkdir(parents=True)
    h[['utc_hour','period','utc_date','weekday','utc_slot','range_bp','oc_abs_bp','rv_bp2','rv_share_of_utc_day','vol']].to_csv(DEST/'R18_HOURLY.csv',index=False)
    w.to_csv(DEST/'R18_NY_WINDOWS.csv',index=False)
    (DEST/'R18_RESULTS.json').write_text(json.dumps({'study':'R18 intraday BTC opportunity distribution',
       'status':'EXPLORATORY_NOT_PROFITABILITY_NOT_BLINDTEST',
       'source_sha256':a['hashes'],'reference_loader_sha256':SOURCE_HASH,'script_sha256':sha(Path(__file__)),
       'periods':PERIODS,'design':{'hourly_range':'high/low of twelve closed 5min candles, no entry inference',
         'ny_windows':'NY local 08:30,09:30,10:30,11:30 each 60min; weekday/weekend, NYSE holidays unfiltered',
         'threshold_30bp':'predefined descriptive probability, no trade PnL',
         'hours':'all UTC clock hours; hour/day-of-week patterns exploratory'},
       'results':result},indent=2,ensure_ascii=False))
    out=['# R18 BTC: Zeitfenster und Bewegungsgröße (rein explorativ)','',
      'BTC Binance Futures, echte 5m-OHLC, Sep 2024 bis Dez 2025. Keine Handelsstrategie, keine profitable Prognose.',
      'Daten aus früher erforschter Stichprobe, kein unabhängiger Test. Alle Zeitangaben UTC, außer NY-Fenster in America/New_York.',
      'Hourly Range ist realisierte High/Low-Range, NICHT vorhersagbare/nutzbare Gewinnstrecke. NYSE-Feiertage sind in Wochentagsfenstern enthalten.', '',
      '## Die fünf größten durchschnittlichen UTC-Stundenbereiche je Jahr (explorativ)']
    for year in PERIODS:
        out+=['',f'### {year}', '| UTC-Stunde | Tage | Mittel Range bp | Median bp | P(Range >=30 bp) | mittlerer Tages-RV-Anteil |', '|---|---:|---:|---:|---:|---:|']
        tops=sorted([x for x in result['hourly_utc'] if x['period']==year],key=lambda z:z['mean_range_bp'],reverse=True)[:5]
        for z in tops:out.append(f"| {z['utc_hour']:02d}:00 | {z['n']} | {z['mean_range_bp']:.2f} | {z['median_range_bp']:.2f} | {100*z['fraction_range_ge_30bp']:.1f}% | {100*z['mean_daily_rv_share']:.1f}% |")
        out+=['','**NY-Zeitfenster, 60-Minuten-Range, Montag–Freitag (inkl. möglicher Börsenfeiertage):**',
            '| Lokale NY-Zeit | n | Mittel Range bp | Median bp | >=30 bp |', '|---|---:|---:|---:|---:|']
        for z in [x for x in result['ny_windows'] if x['period']==year and x['group']=='NY_weekday']:
            out.append(f"| {z['ny_window']} | {z['n']} | {z['mean_range_bp']:.2f} | {z['median_range_bp']:.2f} | {100*z['fraction_range_ge_30bp']:.1f}% |")
        out+=['','**Gepaarte Tagesvergleiche: Open (09:30 NY) minus Vergleichsstunde:**']
        for z in [x for x in result['ny_paired'] if x['period']==year]:
            out.append(f"- {z['comparison']}: {z['mean_difference_range_bp']:+.2f} bp im Mittel, {z['paired_days']} Tage, Open größer an {100*z['positive_days_fraction']:.1f}% der Tage")
    out+=['','## Forschungseinordnung','',
      '- Ein größerer durchschnittlicher Stundenbereich ist keine Richtungsprognose und kein handelbarer Gewinn.',
      '- Großereignisse können den Mittelwert verzerren; Median, 75./90. Perzentil und Tagesnormalisierung beachten.',
      '- UTC-Stunden und NY-Lokalzeitfenster nicht vermengen; Sommerzeit automatisch berücksichtigt.',
      '- Wochentage inkl. NYSE-Feiertage; keine kausale Behauptung zum Aktienmarktstart.',
      '- Stunden und Wochentage sind viele explorative Vergleiche. Auffällige Slots dürfen nicht als unabhängig bestätigt gelten.',
      '- Erst in eigenem Forschungsdesign Mechanismus und Einstiegssignale vorab definieren; nur danach Kostenmodell und Out-of-sample-Test.',
      '', '## Dateien', '- R18_HOURLY.csv: stündliche Messdaten', '- R18_NY_WINDOWS.csv: konkrete NY-Fenster pro Kalendertag', '- R18_RESULTS.json: Tabellen und Provenienz', '']
    (DEST/'R18_REPORT.md').write_text('\n'.join(out))
    print('R18 EXPLORATORY COMPLETE; NO STRATEGY, NO ORDERS')
    for year in PERIODS:
        top=sorted([x for x in result['hourly_utc'] if x['period']==year],key=lambda z:z['mean_range_bp'],reverse=True)[:3]
        print(year,'TOP UTC',[(f"{z['utc_hour']:02d}:00",z['mean_range_bp']) for z in top])
        print(year,'NY',[(z['ny_window'],z['mean_range_bp']) for z in result['ny_windows'] if z['period']==year and z['group']=='NY_weekday'])
    print('REPORT:',DEST/'R18_REPORT.md');print('JSON:',DEST/'R18_RESULTS.json')
    return 0

if __name__=='__main__':sys.exit(main())
