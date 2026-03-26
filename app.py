# ============================================================
# SMART-LOTO — V3.0 — VERSION COMPLÈTE
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

st.set_page_config(page_title="Smart-Loto", page_icon="🎱", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .main-header {font-size:2.5rem;font-weight:800;background:linear-gradient(135deg,#1e40af,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;padding:10px 0;}
    .sub-header {text-align:center;color:#64748b;font-size:1.1rem;margin-bottom:30px;}
    .boule {background:linear-gradient(135deg,#1e40af,#3b82f6);color:white;border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;margin:5px;box-shadow:0 4px 12px rgba(30,64,175,0.4);}
    .etoile {background:linear-gradient(135deg,#f59e0b,#fbbf24);color:white;border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;margin:5px;box-shadow:0 4px 12px rgba(245,158,11,0.4);}
    .grille-container {display:flex;align-items:center;justify-content:center;padding:25px;background:linear-gradient(135deg,#f8fafc,#e2e8f0);border-radius:20px;margin:15px 0;border:2px solid #e2e8f0;}
    .footer-disclaimer {background:#fef3c7;border:1px solid #f59e0b;border-radius:12px;padding:15px;margin-top:30px;text-align:center;font-size:0.9rem;}
    .alert-card {background:linear-gradient(135deg,#fef2f2,#fee2e2);border:2px solid #ef4444;border-radius:16px;padding:20px;margin:10px 0;}
    .success-card {background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:2px solid #22c55e;border-radius:16px;padding:20px;margin:10px 0;}
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom":"Euromillions","emoji":"⭐","boules_max":50,"nb_boules":5,"etoiles_max":12,"nb_etoiles":2,"prix":2.50,"somme_min":90,"somme_max":160},
    "loto": {"nom":"Loto","emoji":"🎱","boules_max":49,"nb_boules":5,"etoiles_max":None,"nb_etoiles":0,"prix":2.20,"somme_min":60,"somme_max":180}
}

# ============================================================
# CHARGEMENT CSV
# ============================================================

def detecter_et_charger_csv(uploaded_file, jeu_id):
    jeu = JEUX[jeu_id]; debug = {}
    content = uploaded_file.read(); uploaded_file.seek(0)
    text = None
    for enc in ["utf-8-sig","utf-8","latin-1","cp1252"]:
        try: text = content.decode(enc); debug["encodage"] = enc; break
        except: continue
    if text is None: return None, {"erreur":"Décodage impossible"}
    text = text.lstrip("\ufeff")

    df = None; sep_final = None
    for try_sep in [";",",","\t"]:
        try:
            dft = pd.read_csv(io.StringIO(text), sep=try_sep, engine="python")
            dft = dft.loc[:, ~dft.columns.str.match(r'^Unnamed')]
            dft = dft.loc[:, dft.columns.str.strip() != '']
            dft.columns = [c.strip() for c in dft.columns]
            debug[f"sep_{repr(try_sep)}"] = f"{len(dft.columns)} cols"
            if len(dft.columns) >= 7 and (df is None or len(dft.columns) > len(df.columns)):
                df = dft; sep_final = try_sep
        except: pass
    if df is None or len(df.columns) < 7:
        return None, {**debug, "erreur": "Pas assez de colonnes"}

    debug["separateur"] = repr(sep_final); debug["colonnes"] = list(df.columns)
    cl = {c.upper(): c for c in df.columns}

    # Date
    date_col = None
    for cand in ["DATE","Date","date","DATE_DE_TIRAGE","date_de_tirage"]:
        if cand in df.columns: date_col = cand; break
        if cand.upper() in cl: date_col = cl[cand.upper()]; break
    if not date_col:
        for c in df.columns:
            if "date" in c.lower(): date_col = c; break
    if not date_col:
        for c in df.columns:
            try:
                s = str(df[c].iloc[0]).strip()
                if re.match(r'\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}', s): date_col = c; break
            except: continue
    if not date_col: return None, {**debug, "erreur": "Colonne date introuvable"}

    # Boules
    bcols = []
    for i in range(1, 6):
        for cand in [f"N{i}",f"n{i}",f"BOULE_{i}",f"boule_{i}",f"B{i}",f"b{i}"]:
            if cand in df.columns: bcols.append(cand); break
            elif cand.upper() in cl: bcols.append(cl[cand.upper()]); break
    if len(bcols) < 5:
        bcols = []
        for c in df.columns:
            if c == date_col: continue
            try:
                v = pd.to_numeric(df[c], errors="coerce").dropna()
                if len(v) > len(df)*.3 and v.min() >= 1 and v.max() <= jeu["boules_max"]:
                    bcols.append(c)
                    if len(bcols) >= 5: break
            except: continue
    if len(bcols) < 5: return None, {**debug, "erreur": f"{len(bcols)} boules trouvées"}

    # Étoiles
    ecols = []
    if jeu["nb_etoiles"] > 0:
        for i in range(1, 3):
            for cand in [f"E{i}",f"e{i}",f"ETOILE_{i}",f"etoile_{i}",f"S{i}"]:
                if cand in df.columns: ecols.append(cand); break
                elif cand.upper() in cl: ecols.append(cl[cand.upper()]); break
        if len(ecols) < 2:
            ecols = []; used = set(bcols) | {date_col}
            for c in df.columns:
                if c in used: continue
                try:
                    v = pd.to_numeric(df[c], errors="coerce").dropna()
                    if len(v) > len(df)*.3 and v.min() >= 1 and v.max() <= 12:
                        ecols.append(c)
                        if len(ecols) >= 2: break
                except: continue

    # Jour de semaine
    jour_col = None
    for cand in ["JOUR","jour","JOUR_DE_TIRAGE","jour_de_tirage","DAY"]:
        if cand in df.columns: jour_col = cand; break
        elif cand.upper() in cl: jour_col = cl[cand.upper()]; break

    # Build result
    result = pd.DataFrame()
    for fmt in [None, "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
        try:
            if fmt: result["date"] = pd.to_datetime(df[date_col], format=fmt, errors="coerce").dt.date
            else: result["date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce").dt.date
            if result["date"].notna().sum() > len(df)*.5: break
        except: continue

    for i, c in enumerate(bcols[:5], 1):
        result[f"boule_{i}"] = pd.to_numeric(df[c], errors="coerce")
    for i, c in enumerate(ecols[:2], 1):
        result[f"etoile_{i}"] = pd.to_numeric(df[c], errors="coerce")

    # Jour
    if jour_col and jour_col in df.columns:
        result["jour"] = df[jour_col].astype(str).str.strip().str.lower()
    else:
        try:
            result["jour"] = pd.to_datetime(result["date"]).dt.day_name().str.lower()
            jour_map = {"monday":"lundi","tuesday":"mardi","wednesday":"mercredi",
                       "thursday":"jeudi","friday":"vendredi","saturday":"samedi","sunday":"dimanche"}
            result["jour"] = result["jour"].map(lambda x: jour_map.get(x, x))
        except: result["jour"] = "inconnu"

    result = result.dropna(subset=["date","boule_1","boule_2","boule_3","boule_4","boule_5"])
    for i in range(1,6): result[f"boule_{i}"] = result[f"boule_{i}"].astype(int)
    for i in range(1,3):
        if f"etoile_{i}" in result.columns: result[f"etoile_{i}"] = result[f"etoile_{i}"].fillna(0).astype(int)
    for i in range(1,6): result = result[(result[f"boule_{i}"]>=1)&(result[f"boule_{i}"]<=jeu["boules_max"])]
    result = result.sort_values("date", ascending=False).drop_duplicates("date").reset_index(drop=True)

    debug["succes"] = len(result) > 0; debug["nb_tirages"] = len(result)
    debug["mapping"] = {"date":date_col,"boules":bcols[:5],"etoiles":ecols[:2]}
    if len(result) > 0:
        debug["premier"] = str(result.iloc[-1]["date"]); debug["dernier"] = str(result.iloc[0]["date"])
        debug["exemple"] = {"date":str(result.iloc[0]["date"]),
            "boules":[int(result.iloc[0][f"boule_{i}"]) for i in range(1,6)],
            "etoiles":[int(result.iloc[0][f"etoile_{i}"]) for i in range(1,3)] if "etoile_1" in result.columns else []}
        debug["jours_disponibles"] = result["jour"].unique().tolist() if "jour" in result.columns else []
    return result, debug


def generer_historique_simule(jeu_id, nb=500):
    random.seed(42); np.random.seed(42)
    jeu = JEUX[jeu_id]; tirages = []; now = datetime.now()
    jours_cycle = ["mardi","vendredi"] if jeu_id == "euromillions" else ["lundi","mercredi","samedi"]
    for i in range(nb):
        b = sorted(random.sample(range(1,jeu["boules_max"]+1),5))
        e = sorted(random.sample(range(1,jeu["etoiles_max"]+1),2)) if jeu["etoiles_max"] else []
        t = {"date":(now-timedelta(days=i*3.5)).date(),"boule_1":b[0],"boule_2":b[1],"boule_3":b[2],"boule_4":b[3],"boule_5":b[4],"jour":jours_cycle[i%len(jours_cycle)]}
        if e: t["etoile_1"]=e[0]; t["etoile_2"]=e[1]
        tirages.append(t)
    return pd.DataFrame(tirages).sort_values("date",ascending=False).reset_index(drop=True)


# ============================================================
# MOTEUR STATISTIQUE
# ============================================================

@st.cache_data
def calculer_stats(df_json, jeu_id, jour_filtre=None):
    df = pd.read_json(io.StringIO(df_json)); df["date"] = pd.to_datetime(df["date"]).dt.date
    if jour_filtre and jour_filtre != "tous" and "jour" in df.columns:
        df = df[df["jour"].str.lower() == jour_filtre.lower()].reset_index(drop=True)

    jeu = JEUX[jeu_id]; stats = {}; cols = [f"boule_{i}" for i in range(1,6)]
    all_n = [];
    for c in cols: all_n.extend(df[c].tolist())
    df20 = df.head(20); n20 = []
    for c in cols: n20.extend(df20[c].tolist())
    d12m = datetime.now().date()-timedelta(days=365); df12 = df[df["date"]>=d12m]; n12 = []
    for c in cols: n12.extend(df12[c].tolist())
    fa,f20,f12 = Counter(all_n),Counter(n20),Counter(n12)

    for n in range(1,jeu["boules_max"]+1):
        ec = 0
        for _,r in df.iterrows():
            if n in [int(r[c]) for c in cols]: break
            ec += 1
        pos = [idx for idx,r in df.iterrows() if n in [int(r[c]) for c in cols]]
        ech = [pos[i+1]-pos[i] for i in range(len(pos)-1)] if len(pos)>1 else []
        em = np.mean(ech) if ech else 10; ex = max(ech) if ech else ec
        dern = None
        for _,r in df.iterrows():
            if n in [int(r[c]) for c in cols]: dern=r["date"]; break
        fo=(f20.get(n,0)/max(len(df20),1))*100; ft=(len(df12)*5)/jeu["boules_max"]
        fn=(f12.get(n,0)/max(ft,1))*50; ep=max(0,30-(ec*2))
        ch=min(100,max(0,.40*fo+.35*fn+.25*ep))
        ratio_ecart = (ec / ex * 100) if ex > 0 else 0
        stats[n] = {"numero":n,"ecart_actuel":ec,"ecart_moyen":round(em,1),"ecart_max":ex,
            "frequence_totale":fa.get(n,0),"frequence_20t":f20.get(n,0),"frequence_12m":f12.get(n,0),
            "indice_chaleur":round(ch,1),"derniere_sortie":str(dern) if dern else "—",
            "ratio_ecart_record":round(ratio_ecart,1)}

    se = {}
    if jeu["nb_etoiles"] and jeu["nb_etoiles"]>0 and "etoile_1" in df.columns:
        ce = [f"etoile_{i}" for i in range(1,jeu["nb_etoiles"]+1)]
        ae=[]; e20l=[]
        for c in ce:
            if c in df.columns: ae.extend(df[c].tolist()); e20l.extend(df20[c].tolist())
        fe,fe20 = Counter(ae),Counter(e20l)
        for n in range(1,jeu["etoiles_max"]+1):
            ec=0
            for _,r in df.iterrows():
                if n in [int(r[c]) for c in ce if c in df.columns]: break
                ec+=1
            se[n]={"numero":n,"ecart_actuel":ec,"frequence_totale":fe.get(n,0),"frequence_20t":fe20.get(n,0)}

    paires = Counter()
    for _,r in df.iterrows():
        bs=sorted([int(r[c])for c in cols])
        for i in range(len(bs)):
            for j in range(i+1,len(bs)): paires[(bs[i],bs[j])]+=1

    # Analyse structurelle des tirages
    analyses_tirages = []
    for _,r in df.iterrows():
        bs = [int(r[c]) for c in cols]
        nb_pairs = sum(1 for b in bs if b%2==0)
        nb_bas = sum(1 for b in bs if b<=25)
        somme = sum(bs)
        analyses_tirages.append({"date":r["date"],"pairs":nb_pairs,"impairs":5-nb_pairs,
            "bas":nb_bas,"hauts":5-nb_bas,"somme":somme})

    return {"boules":stats,"etoiles":se,"paires":paires.most_common(20),
        "nb_tirages":len(df),
        "date_premier":str(df.iloc[-1]["date"]) if len(df)>0 else "—",
        "date_dernier":str(df.iloc[0]["date"]) if len(df)>0 else "—",
        "analyses_tirages":analyses_tirages}


# ============================================================
# SCORE & GÉNÉRATEUR
# ============================================================

def score_robustesse(gr,et,stats,jid):
    jeu=JEUX[jid];sc={}
    np2=sum(1 for n in gr if n%2==0);r=np2/len(gr)
    sc["⚖️ Parité"]=25 if .3<=r<=.7 else(15 if .2<=r<=.8 else 5)
    dz=Counter(n//10 for n in gr)
    sc["📊 Dizaines"]=20 if(len(dz)>=4 and max(dz.values())<=2)else(15 if(len(dz)>=3 and max(dz.values())<=3)else 5)
    s=sum(gr);m=jeu["nb_boules"]*(jeu["boules_max"]+1)/2;z=abs(s-m)/35
    sc["➕ Somme"]=20 if z<=.5 else(15 if z<=1 else(10 if z<=1.5 else 3))
    ecs=[stats["boules"][n]["ecart_actuel"] for n in gr if n in stats["boules"]]
    sc["🔀 Diversité"]=(15 if float(np.std(ecs))>5 else(10 if float(np.std(ecs))>3 else 5))if len(set(ecs))>1 else 5
    g=sorted(gr);hs=any(g[i+1]==g[i]+1 and g[i+2]==g[i]+2 for i in range(len(g)-2))
    sc["🚫 Anti-suite"]=2 if hs else 10
    if et and len(et)==2:ec=abs(et[0]-et[1]);sc["⭐ Étoiles"]=10 if ec>=3 else(6 if ec>=2 else 2)
    else:sc["⭐ Étoiles"]=10
    return{"total":sum(sc.values()),"detail":sc}

def generer_grille(jid,stats,mode="aleatoire",fp=False,fs=False,fd=False,fa=False,
                   chasseur=0,forces=None,ee=0,plafond="aucun",mt=1000):
    jeu=JEUX[jid]
    for t in range(mt):
        if mode=="chaud":pool=sorted(stats["boules"],key=lambda x:stats["boules"][x]["indice_chaleur"],reverse=True)[:20]
        elif mode=="froid":pool=sorted(stats["boules"],key=lambda x:stats["boules"][x]["ecart_actuel"],reverse=True)[:20]
        elif mode=="top":pool=sorted(stats["boules"],key=lambda x:stats["boules"][x]["frequence_12m"],reverse=True)[:15]
        elif mode=="hybride":
            ns=list(stats["boules"].keys());pw=[stats["boules"][n]["indice_chaleur"]**1.5+5 for n in ns]
            tp=sum(pw);pool=list(np.random.choice(ns,size=min(25,len(ns)),replace=False,p=[p/tp for p in pw]))
        else:pool=list(range(1,jeu["boules_max"]+1))
        if plafond=="moins_40":pool=[n for n in pool if n<40]
        if chasseur>0:
            pf=[n for n in pool if stats["boules"][n]["ecart_actuel"]>=chasseur]
            if len(pf)>=5:pool=pf
        fo=[f for f in(forces or[])if 1<=f<=jeu["boules_max"]]
        di=[n for n in pool if n not in fo];mq=5-len(fo)
        if mq>len(di):di=[n for n in range(1,jeu["boules_max"]+1)if n not in fo]
        ch=random.sample(di,min(mq,len(di)))if mq>0 else[]
        gr=sorted(fo+ch)[:5]
        if plafond=="force_40"and not any(n>=40 for n in gr):
            s40=[n for n in range(40,jeu["boules_max"]+1)if n not in gr]
            nf=[n for n in gr if n not in fo]
            if s40 and nf:rm=min(nf,key=lambda x:stats["boules"][x]["indice_chaleur"]);gr.remove(rm);gr.append(random.choice(s40));gr=sorted(gr)
        et=[]
        if jeu["nb_etoiles"]and jeu["nb_etoiles"]>0 and jeu["etoiles_max"]:
            for _ in range(100):
                et=sorted(random.sample(range(1,jeu["etoiles_max"]+1),jeu["nb_etoiles"]))
                if ee>0 and len(et)==2 and abs(et[0]-et[1])>=ee:break
                elif ee==0:break
        v=True
        if fp:np2=sum(1 for n in gr if n%2==0);v=v and np2>0 and np2<5
        if fs:v=v and jeu["somme_min"]<=sum(gr)<=jeu["somme_max"]
        if fd:v=v and max(Counter(n//10 for n in gr).values())<=3
        if fa:gs=sorted(gr);v=v and not any(gs[i+1]==gs[i]+1 and gs[i+2]==gs[i]+2 for i in range(len(gs)-2))
        if v:return{"grille":gr,"etoiles":et,"score":score_robustesse(gr,et,stats,jid),"tentatives":t+1,"mode":mode}
    gr=sorted(random.sample(range(1,jeu["boules_max"]+1),5))
    et=sorted(random.sample(range(1,jeu["etoiles_max"]+1),2))if jeu["etoiles_max"]else[]
    return{"grille":gr,"etoiles":et,"score":score_robustesse(gr,et,stats,jid),"tentatives":mt,"mode":"fallback"}

def mini_backtest(df,jid,stats,mode,nt=50,gpt=1):
    jeu=JEUX[jid];cols=[f"boule_{i}"for i in range(1,6)]
    res={str(i):0 for i in range(6)};tm=0;tg=0;gt={0:0,1:0,2:0,3:4,4:50,5:5000};hist=[]
    for idx in range(min(nt,len(df))):
        row=df.iloc[idx];bt=set(int(row[c])for c in cols)
        for _ in range(gpt):
            r=generer_grille(jid,stats,mode=mode);nb=len(set(r["grille"])&bt)
            res[str(nb)]+=1;tm+=jeu["prix"];g=gt.get(nb,0);tg+=g
            if nb>=3:hist.append({"date":str(row["date"]),"grille":r["grille"],"tirage":sorted(bt),"bons":nb,"gain":g})
    return{"resultats":res,"total_mise":round(tm,2),"total_gains":round(tg,2),"bilan":round(tg-tm,2),"nb_grilles":nt*gpt,"historique":hist}

def systeme_reducteur(nums,taille=5):
    from itertools import combinations
    if len(nums)<=taille:return[sorted(nums)]
    combs=list(combinations(nums,taille));random.shuffle(combs)
    grilles=[];couverts=set()
    for c in combs:
        if set(c)-couverts or not grilles:grilles.append(sorted(c));couverts|=set(c)
        if couverts==set(nums)and len(grilles)>=3:break
        if len(grilles)>=12:break
    return grilles


# ============================================================
# AFFICHAGE GRILLE (réutilisable)
# ============================================================

def afficher_grille_html(gr, et, stats, jeu_id):
    html = "<div class='grille-container'>"
    for b in gr:
        ch = stats["boules"][b]["indice_chaleur"]
        bg = "linear-gradient(135deg,#dc2626,#ef4444)" if ch>=60 else("linear-gradient(135deg,#1e40af,#3b82f6)"if ch>=40 else"linear-gradient(135deg,#1e3a5f,#475569)")
        html += f"<span style='background:{bg};color:white;border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;margin:5px;box-shadow:0 4px 12px rgba(0,0,0,0.3);'>{b}</span>"
    if et:
        html += "<span style='margin:0 15px;font-size:28px;color:#94a3b8;'>|</span>"
        for e in et: html += f"<span class='etoile'>⭐{e}</span>"
    html += "</div>"
    return html

def afficher_score(sc):
    ev = "⭐⭐⭐⭐⭐" if sc["total"]>=80 else("⭐⭐⭐⭐"if sc["total"]>=65 else("⭐⭐⭐"if sc["total"]>=50 else"⭐⭐"))
    sc_c = "#22c55e" if sc["total"]>=70 else("#f59e0b"if sc["total"]>=50 else"#ef4444")
    cs1, cs2 = st.columns([1,2])
    with cs1:
        st.markdown(f"<div style='text-align:center;'><div style='font-size:3rem;font-weight:800;color:{sc_c};'>{sc['total']}</div><div style='color:#64748b;'>/ 100 {ev}</div></div>",unsafe_allow_html=True)
    with cs2:
        mx={"⚖️ Parité":25,"📊 Dizaines":20,"➕ Somme":20,"🔀 Diversité":15,"🚫 Anti-suite":10,"⭐ Étoiles":10}
        for cr,pt in sc["detail"].items():
            m=mx.get(cr,10);pct=pt/m if m else 0
            cl="#22c55e"if pct>=.7 else("#f59e0b"if pct>=.4 else"#ef4444")
            bar="█"*int(pct*12)+"░"*(12-int(pct*12))
            st.markdown(f"`{cr}` <span style='color:{cl};font-family:monospace;'>{bar}</span> **{pt}/{m}**",unsafe_allow_html=True)


# ============================================================
# INTERFACE PRINCIPALE
# ============================================================

def main():
    st.sidebar.markdown("<div style='text-align:center;'><h1 style='font-size:2rem;'>🎱 Smart-Loto</h1><p style='color:#64748b;'>V3.0</p></div>",unsafe_allow_html=True)
    st.sidebar.markdown("---")
    jeu_id = st.sidebar.selectbox("🎮 Jeu",["euromillions","loto"],format_func=lambda x:f"{JEUX[x]['emoji']} {JEUX[x]['nom']}")
    jeu = JEUX[jeu_id]
    st.sidebar.markdown("---")
    uploaded = st.sidebar.file_uploader(f"📤 CSV {jeu['nom']}",type=["csv","txt"])

    donnees_reelles = False; debug = {}
    if uploaded:
        df, debug = detecter_et_charger_csv(uploaded, jeu_id)
        if df is not None and len(df) > 0:
            donnees_reelles = True
            st.sidebar.success(f"✅ {len(df)} tirages réels")
            if "mapping" in debug:
                m=debug["mapping"]
                st.sidebar.caption(f"📅{m['date']} 🎱{m['boules']} ⭐{m['etoiles']}")
        else:
            st.sidebar.error("❌ Erreur CSV")
            df = generer_historique_simule(jeu_id)
    else:
        df = generer_historique_simule(jeu_id)
        st.sidebar.info("💡 Importe un CSV FDJ")

    # Sauvegarde en session
    if "grilles_generees" not in st.session_state:
        st.session_state.grilles_generees = []

    st.sidebar.markdown("---")
    page = st.sidebar.radio("📑 Menu", [
        "🏠 Dashboard", "🎯 Générateur", "📊 Statistiques",
        "📅 Par Jour", "🔮 Mes Fétiches", "✅ Vérificateur",
        "🚨 Alertes Écart", "📈 Évolution", "🆚 Comparateur",
        "🧪 Backtesting", "🧮 Réducteur", "🏆 Hall of Fame",
        "🔍 Debug CSV", "ℹ️ À propos"
    ])
    st.sidebar.markdown("---")
    st.sidebar.caption("⚠️ Aucune garantie de gain\n🛡️ 09 74 75 13 13")

    stats = calculer_stats(df.to_json(), jeu_id)
    badge = "🟢 Réelles" if donnees_reelles else "🟡 Simulées"

    # ════════════════════════════
    # DASHBOARD
    # ════════════════════════════
    if page == "🏠 Dashboard":
        st.markdown("<div class='main-header'>🏠 Dashboard</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{jeu['nom']} — {badge} — {stats['nb_tirages']} tirages</div>",unsafe_allow_html=True)
        if donnees_reelles: st.success(f"✅ {stats['nb_tirages']} tirages ({stats['date_premier']} → {stats['date_dernier']})")

        d=df.iloc[0]; bs=[int(d[f"boule_{i}"])for i in range(1,6)]
        et_d = [int(d[f"etoile_{i}"]) for i in range(1,jeu["nb_etoiles"]+1)] if jeu["nb_etoiles"] and "etoile_1" in df.columns else []
        st.subheader(f"🎱 Dernier tirage — {d['date']}")
        st.markdown(afficher_grille_html(bs, et_d, stats, jeu_id), unsafe_allow_html=True)

        st.subheader("📋 10 derniers tirages")
        dern=[]
        for i in range(min(10,len(df))):
            r=df.iloc[i]
            t=" - ".join(str(int(r[f"boule_{j}"]))for j in range(1,6))
            e = f"⭐{int(r['etoile_1'])} ⭐{int(r['etoile_2'])}" if jeu["nb_etoiles"] and "etoile_1" in df.columns else ""
            j = r.get("jour","") if "jour" in df.columns else ""
            dern.append({"📅":str(r["date"]),"📆":j,"🎱":t,"⭐":e})
        st.dataframe(pd.DataFrame(dern),hide_index=True,use_container_width=True)

        st.markdown("---")
        c1,c2=st.columns(2)
        with c1:
            st.subheader("🔥 Top 10 Chauds")
            ch=sorted(stats["boules"].values(),key=lambda x:x["indice_chaleur"],reverse=True)[:10]
            st.dataframe(pd.DataFrame(ch)[["numero","indice_chaleur","frequence_20t","ecart_actuel"]].rename(columns={"numero":"N°","indice_chaleur":"🌡️","frequence_20t":"F20","ecart_actuel":"Éc."}),hide_index=True,use_container_width=True)
        with c2:
            st.subheader("🧊 Top 10 Absents")
            fr=sorted(stats["boules"].values(),key=lambda x:x["ecart_actuel"],reverse=True)[:10]
            st.dataframe(pd.DataFrame(fr)[["numero","ecart_actuel","ecart_moyen","ecart_max","ratio_ecart_record"]].rename(columns={"numero":"N°","ecart_actuel":"Éc.","ecart_moyen":"Moy","ecart_max":"Record","ratio_ecart_record":"% Record"}),hide_index=True,use_container_width=True)

        st.subheader("💑 Paires fréquentes")
        pd_d=[{"Paire":f"{p[0][0]}—{p[0][1]}","Freq":p[1]}for p in stats["paires"][:10]]
        c1,c2=st.columns(2)
        with c1:st.dataframe(pd.DataFrame(pd_d[:5]),hide_index=True,use_container_width=True)
        with c2:st.dataframe(pd.DataFrame(pd_d[5:]),hide_index=True,use_container_width=True)

    # ════════════════════════════
    # GÉNÉRATEUR
    # ════════════════════════════
    elif page == "🎯 Générateur":
        st.markdown("<div class='main-header'>🎯 Générateur</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{badge}</div>",unsafe_allow_html=True)

        c1,c2=st.columns(2)
        with c1:
            mode=st.selectbox("🎯 Mode",["aleatoire","chaud","froid","top","hybride"],format_func=lambda x:{"aleatoire":"🎲 Aléatoire","chaud":"🔥 Chauds","froid":"🧊 Absents","top":"⭐ Top","hybride":"🧠 Hybride"}[x])
            fi=st.text_input("🔒 Forcés",placeholder="7, 14, 23")
            forces=[int(n.strip())for n in fi.split(",")if n.strip().isdigit()and 1<=int(n.strip())<=jeu["boules_max"]][:3]if fi else[]
            chasseur=st.slider("🎯 Écart min",0,30,0)
            plafond=st.selectbox("🔝 Plafond",["aucun","moins_40","force_40"],format_func=lambda x:{"aucun":"Aucun","moins_40":"< 40","force_40":"Forcer ≥40"}[x])
        with c2:
            fpa=st.checkbox("⚖️ Parité",True);fso=st.checkbox("➕ Somme",True)
            fdi=st.checkbox("📊 Dizaines",True);fan=st.checkbox("🚫 Anti-suite",True)
            eet=st.slider("⭐ Écart étoiles",0,8,2)if jeu["nb_etoiles"]else 0
            nbg=st.selectbox("Grilles",[1,3,5,10],index=1)

        if st.button("🎱 GÉNÉRER",type="primary",use_container_width=True):
            all_g=[]
            for gi in range(nbg):
                r=generer_grille(jeu_id,stats,mode,fpa,fso,fdi,fan,chasseur,forces,eet,plafond)
                all_g.append(r)
                st.markdown(f"#### Grille {gi+1}/{nbg}")
                st.markdown(afficher_grille_html(r["grille"],r["etoiles"],stats,jeu_id),unsafe_allow_html=True)
                afficher_score(r["score"])
                st.markdown("---")

            # Sauvegarder
            for r in all_g:
                st.session_state.grilles_generees.append({
                    "grille":r["grille"],"etoiles":r["etoiles"],
                    "score":r["score"]["total"],"mode":mode,
                    "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M")
                })

            # Mode buraliste
            st.subheader("📱 Mode Buraliste")
            for i,r in enumerate(all_g):
                gs=" — ".join(str(n)for n in r["grille"])
                es=f"  |  ⭐ {' — '.join(str(e)for e in r['etoiles'])}"if r["etoiles"]else""
                st.markdown(f"<div style='text-align:center;font-size:28px;font-weight:bold;padding:15px;background:#f8fafc;border-radius:12px;margin:8px 0;'>G{i+1}: {gs}{es}</div>",unsafe_allow_html=True)

            # 💾 EXPORT
            st.subheader("💾 Exporter les grilles")
            export_text = f"Smart-Loto — {jeu['nom']} — {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            export_text += f"Mode: {mode} | Filtres: Parité={fpa} Somme={fso} Dizaines={fdi} Anti-suite={fan}\n"
            export_text += "="*50 + "\n\n"
            for i,r in enumerate(all_g):
                gs=" - ".join(str(n)for n in r["grille"])
                es=f" | Étoiles: {' - '.join(str(e)for e in r['etoiles'])}"if r["etoiles"]else""
                export_text += f"Grille {i+1}: {gs}{es} (Score: {r['score']['total']}/100)\n"
            export_text += f"\n⚠️ Aucune garantie de gain. Joueurs Info Service: 09 74 75 13 13"

            st.download_button("📥 Télécharger (.txt)", export_text, f"smart-loto-grilles-{datetime.now().strftime('%Y%m%d')}.txt", "text/plain")

    # ════════════════════════════
    # STATISTIQUES
    # ════════════════════════════
    elif page == "📊 Statistiques":
        st.markdown("<div class='main-header'>📊 Statistiques</div>",unsafe_allow_html=True)

        st.subheader("🌡️ Carte de Chaleur")
        nc=10;nr=(jeu["boules_max"]+nc-1)//nc;zd=[];td=[]
        for row in range(nr):
            zr=[];tr=[]
            for col in range(nc):
                n=row*nc+col+1
                if n<=jeu["boules_max"]:s=stats["boules"][n];zr.append(s["indice_chaleur"]);tr.append(f"N°{n}<br>🌡️{s['indice_chaleur']}<br>Éc:{s['ecart_actuel']}")
                else:zr.append(None);tr.append("")
            zd.append(zr);td.append(tr)
        fh=go.Figure(data=go.Heatmap(z=zd,text=td,hoverinfo="text",colorscale=[[0,"#1e3a5f"],[.5,"#f59e0b"],[1,"#ef4444"]],showscale=True))
        for row in range(nr):
            for col in range(nc):
                n=row*nc+col+1
                if n<=jeu["boules_max"]:fh.add_annotation(x=col,y=row,text=str(n),showarrow=False,font=dict(color="white",size=14))
        fh.update_layout(height=350,margin=dict(l=20,r=20,t=20,b=20),xaxis=dict(showticklabels=False),yaxis=dict(showticklabels=False))
        st.plotly_chart(fh,use_container_width=True)

        # Analyse structurelle des tirages passés
        st.subheader("📊 Analyse Structurelle des Tirages Passés")
        if stats["analyses_tirages"]:
            at = stats["analyses_tirages"]

            c1,c2,c3 = st.columns(3)
            with c1:
                st.markdown("**Distribution Pairs/Impairs**")
                distrib_pi = Counter(f"{a['pairs']}P/{a['impairs']}I" for a in at)
                fig_pi = go.Figure(go.Bar(x=list(distrib_pi.keys()),y=list(distrib_pi.values()),
                    marker_color=["#3b82f6","#22c55e","#f59e0b","#ef4444","#8b5cf6","#ec4899"]))
                fig_pi.update_layout(height=250,title="Pairs/Impairs")
                st.plotly_chart(fig_pi,use_container_width=True)

            with c2:
                st.markdown("**Distribution Bas/Hauts (1-25 vs 26-50)**")
                distrib_bh = Counter(f"{a['bas']}B/{a['hauts']}H" for a in at)
                fig_bh = go.Figure(go.Bar(x=list(distrib_bh.keys()),y=list(distrib_bh.values()),
                    marker_color=["#3b82f6","#22c55e","#f59e0b","#ef4444","#8b5cf6","#ec4899"]))
                fig_bh.update_layout(height=250,title="Bas/Hauts")
                st.plotly_chart(fig_bh,use_container_width=True)

            with c3:
                st.markdown("**Distribution des Sommes**")
                sommes = [a["somme"] for a in at]
                fig_s = go.Figure(go.Histogram(x=sommes,nbinsx=30,marker_color="#3b82f6"))
                fig_s.add_vline(x=np.mean(sommes),line_dash="dash",line_color="#ef4444",
                    annotation_text=f"Moy: {np.mean(sommes):.0f}")
                fig_s.update_layout(height=250,title="Sommes des tirages")
                st.plotly_chart(fig_s,use_container_width=True)

        st.subheader("📋 Tableau complet")
        tri=st.selectbox("Tri",["🌡️","Écart","F20","F12m","% Record"])
        col_map = {"🌡️":"indice_chaleur","Écart":"ecart_actuel","F20":"frequence_20t","F12m":"frequence_12m","% Record":"ratio_ecart_record"}
        dfc=pd.DataFrame([{"N°":n,"🌡️":stats["boules"][n]["indice_chaleur"],"Écart":stats["boules"][n]["ecart_actuel"],
            "Moy":stats["boules"][n]["ecart_moyen"],"Max":stats["boules"][n]["ecart_max"],
            "F20":stats["boules"][n]["frequence_20t"],"F12m":stats["boules"][n]["frequence_12m"],
            "% Record":stats["boules"][n]["ratio_ecart_record"]}for n in range(1,jeu["boules_max"]+1)])
        st.dataframe(dfc.sort_values(col_map.get(tri,tri),ascending=(tri=="Écart"or tri=="% Record")),hide_index=True,use_container_width=True,height=500)

    # ════════════════════════════
    # 📅 ANALYSE PAR JOUR — NOUVEAU
    # ════════════════════════════
    elif page == "📅 Par Jour":
        st.markdown("<div class='main-header'>📅 Analyse par Jour</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Compare les statistiques selon le jour du tirage</div>",unsafe_allow_html=True)

        if "jour" in df.columns:
            jours_dispo = [j for j in df["jour"].unique() if j and j != "inconnu"]
            st.info(f"Jours disponibles : {', '.join(jours_dispo)}")

            if len(jours_dispo) >= 2:
                c1,c2 = st.columns(2)
                with c1:
                    jour1 = st.selectbox("Jour 1", jours_dispo, index=0)
                    stats_j1 = calculer_stats(df.to_json(), jeu_id, jour1)
                    st.subheader(f"🔥 Top 10 — {jour1.capitalize()}")
                    ch1=sorted(stats_j1["boules"].values(),key=lambda x:x["indice_chaleur"],reverse=True)[:10]
                    st.dataframe(pd.DataFrame(ch1)[["numero","indice_chaleur","frequence_20t","ecart_actuel"]].rename(columns={"numero":"N°","indice_chaleur":"🌡️","frequence_20t":"F20","ecart_actuel":"Éc."}),hide_index=True,use_container_width=True)

                with c2:
                    jour2 = st.selectbox("Jour 2", jours_dispo, index=min(1,len(jours_dispo)-1))
                    stats_j2 = calculer_stats(df.to_json(), jeu_id, jour2)
                    st.subheader(f"🔥 Top 10 — {jour2.capitalize()}")
                    ch2=sorted(stats_j2["boules"].values(),key=lambda x:x["indice_chaleur"],reverse=True)[:10]
                    st.dataframe(pd.DataFrame(ch2)[["numero","indice_chaleur","frequence_20t","ecart_actuel"]].rename(columns={"numero":"N°","indice_chaleur":"🌡️","frequence_20t":"F20","ecart_actuel":"Éc."}),hide_index=True,use_container_width=True)

                # Différences
                st.subheader(f"🔀 Numéros qui préfèrent le {jour1.capitalize()}")
                diffs = []
                for n in range(1,jeu["boules_max"]+1):
                    c1_val = stats_j1["boules"][n]["indice_chaleur"]
                    c2_val = stats_j2["boules"][n]["indice_chaleur"]
                    diffs.append({"N°":n, f"🌡️ {jour1}":c1_val, f"🌡️ {jour2}":c2_val, "Diff":round(c1_val-c2_val,1)})
                diffs.sort(key=lambda x:abs(x["Diff"]),reverse=True)
                st.dataframe(pd.DataFrame(diffs[:15]),hide_index=True,use_container_width=True)
            else:
                st.warning("Pas assez de jours différents dans les données")
        else:
            st.warning("Colonne 'jour' non disponible dans les données")

    # ════════════════════════════
    # 🔮 MES FÉTICHES — NOUVEAU
    # ════════════════════════════
    elif page == "🔮 Mes Fétiches":
        st.markdown("<div class='main-header'>🔮 Mes Numéros Fétiches</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Analyse détaillée de tes numéros préférés</div>",unsafe_allow_html=True)

        fetiches_input = st.text_input("🔢 Entre tes numéros fétiches", placeholder="7, 14, 23, 42")
        if fetiches_input:
            fetiches = [int(n.strip()) for n in fetiches_input.split(",") if n.strip().isdigit() and 1<=int(n.strip())<=jeu["boules_max"]]
            if fetiches:
                st.success(f"Analyse de : {fetiches}")

                for n in fetiches:
                    s = stats["boules"][n]
                    st.markdown(f"### 🎱 Numéro {n}")

                    c1,c2,c3,c4 = st.columns(4)
                    c1.metric("🌡️ Chaleur",f"{s['indice_chaleur']}/100")
                    c2.metric("📏 Écart actuel",s["ecart_actuel"],delta=f"Moy: {s['ecart_moyen']}")
                    c3.metric("📊 Freq 20t",s["frequence_20t"])
                    c4.metric("📅 Dernière sortie",s["derniere_sortie"])

                    # Jauge écart vs record
                    pct_record = s["ratio_ecart_record"]
                    if pct_record >= 90:
                        st.markdown(f"<div class='alert-card'>🚨 <b>ALERTE !</b> Le {n} est à <b>{pct_record}%</b> de son record d'absence ({s['ecart_max']} tirages) !</div>",unsafe_allow_html=True)
                    elif pct_record >= 70:
                        st.warning(f"⚠️ Le {n} est à {pct_record}% de son record d'absence")
                    else:
                        st.info(f"✅ Le {n} est à {pct_record}% de son record ({s['ecart_actuel']}/{s['ecart_max']})")

                    # Partenaires fréquents
                    partenaires = [(p[0][0] if p[0][1]==n else p[0][1], p[1]) for p in stats["paires"] if n in p[0]]
                    if partenaires:
                        st.markdown(f"**💑 Sort le plus souvent avec :** {', '.join(f'N°{p[0]} ({p[1]}x)' for p in partenaires[:5])}")

                    st.markdown("---")

                # Score global des fétiches
                moy_chaleur = np.mean([stats["boules"][n]["indice_chaleur"] for n in fetiches])
                st.subheader(f"📊 Score global de tes fétiches : {moy_chaleur:.1f}/100")
                if moy_chaleur >= 50:
                    st.markdown("<div class='success-card'>✅ Tes numéros sont globalement en forme !</div>",unsafe_allow_html=True)
                else:
                    st.markdown("<div class='alert-card'>🧊 Tes numéros sont plutôt froids en ce moment</div>",unsafe_allow_html=True)

    # ════════════════════════════
    # ✅ VÉRIFICATEUR — NOUVEAU
    # ════════════════════════════
    elif page == "✅ Vérificateur":
        st.markdown("<div class='main-header'>✅ Vérificateur de Grille</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Compare ta grille avec tous les tirages passés</div>",unsafe_allow_html=True)

        gi = st.text_input("🎱 Ta grille (5 numéros)", placeholder="7, 14, 23, 31, 42")
        if gi:
            grille = sorted(set(int(n.strip()) for n in gi.split(",") if n.strip().isdigit() and 1<=int(n.strip())<=jeu["boules_max"]))
            if len(grille) == 5:
                st.success(f"Vérification de : {grille}")
                cols_b = [f"boule_{i}" for i in range(1,6)]

                # Vérifier contre tous les tirages
                resultats = []
                for idx in range(len(df)):
                    row = df.iloc[idx]
                    tirage = set(int(row[c]) for c in cols_b)
                    communs = set(grille) & tirage
                    if len(communs) >= 2:
                        resultats.append({"date":str(row["date"]),"tirage":sorted(tirage),
                            "communs":sorted(communs),"nb":len(communs)})

                if resultats:
                    st.subheader(f"📋 {len(resultats)} tirages avec ≥ 2 numéros en commun")
                    # Stats
                    distrib = Counter(r["nb"] for r in resultats)
                    c1,c2,c3,c4=st.columns(4)
                    c1.metric("5/5 🎉",distrib.get(5,0))
                    c2.metric("4/5",distrib.get(4,0))
                    c3.metric("3/5",distrib.get(3,0))
                    c4.metric("2/5",distrib.get(2,0))

                    # Détail
                    best = sorted(resultats, key=lambda x:x["nb"], reverse=True)[:20]
                    for r in best:
                        emoji = "🎉" if r["nb"]>=4 else("🟢"if r["nb"]==3 else"🔵")
                        st.markdown(f"{emoji} **{r['date']}** — Tirage: `{r['tirage']}` — En commun: **`{r['communs']}`** ({r['nb']}/5)")
                else:
                    st.info("Aucun tirage avec 2+ numéros en commun")

                # Cette combinaison exacte est-elle déjà sortie ?
                grille_set = set(grille)
                deja_sortie = False
                for idx in range(len(df)):
                    row = df.iloc[idx]
                    tirage = set(int(row[c]) for c in cols_b)
                    if grille_set == tirage:
                        st.markdown(f"<div class='alert-card'>⚠️ Cette combinaison EXACTE est déjà sortie le **{row['date']}** !</div>",unsafe_allow_html=True)
                        deja_sortie = True; break
                if not deja_sortie:
                    st.markdown("<div class='success-card'>✅ Cette combinaison n'est jamais sortie (sur {stats['nb_tirages']} tirages)</div>",unsafe_allow_html=True)
            else:
                st.warning(f"Il faut exactement 5 numéros ({len(grille)} saisis)")

    # ════════════════════════════
    # 🚨 ALERTES ÉCART — NOUVEAU
    # ════════════════════════════
    elif page == "🚨 Alertes Écart":
        st.markdown("<div class='main-header'>🚨 Alertes Écart Record</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Numéros qui approchent ou dépassent leur record d'absence</div>",unsafe_allow_html=True)

        seuil = st.slider("Seuil d'alerte (% du record)",50,100,75)

        alertes = []
        for n in range(1,jeu["boules_max"]+1):
            s = stats["boules"][n]
            if s["ratio_ecart_record"] >= seuil:
                alertes.append(s)

        alertes.sort(key=lambda x:x["ratio_ecart_record"],reverse=True)

        if alertes:
            st.error(f"🚨 {len(alertes)} numéros en alerte (≥ {seuil}% de leur record)")
            for a in alertes:
                pct = a["ratio_ecart_record"]
                color = "#ef4444" if pct >= 90 else("#f59e0b" if pct >= 75 else "#3b82f6")
                bar_len = int(pct/100*20)
                bar = "🟥"*bar_len + "⬜"*(20-bar_len)
                st.markdown(f"**N°{a['numero']}** — Écart: **{a['ecart_actuel']}** / Record: **{a['ecart_max']}** ({pct}%)")
                st.markdown(f"{bar}")
                st.markdown("---")

            # Générer une grille avec ces numéros
            if st.button("🎯 Générer une grille avec ces numéros en alerte"):
                pool_alerte = [a["numero"] for a in alertes]
                if len(pool_alerte) >= 5:
                    choisis = sorted(random.sample(pool_alerte,5))
                else:
                    choisis = sorted(pool_alerte + random.sample([n for n in range(1,jeu["boules_max"]+1) if n not in pool_alerte], 5-len(pool_alerte)))
                et_al = sorted(random.sample(range(1,jeu["etoiles_max"]+1),2)) if jeu["etoiles_max"] else []
                sc_al = score_robustesse(choisis,et_al,stats,jeu_id)
                st.markdown(afficher_grille_html(choisis,et_al,stats,jeu_id),unsafe_allow_html=True)
                afficher_score(sc_al)
        else:
            st.success(f"✅ Aucun numéro n'est à ≥ {seuil}% de son record d'absence")

    # ════════════════════════════
    # 📈 ÉVOLUTION — NOUVEAU
    # ════════════════════════════
    elif page == "📈 Évolution":
        st.markdown("<div class='main-header'>📈 Évolution d'un Numéro</div>",unsafe_allow_html=True)

        num = st.number_input("Numéro à analyser",1,jeu["boules_max"],7)
        cols_b = [f"boule_{i}" for i in range(1,6)]

        # Calculer les sorties par mois
        sorties = []
        for _,row in df.iterrows():
            if num in [int(row[c]) for c in cols_b]:
                sorties.append(row["date"])

        if sorties:
            df_sorties = pd.DataFrame({"date":sorties})
            df_sorties["date"] = pd.to_datetime(df_sorties["date"])
            df_sorties["mois"] = df_sorties["date"].dt.to_period("M").astype(str)
            freq_mois = df_sorties.groupby("mois").size().reset_index(name="sorties")

            fig_evo = go.Figure(go.Bar(x=freq_mois["mois"],y=freq_mois["sorties"],marker_color="#3b82f6"))
            fig_evo.update_layout(height=400,title=f"Fréquence du N°{num} par mois",xaxis_title="Mois",yaxis_title="Sorties")
            st.plotly_chart(fig_evo,use_container_width=True)

            # Écarts successifs
            positions = []
            for idx,row in df.iterrows():
                if num in [int(row[c]) for c in cols_b]:
                    positions.append(idx)
            ecarts_successifs = [positions[i+1]-positions[i] for i in range(len(positions)-1)]

            if ecarts_successifs:
                fig_ec = go.Figure(go.Scatter(x=list(range(1,len(ecarts_successifs)+1)),y=ecarts_successifs,mode="lines+markers",marker_color="#f59e0b"))
                fig_ec.add_hline(y=np.mean(ecarts_successifs),line_dash="dash",line_color="#ef4444",annotation_text=f"Moy: {np.mean(ecarts_successifs):.1f}")
                fig_ec.update_layout(height=300,title=f"Écarts successifs du N°{num}",xaxis_title="Occurrence",yaxis_title="Écart")
                st.plotly_chart(fig_ec,use_container_width=True)

            s = stats["boules"][num]
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total sorties",s["frequence_totale"])
            c2.metric("Écart actuel",s["ecart_actuel"])
            c3.metric("Écart moyen",s["ecart_moyen"])
            c4.metric("Écart max",s["ecart_max"])
        else:
            st.warning(f"Le N°{num} n'est jamais sorti dans les données")

    # ════════════════════════════
    # 🆚 COMPARATEUR — NOUVEAU
    # ════════════════════════════
    elif page == "🆚 Comparateur":
        st.markdown("<div class='main-header'>🆚 Comparateur de Stratégies</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Compare les modes sur le même historique</div>",unsafe_allow_html=True)

        nbt = st.selectbox("Tirages à tester",[20,50,100],index=1)

        if st.button("🆚 COMPARER TOUTES LES STRATÉGIES",type="primary",use_container_width=True):
            with st.spinner("⏳ Comparaison en cours..."):
                resultats_comp = {}
                for m in ["aleatoire","chaud","froid","top","hybride"]:
                    rb = mini_backtest(df,jeu_id,stats,m,nbt)
                    resultats_comp[m] = rb

            # Tableau comparatif
            comp_data = []
            for m,rb in resultats_comp.items():
                emoji = {"aleatoire":"🎲","chaud":"🔥","froid":"🧊","top":"⭐","hybride":"🧠"}[m]
                comp_data.append({
                    "Stratégie":f"{emoji} {m.capitalize()}",
                    "Misé":f"{rb['total_mise']}€",
                    "Gagné":f"{rb['total_gains']}€",
                    "Bilan":f"{rb['bilan']:+.2f}€",
                    "3+ bons":sum(rb["resultats"][str(i)] for i in range(3,6)),
                    "4+ bons":sum(rb["resultats"][str(i)] for i in range(4,6)),
                    "5 bons":rb["resultats"]["5"]
                })
            st.dataframe(pd.DataFrame(comp_data),hide_index=True,use_container_width=True)

            # Graphique
            fig_comp = go.Figure()
            for m,rb in resultats_comp.items():
                emoji = {"aleatoire":"🎲","chaud":"🔥","froid":"🧊","top":"⭐","hybride":"🧠"}[m]
                fig_comp.add_trace(go.Bar(name=f"{emoji} {m}",x=["3 bons","4 bons","5 bons"],
                    y=[rb["resultats"]["3"],rb["resultats"]["4"],rb["resultats"]["5"]]))
            fig_comp.update_layout(barmode="group",height=400,title="Correspondances par stratégie")
            st.plotly_chart(fig_comp,use_container_width=True)

    # ════════════════════════════
    # BACKTESTING
    # ════════════════════════════
    elif page == "🧪 Backtesting":
        st.markdown("<div class='main-header'>🧪 Backtesting</div>",unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1:mbt=st.selectbox("Stratégie",["aleatoire","chaud","froid","top","hybride"],format_func=lambda x:{"aleatoire":"🎲","chaud":"🔥","froid":"🧊","top":"⭐","hybride":"🧠"}[x]+f" {x}")
        with c2:nbt=st.selectbox("Tirages",[20,50,100,200],index=1)
        if st.button("🚀 LANCER",type="primary",use_container_width=True):
            with st.spinner("⏳..."):rb=mini_backtest(df,jeu_id,stats,mbt,nbt)
            c1,c2,c3=st.columns(3);c1.metric("💰",f"{rb['total_mise']}€");c2.metric("🏆",f"{rb['total_gains']}€");c3.metric("📈",f"{rb['bilan']:+.2f}€")
            res=rb["resultats"]
            fb=go.Figure(go.Bar(x=[f"{k} bons"for k in sorted(res)],y=[res[k]for k in sorted(res)],marker_color=["#ef4444","#f97316","#f59e0b","#84cc16","#22c55e","#15803d"]))
            fb.update_layout(height=300);st.plotly_chart(fb,use_container_width=True)
            if rb["historique"]:
                for h in rb["historique"][:10]:st.markdown(f"📅 **{h['date']}** — `{h['grille']}` vs `{h['tirage']}` — **{h['bons']}** — {h['gain']}€")

    # ════════════════════════════
    # RÉDUCTEUR
    # ════════════════════════════
    elif page == "🧮 Réducteur":
        st.markdown("<div class='main-header'>🧮 Réducteur</div>",unsafe_allow_html=True)
        with st.expander("💡 Suggestions"):
            top=sorted(stats["boules"].values(),key=lambda x:x["indice_chaleur"],reverse=True)[:10]
            st.markdown(f"**Top:** `{', '.join(str(n['numero'])for n in top)}`")
        ni=st.text_input("🔢 Numéros (6-15)",placeholder="3, 7, 14, 19, 23, 28, 34, 41")
        if ni:
            nums=sorted(set(int(n.strip())for n in ni.split(",")if n.strip().isdigit()and 1<=int(n.strip())<=jeu["boules_max"]))
            if len(nums)>=6:
                st.success(f"✅ {len(nums)}: {nums}")
                if st.button("🧮 GÉNÉRER",type="primary",use_container_width=True):
                    grs=systeme_reducteur(nums)
                    st.info(f"💰 {len(grs)}×{jeu['prix']}€ = **{len(grs)*jeu['prix']:.2f}€**")
                    for i,g in enumerate(grs):
                        st.markdown(f"<div class='grille-container'><b>G{i+1}</b>&nbsp;&nbsp;{'&nbsp;&nbsp;'.join(f'<span class=\"boule\">{b}</span>' for b in g)}</div>",unsafe_allow_html=True)

    # ════════════════════════════
    # 🏆 HALL OF FAME — NOUVEAU
    # ════════════════════════════
    elif page == "🏆 Hall of Fame":
        st.markdown("<div class='main-header'>🏆 Hall of Fame</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Tes meilleures grilles générées cette session</div>",unsafe_allow_html=True)

        if st.session_state.grilles_generees:
            # Trier par score
            sorted_g = sorted(st.session_state.grilles_generees, key=lambda x:x["score"], reverse=True)

            st.metric("Total grilles générées",len(sorted_g))
            st.metric("Meilleur score",f"{sorted_g[0]['score']}/100")

            for i,g in enumerate(sorted_g[:20]):
                medal = "🥇" if i==0 else("🥈"if i==1 else("🥉"if i==2 else f"#{i+1}"))
                gs=" — ".join(str(n)for n in g["grille"])
                es=f" | ⭐{' — '.join(str(e)for e in g['etoiles'])}"if g["etoiles"]else""
                st.markdown(f"{medal} **{g['score']}/100** — `{gs}{es}` — {g['mode']} — {g['timestamp']}")

            # Export
            if st.button("📥 Exporter le Hall of Fame"):
                txt = "Smart-Loto — Hall of Fame\n" + "="*50 + "\n\n"
                for i,g in enumerate(sorted_g):
                    gs=" - ".join(str(n)for n in g["grille"])
                    es=f" | ⭐{' - '.join(str(e)for e in g['etoiles'])}"if g["etoiles"]else""
                    txt+=f"#{i+1} — Score:{g['score']} — {gs}{es} — {g['mode']} — {g['timestamp']}\n"
                st.download_button("📥 Télécharger",txt,"hall-of-fame.txt")

            if st.button("🗑️ Réinitialiser"):
                st.session_state.grilles_generees = []
                st.rerun()
        else:
            st.info("Aucune grille générée. Va dans 🎯 Générateur pour commencer !")

    # ════════════════════════════
    # DEBUG CSV
    # ════════════════════════════
    elif page == "🔍 Debug CSV":
        st.markdown("<div class='main-header'>🔍 Debug</div>",unsafe_allow_html=True)
        if debug:
            if debug.get("succes"):
                st.success(f"✅ {debug.get('nb_tirages','?')} tirages")
                if "exemple" in debug:st.info(f"Dernier: {debug['exemple']}")
                if "jours_disponibles" in debug:st.info(f"Jours: {debug['jours_disponibles']}")
            else:st.error(debug.get("erreur","Erreur"))
            for k,v in debug.items():
                if k.startswith("sep_"):st.markdown(f"Séparateur `{k}` → **{v}**")
            if "colonnes" in debug:
                st.subheader("Colonnes")
                for i,c in enumerate(debug["colonnes"][:20]):st.markdown(f"`{i}` → **{c}**")
            if "mapping" in debug:
                m=debug["mapping"];st.success(f"📅{m['date']} 🎱{m['boules']} ⭐{m['etoiles']}")
        st.dataframe(df.head(10),use_container_width=True)

    # ════════════════════════════
    # À PROPOS
    # ════════════════════════════
    elif page == "ℹ️ À propos":
        st.markdown("<div class='main-header'>ℹ️ V3.0</div>",unsafe_allow_html=True)
        st.markdown(f"""
## Nouveautés V3.0

| Module | Description |
|---|---|
| 📅 **Par Jour** | Compare les stats Mardi vs Vendredi |
| 🔮 **Mes Fétiches** | Analyse détaillée de tes numéros |
| ✅ **Vérificateur** | Compare ta grille vs historique |
| 🚨 **Alertes Écart** | Numéros proches de leur record |
| 📈 **Évolution** | Graphique temporel par numéro |
| 🆚 **Comparateur** | Compare 5 stratégies en 1 clic |
| 💾 **Export** | Télécharge tes grilles |
| 📊 **Analyse Structurelle** | Pairs/Impairs, Bas/Hauts, Sommes |
| 🏆 **Hall of Fame** | Tes meilleures grilles de la session |
| 🎨 **Boules colorées** | Rouge=chaud, Bleu=normal, Gris=froid |

{badge} | {stats['nb_tirages']} tirages

⚠️ Aucune garantie de gain | 🛡️ 09 74 75 13 13
        """)

    st.markdown("<div class='footer-disclaimer'>⚠️ Outil d'analyse — Aucune garantie de gain — 🛡️ <a href='https://www.joueurs-info-service.fr/'>Joueurs Info Service</a> 09 74 75 13 13</div>",unsafe_allow_html=True)

if __name__=="__main__":
    main()
