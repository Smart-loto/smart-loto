# ============================================================
# SMART-LOTO — V5.1 — COMPLETE + ALL FIXES
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import io, re

st.set_page_config(page_title="Smart-Loto V5", page_icon="🎱", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header {
        font-size:2.5rem;font-weight:800;
        background:linear-gradient(135deg,#1e40af,#7c3aed);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        text-align:center;padding:10px 0;
    }
    .sub-header {text-align:center;color:#475569 !important;font-size:1.1rem;margin-bottom:30px;}
    .boule {
        background:linear-gradient(135deg,#1e40af,#3b82f6);color:#fff !important;
        border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;
        justify-content:center;font-size:22px;font-weight:bold;margin:5px;
        box-shadow:0 4px 12px rgba(30,64,175,0.4);
    }
    .etoile {
        background:linear-gradient(135deg,#f59e0b,#fbbf24);color:#fff !important;
        border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;
        justify-content:center;font-size:22px;font-weight:bold;margin:5px;
        box-shadow:0 4px 12px rgba(245,158,11,0.4);
    }
    .grille-container {
        display:flex;align-items:center;justify-content:center;padding:25px;
        background:linear-gradient(135deg,#f8fafc,#e2e8f0);border-radius:20px;
        margin:15px 0;border:2px solid #e2e8f0;color:#1e293b !important;
    }
    .grille-container b,.grille-container strong{color:#1e293b !important;}
    .footer-disclaimer {
        background:#fef3c7;border:1px solid #f59e0b;border-radius:12px;padding:15px;
        margin-top:30px;text-align:center;font-size:0.9rem;color:#92400e !important;
    }
    .footer-disclaimer a{color:#b45309 !important;text-decoration:underline;}
    .alert-card {
        background:linear-gradient(135deg,#fef2f2,#fee2e2);border:2px solid #ef4444;
        border-radius:16px;padding:20px;margin:10px 0;color:#991b1b !important;
    }
    .alert-card b,.alert-card strong{color:#7f1d1d !important;}
    .alert-card span{color:#991b1b !important;}
    .success-card {
        background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:2px solid #22c55e;
        border-radius:16px;padding:20px;margin:10px 0;color:#166534 !important;
    }
    .success-card b,.success-card strong{color:#14532d !important;}
    .success-card span{color:#166534 !important;}
    .insight-card {
        background:linear-gradient(135deg,#eff6ff,#dbeafe);border:2px solid #3b82f6;
        border-radius:16px;padding:20px;margin:10px 0;color:#1e3a5f !important;
    }
    .insight-card b,.insight-card strong,.insight-card span{color:#1e3a5f !important;}
    .reco-card {
        background:linear-gradient(135deg,#fdf4ff,#f3e8ff);border:2px solid #a855f7;
        border-radius:16px;padding:20px;margin:10px 0;color:#581c87 !important;
    }
    .reco-card b,.reco-card strong,.reco-card span{color:#581c87 !important;}
    .buraliste-card {
        text-align:center;font-size:28px;font-weight:bold;padding:15px;
        background:#f8fafc;border-radius:12px;margin:8px 0;
        color:#1e293b !important;border:1px solid #e2e8f0;
    }
    .score-big{text-align:center;}
    .score-big .score-number{font-size:3rem;font-weight:800;}
    .score-big .score-label{color:#64748b !important;font-size:0.9rem;}
    .element-container div[data-testid="stMarkdownContainer"] > div{color:#1e293b;}
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions":{"nom":"Euromillions","emoji":"⭐","boules_max":50,"nb_boules":5,"etoiles_max":12,"nb_etoiles":2,"prix":2.50,"somme_min":90,"somme_max":160},
    "loto":{"nom":"Loto","emoji":"🎱","boules_max":49,"nb_boules":5,"etoiles_max":None,"nb_etoiles":0,"prix":2.20,"somme_min":60,"somme_max":180}
}

# ============================================================
# CSV LOADER
# ============================================================
def load_csv(up, jid):
    jeu=JEUX[jid]; dbg={}
    content=up.read(); up.seek(0); text=None
    for enc in ["utf-8-sig","utf-8","latin-1","cp1252"]:
        try: text=content.decode(enc); dbg["enc"]=enc; break
        except: continue
    if not text: return None,{"err":"Decode fail"}
    text=text.lstrip("\ufeff")
    df=None; sf=None
    for s in [";",",","\t"]:
        try:
            d=pd.read_csv(io.StringIO(text),sep=s,engine="python")
            d=d.loc[:,~d.columns.str.match(r'^Unnamed')]; d.columns=[c.strip() for c in d.columns]
            if len(d.columns)>=7 and(df is None or len(d.columns)>len(df.columns)): df=d; sf=s
        except: pass
    if df is None or len(df.columns)<7: return None,{**dbg,"err":"Not enough cols","cols":list(df.columns) if df is not None else []}
    dbg["cols"]=list(df.columns); cl={c.upper():c for c in df.columns}
    dc=None
    for c in ["DATE","date","DATE_DE_TIRAGE"]:
        if c in df.columns: dc=c; break
        if c.upper() in cl: dc=cl[c.upper()]; break
    if not dc:
        for c in df.columns:
            if "date" in c.lower(): dc=c; break
    if not dc: return None,{**dbg,"err":"No date col"}
    bc=[]
    for i in range(1,6):
        for c in [f"N{i}",f"n{i}",f"BOULE_{i}",f"boule_{i}"]:
            if c in df.columns: bc.append(c); break
            elif c.upper() in cl: bc.append(cl[c.upper()]); break
    if len(bc)<5:
        bc=[]
        for c in df.columns:
            if c==dc: continue
            try:
                v=pd.to_numeric(df[c],errors="coerce").dropna()
                if len(v)>len(df)*.3 and v.min()>=1 and v.max()<=jeu["boules_max"]: bc.append(c)
                if len(bc)>=5: break
            except: continue
    if len(bc)<5: return None,{**dbg,"err":f"Only {len(bc)} ball cols"}
    ec=[]
    if jeu["nb_etoiles"]>0:
        for i in range(1,3):
            for c in [f"E{i}",f"e{i}",f"ETOILE_{i}",f"etoile_{i}"]:
                if c in df.columns: ec.append(c); break
                elif c.upper() in cl: ec.append(cl[c.upper()]); break
    r=pd.DataFrame()
    for fmt in [None,"%d/%m/%Y","%Y-%m-%d"]:
        try:
            if fmt: r["date"]=pd.to_datetime(df[dc],format=fmt,errors="coerce").dt.date
            else: r["date"]=pd.to_datetime(df[dc],dayfirst=True,errors="coerce").dt.date
            if r["date"].notna().sum()>len(df)*.5: break
        except: continue
    for i,c in enumerate(bc[:5],1): r[f"boule_{i}"]=pd.to_numeric(df[c],errors="coerce")
    for i,c in enumerate(ec[:2],1): r[f"etoile_{i}"]=pd.to_numeric(df[c],errors="coerce")
    try:
        r["jour"]=pd.to_datetime(r["date"]).dt.day_name()
        jm={"Monday":"lundi","Tuesday":"mardi","Wednesday":"mercredi","Friday":"vendredi","Saturday":"samedi"}
        r["jour"]=r["jour"].map(lambda x:jm.get(x,x))
    except: r["jour"]="?"
    try: r["mois"]=pd.to_datetime(r["date"]).dt.month
    except: r["mois"]=0
    r=r.dropna(subset=["date","boule_1","boule_2","boule_3","boule_4","boule_5"])
    for i in range(1,6): r[f"boule_{i}"]=r[f"boule_{i}"].astype(int)
    for i in range(1,3):
        if f"etoile_{i}" in r.columns: r[f"etoile_{i}"]=r[f"etoile_{i}"].fillna(0).astype(int)
    for i in range(1,6): r=r[(r[f"boule_{i}"]>=1)&(r[f"boule_{i}"]<=jeu["boules_max"])]
    r=r.sort_values("date",ascending=False).drop_duplicates("date").reset_index(drop=True)
    dbg["ok"]=len(r)>0; dbg["n"]=len(r); dbg["map"]={"d":dc,"b":bc[:5],"e":ec[:2]}
    return r, dbg

def gen_simul(jid, nb=500):
    random.seed(42); np.random.seed(42); jeu=JEUX[jid]; t=[]; now=datetime.now()
    js=["mardi","vendredi"] if jid=="euromillions" else ["lundi","mercredi","samedi"]
    for i in range(nb):
        b=sorted(random.sample(range(1,jeu["boules_max"]+1),5))
        e=sorted(random.sample(range(1,jeu["etoiles_max"]+1),2)) if jeu["etoiles_max"] else []
        d={"date":(now-timedelta(days=i*3.5)).date(),"boule_1":b[0],"boule_2":b[1],"boule_3":b[2],"boule_4":b[3],"boule_5":b[4],"jour":js[i%len(js)],"mois":(now-timedelta(days=i*3.5)).month}
        if e: d["etoile_1"]=e[0]; d["etoile_2"]=e[1]
        t.append(d)
    return pd.DataFrame(t).sort_values("date",ascending=False).reset_index(drop=True)

# ============================================================
# STATS ENGINE
# ============================================================
@st.cache_data
def calc_stats(df_json, jid, jf=None):
    df=pd.read_json(io.StringIO(df_json)); df["date"]=pd.to_datetime(df["date"]).dt.date
    if jf and jf!="tous" and "jour" in df.columns:
        df=df[df["jour"].str.lower()==jf.lower()].reset_index(drop=True)
    jeu=JEUX[jid]; S={}; C=[f"boule_{i}" for i in range(1,6)]
    an=[]
    for c in C: an.extend(df[c].tolist())
    d20=df.head(20); n20=[]
    for c in C: n20.extend(d20[c].tolist())
    dt12=datetime.now().date()-timedelta(days=365); df12=df[df["date"]>=dt12]; n12=[]
    for c in C: n12.extend(df12[c].tolist())
    dt3=datetime.now().date()-timedelta(days=90); df3=df[df["date"]>=dt3]; n3=[]
    for c in C: n3.extend(df3[c].tolist())
    fa,f20,f12,f3=Counter(an),Counter(n20),Counter(n12),Counter(n3)
    for n in range(1,jeu["boules_max"]+1):
        ec=0
        for _,r in df.iterrows():
            if n in [int(r[c]) for c in C]: break
            ec+=1
        pos=[i for i,r in df.iterrows() if n in [int(r[c]) for c in C]]
        ech=[pos[i+1]-pos[i] for i in range(len(pos)-1)] if len(pos)>1 else []
        em=np.mean(ech) if ech else 10; ex=max(ech) if ech else ec
        es=np.std(ech) if len(ech)>1 else 5
        dn=None
        for _,r in df.iterrows():
            if n in [int(r[c]) for c in C]: dn=r["date"]; break
        fo=(f20.get(n,0)/max(len(d20),1))*100
        ft=(len(df12)*5)/jeu["boules_max"]; fn=(f12.get(n,0)/max(ft,1))*50
        ep=max(0,30-(ec*2)); ch=min(100,max(0,.4*fo+.35*fn+.25*ep))
        rr=(ec/ex*100) if ex>0 else 0
        if em>0: zz=(ec-em)/max(es,1); pb=min(99,max(1,50+zz*15))
        else: pb=50
        fp1=f3.get(n,0); fp2=f12.get(n,0)-f3.get(n,0)
        t1=fp1/max(len(df3),1)*100; t2=fp2/max(len(df12)-len(df3),1)*100
        td="↗️" if t1>t2*1.3 else ("↘️" if t1<t2*0.7 else "→")
        ret=max(0,round(em-ec))
        S[n]={"numero":n,"ecart":ec,"ecart_moy":round(em,1),"ecart_max":ex,"ecart_std":round(es,1),
            "freq_tot":fa.get(n,0),"f20":f20.get(n,0),"f12m":f12.get(n,0),"f3m":f3.get(n,0),
            "chaleur":round(ch,1),"dern":str(dn) if dn else "—","ratio_rec":round(rr,1),
            "proba":round(pb,1),"tend":td,"term":n%10,"diz":(n-1)//10,"retard":ret}
    se={}
    if jeu["nb_etoiles"] and "etoile_1" in df.columns:
        ce=[f"etoile_{i}" for i in range(1,jeu["nb_etoiles"]+1)]
        ae=[]; e20=[]
        for c in ce:
            if c in df.columns: ae.extend(df[c].tolist()); e20.extend(d20[c].tolist())
        fe,fe20=Counter(ae),Counter(e20)
        for n in range(1,jeu["etoiles_max"]+1):
            ec=0
            for _,r in df.iterrows():
                if n in [int(r[c]) for c in ce if c in df.columns]: break
                ec+=1
            se[n]={"numero":n,"ecart":ec,"freq_tot":fe.get(n,0),"f20":fe20.get(n,0)}
    paires=Counter()
    for _,r in df.iterrows():
        bs=sorted([int(r[c]) for c in C])
        for i in range(len(bs)):
            for j in range(i+1,len(bs)): paires[(bs[i],bs[j])]+=1
    analyses=[]
    for _,r in df.iterrows():
        bs=[int(r[c]) for c in C]
        analyses.append({"pairs":sum(1 for b in bs if b%2==0),"bas":sum(1 for b in bs if b<=25),
            "somme":sum(bs),"terms_diff":len(set(b%10 for b in bs)),"diz_diff":len(set((b-1)//10 for b in bs))})
    sommes=[a["somme"] for a in analyses]
    po={"somme_moy":round(np.mean(sommes),1),"somme_q1":round(np.percentile(sommes,25),1),
        "somme_q3":round(np.percentile(sommes,75),1),
        "pairs_moy":round(np.mean([a["pairs"] for a in analyses]),1),
        "bas_moy":round(np.mean([a["bas"] for a in analyses]),1),
        "terms_moy":round(np.mean([a["terms_diff"] for a in analyses]),1),
        "diz_moy":round(np.mean([a["diz_diff"] for a in analyses]),1)}
    saison={}
    if "mois" in df.columns:
        for m in range(1,13):
            dfm=df[df["mois"]==m]
            if len(dfm)>0:
                nm=[]
                for c in C: nm.extend(dfm[c].tolist())
                saison[m]={"nb":len(dfm),"top":Counter(nm).most_common(5)}
    return {"boules":S,"etoiles":se,"paires":paires.most_common(30),
        "analyses":analyses,"profil":po,"saison":saison,"nb_tirages":len(df),
        "date_1":str(df.iloc[-1]["date"]) if len(df)>0 else "—",
        "date_n":str(df.iloc[0]["date"]) if len(df)>0 else "—"}

# ============================================================
# SCORE
# ============================================================
def score_v5(gr, et, st_, jid):
    jeu=JEUX[jid]; sc={}; po=st_.get("profil",{})
    np2=sum(1 for n in gr if n%2==0)
    sc["⚖️ Parité"]=15 if abs(np2-po.get("pairs_moy",2.5))<=0.5 else (10 if abs(np2-po.get("pairs_moy",2.5))<=1.5 else 5)
    dz=Counter((n-1)//10 for n in gr)
    sc["📊 Dizaines"]=12 if len(dz)>=round(po.get("diz_moy",4)) else (8 if len(dz)>=round(po.get("diz_moy",4))-1 else 4)
    s=sum(gr); q1=po.get("somme_q1",90); q3=po.get("somme_q3",160)
    sc["➕ Somme"]=15 if q1<=s<=q3 else (10 if jeu["somme_min"]<=s<=jeu["somme_max"] else 3)
    ecs=[st_["boules"][n]["ecart"] for n in gr if n in st_["boules"]]
    sc["🔀 Diversité"]=(10 if float(np.std(ecs))>5 else (7 if float(np.std(ecs))>3 else 4)) if len(set(ecs))>1 else 4
    g=sorted(gr); hs=any(g[i+1]==g[i]+1 and g[i+2]==g[i]+2 for i in range(len(g)-2))
    sc["🚫 Suite"]=2 if hs else 8
    if et and len(et)==2: e=abs(et[0]-et[1]); sc["⭐ Étoiles"]=8 if e>=3 else (5 if e>=2 else 2)
    else: sc["⭐ Étoiles"]=8
    terms=set(n%10 for n in gr)
    sc["🔢 Terms"]=8 if len(terms)>=round(po.get("terms_moy",4)) else (5 if len(terms)>=round(po.get("terms_moy",4))-1 else 2)
    nb_bas=sum(1 for n in gr if n<=jeu["boules_max"]//2)
    sc["⬆️⬇️ B/H"]=8 if abs(nb_bas-po.get("bas_moy",2.5))<=0.5 else (5 if abs(nb_bas-po.get("bas_moy",2.5))<=1.5 else 2)
    chs=[st_["boules"][n]["chaleur"] for n in gr if n in st_["boules"]]
    mc=np.mean(chs) if chs else 50
    sc["🌡️ Chaleur"]=8 if 35<=mc<=65 else (5 if 20<=mc<=80 else 2)
    pbs=[st_["boules"][n]["proba"] for n in gr if n in st_["boules"]]
    mp=np.mean(pbs) if pbs else 50
    sc["📊 Proba"]=8 if mp>=55 else (5 if mp>=45 else 2)
    return {"total":sum(sc.values()),"detail":sc,"max":100}

# ============================================================
# GENERATOR
# ============================================================
def gen_grille(jid, st_, mode="aleatoire", fp=False, fs=False, fd=False, fa=False,
               chasseur=0, forces=None, ee=0, plafond="aucun",
               f_term=False, f_bh=False, pw_ch=50, pw_ec=50, pw_pr=50, mt=2000):
    jeu=JEUX[jid]
    for t in range(mt):
        if mode=="optimal":
            ns=list(st_["boules"].keys())
            sc=[(pw_ch/100)*st_["boules"][n]["chaleur"]+(pw_ec/100)*min(100,st_["boules"][n]["ecart"]*8)+(pw_pr/100)*st_["boules"][n]["proba"] for n in ns]
            sc=[s**1.5+1 for s in sc]; tp=sum(sc)
            pool=list(np.random.choice(ns,size=min(25,len(ns)),replace=False,p=[s/tp for s in sc]))
        elif mode=="contrarian": pool=sorted(st_["boules"],key=lambda x:st_["boules"][x]["freq_tot"])[:20]
        elif mode=="probabiliste": pool=sorted(st_["boules"],key=lambda x:st_["boules"][x]["proba"],reverse=True)[:20]
        elif mode=="tendance":
            pool=[n for n in st_["boules"] if st_["boules"][n]["tend"]=="↗️"]
            if len(pool)<10: pool+=sorted(st_["boules"],key=lambda x:st_["boules"][x]["chaleur"],reverse=True)[:20]
            pool=pool[:25]
        elif mode=="retard": pool=sorted(st_["boules"],key=lambda x:st_["boules"][x]["retard"])[:20]
        elif mode=="chaud": pool=sorted(st_["boules"],key=lambda x:st_["boules"][x]["chaleur"],reverse=True)[:20]
        elif mode=="froid": pool=sorted(st_["boules"],key=lambda x:st_["boules"][x]["ecart"],reverse=True)[:20]
        elif mode=="top": pool=sorted(st_["boules"],key=lambda x:st_["boules"][x]["f12m"],reverse=True)[:15]
        elif mode=="hybride":
            ns=list(st_["boules"].keys()); pw=[st_["boules"][n]["chaleur"]**1.5+5 for n in ns]
            tp=sum(pw); pool=list(np.random.choice(ns,size=min(25,len(ns)),replace=False,p=[p/tp for p in pw]))
        else: pool=list(range(1,jeu["boules_max"]+1))
        if plafond=="moins_40": pool=[n for n in pool if n<40]
        if chasseur>0:
            pf=[n for n in pool if st_["boules"][n]["ecart"]>=chasseur]
            if len(pf)>=5: pool=pf
        fo=[f for f in (forces or []) if 1<=f<=jeu["boules_max"]]
        di=[n for n in pool if n not in fo]; mq=5-len(fo)
        if mq>len(di): di=[n for n in range(1,jeu["boules_max"]+1) if n not in fo]
        ch=random.sample(di,min(mq,len(di))) if mq>0 else []
        gr=sorted(fo+ch)[:5]
        if plafond=="force_40" and not any(n>=40 for n in gr):
            s40=[n for n in range(40,jeu["boules_max"]+1) if n not in gr]
            nf=[n for n in gr if n not in fo]
            if s40 and nf:
                rm=min(nf,key=lambda x:st_["boules"][x]["chaleur"])
                gr.remove(rm); gr.append(random.choice(s40)); gr=sorted(gr)
        et=[]
        if jeu["nb_etoiles"] and jeu["etoiles_max"]:
            for _ in range(100):
                et=sorted(random.sample(range(1,jeu["etoiles_max"]+1),jeu["nb_etoiles"]))
                if ee>0 and len(et)==2 and abs(et[0]-et[1])>=ee: break
                elif ee==0: break
        v=True
        if fp: np2=sum(1 for n in gr if n%2==0); v=v and 0<np2<5
        if fs: v=v and jeu["somme_min"]<=sum(gr)<=jeu["somme_max"]
        if fd: v=v and max(Counter((n-1)//10 for n in gr).values())<=3
        if fa: gs=sorted(gr); v=v and not any(gs[i+1]==gs[i]+1 and gs[i+2]==gs[i]+2 for i in range(len(gs)-2))
        if f_term: v=v and len(set(n%10 for n in gr))>=4
        if f_bh: nb=sum(1 for n in gr if n<=jeu["boules_max"]//2); v=v and 1<=nb<=4
        if v: return {"grille":gr,"etoiles":et,"score":score_v5(gr,et,st_,jid),"mode":mode}
    gr=sorted(random.sample(range(1,jeu["boules_max"]+1),5))
    et=sorted(random.sample(range(1,jeu["etoiles_max"]+1),2)) if jeu["etoiles_max"] else []
    return {"grille":gr,"etoiles":et,"score":score_v5(gr,et,st_,jid),"mode":"fallback"}

def backtest(df,jid,st_,mode,nt=50):
    jeu=JEUX[jid]; C=[f"boule_{i}" for i in range(1,6)]
    res={str(i):0 for i in range(6)}; tm=0; tg=0; gt={0:0,1:0,2:0,3:4,4:50,5:5000}; hi=[]
    for idx in range(min(nt,len(df))):
        row=df.iloc[idx]; bt=set(int(row[c]) for c in C)
        r=gen_grille(jid,st_,mode=mode); nb=len(set(r["grille"])&bt)
        res[str(nb)]+=1; tm+=jeu["prix"]; g=gt.get(nb,0); tg+=g
        if nb>=3: hi.append({"date":str(row["date"]),"grille":r["grille"],"tirage":sorted(bt),"bons":nb,"gain":g})
    return {"res":res,"mise":round(tm,2),"gains":round(tg,2),"bilan":round(tg-tm,2),"nb":nt,"hi":hi}

def reducteur(nums,t=5):
    from itertools import combinations
    if len(nums)<=t: return [sorted(nums)]
    combs=list(combinations(nums,t)); random.shuffle(combs)
    gr=[]; co=set()
    for c in combs:
        if set(c)-co or not gr: gr.append(sorted(c)); co|=set(c)
        if co==set(nums) and len(gr)>=3: break
        if len(gr)>=12: break
    return gr

# ============================================================
# UI HELPERS
# ============================================================
def html_gr(gr, et, st_, jid):
    h="<div class='grille-container'>"
    for b in gr:
        ch=st_["boules"][b]["chaleur"]
        bg="linear-gradient(135deg,#dc2626,#ef4444)" if ch>=60 else ("linear-gradient(135deg,#1e40af,#3b82f6)" if ch>=40 else "linear-gradient(135deg,#1e3a5f,#475569)")
        h+=f"<span style='background:{bg};color:#fff;border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;margin:5px;box-shadow:0 4px 12px rgba(0,0,0,0.3);'>{b}</span>"
    if et:
        h+="<span style='margin:0 15px;font-size:28px;color:#94a3b8;'>|</span>"
        for e in et: h+=f"<span class='etoile'>⭐{e}</span>"
    h+="</div>"; return h

def show_sc(sc):
    ev="⭐"*max(1,min(5,(sc["total"]-20)//15+1))
    cc="#22c55e" if sc["total"]>=70 else ("#f59e0b" if sc["total"]>=50 else "#ef4444")
    c1,c2=st.columns([1,2])
    with c1:
        st.markdown(f"<div class='score-big'><div class='score-number' style='color:{cc};'>{sc['total']}</div><div class='score-label'>/ {sc['max']} {ev}</div></div>",unsafe_allow_html=True)
    with c2:
        mx={"⚖️ Parité":15,"📊 Dizaines":12,"➕ Somme":15,"🔀 Diversité":10,"🚫 Suite":8,"⭐ Étoiles":8,"🔢 Terms":8,"⬆️⬇️ B/H":8,"🌡️ Chaleur":8,"📊 Proba":8}
        for cr,pt in sc["detail"].items():
            m=mx.get(cr,8); pct=pt/m if m else 0
            cl="#22c55e" if pct>=.7 else ("#f59e0b" if pct>=.4 else "#ef4444")
            bar="█"*int(pct*10)+"░"*(10-int(pct*10))
            st.markdown(f"<span style='font-size:.85rem;color:#1e293b;'>`{cr}` <span style='color:{cl};font-family:monospace;'>{bar}</span> **{pt}/{m}**</span>",unsafe_allow_html=True)

def auto_sug(st_, jid):
    jeu=JEUX[jid]; rc=[]
    nh=sum(1 for s in st_["boules"].values() if s["tend"]=="↗️")
    if nh>jeu["boules_max"]*.25: rc.append({"m":"tendance","r":f"{nh} numéros en hausse","c":80})
    nr=sum(1 for s in st_["boules"].values() if s["ratio_rec"]>=80)
    if nr>=5: rc.append({"m":"retard","r":f"{nr} numéros à ≥80% du record","c":75})
    mp=np.mean([s["proba"] for s in st_["boules"].values()])
    if mp>55: rc.append({"m":"probabiliste","r":f"Proba moy élevée ({mp:.1f}%)","c":70})
    me=np.mean([s["ecart"] for s in st_["boules"].values()])
    ma=jeu["boules_max"]/5
    if me>ma*1.2: rc.append({"m":"froid","r":f"Écart moy élevé ({me:.1f})","c":65})
    else: rc.append({"m":"chaud","r":"Écart moy normal → chauds","c":60})
    rc.append({"m":"optimal","r":"Compromis intelligent","c":70})
    rc.sort(key=lambda x:x["c"],reverse=True); return rc

# ============================================================
# MAIN
# ============================================================
def main():
    st.sidebar.markdown("<div style='text-align:center;'><h1 style='font-size:2rem;color:#1e293b;'>🎱 Smart-Loto</h1><p style='color:#64748b;'>V5.1</p></div>",unsafe_allow_html=True)
    st.sidebar.markdown("---")
    jid=st.sidebar.selectbox("🎮",["euromillions","loto"],format_func=lambda x:f"{JEUX[x]['emoji']} {JEUX[x]['nom']}")
    jeu=JEUX[jid]
    st.sidebar.markdown("---")
    up=st.sidebar.file_uploader("📤 CSV",type=["csv","txt"])
    reel=False; dbg={}
    if up:
        df,dbg=load_csv(up,jid)
        if df is not None and len(df)>0: reel=True; st.sidebar.success(f"✅ {len(df)} tirages")
        else: st.sidebar.error("❌"); df=gen_simul(jid)
    else: df=gen_simul(jid); st.sidebar.info("💡 Importe CSV")
    if "gg" not in st.session_state: st.session_state.gg=[]
    st.sidebar.markdown("---")
    page=st.sidebar.radio("📑",[
        "🏠 Dashboard","🎯 Générateur","📊 Stats",
        "🔮 Suggestion","📆 Saisonnier","📈 Tendance",
        "⏳ Retard","💰 Budget","📱 Checker",
        "🎰 Monte Carlo","🔗 Couverture","🆚 Comparateur",
        "🧪 Backtest","🧮 Réducteur","🚫 Anti-Pop",
        "💎 Espérance","📐 Optimiseur","🏆 Hall of Fame",
        "🔍 Debug","ℹ️ Info"])
    st.sidebar.markdown("---")
    st.sidebar.caption("⚠️ Aucune garantie de gain")
    st.sidebar.caption("🛡️ 09 74 75 13 13")
    stats=calc_stats(df.to_json(),jid)
    bdg="🟢 Réelles" if reel else "🟡 Simulées"

    # ══════════════════
    # DASHBOARD
    # ══════════════════
    if page=="🏠 Dashboard":
        st.markdown("<div class='main-header'>🏠 Dashboard</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{jeu['nom']} — {bdg} — {stats['nb_tirages']} tirages</div>",unsafe_allow_html=True)
        d=df.iloc[0]; bs=[int(d[f"boule_{i}"]) for i in range(1,6)]
        et_d=[int(d[f"etoile_{i}"]) for i in range(1,jeu["nb_etoiles"]+1)] if jeu["nb_etoiles"] and "etoile_1" in df.columns else []
        st.subheader(f"🎱 Dernier — {d['date']}")
        st.markdown(html_gr(bs,et_d,stats,jid),unsafe_allow_html=True)
        rc=auto_sug(stats,jid)
        if rc:
            b=rc[0]
            st.markdown(f"<div class='reco-card'>🔮 <b>Recommandation :</b> Mode <b>{b['m'].upper()}</b> — {b['r']} (confiance {b['c']}%)</div>",unsafe_allow_html=True)
        st.subheader("📋 10 derniers")
        dern=[]
        for i in range(min(10,len(df))):
            r=df.iloc[i]
            t=" - ".join(str(int(r[f"boule_{j}"])) for j in range(1,6))
            e=f"⭐{int(r['etoile_1'])} ⭐{int(r['etoile_2'])}" if jeu["nb_etoiles"] and "etoile_1" in df.columns else ""
            dern.append({"📅":str(r["date"]),"🎱":t,"⭐":e})
        st.dataframe(pd.DataFrame(dern),hide_index=True,use_container_width=True)
        st.markdown("---")
        c1,c2=st.columns(2)
        with c1:
            st.subheader("🔥 Top 10 Chauds")
            ch=sorted(stats["boules"].values(),key=lambda x:x["chaleur"],reverse=True)[:10]
            st.dataframe(pd.DataFrame(ch)[["numero","chaleur","f20","ecart","tend","proba"]].rename(columns={"numero":"N°","chaleur":"🌡️","f20":"F20","ecart":"Éc.","tend":"📈","proba":"P%"}),hide_index=True,use_container_width=True)
        with c2:
            st.subheader("⏳ Top 10 Retard")
            rt=sorted(stats["boules"].values(),key=lambda x:x["retard"])[:10]
            st.dataframe(pd.DataFrame(rt)[["numero","retard","ecart","ecart_moy","proba"]].rename(columns={"numero":"N°","retard":"⏳","ecart":"Éc.","ecart_moy":"Moy","proba":"P%"}),hide_index=True,use_container_width=True)
        st.subheader("💑 Paires")
        pd_=[{"Paire":f"{p[0][0]}—{p[0][1]}","Freq":p[1]} for p in stats["paires"][:10]]
        c1,c2=st.columns(2)
        with c1: st.dataframe(pd.DataFrame(pd_[:5]),hide_index=True,use_container_width=True)
        with c2: st.dataframe(pd.DataFrame(pd_[5:]),hide_index=True,use_container_width=True)
        if stats["etoiles"]:
            st.subheader("⭐ Étoiles")
            st.dataframe(pd.DataFrame([{"⭐":f"E{s['numero']}","Éc.":s["ecart"],"F20":s["f20"]} for s in stats["etoiles"].values()]),hide_index=True,use_container_width=True)

    # ══════════════════
    # GÉNÉRATEUR
    # ══════════════════
    elif page=="🎯 Générateur":
        st.markdown("<div class='main-header'>🎯 Générateur Pro</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{bdg}</div>",unsafe_allow_html=True)
        c1,c2,c3=st.columns(3)
        with c1:
            mode=st.selectbox("Mode",["aleatoire","chaud","froid","top","hybride","optimal","probabiliste","tendance","retard","contrarian"],
                format_func=lambda x:{"aleatoire":"🎲 Aléatoire","chaud":"🔥 Chauds","froid":"🧊 Froids","top":"⭐ Top","hybride":"🧠 Hybride","optimal":"🏆 Optimal","probabiliste":"📊 Proba","tendance":"📈 Tendance","retard":"⏳ Retard","contrarian":"🔄 Contrarian"}[x])
            if mode=="optimal":
                pw_ch=st.slider("🌡️ Chaleur",0,100,50); pw_ec=st.slider("📏 Écart",0,100,50); pw_pr=st.slider("📊 Proba",0,100,50)
            else: pw_ch=pw_ec=pw_pr=50
        with c2:
            fi=st.text_input("🔒 Forcés",placeholder="7, 14")
            forces=[int(n.strip()) for n in fi.split(",") if n.strip().isdigit() and 1<=int(n.strip())<=jeu["boules_max"]][:3] if fi else []
            chasseur=st.slider("🎯 Écart min",0,30,0)
            plafond=st.selectbox("🔝",["aucun","moins_40","force_40"],format_func=lambda x:{"aucun":"—","moins_40":"<40","force_40":"≥40"}[x])
            ee=st.slider("⭐ Éc.ét.",0,8,2) if jeu["nb_etoiles"] else 0
            nbg=st.selectbox("Grilles",[1,3,5,10],index=1)
        with c3:
            fpa=st.checkbox("⚖️ Parité",True); fso=st.checkbox("➕ Somme",True)
            fdi=st.checkbox("📊 Dizaines",True); fan=st.checkbox("🚫 Suite",True)
            ftm=st.checkbox("🔢 Terminaisons",False); fbh=st.checkbox("⬆️⬇️ Bas/Hauts",False)
        if st.button("🎱 GÉNÉRER",type="primary",use_container_width=True):
            ag=[]
            for gi in range(nbg):
                r=gen_grille(jid,stats,mode,fpa,fso,fdi,fan,chasseur,forces,ee,plafond,ftm,fbh,pw_ch,pw_ec,pw_pr)
                ag.append(r)
                st.markdown(f"#### G{gi+1}/{nbg}")
                st.markdown(html_gr(r["grille"],r["etoiles"],stats,jid),unsafe_allow_html=True)
                show_sc(r["score"])
                with st.expander(f"📋 Détail G{gi+1}"):
                    det=[{"N°":b,"🌡️":stats["boules"][b]["chaleur"],"Éc.":stats["boules"][b]["ecart"],"P%":stats["boules"][b]["proba"],"📈":stats["boules"][b]["tend"],"⏳":stats["boules"][b]["retard"]} for b in r["grille"]]
                    st.dataframe(pd.DataFrame(det),hide_index=True,use_container_width=True)
                st.markdown("---")
            st.session_state.gg.extend([{"g":r["grille"],"e":r["etoiles"],"s":r["score"]["total"],"m":mode,"t":datetime.now().strftime("%H:%M")} for r in ag])
            st.subheader("📱 Buraliste")
            for i,r in enumerate(ag):
                gs=" — ".join(str(n) for n in r["grille"])
                es=f"  |  ⭐ {' — '.join(str(e) for e in r['etoiles'])}" if r["etoiles"] else ""
                st.markdown(f"<div class='buraliste-card'>G{i+1} : {gs}{es}</div>",unsafe_allow_html=True)
            exp="".join(f"G{i+1}: {' - '.join(str(n) for n in r['grille'])}{' | E:'+' - '.join(str(e) for e in r['etoiles']) if r['etoiles'] else ''} (S:{r['score']['total']})\n" for i,r in enumerate(ag))
            st.download_button("📥 Télécharger",exp,f"grilles-{datetime.now().strftime('%Y%m%d')}.txt")

    # ══════════════════
    # STATS
    # ══════════════════
    elif page=="📊 Stats":
        st.markdown("<div class='main-header'>📊 Statistiques</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{bdg} — {stats['nb_tirages']} tirages</div>",unsafe_allow_html=True)
        st.subheader("🌡️ Carte de Chaleur")
        nc=10; nr=(jeu["boules_max"]+nc-1)//nc; zd=[]; td=[]
        for row in range(nr):
            zr=[]; tr=[]
            for col in range(nc):
                n=row*nc+col+1
                if n<=jeu["boules_max"]:
                    s=stats["boules"][n]; zr.append(s["chaleur"])
                    tr.append(f"N°{n}<br>🌡️{s['chaleur']}<br>P:{s['proba']}%<br>Éc:{s['ecart']}<br>{s['tend']}")
                else: zr.append(None); tr.append("")
            zd.append(zr); td.append(tr)
        fh=go.Figure(data=go.Heatmap(z=zd,text=td,hoverinfo="text",colorscale=[[0,"#1e3a5f"],[.5,"#f59e0b"],[1,"#ef4444"]],showscale=True))
        for row in range(nr):
            for col in range(nc):
                n=row*nc+col+1
                if n<=jeu["boules_max"]: fh.add_annotation(x=col,y=row,text=str(n),showarrow=False,font=dict(color="white",size=14))
        fh.update_layout(height=350,margin=dict(l=20,r=20,t=20,b=20),xaxis=dict(showticklabels=False),yaxis=dict(showticklabels=False))
        st.plotly_chart(fh,use_container_width=True)
        st.subheader("📋 Tableau complet")
        tri=st.selectbox("Trier par",["Chaleur","Écart","Proba","F20","Retard","% Record"])
        col_map={"Chaleur":"🌡️","Écart":"Éc.","Proba":"P%","F20":"F20","Retard":"⏳","% Record":"%Rec"}
        dfc=pd.DataFrame([{
            "N°":n,"🌡️":stats["boules"][n]["chaleur"],"Éc.":stats["boules"][n]["ecart"],
            "Moy":stats["boules"][n]["ecart_moy"],"Max":stats["boules"][n]["ecart_max"],
            "P%":stats["boules"][n]["proba"],"📈":stats["boules"][n]["tend"],
            "F20":stats["boules"][n]["f20"],"F12m":stats["boules"][n]["f12m"],
            "⏳":stats["boules"][n]["retard"],"%Rec":stats["boules"][n]["ratio_rec"]
        } for n in range(1,jeu["boules_max"]+1)])
        col_tri=col_map.get(tri,"🌡️")
        st.dataframe(dfc.sort_values(col_tri,ascending=(tri in ["Écart","Retard"])),hide_index=True,use_container_width=True,height=500)

    # ══════════════════
    # SUGGESTION
    # ══════════════════
    elif page=="🔮 Suggestion":
        st.markdown("<div class='main-header'>🔮 Auto-Suggestion</div>",unsafe_allow_html=True)
        rc=auto_sug(stats,jid)
        for i,r in enumerate(rc):
            em={"tendance":"📈","retard":"⏳","probabiliste":"📊","froid":"🧊","chaud":"🔥","optimal":"🏆"}.get(r["m"],"🎯")
            md="🥇" if i==0 else ("🥈" if i==1 else ("🥉" if i==2 else f"#{i+1}"))
            cc="#22c55e" if r["c"]>=75 else ("#f59e0b" if r["c"]>=60 else "#3b82f6")
            st.markdown(f"<div class='reco-card'><span style='font-size:1.5rem;'>{md} {em} <b>{r['m'].upper()}</b></span><br><b>Raison :</b> {r['r']}<br><b>Confiance :</b> <span style='color:{cc};font-weight:bold;'>{r['c']}%</span></div>",unsafe_allow_html=True)
        if st.button("🎱 Générer avec la meilleure",type="primary",use_container_width=True):
            for i in range(3):
                r=gen_grille(jid,stats,rc[0]["m"],True,True,True,True)
                st.markdown(f"#### G{i+1}"); st.markdown(html_gr(r["grille"],r["etoiles"],stats,jid),unsafe_allow_html=True)
                show_sc(r["score"]); st.markdown("---")

    # ══════════════════
    # SAISONNIER
    # ══════════════════
    elif page=="📆 Saisonnier":
        st.markdown("<div class='main-header'>📆 Saisonnier</div>",unsafe_allow_html=True)
        mn={1:"Janvier",2:"Février",3:"Mars",4:"Avril",5:"Mai",6:"Juin",7:"Juillet",8:"Août",9:"Septembre",10:"Octobre",11:"Novembre",12:"Décembre"}
        if stats["saison"]:
            mc=st.selectbox("Mois",list(stats["saison"].keys()),format_func=lambda x:mn.get(x,f"M{x}"))
            if mc in stats["saison"]:
                sm=stats["saison"][mc]
                st.info(f"📅 {mn.get(mc,'')} : {sm['nb']} tirages")
                st.subheader(f"🔥 Top numéros de {mn.get(mc,'')}")
                for n,f in sm["top"]: st.markdown(f"**N°{n}** — sorti **{f} fois**")
        else: st.warning("Données insuffisantes")

    # ══════════════════
    # TENDANCE
    # ══════════════════
    elif page=="📈 Tendance":
        st.markdown("<div class='main-header'>📈 Tendance Glissante</div>",unsafe_allow_html=True)
        nt=st.number_input("Numéro",1,jeu["boules_max"],7)
        fen=st.slider("Fenêtre",10,100,30)
        CB=[f"boule_{i}" for i in range(1,6)]
        pr=[]
        for idx,row in df.iterrows():
            p=1 if nt in [int(row[c]) for c in CB] else 0
            pr.append({"idx":idx,"date":row["date"],"p":p})
        if pr:
            dp=pd.DataFrame(pr); dp["ma"]=dp["p"].rolling(window=fen,min_periods=1).mean()*100
            dp["date"]=pd.to_datetime(dp["date"])
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=dp["date"],y=dp["ma"],mode="lines",name=f"MA{fen}",line=dict(color="#3b82f6",width=2)))
            ft=5/jeu["boules_max"]*100
            fig.add_hline(y=ft,line_dash="dash",line_color="#ef4444",annotation_text=f"Théo: {ft:.1f}%")
            fig.update_layout(height=400,title=f"N°{nt}",xaxis_title="Date",yaxis_title="%")
            st.plotly_chart(fig,use_container_width=True)
            lm=dp["ma"].iloc[0]
            if lm>ft*1.3: st.markdown(f"<div class='success-card'>🔥 Au-dessus ({lm:.1f}% vs {ft:.1f}%)</div>",unsafe_allow_html=True)
            elif lm<ft*0.7: st.markdown(f"<div class='alert-card'>🧊 En-dessous ({lm:.1f}% vs {ft:.1f}%)</div>",unsafe_allow_html=True)
            else: st.markdown(f"<div class='insight-card'>→ Normal ({lm:.1f}% vs {ft:.1f}%)</div>",unsafe_allow_html=True)

    # ══════════════════
    # RETARD
    # ══════════════════
    elif page=="⏳ Retard":
        st.markdown("<div class='main-header'>⏳ Retard Prédit</div>",unsafe_allow_html=True)
        ret=sorted(stats["boules"].values(),key=lambda x:x["retard"])
        st.subheader("🔴 En retard (≤ 0)")
        er=[s for s in ret if s["retard"]<=0]
        if er:
            for s in er: st.markdown(f"🔴 **N°{s['numero']}** — Éc: {s['ecart']} (moy: {s['ecart_moy']}) — retard {abs(s['retard'])} — P={s['proba']}%")
        else: st.info("Aucun")
        st.subheader("🟡 Bientôt (1-3)")
        for s in [s for s in ret if 1<=s["retard"]<=3]: st.markdown(f"🟡 **N°{s['numero']}** — ~{s['retard']} tirages — Éc: {s['ecart']}/{s['ecart_moy']}")
        st.subheader("🟢 Pas encore (> 3)")
        for s in [s for s in ret if s["retard"]>3][:10]: st.markdown(f"🟢 N°{s['numero']} — ~{s['retard']} — Éc: {s['ecart']}/{s['ecart_moy']}")
        st.markdown("<div class='insight-card'>💡 Retard = écart moyen − écart actuel. Chaque tirage est indépendant.</div>",unsafe_allow_html=True)
        if st.button("🎯 Grille retard",type="primary"):
            r=gen_grille(jid,stats,"retard",True,True,True,True)
            st.markdown(html_gr(r["grille"],r["etoiles"],stats,jid),unsafe_allow_html=True); show_sc(r["score"])

    # ══════════════════
    # BUDGET
    # ══════════════════
    elif page=="💰 Budget":
        st.markdown("<div class='main-header'>💰 Budget</div>",unsafe_allow_html=True)
        budget=st.number_input("💶 Budget (€)",min_value=jeu["prix"],max_value=100.0,value=10.0,step=jeu["prix"])
        nbp=int(budget/jeu["prix"]); st.info(f"**{nbp} grilles** pour {budget}€")
        strat=st.selectbox("Stratégie",["🎯 Même mode","🔀 Mix","🏆 Optimisation max"])
        if st.button("💰 PLANIFIER",type="primary",use_container_width=True):
            gr=[]
            if strat.startswith("🎯"):
                for _ in range(nbp): gr.append(gen_grille(jid,stats,"optimal",True,True,True,True))
            elif strat.startswith("🔀"):
                ms=["chaud","froid","probabiliste","tendance","optimal"]
                for i in range(nbp): gr.append(gen_grille(jid,stats,ms[i%len(ms)],True,True,True,True))
            else:
                cands=[gen_grille(jid,stats,"optimal",True,True,True,True) for _ in range(nbp*5)]
                cands.sort(key=lambda x:x["score"]["total"],reverse=True); gr=cands[:nbp]
            tous=set()
            for r in gr: tous|=set(r["grille"])
            c1,c2,c3=st.columns(3)
            c1.metric("Grilles",len(gr)); c2.metric("Couverture",f"{len(tous)/jeu['boules_max']*100:.0f}%")
            c3.metric("Score moy",f"{np.mean([r['score']['total'] for r in gr]):.0f}/100")
            for i,r in enumerate(gr):
                gs=" — ".join(str(n) for n in r["grille"])
                es=f" | ⭐{' — '.join(str(e) for e in r['etoiles'])}" if r["etoiles"] else ""
                st.markdown(f"<div class='buraliste-card'>G{i+1} : {gs}{es} — S:{r['score']['total']}</div>",unsafe_allow_html=True)

    # ══════════════════
    # CHECKER
    # ══════════════════
    elif page=="📱 Checker":
        st.markdown("<div class='main-header'>📱 Checker</div>",unsafe_allow_html=True)
        ti=st.text_input("🎱 Tirage (5 numéros)",placeholder="3, 17, 28, 34, 45")
        ei=""
        if jeu["nb_etoiles"]: ei=st.text_input("⭐ Étoiles",placeholder="2, 11")
        if ti:
            tirage=sorted(set(int(n.strip()) for n in ti.split(",") if n.strip().isdigit()))
            etoiles_t=sorted(set(int(n.strip()) for n in ei.split(",") if n.strip().isdigit())) if ei else []
            if len(tirage)==5:
                st.markdown(html_gr(tirage,etoiles_t,stats,jid),unsafe_allow_html=True)
                if st.session_state.gg:
                    st.subheader(f"📋 {len(st.session_state.gg)} grilles")
                    res=[]
                    for i,g in enumerate(st.session_state.gg):
                        cm=set(g["g"])&set(tirage); eo=set(g.get("e",[]))&set(etoiles_t) if etoiles_t else set()
                        res.append({"i":i+1,"g":g["g"],"b":len(cm),"c":sorted(cm),"eo":len(eo),"m":g["m"]})
                    res.sort(key=lambda x:x["b"],reverse=True)
                    for r in res:
                        em="🎉🎉" if r["b"]>=4 else ("🎉" if r["b"]==3 else ("👍" if r["b"]==2 else "—"))
                        st.markdown(f"{em} **G{r['i']}** `{r['g']}` → **{r['b']}/5** {list(r['c'])} ({r['m']})")
                    best=max(res,key=lambda x:x["b"])
                    if best["b"]>=3: st.balloons(); st.markdown(f"<div class='success-card'>🎉 Meilleur : <b>{best['b']}/5</b> !</div>",unsafe_allow_html=True)
                else: st.info("Génère des grilles d'abord !")

    # ══════════════════
    # MONTE CARLO
    # ══════════════════
    elif page=="🎰 Monte Carlo":
        st.markdown("<div class='main-header'>🎰 Monte Carlo</div>",unsafe_allow_html=True)
        mmc=st.selectbox("Stratégie",["aleatoire","chaud","optimal","probabiliste","retard"])
        ns=st.selectbox("Simulations",[100,500,1000],index=1)
        bmc=st.number_input("Budget (€)",10.0,500.0,50.0,step=10.0)
        ngm=int(bmc/jeu["prix"])
        if st.button("🎰 SIMULER",type="primary",use_container_width=True):
            with st.spinner(f"⏳ {ns} sims..."):
                bilans=[]; mrangs=[]
                for _ in range(ns):
                    gs=[gen_grille(jid,stats,mmc) for _ in range(ngm)]
                    ts=sorted(random.sample(range(1,jeu["boules_max"]+1),5))
                    bm=max(len(set(g["grille"])&set(ts)) for g in gs)
                    gain={0:0,1:0,2:0,3:4,4:50,5:5000}.get(bm,0)
                    bilans.append(gain-bmc); mrangs.append(bm)
            c1,c2,c3=st.columns(3)
            c1.metric("Bilan moy",f"{np.mean(bilans):+.2f}€"); c2.metric("Meilleur",f"{max(bilans):+.2f}€")
            c3.metric("% Positif",f"{sum(1 for b in bilans if b>0)/len(bilans)*100:.1f}%")
            dist=Counter(mrangs)
            fig=go.Figure(go.Bar(x=[f"{k} bons" for k in sorted(dist)],y=[dist[k] for k in sorted(dist)],
                marker_color=["#ef4444","#f97316","#f59e0b","#84cc16","#22c55e","#15803d"]))
            fig.update_layout(height=350); st.plotly_chart(fig,use_container_width=True)

    # ══════════════════
    # COUVERTURE
    # ══════════════════
    elif page=="🔗 Couverture":
        st.markdown("<div class='main-header'>🔗 Couverture</div>",unsafe_allow_html=True)
        if st.session_state.gg:
            grilles=[g["g"] for g in st.session_state.gg]; tous=set()
            for g in grilles: tous|=set(g)
            fg=Counter()
            for g in grilles:
                for n in g: fg[n]+=1
            st.metric("Grilles",len(grilles)); st.metric("Couverture",f"{len(tous)}/{jeu['boules_max']} ({len(tous)/jeu['boules_max']*100:.0f}%)")
            nc=10; nr=(jeu["boules_max"]+nc-1)//nc; zd=[]
            for row in range(nr):
                zr=[]
                for col in range(nc):
                    n=row*nc+col+1
                    zr.append(fg.get(n,0) if n<=jeu["boules_max"] else None)
                zd.append(zr)
            fh=go.Figure(data=go.Heatmap(z=zd,colorscale=[[0,"#f1f5f9"],[.5,"#3b82f6"],[1,"#1e3a5f"]],showscale=True))
            for row in range(nr):
                for col in range(nc):
                    n=row*nc+col+1
                    if n<=jeu["boules_max"]:
                        cl="white" if fg.get(n,0)>0 else "#94a3b8"
                        fh.add_annotation(x=col,y=row,text=str(n),showarrow=False,font=dict(color=cl,size=14))
            fh.update_layout(height=350,margin=dict(l=20,r=20,t=40,b=20),xaxis=dict(showticklabels=False),yaxis=dict(showticklabels=False))
            st.plotly_chart(fh,use_container_width=True)
            mq=sorted(set(range(1,jeu["boules_max"]+1))-tous)
            if mq: st.warning(f"⚠️ Non couverts : {mq}")
        else: st.info("Génère des grilles d'abord !")

    # ══════════════════
    # COMPARATEUR
    # ══════════════════
    elif page=="🆚 Comparateur":
        st.markdown("<div class='main-header'>🆚 Comparateur</div>",unsafe_allow_html=True)
        nbt=st.selectbox("Tirages",[20,50,100],index=1)
        if st.button("🆚 GO",type="primary",use_container_width=True):
            with st.spinner("⏳"):
                comp={m:backtest(df,jid,stats,m,nbt) for m in ["aleatoire","chaud","froid","optimal","probabiliste","tendance","retard"]}
            cd=[{"Mode":m,"Misé":f"{r['mise']}€","Gagné":f"{r['gains']}€","Bilan":f"{r['bilan']:+.2f}€",
                "≥3":sum(r["res"][str(i)] for i in range(3,6))} for m,r in comp.items()]
            st.dataframe(pd.DataFrame(cd),hide_index=True,use_container_width=True)

    # ══════════════════
    # BACKTEST
    # ══════════════════
    elif page=="🧪 Backtest":
        st.markdown("<div class='main-header'>🧪 Backtest</div>",unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1: m=st.selectbox("Mode",["aleatoire","chaud","froid","optimal","probabiliste","tendance","retard"])
        with c2: nt=st.selectbox("Tirages",[20,50,100,200],index=1)
        if st.button("🚀",type="primary",use_container_width=True):
            with st.spinner("⏳"): rb=backtest(df,jid,stats,m,nt)
            c1,c2,c3=st.columns(3)
            c1.metric("💰",f"{rb['mise']}€"); c2.metric("🏆",f"{rb['gains']}€"); c3.metric("📈",f"{rb['bilan']:+.2f}€")
            res=rb["res"]
            fig=go.Figure(go.Bar(x=[f"{k}" for k in sorted(res)],y=[res[k] for k in sorted(res)],
                marker_color=["#ef4444","#f97316","#f59e0b","#84cc16","#22c55e","#15803d"]))
            fig.update_layout(height=300); st.plotly_chart(fig,use_container_width=True)
            for h in rb["hi"][:10]: st.markdown(f"📅 **{h['date']}** — `{h['grille']}` vs `{h['tirage']}` — **{h['bons']}** — {h['gain']}€")

    # ══════════════════
    # RÉDUCTEUR
    # ══════════════════
    elif page=="🧮 Réducteur":
        st.markdown("<div class='main-header'>🧮 Réducteur</div>",unsafe_allow_html=True)
        with st.expander("💡 Suggestions"):
            tp=sorted(stats["boules"].values(),key=lambda x:x["proba"],reverse=True)[:10]
            st.markdown(f"**Top proba :** `{', '.join(str(n['numero']) for n in tp)}`")
        ni=st.text_input("🔢 Numéros (6-15)",placeholder="3, 7, 14, 19, 23, 28, 34, 41")
        if ni:
            nums=sorted(set(int(n.strip()) for n in ni.split(",") if n.strip().isdigit() and 1<=int(n.strip())<=jeu["boules_max"]))
            if len(nums)>=6:
                st.success(f"✅ {len(nums)} : {nums}")
                if st.button("🧮 GO",type="primary",use_container_width=True):
                    grs=reducteur(nums)
                    st.info(f"💰 {len(grs)}×{jeu['prix']}€ = **{len(grs)*jeu['prix']:.2f}€**")
                    for i,g in enumerate(grs):
                        st.markdown(f"<div class='grille-container'><b>G{i+1}</b>&nbsp;&nbsp;{'&nbsp;&nbsp;'.join(f'<span class=\"boule\">{b}</span>' for b in g)}</div>",unsafe_allow_html=True)
            else: st.warning(f"Min 6 ({len(nums)})")

    # ══════════════════
    # ANTI-POP
    # ══════════════════
    elif page=="🚫 Anti-Pop":
        st.markdown("<div class='main-header'>🚫 Anti-Popularité</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Maximise ton gain en cas de victoire</div>",unsafe_allow_html=True)
        st.markdown("""<div class='insight-card'>
        💡 <b>Le vrai secret :</b> Tu ne peux pas augmenter tes chances de gagner.
        Mais tu peux augmenter <b>combien</b> tu gagnes si tu gagnes.<br><br>
        <b>Comment ?</b> En évitant les numéros que tout le monde joue.
        Moins de partage = plus de gains pour toi.
        </div>""",unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("""<div class='alert-card'>
        <b>Numéros sur-joués à ÉVITER :</b><br><br>
        🎂 <b>1-31</b> : dates de naissance (70% des joueurs)<br>
        7️⃣ <b>7</b> : porte-bonheur n°1 (3x plus choisi)<br>
        🔢 <b>13, 3, 9</b> : fétiches populaires<br>
        📏 <b>1-2-3-4-5</b> : ~10 000 personnes par tirage<br>
        📐 <b>Multiples de 5/10</b> : sur-représentés
        </div>""",unsafe_allow_html=True)
        st.markdown("---")
        st.subheader("✅ Numéros sous-joués (32-50) les plus chauds")
        sjc=sorted([n for n in range(32,jeu["boules_max"]+1)],key=lambda x:stats["boules"][x]["chaleur"],reverse=True)[:10]
        for n in sjc:
            s=stats["boules"][n]
            st.markdown(f"**N°{n}** — 🌡️ {s['chaleur']} — Éc: {s['ecart']} — {s['tend']}")
        st.markdown("---")
        nb_anti=st.selectbox("Numéros > 31 dans la grille",[2,3,4,5],index=1)
        if st.button("🚫 Générer Anti-Pop",type="primary",use_container_width=True):
            populaires={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,20,25,30,31}
            for gi in range(3):
                for att in range(500):
                    ph=[n for n in range(32,jeu["boules_max"]+1)]
                    pb=[n for n in range(1,32) if n not in populaires]
                    ch_h=sorted(random.sample(ph,min(nb_anti,len(ph))))
                    ch_b=sorted(random.sample(pb,min(5-nb_anti,len(pb))))
                    gr=sorted(ch_h+ch_b)[:5]
                    np2=sum(1 for n in gr if n%2==0)
                    if np2==0 or np2==5: continue
                    if not(jeu["somme_min"]<=sum(gr)<=jeu["somme_max"]): continue
                    gs=sorted(gr)
                    if any(gs[i+1]==gs[i]+1 and gs[i+2]==gs[i]+2 for i in range(len(gs)-2)): continue
                    et=sorted(random.sample(range(1,jeu["etoiles_max"]+1),jeu["nb_etoiles"])) if jeu["etoiles_max"] else []
                    sc=score_v5(gr,et,stats,jid)
                    st.markdown(f"#### G{gi+1}")
                    st.markdown(html_gr(gr,et,stats,jid),unsafe_allow_html=True)
                    show_sc(sc)
                    ns31=sum(1 for n in gr if n>31); npop=sum(1 for n in gr if n in populaires)
                    st.markdown(f"<div class='success-card'>✅ {ns31}/5 numéros > 31 | {5-npop}/5 hors populaires | 💰 Moins de partage si tu gagnes</div>",unsafe_allow_html=True)
                    st.markdown("---"); break
        st.markdown("---")
        st.markdown("""
        | Scénario | Gagnants estimés | Ton gain (JP 100M€) |
        |----------|:---:|:---:|
        | Grille populaire (1-7-13-21-30) | ~50 | **~2M€** |
        | Grille mixte (8-23-34-41-47) | ~10 | **~10M€** |
        | Grille anti-pop (33-37-42-46-49) | ~2-3 | **~35-50M€** |
        """)

    # ══════════════════
    # ESPÉRANCE
    # ══════════════════
    elif page=="💎 Espérance":
        st.markdown("<div class='main-header'>💎 Espérance Mathématique</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Quand est-ce « moins mauvais » de jouer ?</div>",unsafe_allow_html=True)
        st.markdown("""<div class='insight-card'>
        💡 <b>L'espérance</b> = ce que tu gagnes EN MOYENNE par grille. Toujours négative.
        Mais <b>moins négative</b> quand le jackpot est très élevé.
        </div>""",unsafe_allow_html=True)
        jp=st.number_input("💰 Jackpot (M€)",17,250,50,step=1)
        jpe=jp*1_000_000
        if jid=="euromillions":
            pr={"5+2":1/139838160,"5+1":1/6991908,"5+0":1/3107515,"4+2":1/621503,"4+1":1/31075,"4+0":1/13811,"3+2":1/14125,"3+1":1/706,"3+0":1/314,"2+2":1/985,"2+1":1/49,"1+2":1/188}
            gf={"5+2":jpe,"5+1":500000,"5+0":50000,"4+2":5000,"4+1":200,"4+0":100,"3+2":60,"3+1":14,"3+0":13,"2+2":17,"2+1":8,"1+2":10}
        else:
            pr={"5+1":1/19068840,"5+0":1/2118760,"4+1":1/86677,"4+0":1/9631,"3+1":1/2016,"3+0":1/224,"2+1":1/144,"2+0":1/16}
            gf={"5+1":jpe,"5+0":100000,"4+1":2000,"4+0":500,"3+1":50,"3+0":10,"2+1":6,"2+0":3}
        esp=sum(pr[r]*gf[r] for r in pr)
        espn=esp-jeu["prix"]
        c1,c2,c3=st.columns(3)
        c1.metric("Espérance brute",f"{esp:.2f}€"); c2.metric("Coût grille",f"{jeu['prix']}€")
        c3.metric("Espérance nette",f"{espn:+.2f}€",delta_color="normal" if espn>=0 else "inverse")
        det=[{"Rang":r,"Probabilité":f"1/{int(1/pr[r]):,}".replace(",","."),"Gain":f"{gf[r]:,.0f}€".replace(",","."),"Esp.":f"{pr[r]*gf[r]:.4f}€"} for r in pr]
        st.dataframe(pd.DataFrame(det),hide_index=True,use_container_width=True)
        seuil=jeu["prix"]/pr[list(pr.keys())[0]]; sm=seuil/1e6
        if espn>=0: st.markdown(f"<div class='success-card'>✅ JP à <b>{jp}M€</b> → espérance <b>positive</b> ! Meilleur moment.</div>",unsafe_allow_html=True)
        else:
            pp=abs(espn)/jeu["prix"]*100
            st.markdown(f"<div class='alert-card'>📉 Tu perds en moy <b>{abs(espn):.2f}€</b>/grille ({pp:.0f}%). Il faudrait ~<b>{sm:.0f}M€</b> de JP pour être positif.</div>",unsafe_allow_html=True)
        jps=list(range(17,251,5))
        esps=[]
        for j in jps:
            gft=gf.copy(); gft[list(gft.keys())[0]]=j*1e6
            esps.append(sum(pr[r]*gft[r] for r in pr)-jeu["prix"])
        fig=go.Figure()
        fig.add_trace(go.Scatter(x=jps,y=esps,mode="lines+markers",line=dict(color="#3b82f6",width=2)))
        fig.add_hline(y=0,line_dash="dash",line_color="#22c55e",annotation_text="Seuil rentabilité")
        fig.add_vline(x=jp,line_dash="dash",line_color="#f59e0b",annotation_text=f"Actuel: {jp}M€")
        fig.update_layout(height=400,title="Espérance vs Jackpot",xaxis_title="JP (M€)",yaxis_title="Espérance (€)")
        st.plotly_chart(fig,use_container_width=True)

    # ══════════════════
    # OPTIMISEUR
    # ══════════════════
    elif page=="📐 Optimiseur":
        st.markdown("<div class='main-header'>📐 Optimiseur Portefeuille</div>",unsafe_allow_html=True)
        bo=st.number_input("💶 Budget (€)",min_value=jeu["prix"]*2,max_value=100.0,value=12.50,step=jeu["prix"])
        ngo=int(bo/jeu["prix"]); st.info(f"**{ngo} grilles** pour {bo}€")
        obj=st.radio("🎯 Objectif",["🔀 Couverture max","🎯 Score max","🚫 Anti-popularité","⚖️ Équilibré"])
        if st.button("📐 OPTIMISER",type="primary",use_container_width=True):
            gro=[]; nu=Counter(); populaires={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,20,25,30,31}
            with st.spinner("⏳"):
                for gi in range(ngo):
                    best=None; bs=-1
                    for _ in range(200):
                        r=gen_grille(jid,stats,"optimal",True,True,True,True); gr=r["grille"]
                        if obj.startswith("🚫"):
                            npop=sum(1 for n in gr if n in populaires); sc=r["score"]["total"]+(5-npop)*20
                        elif obj.startswith("🔀"):
                            nn=sum(1 for n in gr if nu[n]==0); sc=r["score"]["total"]+nn*15
                        elif obj.startswith("🎯"): sc=r["score"]["total"]
                        else:
                            nn=sum(1 for n in gr if nu[n]==0); npop=sum(1 for n in gr if n in populaires)
                            sc=r["score"]["total"]+nn*10+(5-npop)*5
                        if sc>bs: bs=sc; best=r
                    gro.append(best)
                    for n in best["grille"]: nu[n]+=1
            tous=set()
            for r in gro: tous|=set(r["grille"])
            c1,c2,c3=st.columns(3)
            c1.metric("Grilles",ngo); c2.metric("Couverture",f"{len(tous)/jeu['boules_max']*100:.0f}%")
            c3.metric("Score moy",f"{np.mean([r['score']['total'] for r in gro]):.0f}/100")
            for i,r in enumerate(gro):
                st.markdown(f"#### G{i+1}")
                st.markdown(html_gr(r["grille"],r["etoiles"],stats,jid),unsafe_allow_html=True)
                show_sc(r["score"]); st.markdown("---")
            st.subheader("📱 Buraliste")
            for i,r in enumerate(gro):
                gs=" — ".join(str(n) for n in r["grille"])
                es=f" | ⭐{' — '.join(str(e) for e in r['etoiles'])}" if r["etoiles"] else ""
                st.markdown(f"<div class='buraliste-card'>G{i+1} : {gs}{es}</div>",unsafe_allow_html=True)
            exp=f"Smart-Loto — {datetime.now().strftime('%d/%m/%Y')}\nBudget: {bo}€ — {ngo} grilles\n{'='*40}\n\n"
            for i,r in enumerate(gro):
                gs=" - ".join(str(n) for n in r["grille"])
                es=f" | E: {' - '.join(str(e) for e in r['etoiles'])}" if r["etoiles"] else ""
                exp+=f"G{i+1}: {gs}{es} (S:{r['score']['total']})\n"
            st.download_button("📥 Télécharger",exp,f"portefeuille-{datetime.now().strftime('%Y%m%d')}.txt")

    # ══════════════════
    # HALL OF FAME
    # ══════════════════
    elif page=="🏆 Hall of Fame":
        st.markdown("<div class='main-header'>🏆 Hall of Fame</div>",unsafe_allow_html=True)
        if st.session_state.gg:
            sg=sorted(st.session_state.gg,key=lambda x:x["s"],reverse=True)
            st.metric("Total",len(sg)); st.metric("Top",f"{sg[0]['s']}/100")
            for i,g in enumerate(sg[:20]):
                md="🥇" if i==0 else ("🥈" if i==1 else ("🥉" if i==2 else f"#{i+1}"))
                gs=" — ".join(str(n) for n in g["g"])
                es=f" | ⭐{' — '.join(str(e) for e in g['e'])}" if g["e"] else ""
                st.markdown(f"{md} **{g['s']}/100** — `{gs}{es}` — {g['m']} — {g['t']}")
            if st.button("🗑️ Reset"): st.session_state.gg=[]; st.rerun()
        else: st.info("Génère des grilles !")

    # ══════════════════
    # DEBUG
    # ══════════════════
    elif page=="🔍 Debug":
        st.markdown("<div class='main-header'>🔍 Debug</div>",unsafe_allow_html=True)
        if dbg:
            if dbg.get("ok"): st.success(f"✅ {dbg.get('n','?')} tirages")
            else: st.error(f"❌ {dbg.get('err','?')}")
            if "cols" in dbg:
                for i,c in enumerate(dbg["cols"][:15]): st.markdown(f"`{i}` → **{c}**")
            if "map" in dbg:
                m=dbg["map"]; st.success(f"📅 {m['d']} | 🎱 {m['b']} | ⭐ {m['e']}")
        st.dataframe(df.head(10),use_container_width=True)

    # ══════════════════
    # INFO
    # ══════════════════
    elif page=="ℹ️ Info":
        st.markdown("<div class='main-header'>ℹ️ V5.1</div>",unsafe_allow_html=True)
        st.markdown(f"""
## 20 pages • 10 modes • 10 critères

| Module | Description |
|---|---|
| 🏠 Dashboard | Vue d'ensemble + auto-suggestion |
| 🎯 Générateur | 10 modes, 6 filtres, 10 critères |
| 📊 Stats | Heatmap + tableau complet |
| 🔮 Suggestion | L'outil choisit la stratégie |
| 📆 Saisonnier | Analyse par mois |
| 📈 Tendance | Moving average |
| ⏳ Retard | Quand va-t-il sortir ? |
| 💰 Budget | Planificateur de grilles |
| 📱 Checker | Vérifie tes grilles vs résultat |
| 🎰 Monte Carlo | Simulation de sessions |
| 🔗 Couverture | Heatmap des numéros couverts |
| 🆚 Comparateur | Compare 7 stratégies |
| 🧪 Backtest | Teste sur l'historique |
| 🧮 Réducteur | Système de couverture |
| 🚫 **Anti-Pop** | Maximise les gains potentiels |
| 💎 **Espérance** | Quand jouer ? |
| 📐 **Optimiseur** | Portefeuille de grilles |
| 🏆 Hall of Fame | Tes meilleures grilles |

**Données :** {bdg} | **Tirages :** {stats['nb_tirages']}

⚠️ Aucune garantie — 🛡️ 09 74 75 13 13
        """)

    st.markdown("<div class='footer-disclaimer'>⚠️ Outil d'analyse — Aucune garantie de gain — Chaque tirage est indépendant<br>🛡️ <a href='https://www.joueurs-info-service.fr/'>Joueurs Info Service</a> : 09 74 75 13 13</div>",unsafe_allow_html=True)

if __name__=="__main__":
    main()
