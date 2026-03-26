# ============================================================
# SMART-LOTO — V5.2 — SIMPLE + EXPERT + TOOLTIPS
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
    .main-header {font-size:2.5rem;font-weight:800;background:linear-gradient(135deg,#1e40af,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;padding:10px 0;}
    .sub-header {text-align:center;color:#475569 !important;font-size:1.1rem;margin-bottom:30px;}
    .boule {background:linear-gradient(135deg,#1e40af,#3b82f6);color:#fff !important;border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;margin:5px;box-shadow:0 4px 12px rgba(30,64,175,0.4);}
    .etoile {background:linear-gradient(135deg,#f59e0b,#fbbf24);color:#fff !important;border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;margin:5px;box-shadow:0 4px 12px rgba(245,158,11,0.4);}
    .grille-container {display:flex;align-items:center;justify-content:center;padding:25px;background:linear-gradient(135deg,#f8fafc,#e2e8f0);border-radius:20px;margin:15px 0;border:2px solid #e2e8f0;color:#1e293b !important;}
    .grille-container b,.grille-container strong{color:#1e293b !important;}
    .footer-disclaimer {background:#fef3c7;border:1px solid #f59e0b;border-radius:12px;padding:15px;margin-top:30px;text-align:center;font-size:0.9rem;color:#92400e !important;}
    .footer-disclaimer a{color:#b45309 !important;text-decoration:underline;}
    .alert-card {background:linear-gradient(135deg,#fef2f2,#fee2e2);border:2px solid #ef4444;border-radius:16px;padding:20px;margin:10px 0;color:#991b1b !important;}
    .alert-card b,.alert-card strong{color:#7f1d1d !important;}
    .success-card {background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:2px solid #22c55e;border-radius:16px;padding:20px;margin:10px 0;color:#166534 !important;}
    .success-card b,.success-card strong{color:#14532d !important;}
    .insight-card {background:linear-gradient(135deg,#eff6ff,#dbeafe);border:2px solid #3b82f6;border-radius:16px;padding:20px;margin:10px 0;color:#1e3a5f !important;}
    .insight-card b,.insight-card strong,.insight-card span{color:#1e3a5f !important;}
    .reco-card {background:linear-gradient(135deg,#fdf4ff,#f3e8ff);border:2px solid #a855f7;border-radius:16px;padding:20px;margin:10px 0;color:#581c87 !important;}
    .reco-card b,.reco-card strong,.reco-card span{color:#581c87 !important;}
    .buraliste-card {text-align:center;font-size:28px;font-weight:bold;padding:15px;background:#f8fafc;border-radius:12px;margin:8px 0;color:#1e293b !important;border:1px solid #e2e8f0;}
    .score-big{text-align:center;}
    .score-big .score-number{font-size:3rem;font-weight:800;}
    .score-big .score-label{color:#64748b !important;font-size:0.9rem;}
    .preset-card {background:linear-gradient(135deg,#f8fafc,#e2e8f0);border:2px solid #cbd5e1;border-radius:16px;padding:20px;margin:10px 0;color:#1e293b !important;cursor:pointer;transition:all 0.2s;}
    .preset-card:hover {border-color:#3b82f6;box-shadow:0 4px 12px rgba(59,130,246,0.2);}
    .preset-card b,.preset-card strong{color:#1e293b !important;}
    .element-container div[data-testid="stMarkdownContainer"] > div{color:#1e293b;}
    .glossary-term {background:#f1f5f9;border:1px solid #cbd5e1;border-radius:8px;padding:12px;margin:6px 0;color:#1e293b !important;}
    .glossary-term b{color:#1e40af !important;}
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions":{"nom":"Euromillions","emoji":"⭐","boules_max":50,"nb_boules":5,"etoiles_max":12,"nb_etoiles":2,"prix":2.50,"somme_min":90,"somme_max":160},
    "loto":{"nom":"Loto","emoji":"🎱","boules_max":49,"nb_boules":5,"etoiles_max":None,"nb_etoiles":0,"prix":2.20,"somme_min":60,"somme_max":180}
}

# ============================================================
# GLOSSAIRE — TOUTES LES DÉFINITIONS
# ============================================================
GLOSSAIRE = {
    "Chaleur (🌡️)": "Score de 0 à 100 indiquant si un numéro sort souvent en ce moment. Plus c'est élevé, plus le numéro est 'chaud' (sorti récemment et fréquemment).",
    "Écart (Éc.)": "Nombre de tirages consécutifs où ce numéro n'est PAS sorti. Un écart de 15 = absent depuis 15 tirages.",
    "Écart moyen (Moy)": "En moyenne, combien de tirages séparent deux sorties de ce numéro. Permet de savoir si l'écart actuel est normal ou anormal.",
    "Écart max (Max)": "Le plus long écart jamais enregistré pour ce numéro. Record historique d'absence.",
    "F20": "Fréquence sur les 20 derniers tirages. Combien de fois ce numéro est sorti sur les 20 derniers tirages. Maximum possible : 20.",
    "F12m": "Fréquence sur 12 mois. Nombre de sorties sur la dernière année.",
    "F3m": "Fréquence sur 3 mois. Nombre de sorties sur le dernier trimestre.",
    "Probabilité (P%)": "Estimation statistique de la 'probabilité' que ce numéro sorte bientôt, basée sur son écart actuel vs son écart moyen. ⚠️ Ce n'est PAS une vraie probabilité — chaque tirage est indépendant.",
    "Tendance (📈)": "Direction récente : ↗️ = sort plus souvent ces 3 derniers mois qu'avant. ↘️ = sort moins souvent. → = stable.",
    "Retard (⏳)": "Estimation du nombre de tirages restants avant la prochaine sortie (écart moyen - écart actuel). Si négatif = le numéro est 'en retard'. ⚠️ Simple estimation.",
    "% Record (%Rec)": "L'écart actuel en pourcentage du record. 90% = le numéro est presque à son record d'absence.",
    "Parité": "Équilibre entre numéros pairs (2,4,6...) et impairs (1,3,5...). Une bonne grille a un mix, par exemple 2 pairs + 3 impairs.",
    "Somme": "La somme des 5 numéros de la grille. Les tirages réels ont en moyenne une somme entre 90 et 160 (Euromillions). Les extrêmes sont très rares.",
    "Dizaines": "Répartition des numéros par tranche de 10 (1-10, 11-20, 21-30...). Une bonne grille couvre au moins 3-4 dizaines différentes.",
    "Terminaisons": "Le dernier chiffre de chaque numéro (7→7, 23→3, 40→0). Une bonne grille a des terminaisons variées.",
    "Bas/Hauts (B/H)": "Répartition entre numéros bas (1-25) et hauts (26-50). Un bon mix est 2-3 bas + 2-3 hauts.",
    "Score de robustesse": "Note de 0 à 100 évaluant la 'qualité structurelle' de ta grille : parité, somme, dizaines, terminaisons, etc. Plus c'est élevé, plus ta grille ressemble aux vrais tirages historiques.",
    "Anti-popularité": "Stratégie consistant à éviter les numéros que tout le monde joue (dates de naissance 1-31, numéro 7...). Si tu gagnes, tu partages avec moins de gens = tu gagnes plus.",
    "Système réducteur": "Technique qui prend plus de numéros que nécessaire (ex: 10 au lieu de 5) et génère un ensemble de grilles couvrant toutes les combinaisons possibles.",
    "Backtest": "Test d'une stratégie sur les tirages passés. 'Si j'avais joué comme ça pendant 2 ans, qu'est-ce que ça aurait donné ?'",
    "Espérance": "Ce que tu gagnes EN MOYENNE par grille jouée. Toujours négative au Loto (sinon la FDJ perdrait de l'argent). Moins négative quand le jackpot est très élevé.",
    "Monte Carlo": "Simulation de milliers de sessions de jeu virtuelles pour évaluer statistiquement une stratégie."
}

# ============================================================
# PROFILS PRÉDÉFINIS (MODE SIMPLE)
# ============================================================
PROFILS = {
    "🎯 Équilibré": {
        "desc": "Le meilleur compromis. Mix de numéros chauds et froids, grille bien structurée.",
        "mode": "optimal",
        "fp": True, "fs": True, "fd": True, "fa": True,
        "ft": False, "fb": True,
        "chasseur": 0, "plafond": "aucun",
        "pw_ch": 50, "pw_ec": 50, "pw_pr": 50,
        "couleur": "#3b82f6"
    },
    "🔥 Agressif": {
        "desc": "Privilégie les numéros les plus chauds du moment. Idéal si tu crois aux séries.",
        "mode": "chaud",
        "fp": True, "fs": True, "fd": True, "fa": True,
        "ft": False, "fb": False,
        "chasseur": 0, "plafond": "aucun",
        "pw_ch": 80, "pw_ec": 20, "pw_pr": 50,
        "couleur": "#ef4444"
    },
    "🧊 Chasseur": {
        "desc": "Mise sur les numéros absents depuis longtemps. Stratégie 'ils vont bien finir par sortir'.",
        "mode": "retard",
        "fp": True, "fs": True, "fd": True, "fa": True,
        "ft": False, "fb": False,
        "chasseur": 0, "plafond": "aucun",
        "pw_ch": 20, "pw_ec": 80, "pw_pr": 50,
        "couleur": "#3b82f6"
    },
    "📊 Statisticien": {
        "desc": "Basé sur la probabilité de sortie. Approche la plus mathématique.",
        "mode": "probabiliste",
        "fp": True, "fs": True, "fd": True, "fa": True,
        "ft": True, "fb": True,
        "chasseur": 0, "plafond": "aucun",
        "pw_ch": 40, "pw_ec": 40, "pw_pr": 80,
        "couleur": "#8b5cf6"
    },
    "🚫 Anti-Populaire": {
        "desc": "Évite les numéros que tout le monde joue (1-31). Si tu gagnes, tu partages avec moins de gens = plus d'argent pour toi.",
        "mode": "optimal",
        "fp": True, "fs": True, "fd": True, "fa": True,
        "ft": True, "fb": True,
        "chasseur": 0, "plafond": "force_40",
        "pw_ch": 50, "pw_ec": 50, "pw_pr": 50,
        "couleur": "#f59e0b"
    },
    "🎲 Chance Pure": {
        "desc": "Tirage 100% aléatoire. Aucun filtre. Le hasard total.",
        "mode": "aleatoire",
        "fp": False, "fs": False, "fd": False, "fa": False,
        "ft": False, "fb": False,
        "chasseur": 0, "plafond": "aucun",
        "pw_ch": 50, "pw_ec": 50, "pw_pr": 50,
        "couleur": "#22c55e"
    }
}

# ============================================================
# CSV + STATS + SCORE + GENERATOR (identique V5.1)
# ============================================================
def load_csv(up, jid):
    jeu=JEUX[jid]; dbg={}
    content=up.read(); up.seek(0); text=None
    for enc in ["utf-8-sig","utf-8","latin-1","cp1252"]:
        try: text=content.decode(enc); dbg["enc"]=enc; break
        except: continue
    if not text: return None,{"err":"Decode fail"}
    text=text.lstrip("\ufeff"); df=None; sf=None
    for s in [";",",","\t"]:
        try:
            d=pd.read_csv(io.StringIO(text),sep=s,engine="python")
            d=d.loc[:,~d.columns.str.match(r'^Unnamed')]; d.columns=[c.strip() for c in d.columns]
            if len(d.columns)>=7 and(df is None or len(d.columns)>len(df.columns)): df=d; sf=s
        except: pass
    if df is None or len(df.columns)<7: return None,{**dbg,"err":"Cols insuffisantes"}
    dbg["cols"]=list(df.columns); cl={c.upper():c for c in df.columns}
    dc=None
    for c in ["DATE","date","DATE_DE_TIRAGE"]:
        if c in df.columns: dc=c; break
        if c.upper() in cl: dc=cl[c.upper()]; break
    if not dc:
        for c in df.columns:
            if "date" in c.lower(): dc=c; break
    if not dc: return None,{**dbg,"err":"No date"}
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
    if len(bc)<5: return None,{**dbg,"err":f"{len(bc)} boules"}
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
        S[n]={"numero":n,"ecart":ec,"ecart_moy":round(em,1),"ecart_max":ex,
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
            if s40 and nf: rm=min(nf,key=lambda x:st_["boules"][x]["chaleur"]); gr.remove(rm); gr.append(random.choice(s40)); gr=sorted(gr)
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
        helps={"⚖️ Parité":"Mix pairs/impairs","📊 Dizaines":"Répartition 1-10, 11-20...","➕ Somme":"Somme des 5 numéros dans la norme","🔀 Diversité":"Écarts variés entre les numéros","🚫 Suite":"Pas de suite 1-2-3","⭐ Étoiles":"Étoiles suffisamment espacées","🔢 Terms":"Derniers chiffres différents","⬆️⬇️ B/H":"Mix petits et grands numéros","🌡️ Chaleur":"Chaleur moyenne de la grille","📊 Proba":"Probabilité moyenne de sortie"}
        for cr,pt in sc["detail"].items():
            m=mx.get(cr,8); pct=pt/m if m else 0
            cl="#22c55e" if pct>=.7 else ("#f59e0b" if pct>=.4 else "#ef4444")
            bar="█"*int(pct*10)+"░"*(10-int(pct*10))
            tip=helps.get(cr,"")
            st.markdown(f"<span style='font-size:.85rem;color:#1e293b;' title='{tip}'>`{cr}` <span style='color:{cl};font-family:monospace;'>{bar}</span> **{pt}/{m}**</span>",unsafe_allow_html=True)

def auto_sug(st_, jid):
    jeu=JEUX[jid]; rc=[]
    nh=sum(1 for s in st_["boules"].values() if s["tend"]=="↗️")
    if nh>jeu["boules_max"]*.25: rc.append({"m":"tendance","r":f"{nh} numéros en hausse","c":80})
    nr=sum(1 for s in st_["boules"].values() if s["ratio_rec"]>=80)
    if nr>=5: rc.append({"m":"retard","r":f"{nr} numéros à ≥80% du record","c":75})
    mp=np.mean([s["proba"] for s in st_["boules"].values()])
    if mp>55: rc.append({"m":"probabiliste","r":f"Proba moy élevée ({mp:.1f}%)","c":70})
    me=np.mean([s["ecart"] for s in st_["boules"].values()]); ma=jeu["boules_max"]/5
    if me>ma*1.2: rc.append({"m":"froid","r":f"Écart moy élevé","c":65})
    else: rc.append({"m":"chaud","r":"Écart moy normal","c":60})
    rc.append({"m":"optimal","r":"Compromis","c":70})
    rc.sort(key=lambda x:x["c"],reverse=True); return rc

# ============================================================
# MAIN
# ============================================================
def main():
    st.sidebar.markdown("<div style='text-align:center;'><h1 style='font-size:2rem;color:#1e293b;'>🎱 Smart-Loto</h1><p style='color:#64748b;'>V5.2 — Simple + Expert</p></div>",unsafe_allow_html=True)
    st.sidebar.markdown("---")
    jid=st.sidebar.selectbox("🎮 Jeu",["euromillions","loto"],format_func=lambda x:f"{JEUX[x]['emoji']} {JEUX[x]['nom']}",help="Choisis le jeu que tu veux analyser")
    jeu=JEUX[jid]
    st.sidebar.markdown("---")
    up=st.sidebar.file_uploader("📤 CSV FDJ",type=["csv","txt"],help="Télécharge le fichier CSV depuis fdj.fr → Historique des tirages")
    reel=False; dbg={}
    if up:
        df,dbg=load_csv(up,jid)
        if df is not None and len(df)>0: reel=True; st.sidebar.success(f"✅ {len(df)} tirages réels")
        else: st.sidebar.error("❌"); df=gen_simul(jid)
    else: df=gen_simul(jid); st.sidebar.info("💡 Importe un CSV FDJ pour des données réelles")
    if "gg" not in st.session_state: st.session_state.gg=[]
    st.sidebar.markdown("---")
    page=st.sidebar.radio("📑 Menu",[
        "🏠 Dashboard",
        "🎱 Générer (Simple)",
        "🎯 Générer (Expert)",
        "📊 Statistiques",
        "📱 Vérifier mes grilles",
        "💎 Quand jouer ?",
        "📖 Glossaire",
        "🧪 Backtest",
        "🧮 Réducteur",
        "🏆 Mes grilles",
        "🔍 Debug"],
        help="Navigue entre les pages de l'application")
    st.sidebar.markdown("---")
    st.sidebar.caption("⚠️ Aucune garantie de gain")
    st.sidebar.caption("🛡️ Joueurs Info Service : 09 74 75 13 13")
    stats=calc_stats(df.to_json(),jid)
    bdg="🟢 Données réelles" if reel else "🟡 Données simulées"

    # ══════════════════
    # DASHBOARD
    # ══════════════════
    if page=="🏠 Dashboard":
        st.markdown("<div class='main-header'>🏠 Dashboard</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{jeu['nom']} — {bdg} — {stats['nb_tirages']} tirages analysés</div>",unsafe_allow_html=True)
        d=df.iloc[0]; bs=[int(d[f"boule_{i}"]) for i in range(1,6)]
        et_d=[int(d[f"etoile_{i}"]) for i in range(1,jeu["nb_etoiles"]+1)] if jeu["nb_etoiles"] and "etoile_1" in df.columns else []
        st.subheader(f"🎱 Dernier tirage — {d['date']}")
        st.markdown(html_gr(bs,et_d,stats,jid),unsafe_allow_html=True)
        rc=auto_sug(stats,jid)
        if rc:
            b=rc[0]
            st.markdown(f"<div class='reco-card'>🔮 <b>Recommandation du jour :</b> Profil <b>{b['m'].upper()}</b> — {b['r']} (confiance {b['c']}%)</div>",unsafe_allow_html=True)
        st.subheader("📋 Derniers tirages")
        dern=[]
        for i in range(min(10,len(df))):
            r=df.iloc[i]
            t=" - ".join(str(int(r[f"boule_{j}"])) for j in range(1,6))
            e=f"⭐{int(r['etoile_1'])} ⭐{int(r['etoile_2'])}" if jeu["nb_etoiles"] and "etoile_1" in df.columns else ""
            dern.append({"📅 Date":str(r["date"]),"🎱 Numéros":t,"⭐ Étoiles":e})
        st.dataframe(pd.DataFrame(dern),hide_index=True,use_container_width=True)
        st.markdown("---")
        c1,c2=st.columns(2)
        with c1:
            st.subheader("🔥 Les plus chauds")
            st.caption("Numéros qui sortent le plus en ce moment")
            ch=sorted(stats["boules"].values(),key=lambda x:x["chaleur"],reverse=True)[:10]
            st.dataframe(pd.DataFrame(ch)[["numero","chaleur","f20","ecart","tend"]].rename(columns={"numero":"N°","chaleur":"Chaleur /100","f20":"Sorties (20 dern.)","ecart":"Absent depuis","tend":"Tendance"}),hide_index=True,use_container_width=True)
        with c2:
            st.subheader("🧊 Les plus attendus")
            st.caption("Numéros absents depuis longtemps")
            rt=sorted(stats["boules"].values(),key=lambda x:x["retard"])[:10]
            st.dataframe(pd.DataFrame(rt)[["numero","retard","ecart","ecart_moy","proba"]].rename(columns={"numero":"N°","retard":"Retard estimé","ecart":"Absent depuis","ecart_moy":"Absence moyenne","proba":"Proba sortie %"}),hide_index=True,use_container_width=True)

    # ══════════════════════════════════════
    # 🎱 GÉNÉRER — MODE SIMPLE (NOUVEAU!)
    # ══════════════════════════════════════
    elif page=="🎱 Générer (Simple)":
        st.markdown("<div class='main-header'>🎱 Générer mes Grilles</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Choisis un profil, c'est tout ! L'outil s'occupe du reste.</div>",unsafe_allow_html=True)

        # Étape 1 : Choix du profil
        st.subheader("1️⃣ Choisis ton style de jeu")

        profil_choisi = st.radio(
            "Quel joueur es-tu ?",
            list(PROFILS.keys()),
            format_func=lambda x: x,
            help="Chaque profil configure automatiquement tous les filtres et paramètres. Tu n'as rien d'autre à faire.",
            horizontal=True
        )

        # Afficher la description du profil
        profil = PROFILS[profil_choisi]
        st.markdown(f"<div class='insight-card'>💡 <b>{profil_choisi}</b> : {profil['desc']}</div>",unsafe_allow_html=True)

        st.markdown("---")

        # Étape 2 : Options simples
        st.subheader("2️⃣ Options (facultatif)")

        c1, c2 = st.columns(2)
        with c1:
            nbg = st.selectbox("Combien de grilles ?", [1, 3, 5, 10], index=1,
                help="Le nombre de grilles à générer. Plus tu en joues, plus tu couvres de numéros différents.")
            fi = st.text_input("🔒 Numéros porte-bonheur (optionnel)", placeholder="7, 23",
                help="Si tu as des numéros fétiches, entre-les ici (max 3). Ils seront inclus dans chaque grille.")
            forces=[int(n.strip()) for n in fi.split(",") if n.strip().isdigit() and 1<=int(n.strip())<=jeu["boules_max"]][:3] if fi else []
        with c2:
            ee = st.slider("⭐ Écart entre les étoiles", 0, 8, 2,
                help="Écart minimum entre tes 2 étoiles. Par exemple, 2 interdit le couple (3,4) mais autorise (3,5). Recommandé : 2.") if jeu["nb_etoiles"] else 0

        st.markdown("---")

        # Étape 3 : Générer
        st.subheader("3️⃣ C'est parti !")

        if st.button("🎱 GÉNÉRER MES GRILLES", type="primary", use_container_width=True):
            p = profil
            ag = []
            for gi in range(nbg):
                r = gen_grille(jid, stats, p["mode"], p["fp"], p["fs"], p["fd"], p["fa"],
                    p["chasseur"], forces, ee, p["plafond"], p["ft"], p["fb"],
                    p["pw_ch"], p["pw_ec"], p["pw_pr"])
                ag.append(r)
                st.markdown(f"#### Grille {gi+1}")
                st.markdown(html_gr(r["grille"], r["etoiles"], stats, jid), unsafe_allow_html=True)

                # Score simplifié
                sc = r["score"]
                ev = "⭐"*max(1,min(5,(sc["total"]-20)//15+1))
                cc = "#22c55e" if sc["total"]>=70 else ("#f59e0b" if sc["total"]>=50 else "#ef4444")

                # Explication en langage simple
                gr = r["grille"]
                nb_pairs = sum(1 for n in gr if n%2==0)
                nb_bas = sum(1 for n in gr if n <= 25)
                somme = sum(gr)

                st.markdown(f"""
                <div style='background:#f8fafc;border-radius:12px;padding:15px;margin:10px 0;color:#1e293b;border:1px solid #e2e8f0;'>
                <span style='font-size:1.5rem;font-weight:800;color:{cc};'>{sc['total']}/100</span> {ev}<br>
                <span style='color:#64748b;font-size:0.9rem;'>
                {nb_pairs} pairs + {5-nb_pairs} impairs •
                {nb_bas} petits + {5-nb_bas} grands •
                Somme = {somme} •
                {len(set(n%10 for n in gr))} terminaisons différentes
                </span>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("📋 Voir le détail de chaque numéro"):
                    det = []
                    for b in gr:
                        s = stats["boules"][b]
                        det.append({
                            "N°": b,
                            "Chaleur /100": s["chaleur"],
                            "Absent depuis": f"{s['ecart']} tirages",
                            "Tendance": s["tend"],
                            "Proba sortie": f"{s['proba']}%",
                            "Dernière sortie": s["dern"]
                        })
                    st.dataframe(pd.DataFrame(det), hide_index=True, use_container_width=True)

                st.markdown("---")

            # Sauvegarder
            st.session_state.gg.extend([{"g":r["grille"],"e":r["etoiles"],"s":r["score"]["total"],"m":profil_choisi,"t":datetime.now().strftime("%H:%M")} for r in ag])

            # Mode buraliste
            st.subheader("📱 Recopie chez le buraliste")
            st.caption("Montre cet écran au buraliste ou recopie les numéros")
            for i, r in enumerate(ag):
                gs = " — ".join(str(n) for n in r["grille"])
                es = f"  |  ⭐ {' — '.join(str(e) for e in r['etoiles'])}" if r["etoiles"] else ""
                st.markdown(f"<div class='buraliste-card'>G{i+1} : {gs}{es}</div>", unsafe_allow_html=True)

            # Export
            exp = f"Smart-Loto — {jeu['nom']} — {datetime.now().strftime('%d/%m/%Y %H:%M')}\nProfil : {profil_choisi}\n{'='*40}\n\n"
            for i, r in enumerate(ag):
                gs = " - ".join(str(n) for n in r["grille"])
                es = f" | Étoiles: {' - '.join(str(e) for e in r['etoiles'])}" if r["etoiles"] else ""
                exp += f"Grille {i+1} : {gs}{es} (Score: {r['score']['total']}/100)\n"
            exp += "\n⚠️ Aucune garantie de gain. Joueurs Info Service : 09 74 75 13 13"
            st.download_button("📥 Télécharger mes grilles", exp, f"mes-grilles-{datetime.now().strftime('%Y%m%d')}.txt")

    # ══════════════════════════════════════
    # 🎯 GÉNÉRER — MODE EXPERT
    # ══════════════════════════════════════
    elif page=="🎯 Générer (Expert)":
        st.markdown("<div class='main-header'>🎯 Générateur Expert</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Contrôle total sur tous les paramètres</div>",unsafe_allow_html=True)

        c1,c2,c3=st.columns(3)
        with c1:
            st.markdown("### 🎯 Stratégie")
            mode=st.selectbox("Mode de sélection",["aleatoire","chaud","froid","top","hybride","optimal","probabiliste","tendance","retard","contrarian"],
                format_func=lambda x:{"aleatoire":"🎲 Aléatoire — Tirage au sort pur","chaud":"🔥 Chauds — Numéros qui sortent beaucoup","froid":"🧊 Froids — Numéros absents depuis longtemps","top":"⭐ Top annuel — Stars des 12 derniers mois","hybride":"🧠 Hybride — Mix pondéré intelligent","optimal":"🏆 Optimal — Compromis chaleur/écart/proba","probabiliste":"📊 Proba — Basé sur la probabilité de sortie","tendance":"📈 Tendance — Numéros en hausse récente","retard":"⏳ Retard — Numéros 'en retard' vs leur moyenne","contrarian":"🔄 Contrarian — Numéros les moins joués"}[x],
                help="Détermine COMMENT les numéros sont choisis. Chaque mode privilégie un critère différent.")
            if mode=="optimal":
                st.caption("Ajuste le poids de chaque critère :")
                pw_ch=st.slider("🌡️ Poids Chaleur",0,100,50,help="Plus c'est élevé, plus les numéros 'chauds' sont favorisés")
                pw_ec=st.slider("📏 Poids Écart",0,100,50,help="Plus c'est élevé, plus les numéros absents longtemps sont favorisés")
                pw_pr=st.slider("📊 Poids Proba",0,100,50,help="Plus c'est élevé, plus les numéros avec une forte probabilité estimée sont favorisés")
            else: pw_ch=pw_ec=pw_pr=50

        with c2:
            st.markdown("### 🔧 Préférences")
            fi=st.text_input("🔒 Numéros forcés (max 3)",placeholder="7, 14",help="Ces numéros seront obligatoirement dans chaque grille générée")
            forces=[int(n.strip()) for n in fi.split(",") if n.strip().isdigit() and 1<=int(n.strip())<=jeu["boules_max"]][:3] if fi else []
            chasseur=st.slider("🎯 Écart minimum requis",0,30,0,help="N'inclut que les numéros absents depuis au moins X tirages. 0 = pas de filtre.")
            plafond=st.selectbox("🔝 Filtre Plafond",["aucun","moins_40","force_40"],
                format_func=lambda x:{"aucun":"— Aucun filtre","moins_40":"Uniquement les numéros < 40","force_40":"Au moins 1 numéro ≥ 40"}[x],
                help="Contrôle si ta grille contient des 'grands' numéros (40-50)")
            ee=st.slider("⭐ Écart min étoiles",0,8,2,help="Écart minimum entre tes 2 étoiles. Ex: 2 interdit (3,4) mais autorise (3,5)") if jeu["nb_etoiles"] else 0
            nbg=st.selectbox("Nombre de grilles",[1,3,5,10],index=1,help="Combien de grilles différentes générer")

        with c3:
            st.markdown("### 🛡️ Filtres de qualité")
            fpa=st.checkbox("⚖️ Parité équilibrée",True,help="Rejette les grilles 100% paires ou 100% impaires. Vise un mix 2/3 ou 3/2.")
            fso=st.checkbox("➕ Somme dans la norme",True,help=f"Rejette si la somme des 5 numéros est hors [{jeu['somme_min']}-{jeu['somme_max']}]. Les tirages réels tombent presque toujours dans cette fourchette.")
            fdi=st.checkbox("📊 Dizaines réparties",True,help="Interdit plus de 3 numéros dans la même dizaine (ex: interdit 21+22+25+29)")
            fan=st.checkbox("🚫 Anti-suite",True,help="Interdit les suites de 3 numéros consécutifs (ex: interdit 7-8-9)")
            ftm=st.checkbox("🔢 Terminaisons variées",False,help="Exige au moins 4 terminaisons (dernier chiffre) différentes sur les 5 numéros")
            fbh=st.checkbox("⬆️⬇️ Bas/Hauts équilibrés",False,help="Exige un mix de petits (1-25) et grands (26-50) numéros")

        if st.button("🎯 GÉNÉRER",type="primary",use_container_width=True):
            ag=[]
            for gi in range(nbg):
                r=gen_grille(jid,stats,mode,fpa,fso,fdi,fan,chasseur,forces,ee,plafond,ftm,fbh,pw_ch,pw_ec,pw_pr)
                ag.append(r)
                st.markdown(f"#### Grille {gi+1}/{nbg}")
                st.markdown(html_gr(r["grille"],r["etoiles"],stats,jid),unsafe_allow_html=True)
                show_sc(r["score"])
                with st.expander(f"📋 Détail G{gi+1}"):
                    det=[{"N°":b,"Chaleur":stats["boules"][b]["chaleur"],"Absent depuis":stats["boules"][b]["ecart"],"Proba %":stats["boules"][b]["proba"],"Tendance":stats["boules"][b]["tend"],"Retard":stats["boules"][b]["retard"]} for b in r["grille"]]
                    st.dataframe(pd.DataFrame(det),hide_index=True,use_container_width=True)
                st.markdown("---")
            st.session_state.gg.extend([{"g":r["grille"],"e":r["etoiles"],"s":r["score"]["total"],"m":mode,"t":datetime.now().strftime("%H:%M")} for r in ag])
            st.subheader("📱 Buraliste")
            for i,r in enumerate(ag):
                gs=" — ".join(str(n) for n in r["grille"])
                es=f"  |  ⭐ {' — '.join(str(e) for e in r['etoiles'])}" if r["etoiles"] else ""
                st.markdown(f"<div class='buraliste-card'>G{i+1} : {gs}{es}</div>",unsafe_allow_html=True)
            exp="".join(f"G{i+1}: {' - '.join(str(n) for n in r['grille'])}{' | E:'+' - '.join(str(e) for e in r['etoiles']) if r['etoiles'] else ''} (S:{r['score']['total']})\n" for i,r in enumerate(ag))
            st.download_button("📥 Télécharger",exp,f"grilles-expert-{datetime.now().strftime('%Y%m%d')}.txt")

    # ══════════════════
    # STATS
    # ══════════════════
    elif page=="📊 Statistiques":
        st.markdown("<div class='main-header'>📊 Statistiques</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{bdg} — {stats['nb_tirages']} tirages</div>",unsafe_allow_html=True)

        st.subheader("🌡️ Carte de Chaleur")
        st.caption("Plus c'est rouge, plus le numéro est 'chaud' (sort souvent en ce moment). Survole pour voir les détails.")
        nc=10; nr=(jeu["boules_max"]+nc-1)//nc; zd=[]; td=[]
        for row in range(nr):
            zr=[]; tr=[]
            for col in range(nc):
                n=row*nc+col+1
                if n<=jeu["boules_max"]:
                    s=stats["boules"][n]; zr.append(s["chaleur"])
                    tr.append(f"N°{n}<br>Chaleur: {s['chaleur']}/100<br>Absent depuis: {s['ecart']} tirages<br>Sorties (20 dern.): {s['f20']}<br>Tendance: {s['tend']}<br>Proba: {s['proba']}%")
                else: zr.append(None); tr.append("")
            zd.append(zr); td.append(tr)
        fh=go.Figure(data=go.Heatmap(z=zd,text=td,hoverinfo="text",colorscale=[[0,"#1e3a5f"],[.5,"#f59e0b"],[1,"#ef4444"]],showscale=True,colorbar=dict(title="Chaleur")))
        for row in range(nr):
            for col in range(nc):
                n=row*nc+col+1
                if n<=jeu["boules_max"]: fh.add_annotation(x=col,y=row,text=str(n),showarrow=False,font=dict(color="white",size=14))
        fh.update_layout(height=350,margin=dict(l=20,r=20,t=20,b=20),xaxis=dict(showticklabels=False),yaxis=dict(showticklabels=False))
        st.plotly_chart(fh,use_container_width=True)

        st.subheader("📋 Tous les numéros")
        st.caption("Clique sur un en-tête de colonne pour trier. Survole les en-têtes pour comprendre chaque terme.")
        tri=st.selectbox("Trier par",["Chaleur","Écart","Proba","Sorties récentes","Retard","% Record"],
            help="Choisis le critère de tri. Les numéros seront classés selon ce critère.")
        col_map={"Chaleur":"Chaleur /100","Écart":"Absent depuis","Proba":"Proba %","Sorties récentes":"Sorties (20 dern.)","Retard":"Retard estimé","% Record":"% du record"}
        dfc=pd.DataFrame([{
            "N°":n,
            "Chaleur /100":stats["boules"][n]["chaleur"],
            "Absent depuis":stats["boules"][n]["ecart"],
            "Absence moy.":stats["boules"][n]["ecart_moy"],
            "Record absence":stats["boules"][n]["ecart_max"],
            "Proba %":stats["boules"][n]["proba"],
            "Tendance":stats["boules"][n]["tend"],
            "Sorties (20 dern.)":stats["boules"][n]["f20"],
            "Sorties (12 mois)":stats["boules"][n]["f12m"],
            "Retard estimé":stats["boules"][n]["retard"],
            "% du record":stats["boules"][n]["ratio_rec"]
        } for n in range(1,jeu["boules_max"]+1)])
        col_tri=col_map.get(tri,"Chaleur /100")
        st.dataframe(dfc.sort_values(col_tri,ascending=(tri in ["Écart","Retard"])),hide_index=True,use_container_width=True,height=500)

    # ══════════════════
    # CHECKER
    # ══════════════════
    elif page=="📱 Vérifier mes grilles":
        st.markdown("<div class='main-header'>📱 Vérifier mes grilles</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Entre les numéros du tirage pour vérifier tes grilles</div>",unsafe_allow_html=True)

        ti=st.text_input("🎱 Les 5 numéros du tirage",placeholder="3, 17, 28, 34, 45",help="Entre les 5 numéros gagnants du tirage, séparés par des virgules")
        ei=""
        if jeu["nb_etoiles"]: ei=st.text_input("⭐ Les 2 étoiles",placeholder="2, 11",help="Entre les 2 étoiles gagnantes")

        if ti:
            tirage=sorted(set(int(n.strip()) for n in ti.split(",") if n.strip().isdigit()))
            etoiles_t=sorted(set(int(n.strip()) for n in ei.split(",") if n.strip().isdigit())) if ei else []
            if len(tirage)==5:
                st.markdown(html_gr(tirage,etoiles_t,stats,jid),unsafe_allow_html=True)
                if st.session_state.gg:
                    st.subheader(f"📋 Résultat pour {len(st.session_state.gg)} grilles")
                    res=[]
                    for i,g in enumerate(st.session_state.gg):
                        cm=set(g["g"])&set(tirage)
                        res.append({"i":i+1,"g":g["g"],"b":len(cm),"c":sorted(cm),"m":g["m"]})
                    res.sort(key=lambda x:x["b"],reverse=True)
                    for r in res:
                        em="🎉🎉🎉" if r["b"]>=5 else ("🎉🎉" if r["b"]==4 else ("🎉" if r["b"]==3 else ("👍" if r["b"]==2 else "—")))
                        st.markdown(f"{em} **Grille {r['i']}** `{r['g']}` → **{r['b']} numéros trouvés** {list(r['c'])} — profil: {r['m']}")
                    best=max(res,key=lambda x:x["b"])
                    if best["b"]>=3:
                        st.balloons()
                        st.markdown(f"<div class='success-card'>🎉 Bravo ! Ta meilleure grille avait <b>{best['b']}/5</b> bons numéros !</div>",unsafe_allow_html=True)
                else: st.info("Tu n'as pas encore généré de grilles. Va dans '🎱 Générer' d'abord !")
            else: st.warning(f"Il faut exactement 5 numéros ({len(tirage)} saisis)")

    # ══════════════════
    # ESPÉRANCE
    # ══════════════════
    elif page=="💎 Quand jouer ?":
        st.markdown("<div class='main-header'>💎 Quand jouer ?</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>L'espérance mathématique te dit quand c'est « le moins mauvais »</div>",unsafe_allow_html=True)
        st.markdown("""<div class='insight-card'>
        💡 <b>L'espérance mathématique</b> = combien tu gagnes EN MOYENNE par grille jouée.<br>
        C'est toujours négatif (sinon la FDJ perdrait de l'argent !)<br>
        Mais c'est <b>moins négatif</b> quand le jackpot est très élevé.
        </div>""",unsafe_allow_html=True)
        jp=st.number_input("💰 Jackpot actuel (en millions €)",17,250,50,step=1,help="Le montant du jackpot affiché par la FDJ. Plus il est élevé, moins tu perds en moyenne.")
        jpe=jp*1_000_000
        if jid=="euromillions":
            pr={"5+2⭐":1/139838160,"5+1⭐":1/6991908,"5+0":1/3107515,"4+2⭐":1/621503,"4+1⭐":1/31075,"4+0":1/13811,"3+2⭐":1/14125,"3+1⭐":1/706,"3+0":1/314,"2+2⭐":1/985,"2+1⭐":1/49,"1+2⭐":1/188}
            gf={"5+2⭐":jpe,"5+1⭐":500000,"5+0":50000,"4+2⭐":5000,"4+1⭐":200,"4+0":100,"3+2⭐":60,"3+1⭐":14,"3+0":13,"2+2⭐":17,"2+1⭐":8,"1+2⭐":10}
        else:
            pr={"5+chance":1/19068840,"5":1/2118760,"4+chance":1/86677,"4":1/9631,"3+chance":1/2016,"3":1/224,"2+chance":1/144,"2":1/16}
            gf={"5+chance":jpe,"5":100000,"4+chance":2000,"4":500,"3+chance":50,"3":10,"2+chance":6,"2":3}
        esp=sum(pr[r]*gf[r] for r in pr); espn=esp-jeu["prix"]
        c1,c2,c3=st.columns(3)
        c1.metric("Tu dépenses",f"{jeu['prix']}€",help="Le prix d'une grille")
        c2.metric("Tu récupères en moyenne",f"{esp:.2f}€",help="Ce que tu gagnes EN MOYENNE par grille (tous rangs confondus)")
        c3.metric("Bilan moyen par grille",f"{espn:+.2f}€",delta_color="normal" if espn>=0 else "inverse",help="Négatif = tu perds en moyenne. Positif = tu gagnes en moyenne (très rare).")
        if espn>=0: st.markdown(f"<div class='success-card'>✅ Jackpot à <b>{jp}M€</b> → C'est le meilleur moment pour jouer (statistiquement) !</div>",unsafe_allow_html=True)
        else:
            pp=abs(espn)/jeu["prix"]*100
            seuil=jeu["prix"]/pr[list(pr.keys())[0]]/1e6
            st.markdown(f"<div class='alert-card'>📉 Tu perds en moyenne <b>{abs(espn):.2f}€</b> par grille ({pp:.0f}% de ta mise).<br>Il faudrait un jackpot de <b>~{seuil:.0f}M€</b> pour que ça devienne rentable.</div>",unsafe_allow_html=True)

    # ══════════════════
    # GLOSSAIRE
    # ══════════════════
    elif page=="📖 Glossaire":
        st.markdown("<div class='main-header'>📖 Glossaire</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Tous les termes expliqués simplement</div>",unsafe_allow_html=True)

        search = st.text_input("🔍 Rechercher un terme", placeholder="chaleur, écart, parité...")

        for terme, definition in GLOSSAIRE.items():
            if search and search.lower() not in terme.lower() and search.lower() not in definition.lower():
                continue
            st.markdown(f"<div class='glossary-term'><b>{terme}</b><br>{definition}</div>",unsafe_allow_html=True)

    # ══════════════════
    # BACKTEST
    # ══════════════════
    elif page=="🧪 Backtest":
        st.markdown("<div class='main-header'>🧪 Backtest</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Teste une stratégie sur les tirages passés</div>",unsafe_allow_html=True)
        st.markdown("""<div class='insight-card'>
        💡 <b>Le backtest</b> simule ta stratégie sur les tirages passés.
        "Si j'avais joué comme ça pendant X tirages, combien j'aurais gagné/perdu ?"
        </div>""",unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1: m=st.selectbox("Stratégie à tester",["aleatoire","chaud","froid","optimal","probabiliste","tendance","retard"],help="La stratégie que tu veux évaluer")
        with c2: nt=st.selectbox("Nombre de tirages",[20,50,100,200],index=1,help="Sur combien de tirages passés tester")
        if st.button("🚀 Lancer le test",type="primary",use_container_width=True):
            with st.spinner("⏳ Simulation en cours..."): rb=backtest(df,jid,stats,m,nt)
            c1,c2,c3=st.columns(3)
            c1.metric("💰 Misé",f"{rb['mise']}€",help="Combien tu aurais dépensé")
            c2.metric("🏆 Gagné",f"{rb['gains']}€",help="Combien tu aurais récupéré")
            c3.metric("📈 Bilan",f"{rb['bilan']:+.2f}€",help="Gagné - Misé")
            res=rb["res"]
            fig=go.Figure(go.Bar(x=[f"{k} bons numéros" for k in sorted(res)],y=[res[k] for k in sorted(res)],
                marker_color=["#ef4444","#f97316","#f59e0b","#84cc16","#22c55e","#15803d"]))
            fig.update_layout(height=300,title="Combien de bons numéros par tirage ?"); st.plotly_chart(fig,use_container_width=True)
            if rb["hi"]:
                st.subheader("🎯 Meilleures correspondances")
                for h in rb["hi"][:10]: st.markdown(f"📅 **{h['date']}** — Ta grille: `{h['grille']}` — Tirage réel: `{h['tirage']}` — **{h['bons']} bons** — Gain: {h['gain']}€")

    # ══════════════════
    # RÉDUCTEUR
    # ══════════════════
    elif page=="🧮 Réducteur":
        st.markdown("<div class='main-header'>🧮 Réducteur</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Choisis plus de numéros → le système crée les grilles</div>",unsafe_allow_html=True)
        st.markdown("""<div class='insight-card'>
        💡 <b>Le réducteur</b> te permet de sélectionner 6 à 15 numéros que tu "sens bien",
        et le système génère automatiquement plusieurs grilles de 5 numéros
        qui couvrent au mieux ta sélection.
        </div>""",unsafe_allow_html=True)
        with st.expander("💡 Suggestions basées sur les stats"):
            tp=sorted(stats["boules"].values(),key=lambda x:x["proba"],reverse=True)[:10]
            st.markdown(f"**Top probabilité :** `{', '.join(str(n['numero']) for n in tp)}`")
            tc=sorted(stats["boules"].values(),key=lambda x:x["chaleur"],reverse=True)[:10]
            st.markdown(f"**Top chaleur :** `{', '.join(str(n['numero']) for n in tc)}`")
        ni=st.text_input("🔢 Tes numéros (entre 6 et 15, séparés par des virgules)",placeholder="3, 7, 14, 19, 23, 28, 34, 41",help="Sélectionne les numéros que tu penses gagnants. Le système créera les combinaisons optimales.")
        if ni:
            nums=sorted(set(int(n.strip()) for n in ni.split(",") if n.strip().isdigit() and 1<=int(n.strip())<=jeu["boules_max"]))
            if len(nums)>=6:
                st.success(f"✅ {len(nums)} numéros sélectionnés : {nums}")
                if st.button("🧮 Générer les grilles",type="primary",use_container_width=True):
                    grs=reducteur(nums)
                    st.info(f"💰 {len(grs)} grilles × {jeu['prix']}€ = **{len(grs)*jeu['prix']:.2f}€**")
                    for i,g in enumerate(grs):
                        st.markdown(f"<div class='grille-container'><b>G{i+1}</b>&nbsp;&nbsp;{'&nbsp;&nbsp;'.join(f'<span class=\"boule\">{b}</span>' for b in g)}</div>",unsafe_allow_html=True)
            else: st.warning(f"Il faut au moins 6 numéros (tu en as {len(nums)})")

    # ══════════════════
    # HALL OF FAME
    # ══════════════════
    elif page=="🏆 Mes grilles":
        st.markdown("<div class='main-header'>🏆 Mes grilles</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Toutes les grilles générées pendant cette session</div>",unsafe_allow_html=True)
        if st.session_state.gg:
            sg=sorted(st.session_state.gg,key=lambda x:x["s"],reverse=True)
            st.metric("Total grilles",len(sg))
            st.metric("Meilleur score",f"{sg[0]['s']}/100")
            for i,g in enumerate(sg[:30]):
                md="🥇" if i==0 else ("🥈" if i==1 else ("🥉" if i==2 else f"#{i+1}"))
                gs=" — ".join(str(n) for n in g["g"])
                es=f" | ⭐{' — '.join(str(e) for e in g['e'])}" if g["e"] else ""
                st.markdown(f"{md} **{g['s']}/100** — `{gs}{es}` — {g['m']} — {g['t']}")
            if st.button("🗑️ Tout effacer"): st.session_state.gg=[]; st.rerun()
        else: st.info("Tu n'as pas encore généré de grilles ! Va dans '🎱 Générer' pour commencer.")

    # ══════════════════
    # DEBUG
    # ══════════════════
    elif page=="🔍 Debug":
        st.markdown("<div class='main-header'>🔍 Debug CSV</div>",unsafe_allow_html=True)
        if dbg:
            if dbg.get("ok"): st.success(f"✅ {dbg.get('n','?')} tirages chargés")
            else: st.error(f"❌ {dbg.get('err','?')}")
            if "cols" in dbg:
                st.subheader("Colonnes détectées")
                for i,c in enumerate(dbg["cols"][:15]): st.markdown(f"`{i}` → **{c}**")
            if "map" in dbg:
                m=dbg["map"]; st.success(f"📅 Date: `{m['d']}` | 🎱 Boules: `{m['b']}` | ⭐ Étoiles: `{m['e']}`")
        else: st.info("Importe un CSV pour voir le diagnostic")
        st.subheader("Aperçu des données")
        st.dataframe(df.head(10),use_container_width=True)

    # FOOTER
    st.markdown("<div class='footer-disclaimer'>⚠️ Outil d'analyse statistique — Aucune garantie de gain — Chaque tirage est un événement indépendant<br>🛡️ <a href='https://www.joueurs-info-service.fr/'>Joueurs Info Service</a> : 09 74 75 13 13</div>",unsafe_allow_html=True)

if __name__=="__main__":
    main()
