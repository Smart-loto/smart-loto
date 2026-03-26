# ============================================================
# SMART-LOTO — V4.0 — ANALYSE DATA AVANCÉE
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import random
from collections import Counter
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import io, re, math

st.set_page_config(page_title="Smart-Loto V4", page_icon="🎱", layout="wide", initial_sidebar_state="expanded")

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
    .insight-card {background:linear-gradient(135deg,#eff6ff,#dbeafe);border:2px solid #3b82f6;border-radius:16px;padding:20px;margin:10px 0;}
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom":"Euromillions","emoji":"⭐","boules_max":50,"nb_boules":5,"etoiles_max":12,"nb_etoiles":2,"prix":2.50,"somme_min":90,"somme_max":160},
    "loto": {"nom":"Loto","emoji":"🎱","boules_max":49,"nb_boules":5,"etoiles_max":None,"nb_etoiles":0,"prix":2.20,"somme_min":60,"somme_max":180}
}

# ============================================================
# CHARGEMENT CSV (identique V3)
# ============================================================

def detecter_et_charger_csv(uploaded_file, jeu_id):
    jeu=JEUX[jeu_id];debug={}
    content=uploaded_file.read();uploaded_file.seek(0)
    text=None
    for enc in ["utf-8-sig","utf-8","latin-1","cp1252"]:
        try:text=content.decode(enc);debug["encodage"]=enc;break
        except:continue
    if not text:return None,{"erreur":"Décodage impossible"}
    text=text.lstrip("\ufeff")
    df=None;sep_final=None
    for s in [";",",","\t"]:
        try:
            dft=pd.read_csv(io.StringIO(text),sep=s,engine="python")
            dft=dft.loc[:,~dft.columns.str.match(r'^Unnamed')]
            dft.columns=[c.strip()for c in dft.columns]
            if len(dft.columns)>=7 and(df is None or len(dft.columns)>len(df.columns)):df=dft;sep_final=s
        except:pass
    if df is None or len(df.columns)<7:return None,{**debug,"erreur":"Colonnes insuffisantes"}
    debug["colonnes"]=list(df.columns);cl={c.upper():c for c in df.columns}
    date_col=None
    for c in["DATE","date","DATE_DE_TIRAGE"]:
        if c in df.columns:date_col=c;break
        if c.upper()in cl:date_col=cl[c.upper()];break
    if not date_col:
        for c in df.columns:
            if"date"in c.lower():date_col=c;break
    if not date_col:return None,{**debug,"erreur":"Date introuvable"}
    bcols=[]
    for i in range(1,6):
        for c in[f"N{i}",f"n{i}",f"BOULE_{i}",f"boule_{i}"]:
            if c in df.columns:bcols.append(c);break
            elif c.upper()in cl:bcols.append(cl[c.upper()]);break
    if len(bcols)<5:
        bcols=[]
        for c in df.columns:
            if c==date_col:continue
            try:
                v=pd.to_numeric(df[c],errors="coerce").dropna()
                if len(v)>len(df)*.3 and v.min()>=1 and v.max()<=jeu["boules_max"]:bcols.append(c)
                if len(bcols)>=5:break
            except:continue
    if len(bcols)<5:return None,{**debug,"erreur":f"{len(bcols)} boules"}
    ecols=[]
    if jeu["nb_etoiles"]>0:
        for i in range(1,3):
            for c in[f"E{i}",f"e{i}",f"ETOILE_{i}",f"etoile_{i}"]:
                if c in df.columns:ecols.append(c);break
                elif c.upper()in cl:ecols.append(cl[c.upper()]);break
    result=pd.DataFrame()
    for fmt in[None,"%d/%m/%Y","%Y-%m-%d"]:
        try:
            result["date"]=pd.to_datetime(df[date_col],format=fmt,dayfirst=True,errors="coerce").dt.date if fmt is None else pd.to_datetime(df[date_col],format=fmt,errors="coerce").dt.date
            if result["date"].notna().sum()>len(df)*.5:break
        except:continue
    for i,c in enumerate(bcols[:5],1):result[f"boule_{i}"]=pd.to_numeric(df[c],errors="coerce")
    for i,c in enumerate(ecols[:2],1):result[f"etoile_{i}"]=pd.to_numeric(df[c],errors="coerce")
    try:
        result["jour"]=pd.to_datetime(result["date"]).dt.day_name()
        jm={"Monday":"lundi","Tuesday":"mardi","Wednesday":"mercredi","Thursday":"jeudi","Friday":"vendredi","Saturday":"samedi","Sunday":"dimanche"}
        result["jour"]=result["jour"].map(lambda x:jm.get(x,x))
    except:result["jour"]="?"
    result=result.dropna(subset=["date","boule_1","boule_2","boule_3","boule_4","boule_5"])
    for i in range(1,6):result[f"boule_{i}"]=result[f"boule_{i}"].astype(int)
    for i in range(1,3):
        if f"etoile_{i}"in result.columns:result[f"etoile_{i}"]=result[f"etoile_{i}"].fillna(0).astype(int)
    for i in range(1,6):result=result[(result[f"boule_{i}"]>=1)&(result[f"boule_{i}"]<=jeu["boules_max"])]
    result=result.sort_values("date",ascending=False).drop_duplicates("date").reset_index(drop=True)
    debug["succes"]=len(result)>0;debug["nb_tirages"]=len(result)
    debug["mapping"]={"date":date_col,"boules":bcols[:5],"etoiles":ecols[:2]}
    if len(result)>0:
        debug["exemple"]={"date":str(result.iloc[0]["date"]),"boules":[int(result.iloc[0][f"boule_{i}"])for i in range(1,6)]}
    return result,debug

def generer_historique_simule(jeu_id,nb=500):
    random.seed(42);np.random.seed(42);jeu=JEUX[jeu_id];t=[];now=datetime.now()
    js=["mardi","vendredi"]if jeu_id=="euromillions"else["lundi","mercredi","samedi"]
    for i in range(nb):
        b=sorted(random.sample(range(1,jeu["boules_max"]+1),5))
        e=sorted(random.sample(range(1,jeu["etoiles_max"]+1),2))if jeu["etoiles_max"]else[]
        d={"date":(now-timedelta(days=i*3.5)).date(),"boule_1":b[0],"boule_2":b[1],"boule_3":b[2],"boule_4":b[3],"boule_5":b[4],"jour":js[i%len(js)]}
        if e:d["etoile_1"]=e[0];d["etoile_2"]=e[1]
        t.append(d)
    return pd.DataFrame(t).sort_values("date",ascending=False).reset_index(drop=True)


# ============================================================
# MOTEUR STATISTIQUE AVANCÉ — V4
# ============================================================

@st.cache_data
def calculer_stats_v4(df_json, jeu_id, jour_filtre=None):
    df=pd.read_json(io.StringIO(df_json));df["date"]=pd.to_datetime(df["date"]).dt.date
    if jour_filtre and jour_filtre!="tous"and"jour"in df.columns:
        df=df[df["jour"].str.lower()==jour_filtre.lower()].reset_index(drop=True)
    jeu=JEUX[jeu_id];stats={};cols=[f"boule_{i}"for i in range(1,6)]

    all_n=[]
    for c in cols:all_n.extend(df[c].tolist())
    df20=df.head(20);n20=[]
    for c in cols:n20.extend(df20[c].tolist())
    d12m=datetime.now().date()-timedelta(days=365);df12=df[df["date"]>=d12m];n12=[]
    for c in cols:n12.extend(df12[c].tolist())
    d3m=datetime.now().date()-timedelta(days=90);df3=df[df["date"]>=d3m];n3=[]
    for c in cols:n3.extend(df3[c].tolist())
    fa,f20,f12,f3=Counter(all_n),Counter(n20),Counter(n12),Counter(n3)

    for n in range(1,jeu["boules_max"]+1):
        ec=0
        for _,r in df.iterrows():
            if n in[int(r[c])for c in cols]:break
            ec+=1
        pos=[idx for idx,r in df.iterrows()if n in[int(r[c])for c in cols]]
        ech=[pos[i+1]-pos[i]for i in range(len(pos)-1)]if len(pos)>1 else[]
        em=np.mean(ech)if ech else 10;ex=max(ech)if ech else ec
        es=np.std(ech)if len(ech)>1 else 5
        dern=None
        for _,r in df.iterrows():
            if n in[int(r[c])for c in cols]:dern=r["date"];break

        fo=(f20.get(n,0)/max(len(df20),1))*100
        ft=(len(df12)*5)/jeu["boules_max"]
        fn=(f12.get(n,0)/max(ft,1))*50
        ep=max(0,30-(ec*2))
        ch=min(100,max(0,.40*fo+.35*fn+.25*ep))
        ratio_record=(ec/ex*100)if ex>0 else 0

        # NOUVEAU : Probabilité de sortie basée sur l'écart
        # P(sortir) augmente si l'écart dépasse la moyenne
        if em > 0:
            z_ecart = (ec - em) / max(es, 1)
            # Probabilité cumulative (distribution normale simplifiée)
            proba_sortie = min(99, max(1, 50 + z_ecart * 15))
        else:
            proba_sortie = 50

        # NOUVEAU : Tendance (hausse/baisse sur 3 périodes)
        f_periode1 = f3.get(n, 0)  # 3 mois
        f_periode2 = f12.get(n, 0) - f3.get(n, 0)  # 3-12 mois
        nb_tirages_3m = len(df3)
        nb_tirages_3_12m = len(df12) - len(df3)
        taux_1 = f_periode1 / max(nb_tirages_3m, 1) * 100
        taux_2 = f_periode2 / max(nb_tirages_3_12m, 1) * 100
        if taux_1 > taux_2 * 1.3:
            tendance = "↗️ Hausse"
        elif taux_1 < taux_2 * 0.7:
            tendance = "↘️ Baisse"
        else:
            tendance = "→ Stable"

        stats[n]={"numero":n,"ecart_actuel":ec,"ecart_moyen":round(em,1),"ecart_max":ex,
            "ecart_std":round(es,1),
            "frequence_totale":fa.get(n,0),"frequence_20t":f20.get(n,0),
            "frequence_12m":f12.get(n,0),"frequence_3m":f3.get(n,0),
            "indice_chaleur":round(ch,1),"derniere_sortie":str(dern)if dern else"—",
            "ratio_ecart_record":round(ratio_record,1),
            "proba_sortie":round(proba_sortie,1),
            "tendance":tendance,
            "terminaison":n%10,
            "dizaine":(n-1)//10}

    # Étoiles
    se={}
    if jeu["nb_etoiles"]and"etoile_1"in df.columns:
        ce=[f"etoile_{i}"for i in range(1,jeu["nb_etoiles"]+1)]
        ae=[];e20=[]
        for c in ce:
            if c in df.columns:ae.extend(df[c].tolist());e20.extend(df20[c].tolist())
        fe,fe20=Counter(ae),Counter(e20)
        for n in range(1,jeu["etoiles_max"]+1):
            ec=0
            for _,r in df.iterrows():
                if n in[int(r[c])for c in ce if c in df.columns]:break
                ec+=1
            se[n]={"numero":n,"ecart_actuel":ec,"frequence_totale":fe.get(n,0),"frequence_20t":fe20.get(n,0)}

    # Paires
    paires=Counter()
    for _,r in df.iterrows():
        bs=sorted([int(r[c])for c in cols])
        for i in range(len(bs)):
            for j in range(i+1,len(bs)):paires[(bs[i],bs[j])]+=1

    # NOUVEAU : Matrice d'affinité complète
    affinite_matrix = {}
    nb_tirages_total = len(df)
    for n1 in range(1, jeu["boules_max"]+1):
        affinite_matrix[n1] = {}
        for n2 in range(n1+1, jeu["boules_max"]+1):
            count = paires.get((n1,n2), 0)
            # Fréquence attendue si indépendants
            f1 = fa.get(n1,0) / max(nb_tirages_total,1)
            f2 = fa.get(n2,0) / max(nb_tirages_total,1)
            expected = f1 * f2 * nb_tirages_total * 10  # Approximation
            ratio = count / max(expected, 0.1)
            affinite_matrix[n1][n2] = {"count":count, "ratio":round(ratio,2)}

    # NOUVEAU : Analyse des terminaisons
    terminaisons = Counter(n % 10 for n in all_n)
    terminaisons_20 = Counter(n % 10 for n in n20)

    # NOUVEAU : Analyse des dizaines
    dizaines = Counter((n-1)//10 for n in all_n)
    dizaines_20 = Counter((n-1)//10 for n in n20)

    # NOUVEAU : Analyse structurelle
    analyses = []
    for _,r in df.iterrows():
        bs=[int(r[c])for c in cols]
        nb_pairs=sum(1 for b in bs if b%2==0)
        nb_bas=sum(1 for b in bs if b<=25)
        nb_consecutifs=0
        bss=sorted(bs)
        for i in range(len(bss)-1):
            if bss[i+1]==bss[i]+1:nb_consecutifs+=1
        somme=sum(bs)
        terminaisons_grille=len(set(b%10 for b in bs))
        dizaines_grille=len(set((b-1)//10 for b in bs))
        analyses.append({"pairs":nb_pairs,"bas":nb_bas,"somme":somme,
            "consecutifs":nb_consecutifs,"terminaisons_diff":terminaisons_grille,
            "dizaines_diff":dizaines_grille})

    # NOUVEAU : Profil optimal basé sur les tirages réels
    sommes = [a["somme"] for a in analyses]
    profil_optimal = {
        "somme_moyenne": round(np.mean(sommes),1),
        "somme_mediane": round(np.median(sommes),1),
        "somme_q1": round(np.percentile(sommes,25),1),
        "somme_q3": round(np.percentile(sommes,75),1),
        "pairs_moyen": round(np.mean([a["pairs"] for a in analyses]),1),
        "bas_moyen": round(np.mean([a["bas"] for a in analyses]),1),
        "consecutifs_pct": round(sum(1 for a in analyses if a["consecutifs"]>0)/max(len(analyses),1)*100,1),
        "terminaisons_moy": round(np.mean([a["terminaisons_diff"] for a in analyses]),1),
        "dizaines_moy": round(np.mean([a["dizaines_diff"] for a in analyses]),1),
    }

    return {"boules":stats,"etoiles":se,"paires":paires.most_common(30),
        "affinite":affinite_matrix,
        "terminaisons":dict(terminaisons),"terminaisons_20":dict(terminaisons_20),
        "dizaines":dict(dizaines),"dizaines_20":dict(dizaines_20),
        "analyses":analyses,"profil_optimal":profil_optimal,
        "nb_tirages":len(df),
        "date_premier":str(df.iloc[-1]["date"])if len(df)>0 else"—",
        "date_dernier":str(df.iloc[0]["date"])if len(df)>0 else"—"}


# ============================================================
# SCORE DE ROBUSTESSE V4 — 10 CRITÈRES
# ============================================================

def score_robustesse_v4(gr, et, stats, jid):
    jeu = JEUX[jid]; sc = {}; po = stats.get("profil_optimal", {})

    # 1. Parité (15 pts)
    np2 = sum(1 for n in gr if n%2==0); r = np2/len(gr)
    ideal_pairs = po.get("pairs_moyen", 2.5)
    diff_pairs = abs(np2 - ideal_pairs)
    sc["⚖️ Parité"] = 15 if diff_pairs <= 0.5 else (10 if diff_pairs <= 1.5 else 5)

    # 2. Dizaines (12 pts)
    dz = Counter((n-1)//10 for n in gr)
    ideal_diz = po.get("dizaines_moy", 4)
    sc["📊 Dizaines"] = 12 if len(dz) >= round(ideal_diz) else (8 if len(dz) >= round(ideal_diz)-1 else 4)

    # 3. Somme (15 pts)
    s = sum(gr)
    q1 = po.get("somme_q1", jeu["somme_min"])
    q3 = po.get("somme_q3", jeu["somme_max"])
    moy = po.get("somme_moyenne", (jeu["somme_min"]+jeu["somme_max"])/2)
    if q1 <= s <= q3:
        sc["➕ Somme"] = 15
    elif jeu["somme_min"] <= s <= jeu["somme_max"]:
        sc["➕ Somme"] = 10
    else:
        sc["➕ Somme"] = 3

    # 4. Diversité écarts (10 pts)
    ecs = [stats["boules"][n]["ecart_actuel"] for n in gr if n in stats["boules"]]
    if len(set(ecs)) > 1:
        std = float(np.std(ecs))
        sc["🔀 Diversité Éc."] = 10 if std > 5 else (7 if std > 3 else 4)
    else:
        sc["🔀 Diversité Éc."] = 4

    # 5. Anti-suite (8 pts)
    g = sorted(gr)
    hs = any(g[i+1]==g[i]+1 and g[i+2]==g[i]+2 for i in range(len(g)-2))
    sc["🚫 Anti-suite"] = 2 if hs else 8

    # 6. Étoiles (8 pts)
    if et and len(et)==2:
        ec=abs(et[0]-et[1])
        sc["⭐ Étoiles"]=8 if ec>=3 else(5 if ec>=2 else 2)
    else:
        sc["⭐ Étoiles"]=8

    # 7. NOUVEAU : Terminaisons diversifiées (8 pts)
    terms = set(n%10 for n in gr)
    ideal_terms = po.get("terminaisons_moy", 4.2)
    sc["🔢 Terminaisons"] = 8 if len(terms) >= round(ideal_terms) else (5 if len(terms) >= round(ideal_terms)-1 else 2)

    # 8. NOUVEAU : Bas/Hauts équilibrés (8 pts)
    nb_bas = sum(1 for n in gr if n <= jeu["boules_max"]//2)
    ideal_bas = po.get("bas_moyen", 2.5)
    diff_bas = abs(nb_bas - ideal_bas)
    sc["⬆️⬇️ Bas/Hauts"] = 8 if diff_bas <= 0.5 else (5 if diff_bas <= 1.5 else 2)

    # 9. NOUVEAU : Chaleur moyenne (8 pts)
    chaleurs = [stats["boules"][n]["indice_chaleur"] for n in gr if n in stats["boules"]]
    moy_ch = np.mean(chaleurs) if chaleurs else 50
    sc["🌡️ Chaleur moy."] = 8 if 35 <= moy_ch <= 65 else (5 if 20 <= moy_ch <= 80 else 2)

    # 10. NOUVEAU : Probabilité composite (8 pts)
    probas = [stats["boules"][n]["proba_sortie"] for n in gr if n in stats["boules"]]
    moy_proba = np.mean(probas) if probas else 50
    sc["📊 Proba moy."] = 8 if moy_proba >= 55 else (5 if moy_proba >= 45 else 2)

    total = sum(sc.values())
    return {"total": total, "detail": sc, "max": 100}


# ============================================================
# GÉNÉRATEUR V4 — MULTI-CRITÈRES
# ============================================================

def generer_grille_v4(jid, stats, mode="aleatoire", fp=False, fs=False, fd=False, fa=False,
                      chasseur=0, forces=None, ee=0, plafond="aucun",
                      f_terminaisons=False, f_anti_corr=False, f_bas_hauts=False,
                      poids_chaleur=50, poids_ecart=50, poids_proba=50,
                      mt=2000):
    jeu = JEUX[jid]

    for t in range(mt):
        # ── Pool de départ selon mode ──
        if mode == "optimal":
            # NOUVEAU : Mode Optimal Pondéré
            ns = list(stats["boules"].keys())
            scores_composite = []
            for n in ns:
                s = stats["boules"][n]
                sc = (
                    (poids_chaleur/100) * s["indice_chaleur"] +
                    (poids_ecart/100) * min(100, s["ecart_actuel"] * 8) +
                    (poids_proba/100) * s["proba_sortie"]
                ) / 3
                scores_composite.append(sc ** 1.5 + 1)
            tp = sum(scores_composite)
            pool = list(np.random.choice(ns, size=min(25,len(ns)), replace=False,
                p=[s/tp for s in scores_composite]))

        elif mode == "contrarian":
            # NOUVEAU : Mode Contrarian (numéros impopulaires)
            pool = sorted(stats["boules"], key=lambda x: stats["boules"][x]["frequence_totale"])[:20]

        elif mode == "probabiliste":
            # NOUVEAU : Mode basé sur la probabilité de sortie
            pool = sorted(stats["boules"], key=lambda x: stats["boules"][x]["proba_sortie"], reverse=True)[:20]

        elif mode == "tendance":
            # NOUVEAU : Mode Tendance (numéros en hausse)
            pool = [n for n in stats["boules"] if stats["boules"][n]["tendance"] == "↗️ Hausse"]
            if len(pool) < 10:
                pool += sorted(stats["boules"], key=lambda x: stats["boules"][x]["indice_chaleur"], reverse=True)[:20]
            pool = pool[:25]

        elif mode == "chaud": pool = sorted(stats["boules"], key=lambda x: stats["boules"][x]["indice_chaleur"], reverse=True)[:20]
        elif mode == "froid": pool = sorted(stats["boules"], key=lambda x: stats["boules"][x]["ecart_actuel"], reverse=True)[:20]
        elif mode == "top": pool = sorted(stats["boules"], key=lambda x: stats["boules"][x]["frequence_12m"], reverse=True)[:15]
        elif mode == "hybride":
            ns=list(stats["boules"].keys());pw=[stats["boules"][n]["indice_chaleur"]**1.5+5 for n in ns]
            tp=sum(pw);pool=list(np.random.choice(ns,size=min(25,len(ns)),replace=False,p=[p/tp for p in pw]))
        else: pool = list(range(1, jeu["boules_max"]+1))

        # ── Filtres de pool ──
        if plafond == "moins_40": pool = [n for n in pool if n < 40]
        if chasseur > 0:
            pf = [n for n in pool if stats["boules"][n]["ecart_actuel"] >= chasseur]
            if len(pf) >= 5: pool = pf

        # ── Construction grille ──
        fo = [f for f in (forces or []) if 1 <= f <= jeu["boules_max"]]
        di = [n for n in pool if n not in fo]; mq = 5 - len(fo)
        if mq > len(di): di = [n for n in range(1, jeu["boules_max"]+1) if n not in fo]
        ch = random.sample(di, min(mq, len(di))) if mq > 0 else []
        gr = sorted(fo + ch)[:5]

        if plafond == "force_40" and not any(n >= 40 for n in gr):
            s40 = [n for n in range(40, jeu["boules_max"]+1) if n not in gr]
            nf = [n for n in gr if n not in fo]
            if s40 and nf:
                rm = min(nf, key=lambda x: stats["boules"][x]["indice_chaleur"])
                gr.remove(rm); gr.append(random.choice(s40)); gr = sorted(gr)

        # Étoiles
        et = []
        if jeu["nb_etoiles"] and jeu["etoiles_max"]:
            for _ in range(100):
                et = sorted(random.sample(range(1, jeu["etoiles_max"]+1), jeu["nb_etoiles"]))
                if ee > 0 and len(et) == 2 and abs(et[0]-et[1]) >= ee: break
                elif ee == 0: break

        # ── Validations ──
        v = True
        if fp:
            np2 = sum(1 for n in gr if n%2==0)
            v = v and 0 < np2 < 5
        if fs:
            v = v and jeu["somme_min"] <= sum(gr) <= jeu["somme_max"]
        if fd:
            v = v and max(Counter((n-1)//10 for n in gr).values()) <= 3
        if fa:
            gs = sorted(gr)
            v = v and not any(gs[i+1]==gs[i]+1 and gs[i+2]==gs[i]+2 for i in range(len(gs)-2))

        # NOUVEAU : Filtre terminaisons diversifiées
        if f_terminaisons:
            terms = set(n%10 for n in gr)
            v = v and len(terms) >= 4  # Au moins 4 terminaisons différentes

        # NOUVEAU : Filtre bas/hauts équilibrés
        if f_bas_hauts:
            nb_bas = sum(1 for n in gr if n <= jeu["boules_max"]//2)
            v = v and 1 <= nb_bas <= 4  # Ni tout bas ni tout haut

        # NOUVEAU : Filtre anti-corrélation
        if f_anti_corr and "affinite" in stats:
            af = stats["affinite"]
            all_ok = True
            for i in range(len(gr)):
                for j in range(i+1, len(gr)):
                    a, b = min(gr[i],gr[j]), max(gr[i],gr[j])
                    if a in af and b in af[a]:
                        if af[a][b]["count"] == 0:
                            all_ok = False; break
                if not all_ok: break
            v = v and all_ok

        if v:
            score = score_robustesse_v4(gr, et, stats, jid)
            return {"grille":gr, "etoiles":et, "score":score, "tentatives":t+1, "mode":mode}

    # Fallback
    gr = sorted(random.sample(range(1,jeu["boules_max"]+1),5))
    et = sorted(random.sample(range(1,jeu["etoiles_max"]+1),2)) if jeu["etoiles_max"] else []
    return {"grille":gr,"etoiles":et,"score":score_robustesse_v4(gr,et,stats,jid),"tentatives":mt,"mode":"fallback"}


# ── Autres fonctions utilitaires ──

def mini_backtest(df,jid,stats,mode,nt=50,gpt=1):
    jeu=JEUX[jid];cols=[f"boule_{i}"for i in range(1,6)]
    res={str(i):0 for i in range(6)};tm=0;tg=0;gt={0:0,1:0,2:0,3:4,4:50,5:5000};hist=[]
    for idx in range(min(nt,len(df))):
        row=df.iloc[idx];bt=set(int(row[c])for c in cols)
        for _ in range(gpt):
            r=generer_grille_v4(jid,stats,mode=mode);nb=len(set(r["grille"])&bt)
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

def afficher_grille_html(gr, et, stats, jid):
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

def afficher_score_v4(sc):
    ev="⭐⭐⭐⭐⭐"if sc["total"]>=85 else("⭐⭐⭐⭐"if sc["total"]>=70 else("⭐⭐⭐"if sc["total"]>=55 else("⭐⭐"if sc["total"]>=40 else"⭐")))
    sc_c="#22c55e"if sc["total"]>=70 else("#f59e0b"if sc["total"]>=50 else"#ef4444")
    cs1,cs2=st.columns([1,2])
    with cs1:
        st.markdown(f"<div style='text-align:center;'><div style='font-size:3rem;font-weight:800;color:{sc_c};'>{sc['total']}</div><div style='color:#64748b;'>/ {sc['max']} {ev}</div></div>",unsafe_allow_html=True)
    with cs2:
        mx_map={"⚖️ Parité":15,"📊 Dizaines":12,"➕ Somme":15,"🔀 Diversité Éc.":10,"🚫 Anti-suite":8,"⭐ Étoiles":8,"🔢 Terminaisons":8,"⬆️⬇️ Bas/Hauts":8,"🌡️ Chaleur moy.":8,"📊 Proba moy.":8}
        for cr,pt in sc["detail"].items():
            m=mx_map.get(cr,8);pct=pt/m if m else 0
            cl="#22c55e"if pct>=.7 else("#f59e0b"if pct>=.4 else"#ef4444")
            bar="█"*int(pct*10)+"░"*(10-int(pct*10))
            st.markdown(f"<span style='font-size:0.85rem;'>`{cr}` <span style='color:{cl};font-family:monospace;'>{bar}</span> **{pt}/{m}**</span>",unsafe_allow_html=True)


# ============================================================
# INTERFACE V4
# ============================================================

def main():
    st.sidebar.markdown("<div style='text-align:center;'><h1 style='font-size:2rem;'>🎱 Smart-Loto</h1><p style='color:#64748b;'>V4.0 — Data Avancée</p></div>",unsafe_allow_html=True)
    st.sidebar.markdown("---")
    jeu_id=st.sidebar.selectbox("🎮 Jeu",["euromillions","loto"],format_func=lambda x:f"{JEUX[x]['emoji']} {JEUX[x]['nom']}")
    jeu=JEUX[jeu_id]
    st.sidebar.markdown("---")
    uploaded=st.sidebar.file_uploader(f"📤 CSV {jeu['nom']}",type=["csv","txt"])
    donnees_reelles=False;debug={}
    if uploaded:
        df,debug=detecter_et_charger_csv(uploaded,jeu_id)
        if df is not None and len(df)>0:donnees_reelles=True;st.sidebar.success(f"✅ {len(df)} tirages")
        else:st.sidebar.error("❌ Erreur");df=generer_historique_simule(jeu_id)
    else:df=generer_historique_simule(jeu_id);st.sidebar.info("💡 Importe CSV")

    if"grilles_gen"not in st.session_state:st.session_state.grilles_gen=[]

    st.sidebar.markdown("---")
    page=st.sidebar.radio("📑 Menu",[
        "🏠 Dashboard","🎯 Générateur Pro","📊 Stats Avancées",
        "🔬 Matrice Affinité","📐 Terminaisons & Dizaines","📈 Scatter Analyse",
        "🚨 Alertes & Probas","🆚 Comparateur","🧪 Backtesting",
        "🧮 Réducteur","🏆 Hall of Fame","🔍 Debug","ℹ️ À propos"])
    st.sidebar.caption("⚠️ Aucune garantie de gain\n🛡️ 09 74 75 13 13")

    stats=calculer_stats_v4(df.to_json(),jeu_id)
    badge="🟢 Réelles"if donnees_reelles else"🟡 Simulées"

    # ════════════════════════════
    # DASHBOARD
    # ════════════════════════════
    if page=="🏠 Dashboard":
        st.markdown("<div class='main-header'>🏠 Dashboard</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{jeu['nom']} — {badge} — {stats['nb_tirages']} tirages</div>",unsafe_allow_html=True)

        d=df.iloc[0];bs=[int(d[f"boule_{i}"])for i in range(1,6)]
        et_d=[int(d[f"etoile_{i}"])for i in range(1,jeu["nb_etoiles"]+1)]if jeu["nb_etoiles"]and"etoile_1"in df.columns else[]
        st.subheader(f"🎱 Dernier tirage — {d['date']}")
        st.markdown(afficher_grille_html(bs,et_d,stats,jeu_id),unsafe_allow_html=True)

        # Profil optimal
        po=stats["profil_optimal"]
        st.subheader("📐 Profil Optimal (basé sur l'historique)")
        c1,c2,c3,c4,c5=st.columns(5)
        c1.metric("Somme moy.",po["somme_moyenne"])
        c2.metric("Pairs moy.",po["pairs_moyen"])
        c3.metric("Bas moy.",po["bas_moyen"])
        c4.metric("Terminaisons",po["terminaisons_moy"])
        c5.metric("% avec consécutifs",f"{po['consecutifs_pct']}%")

        st.markdown("---")
        c1,c2=st.columns(2)
        with c1:
            st.subheader("🔥 Top 10 Chauds")
            ch=sorted(stats["boules"].values(),key=lambda x:x["indice_chaleur"],reverse=True)[:10]
            st.dataframe(pd.DataFrame(ch)[["numero","indice_chaleur","frequence_20t","ecart_actuel","tendance","proba_sortie"]].rename(
                columns={"numero":"N°","indice_chaleur":"🌡️","frequence_20t":"F20","ecart_actuel":"Éc.","tendance":"📈","proba_sortie":"P%"}),hide_index=True,use_container_width=True)
        with c2:
            st.subheader("📊 Top 10 Probabilité")
            pr=sorted(stats["boules"].values(),key=lambda x:x["proba_sortie"],reverse=True)[:10]
            st.dataframe(pd.DataFrame(pr)[["numero","proba_sortie","ecart_actuel","ecart_moyen","tendance"]].rename(
                columns={"numero":"N°","proba_sortie":"P%","ecart_actuel":"Éc.","ecart_moyen":"Moy","tendance":"📈"}),hide_index=True,use_container_width=True)

    # ════════════════════════════
    # GÉNÉRATEUR PRO
    # ════════════════════════════
    elif page=="🎯 Générateur Pro":
        st.markdown("<div class='main-header'>🎯 Générateur Pro</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{badge} — 8 modes × 10 filtres × 10 critères de score</div>",unsafe_allow_html=True)

        c1,c2,c3=st.columns(3)
        with c1:
            st.markdown("### 🎯 Mode")
            mode=st.selectbox("Stratégie",["aleatoire","chaud","froid","top","hybride","optimal","probabiliste","tendance","contrarian"],
                format_func=lambda x:{"aleatoire":"🎲 Aléatoire","chaud":"🔥 Chauds","froid":"🧊 Absents",
                    "top":"⭐ Top 12m","hybride":"🧠 Hybride","optimal":"🏆 Optimal Pondéré",
                    "probabiliste":"📊 Probabiliste","tendance":"📈 Tendance Hausse","contrarian":"🔄 Contrarian"}[x])

            if mode=="optimal":
                st.markdown("#### ⚙️ Poids des critères")
                poids_ch=st.slider("🌡️ Chaleur",0,100,50)
                poids_ec=st.slider("📏 Écart",0,100,50)
                poids_pr=st.slider("📊 Probabilité",0,100,50)
            else:
                poids_ch=poids_ec=poids_pr=50

        with c2:
            st.markdown("### 🔧 Préférences")
            fi=st.text_input("🔒 Forcés",placeholder="7, 14")
            forces=[int(n.strip())for n in fi.split(",")if n.strip().isdigit()and 1<=int(n.strip())<=jeu["boules_max"]][:3]if fi else[]
            chasseur=st.slider("🎯 Écart min",0,30,0)
            plafond=st.selectbox("🔝 Plafond",["aucun","moins_40","force_40"],format_func=lambda x:{"aucun":"—","moins_40":"<40","force_40":"≥40"}[x])
            ee=st.slider("⭐ Écart étoiles",0,8,2)if jeu["nb_etoiles"]else 0
            nbg=st.selectbox("Grilles",[1,3,5,10,20],index=1)

        with c3:
            st.markdown("### 🛡️ Filtres")
            fpa=st.checkbox("⚖️ Parité équilibrée",True)
            fso=st.checkbox("➕ Somme Gauss",True)
            fdi=st.checkbox("📊 Dizaines réparties",True)
            fan=st.checkbox("🚫 Anti-suite",True)
            f_term=st.checkbox("🔢 Terminaisons diversifiées",False,help="Au moins 4 terminaisons différentes")
            f_bh=st.checkbox("⬆️⬇️ Bas/Hauts équilibrés",False,help="Mix de numéros bas et hauts")
            f_ac=st.checkbox("🔗 Anti-corrélation",False,help="Évite les paires qui n'apparaissent jamais ensemble")

        if st.button("🎱 GÉNÉRER",type="primary",use_container_width=True):
            all_g=[]
            for gi in range(nbg):
                r=generer_grille_v4(jeu_id,stats,mode,fpa,fso,fdi,fan,chasseur,forces,ee,plafond,
                    f_term,f_ac,f_bh,poids_ch,poids_ec,poids_pr)
                all_g.append(r)
                st.markdown(f"#### Grille {gi+1}/{nbg}")
                st.markdown(afficher_grille_html(r["grille"],r["etoiles"],stats,jeu_id),unsafe_allow_html=True)
                afficher_score_v4(r["score"])
                with st.expander(f"📋 Détail G{gi+1}"):
                    det=[{"N°":b,"🌡️":stats["boules"][b]["indice_chaleur"],"Éc.":stats["boules"][b]["ecart_actuel"],
                        "P%":stats["boules"][b]["proba_sortie"],"📈":stats["boules"][b]["tendance"],
                        "Term.":stats["boules"][b]["terminaison"],"Diz.":stats["boules"][b]["dizaine"]+1,
                        "Dern.":stats["boules"][b]["derniere_sortie"]}for b in r["grille"]]
                    st.dataframe(pd.DataFrame(det),hide_index=True,use_container_width=True)
                st.markdown("---")

            st.session_state.grilles_gen.extend([{"grille":r["grille"],"etoiles":r["etoiles"],"score":r["score"]["total"],"mode":mode,"ts":datetime.now().strftime("%H:%M")}for r in all_g])

            st.subheader("📱 Mode Buraliste")
            for i,r in enumerate(all_g):
                gs=" — ".join(str(n)for n in r["grille"])
                es=f"  |  ⭐{' — '.join(str(e)for e in r['etoiles'])}"if r["etoiles"]else""
                st.markdown(f"<div style='text-align:center;font-size:28px;font-weight:bold;padding:15px;background:#f8fafc;border-radius:12px;margin:8px 0;'>G{i+1}: {gs}{es}</div>",unsafe_allow_html=True)

            export="".join([f"G{i+1}: {' - '.join(str(n)for n in r['grille'])}{' | ⭐'+' - '.join(str(e)for e in r['etoiles'])if r['etoiles']else''} (Score:{r['score']['total']})\n"for i,r in enumerate(all_g)])
            st.download_button("📥 Télécharger",export,f"grilles-{datetime.now().strftime('%Y%m%d-%H%M')}.txt")

    # ════════════════════════════
    # STATS AVANCÉES
    # ════════════════════════════
    elif page=="📊 Stats Avancées":
        st.markdown("<div class='main-header'>📊 Stats Avancées</div>",unsafe_allow_html=True)

        st.subheader("🌡️ Carte de Chaleur")
        nc=10;nr=(jeu["boules_max"]+nc-1)//nc;zd=[];td=[]
        for row in range(nr):
            zr=[];tr=[]
            for col in range(nc):
                n=row*nc+col+1
                if n<=jeu["boules_max"]:s=stats["boules"][n];zr.append(s["indice_chaleur"]);tr.append(f"N°{n}<br>🌡️{s['indice_chaleur']}<br>P%:{s['proba_sortie']}<br>Éc:{s['ecart_actuel']}<br>{s['tendance']}")
                else:zr.append(None);tr.append("")
            zd.append(zr);td.append(tr)
        fh=go.Figure(data=go.Heatmap(z=zd,text=td,hoverinfo="text",colorscale=[[0,"#1e3a5f"],[.5,"#f59e0b"],[1,"#ef4444"]],showscale=True))
        for row in range(nr):
            for col in range(nc):
                n=row*nc+col+1
                if n<=jeu["boules_max"]:fh.add_annotation(x=col,y=row,text=str(n),showarrow=False,font=dict(color="white",size=14))
        fh.update_layout(height=350,margin=dict(l=20,r=20,t=20,b=20),xaxis=dict(showticklabels=False),yaxis=dict(showticklabels=False))
        st.plotly_chart(fh,use_container_width=True)

        # Distribution structurelle
        st.subheader("📊 Profil des Tirages Réels")
        an=stats["analyses"]
        c1,c2,c3=st.columns(3)
        with c1:
            dp=Counter(f"{a['pairs']}P/{5-a['pairs']}I"for a in an)
            fig=go.Figure(go.Bar(x=list(dp.keys()),y=list(dp.values()),marker_color="#3b82f6"))
            fig.update_layout(height=250,title="Pairs/Impairs");st.plotly_chart(fig,use_container_width=True)
        with c2:
            db=Counter(f"{a['bas']}B/{5-a['bas']}H"for a in an)
            fig=go.Figure(go.Bar(x=list(db.keys()),y=list(db.values()),marker_color="#22c55e"))
            fig.update_layout(height=250,title="Bas/Hauts");st.plotly_chart(fig,use_container_width=True)
        with c3:
            sommes=[a["somme"]for a in an]
            fig=go.Figure(go.Histogram(x=sommes,nbinsx=30,marker_color="#f59e0b"))
            fig.add_vline(x=np.mean(sommes),line_dash="dash",line_color="red",annotation_text=f"μ={np.mean(sommes):.0f}")
            fig.update_layout(height=250,title="Sommes");st.plotly_chart(fig,use_container_width=True)

        # Tableau complet avec nouvelles colonnes
        st.subheader("📋 Tableau complet")
        tri=st.selectbox("Tri",["🌡️","Écart","P%","F20","Tendance","% Record"])
        cm={"🌡️":"indice_chaleur","Écart":"ecart_actuel","P%":"proba_sortie","F20":"frequence_20t","Tendance":"tendance","% Record":"ratio_ecart_record"}
        dfc=pd.DataFrame([{"N°":n,"🌡️":stats["boules"][n]["indice_chaleur"],"Éc.":stats["boules"][n]["ecart_actuel"],
            "Moy":stats["boules"][n]["ecart_moyen"],"Max":stats["boules"][n]["ecart_max"],
            "P%":stats["boules"][n]["proba_sortie"],"📈":stats["boules"][n]["tendance"],
            "F20":stats["boules"][n]["frequence_20t"],"F12m":stats["boules"][n]["frequence_12m"],
            "F3m":stats["boules"][n]["frequence_3m"],"%Rec":stats["boules"][n]["ratio_ecart_record"],
            "Term":stats["boules"][n]["terminaison"],"Diz":stats["boules"][n]["dizaine"]+1
            }for n in range(1,jeu["boules_max"]+1)])
        st.dataframe(dfc.sort_values(cm.get(tri,"indice_chaleur"),ascending=(tri in["Écart","% Record"])),hide_index=True,use_container_width=True,height=500)

    # ════════════════════════════
    # 🔬 MATRICE AFFINITÉ — NOUVEAU
    # ════════════════════════════
    elif page=="🔬 Matrice Affinité":
        st.markdown("<div class='main-header'>🔬 Matrice d'Affinité</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Quels numéros sortent souvent ensemble ?</div>",unsafe_allow_html=True)

        st.subheader("💑 Top 30 Paires les plus fréquentes")
        pd_d=[{"N°A":p[0][0],"N°B":p[0][1],"Ensemble":p[1],"Affinité":"🔥🔥🔥"if p[1]>=stats["paires"][2][1]else("🔥🔥"if p[1]>=stats["paires"][9][1]else"🔥")}for p in stats["paires"][:30]]
        st.dataframe(pd.DataFrame(pd_d),hide_index=True,use_container_width=True)

        # Heatmap des paires pour un numéro choisi
        st.subheader("🔎 Partenaires d'un numéro")
        num_choisi=st.number_input("Analyse le N°",1,jeu["boules_max"],7)

        partenaires=[]
        for p in stats["paires"]:
            if num_choisi in p[0]:
                autre=p[0][0]if p[0][1]==num_choisi else p[0][1]
                partenaires.append({"N°":autre,"Ensemble":p[1]})
        partenaires.sort(key=lambda x:x["Ensemble"],reverse=True)

        if partenaires:
            c1,c2=st.columns(2)
            with c1:
                st.markdown("**🤝 Meilleurs partenaires**")
                st.dataframe(pd.DataFrame(partenaires[:10]),hide_index=True,use_container_width=True)
            with c2:
                st.markdown("**👎 Pires partenaires**")
                st.dataframe(pd.DataFrame(partenaires[-10:]),hide_index=True,use_container_width=True)

                       seuil_p=partenaires[min(4,len(partenaires)-1)]["Ensemble"] if partenaires else 0
            fig_p=go.Figure(go.Bar(x=[str(p["N°"])for p in partenaires[:20]],y=[p["Ensemble"]for p in partenaires[:20]],
                marker_color=["#22c55e"if p["Ensemble"]>=seuil_p else"#3b82f6"for p in partenaires[:20]]))
            fig_p.update_layout(height=300,title=f"Top 20 partenaires du N°{num_choisi}")
            st.plotly_chart(fig_p,use_container_width=True)

    # ════════════════════════════
    # 📐 TERMINAISONS & DIZAINES — NOUVEAU
    # ════════════════════════════
    elif page=="📐 Terminaisons & Dizaines":
        st.markdown("<div class='main-header'>📐 Terminaisons & Dizaines</div>",unsafe_allow_html=True)

        c1,c2=st.columns(2)
        with c1:
            st.subheader("🔢 Terminaisons (dernier chiffre)")
            term_data=stats["terminaisons"]
            term20_data=stats["terminaisons_20"]
            fig_t=go.Figure()
            fig_t.add_trace(go.Bar(name="Global",x=[str(i)for i in range(10)],y=[term_data.get(i,0)for i in range(10)],marker_color="#3b82f6"))
            fig_t.add_trace(go.Bar(name="20 derniers",x=[str(i)for i in range(10)],y=[term20_data.get(i,0)for i in range(10)],marker_color="#f59e0b"))
            fig_t.update_layout(barmode="group",height=350,title="Fréquence par terminaison")
            st.plotly_chart(fig_t,use_container_width=True)

            st.markdown("**🔥 Terminaisons chaudes (20 derniers) :**")
            term_sorted=sorted(term20_data.items(),key=lambda x:x[1],reverse=True)
            for t_val,t_count in term_sorted[:3]:
                st.markdown(f"Terminaison **{t_val}** → {t_count} sorties")

        with c2:
            st.subheader("📊 Dizaines (tranche)")
            diz_data=stats["dizaines"]
            diz20_data=stats["dizaines_20"]
            labels=[f"{i*10+1}-{(i+1)*10}"for i in range(jeu["boules_max"]//10+1)]
            fig_d=go.Figure()
            fig_d.add_trace(go.Bar(name="Global",x=labels[:len(diz_data)],y=[diz_data.get(i,0)for i in range(len(labels))],marker_color="#22c55e"))
            fig_d.add_trace(go.Bar(name="20 derniers",x=labels[:len(diz20_data)],y=[diz20_data.get(i,0)for i in range(len(labels))],marker_color="#ef4444"))
            fig_d.update_layout(barmode="group",height=350,title="Fréquence par dizaine")
            st.plotly_chart(fig_d,use_container_width=True)

            st.markdown("**🔥 Dizaines chaudes (20 derniers) :**")
            diz_sorted=sorted(diz20_data.items(),key=lambda x:x[1],reverse=True)
            for d_val,d_count in diz_sorted[:3]:
                st.markdown(f"Dizaine **{d_val*10+1}-{(d_val+1)*10}** → {d_count} sorties")

        # Insight
        st.markdown("<div class='insight-card'>💡 <b>Insight :</b> Si certaines terminaisons ou dizaines sont sur-représentées récemment, "
            "le filtre 'Terminaisons diversifiées' dans le Générateur Pro peut aider à diversifier vos grilles.</div>",unsafe_allow_html=True)

    # ════════════════════════════
    # 📈 SCATTER ANALYSE — NOUVEAU
    # ════════════════════════════
    elif page=="📈 Scatter Analyse":
        st.markdown("<div class='main-header'>📈 Scatter Analyse</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Visualisation multi-dimensionnelle de chaque numéro</div>",unsafe_allow_html=True)

        # Scatter Écart vs Fréquence
        st.subheader("🎯 Écart vs Fréquence — Les 4 Quadrants")
        scatter_data=[]
        moy_ecart=np.mean([stats["boules"][n]["ecart_actuel"]for n in stats["boules"]])
        moy_freq=np.mean([stats["boules"][n]["frequence_20t"]for n in stats["boules"]])

        for n in range(1,jeu["boules_max"]+1):
            s=stats["boules"][n]
            ec=s["ecart_actuel"];fr=s["frequence_20t"]
            if ec>moy_ecart and fr>moy_freq:quad="🟡 Paradoxal (fréquent + absent)"
            elif ec>moy_ecart and fr<=moy_freq:quad="🧊 Froid (rare + absent)"
            elif ec<=moy_ecart and fr>moy_freq:quad="🔥 Chaud (fréquent + récent)"
            else:quad="😐 Neutre"
            scatter_data.append({"N°":n,"Écart":ec,"Freq 20t":fr,"Chaleur":s["indice_chaleur"],
                "P%":s["proba_sortie"],"Quadrant":quad})

        df_scatter=pd.DataFrame(scatter_data)
        fig_sc=px.scatter(df_scatter,x="Écart",y="Freq 20t",color="Quadrant",size="Chaleur",
            hover_data=["N°","P%"],text="N°",
            color_discrete_map={"🔥 Chaud (fréquent + récent)":"#ef4444","🧊 Froid (rare + absent)":"#3b82f6",
                "🟡 Paradoxal (fréquent + absent)":"#f59e0b","😐 Neutre":"#94a3b8"})
        fig_sc.add_hline(y=moy_freq,line_dash="dash",line_color="gray",opacity=0.5)
        fig_sc.add_vline(x=moy_ecart,line_dash="dash",line_color="gray",opacity=0.5)
        fig_sc.update_traces(textposition="top center",textfont_size=9)
        fig_sc.update_layout(height=600,title="Chaque point = un numéro")
        st.plotly_chart(fig_sc,use_container_width=True)

        st.markdown("""
        **Comment lire ce graphique :**
        - 🔥 **Coin haut-gauche** = Numéros CHAUDS (fréquents + sortis récemment) → Favoris
        - 🧊 **Coin bas-droite** = Numéros FROIDS (rares + longue absence) → Candidats "retour"
        - 🟡 **Coin haut-droite** = PARADOXAUX (fréquents mais absents depuis longtemps) → À surveiller
        - 😐 **Coin bas-gauche** = NEUTRES (rares + récents) → Peu d'intérêt
        """)

        # Scatter Probabilité vs Chaleur
        st.subheader("📊 Probabilité vs Chaleur")
        fig_pc=px.scatter(df_scatter,x="Chaleur",y="P%",text="N°",color="Quadrant",
            color_discrete_map={"🔥 Chaud (fréquent + récent)":"#ef4444","🧊 Froid (rare + absent)":"#3b82f6",
                "🟡 Paradoxal (fréquent + absent)":"#f59e0b","😐 Neutre":"#94a3b8"})
        fig_pc.update_traces(textposition="top center",textfont_size=9)
        fig_pc.update_layout(height=500)
        st.plotly_chart(fig_pc,use_container_width=True)

    # ════════════════════════════
    # 🚨 ALERTES & PROBAS
    # ════════════════════════════
    elif page=="🚨 Alertes & Probas":
        st.markdown("<div class='main-header'>🚨 Alertes & Probabilités</div>",unsafe_allow_html=True)

        st.subheader("📊 Top 15 — Probabilité de sortie")
        top_p=sorted(stats["boules"].values(),key=lambda x:x["proba_sortie"],reverse=True)[:15]
        for s in top_p:
            pct=s["proba_sortie"];n=s["numero"]
            color="#22c55e"if pct>=60 else("#f59e0b"if pct>=50 else"#3b82f6")
            bar_len=int(pct/100*20)
            bar="🟩"*bar_len+"⬜"*(20-bar_len)
            st.markdown(f"**N°{n}** — P={pct}% — Écart:{s['ecart_actuel']} (moy:{s['ecart_moyen']}) — {s['tendance']}")
            st.caption(bar)

        st.markdown("---")
        st.subheader("🚨 Numéros en zone critique")
        seuil=st.slider("Seuil",50,100,80)
        alertes=[s for s in stats["boules"].values()if s["ratio_ecart_record"]>=seuil]
        alertes.sort(key=lambda x:x["ratio_ecart_record"],reverse=True)
        if alertes:
            st.error(f"{len(alertes)} numéros à ≥{seuil}% de leur record !")
            for a in alertes:
                st.markdown(f"🚨 **N°{a['numero']}** — {a['ecart_actuel']}/{a['ecart_max']} tirages ({a['ratio_ecart_record']}% du record) — P={a['proba_sortie']}%")
        else:
            st.success("✅ Aucun numéro en zone critique")

    # ════════════════════════════
    # 🆚 COMPARATEUR
    # ════════════════════════════
    elif page=="🆚 Comparateur":
        st.markdown("<div class='main-header'>🆚 Comparateur</div>",unsafe_allow_html=True)
        nbt=st.selectbox("Tirages",[20,50,100],index=1)
        if st.button("🆚 COMPARER TOUT",type="primary",use_container_width=True):
            with st.spinner("⏳..."):
                comp={}
                for m in["aleatoire","chaud","froid","top","hybride","optimal","probabiliste","tendance","contrarian"]:
                    comp[m]=mini_backtest(df,jeu_id,stats,m,nbt)
            cd=[]
            for m,rb in comp.items():
                em={"aleatoire":"🎲","chaud":"🔥","froid":"🧊","top":"⭐","hybride":"🧠","optimal":"🏆","probabiliste":"📊","tendance":"📈","contrarian":"🔄"}
                cd.append({"Mode":f"{em.get(m,'')} {m}","Misé":f"{rb['total_mise']}€","Gagné":f"{rb['total_gains']}€",
                    "Bilan":f"{rb['bilan']:+.2f}€","≥3":sum(rb["resultats"][str(i)]for i in range(3,6)),
                    "≥4":sum(rb["resultats"][str(i)]for i in range(4,6)),"=5":rb["resultats"]["5"]})
            st.dataframe(pd.DataFrame(cd),hide_index=True,use_container_width=True)

    # ════════════════════════════
    # BACKTESTING
    # ════════════════════════════
    elif page=="🧪 Backtesting":
        st.markdown("<div class='main-header'>🧪 Backtesting</div>",unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1:mbt=st.selectbox("Mode",["aleatoire","chaud","froid","top","hybride","optimal","probabiliste","tendance","contrarian"])
        with c2:nbt=st.selectbox("Tirages",[20,50,100,200],index=1)
        if st.button("🚀 LANCER",type="primary",use_container_width=True):
            with st.spinner("⏳..."):rb=mini_backtest(df,jeu_id,stats,mbt,nbt)
            c1,c2,c3=st.columns(3);c1.metric("💰",f"{rb['total_mise']}€");c2.metric("🏆",f"{rb['total_gains']}€");c3.metric("📈",f"{rb['bilan']:+.2f}€")
            res=rb["resultats"]
            fb=go.Figure(go.Bar(x=[f"{k}"for k in sorted(res)],y=[res[k]for k in sorted(res)],marker_color=["#ef4444","#f97316","#f59e0b","#84cc16","#22c55e","#15803d"]))
            fb.update_layout(height=300);st.plotly_chart(fb,use_container_width=True)
            if rb["historique"]:
                for h in rb["historique"][:10]:st.markdown(f"📅 **{h['date']}** — `{h['grille']}` vs `{h['tirage']}` — **{h['bons']}** — {h['gain']}€")

    # ════════════════════════════
    # RÉDUCTEUR
    # ════════════════════════════
    elif page=="🧮 Réducteur":
        st.markdown("<div class='main-header'>🧮 Réducteur</div>",unsafe_allow_html=True)
        with st.expander("💡 Suggestions"):
            top=sorted(stats["boules"].values(),key=lambda x:x["proba_sortie"],reverse=True)[:10]
            st.markdown(f"**Top proba:** `{', '.join(str(n['numero'])for n in top)}`")
            top2=sorted(stats["boules"].values(),key=lambda x:x["indice_chaleur"],reverse=True)[:10]
            st.markdown(f"**Top chaleur:** `{', '.join(str(n['numero'])for n in top2)}`")
        ni=st.text_input("🔢 Numéros (6-15)",placeholder="3,7,14,19,23,28,34,41")
        if ni:
            nums=sorted(set(int(n.strip())for n in ni.split(",")if n.strip().isdigit()and 1<=int(n.strip())<=jeu["boules_max"]))
            if len(nums)>=6:
                if st.button("🧮 GO",type="primary",use_container_width=True):
                    grs=systeme_reducteur(nums)
                    st.info(f"💰 {len(grs)}×{jeu['prix']}€ = **{len(grs)*jeu['prix']:.2f}€**")
                    for i,g in enumerate(grs):st.markdown(f"<div class='grille-container'><b>G{i+1}</b>&nbsp;&nbsp;{'&nbsp;&nbsp;'.join(f'<span class=\"boule\">{b}</span>'for b in g)}</div>",unsafe_allow_html=True)

    # ════════════════════════════
    # HALL OF FAME
    # ════════════════════════════
    elif page=="🏆 Hall of Fame":
        st.markdown("<div class='main-header'>🏆 Hall of Fame</div>",unsafe_allow_html=True)
        if st.session_state.grilles_gen:
            sg=sorted(st.session_state.grilles_gen,key=lambda x:x["score"],reverse=True)
            st.metric("Total",len(sg));st.metric("Meilleur",f"{sg[0]['score']}/100")
            for i,g in enumerate(sg[:20]):
                md="🥇"if i==0 else("🥈"if i==1 else("🥉"if i==2 else f"#{i+1}"))
                gs=" — ".join(str(n)for n in g["grille"])
                es=f" | ⭐{' — '.join(str(e)for e in g['etoiles'])}"if g["etoiles"]else""
                st.markdown(f"{md} **{g['score']}/100** — `{gs}{es}` — {g['mode']} — {g['ts']}")
            if st.button("🗑️ Reset"):st.session_state.grilles_gen=[];st.rerun()
        else:st.info("Va dans 🎯 Générateur Pro")

    # ════════════════════════════
    # DEBUG
    # ════════════════════════════
    elif page=="🔍 Debug":
        st.markdown("<div class='main-header'>🔍 Debug</div>",unsafe_allow_html=True)
        if debug:
            if debug.get("succes"):st.success(f"✅ {debug.get('nb_tirages','?')} tirages")
            else:st.error(debug.get("erreur","?"))
            if"colonnes"in debug:
                for i,c in enumerate(debug["colonnes"][:15]):st.markdown(f"`{i}` → **{c}**")
            if"mapping"in debug:m=debug["mapping"];st.success(f"📅{m['date']} 🎱{m['boules']} ⭐{m['etoiles']}")
        st.dataframe(df.head(10),use_container_width=True)

    # ════════════════════════════
    # À PROPOS
    # ════════════════════════════
    elif page=="ℹ️ À propos":
        st.markdown("<div class='main-header'>ℹ️ V4.0</div>",unsafe_allow_html=True)
        st.markdown(f"""
## Nouveautés V4.0

### 🔬 Analyse Data
| Module | Description |
|---|---|
| 🔬 **Matrice Affinité** | Quels numéros sortent ensemble |
| 📈 **Scatter Analyse** | Quadrants Écart×Fréquence |
| 📐 **Terminaisons** | Analyse du dernier chiffre |
| 📐 **Dizaines** | Quelle tranche est chaude |
| 📊 **Probabilité de sortie** | Score basé sur l'écart statistique |
| 📈 **Tendance** | Hausse / Baisse / Stable par numéro |

### 🎯 Génération
| Amélioration | Description |
|---|---|
| 🏆 **Mode Optimal Pondéré** | Sliders chaleur/écart/proba |
| 📊 **Mode Probabiliste** | Basé sur la probabilité de sortie |
| 📈 **Mode Tendance** | Numéros en hausse uniquement |
| 🔄 **Mode Contrarian** | Numéros les moins joués |
| 🔢 **Filtre Terminaisons** | Diversité des derniers chiffres |
| ⬆️⬇️ **Filtre Bas/Hauts** | Équilibre petits/grands numéros |
| 🔗 **Filtre Anti-corrélation** | Évite paires jamais vues ensemble |
| 📊 **Score 10 critères** | Évaluation plus fine (100 pts) |

{badge} | {stats['nb_tirages']} tirages
        """)

    st.markdown("<div class='footer-disclaimer'>⚠️ Outil d'analyse — Aucune garantie de gain — 🛡️ <a href='https://www.joueurs-info-service.fr/'>Joueurs Info Service</a> 09 74 75 13 13</div>",unsafe_allow_html=True)

if __name__=="__main__":
    main()
