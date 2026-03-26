# ============================================================
# SMART-LOTO — V5.0 — ULTIMATE EDITION
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

st.set_page_config(page_title="Smart-Loto V5", page_icon="🎱", layout="wide", initial_sidebar_state="expanded")

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
    .reco-card {background:linear-gradient(135deg,#fdf4ff,#f3e8ff);border:2px solid #a855f7;border-radius:16px;padding:20px;margin:10px 0;}
</style>
""", unsafe_allow_html=True)

JEUX = {
    "euromillions": {"nom":"Euromillions","emoji":"⭐","boules_max":50,"nb_boules":5,"etoiles_max":12,"nb_etoiles":2,"prix":2.50,"somme_min":90,"somme_max":160},
    "loto": {"nom":"Loto","emoji":"🎱","boules_max":49,"nb_boules":5,"etoiles_max":None,"nb_etoiles":0,"prix":2.20,"somme_min":60,"somme_max":180}
}

# ============================================================
# CSV LOADER
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
    df=None;sep_f=None
    for s in [";",",","\t"]:
        try:
            dft=pd.read_csv(io.StringIO(text),sep=s,engine="python")
            dft=dft.loc[:,~dft.columns.str.match(r'^Unnamed')];dft.columns=[c.strip()for c in dft.columns]
            if len(dft.columns)>=7 and(df is None or len(dft.columns)>len(df.columns)):df=dft;sep_f=s
        except:pass
    if df is None or len(df.columns)<7:return None,{**debug,"erreur":"Colonnes insuffisantes"}
    debug["colonnes"]=list(df.columns);cl={c.upper():c for c in df.columns}
    dc=None
    for c in["DATE","date","DATE_DE_TIRAGE"]:
        if c in df.columns:dc=c;break
        if c.upper()in cl:dc=cl[c.upper()];break
    if not dc:
        for c in df.columns:
            if"date"in c.lower():dc=c;break
    if not dc:return None,{**debug,"erreur":"Date introuvable"}
    bc=[]
    for i in range(1,6):
        for c in[f"N{i}",f"n{i}",f"BOULE_{i}",f"boule_{i}"]:
            if c in df.columns:bc.append(c);break
            elif c.upper()in cl:bc.append(cl[c.upper()]);break
    if len(bc)<5:
        bc=[]
        for c in df.columns:
            if c==dc:continue
            try:
                v=pd.to_numeric(df[c],errors="coerce").dropna()
                if len(v)>len(df)*.3 and v.min()>=1 and v.max()<=jeu["boules_max"]:bc.append(c)
                if len(bc)>=5:break
            except:continue
    if len(bc)<5:return None,{**debug,"erreur":f"{len(bc)} boules"}
    ec=[]
    if jeu["nb_etoiles"]>0:
        for i in range(1,3):
            for c in[f"E{i}",f"e{i}",f"ETOILE_{i}",f"etoile_{i}"]:
                if c in df.columns:ec.append(c);break
                elif c.upper()in cl:ec.append(cl[c.upper()]);break
    res=pd.DataFrame()
    for fmt in[None,"%d/%m/%Y","%Y-%m-%d"]:
        try:
            if fmt:res["date"]=pd.to_datetime(df[dc],format=fmt,errors="coerce").dt.date
            else:res["date"]=pd.to_datetime(df[dc],dayfirst=True,errors="coerce").dt.date
            if res["date"].notna().sum()>len(df)*.5:break
        except:continue
    for i,c in enumerate(bc[:5],1):res[f"boule_{i}"]=pd.to_numeric(df[c],errors="coerce")
    for i,c in enumerate(ec[:2],1):res[f"etoile_{i}"]=pd.to_numeric(df[c],errors="coerce")
    try:
        res["jour"]=pd.to_datetime(res["date"]).dt.day_name()
        jm={"Monday":"lundi","Tuesday":"mardi","Wednesday":"mercredi","Friday":"vendredi","Saturday":"samedi"}
        res["jour"]=res["jour"].map(lambda x:jm.get(x,x))
    except:res["jour"]="?"
    try:res["mois"]=pd.to_datetime(res["date"]).dt.month
    except:res["mois"]=0
    res=res.dropna(subset=["date","boule_1","boule_2","boule_3","boule_4","boule_5"])
    for i in range(1,6):res[f"boule_{i}"]=res[f"boule_{i}"].astype(int)
    for i in range(1,3):
        if f"etoile_{i}"in res.columns:res[f"etoile_{i}"]=res[f"etoile_{i}"].fillna(0).astype(int)
    for i in range(1,6):res=res[(res[f"boule_{i}"]>=1)&(res[f"boule_{i}"]<=jeu["boules_max"])]
    res=res.sort_values("date",ascending=False).drop_duplicates("date").reset_index(drop=True)
    debug["succes"]=len(res)>0;debug["nb_tirages"]=len(res)
    debug["mapping"]={"date":dc,"boules":bc[:5],"etoiles":ec[:2]}
    return res,debug

def gen_simul(jid,nb=500):
    random.seed(42);np.random.seed(42);jeu=JEUX[jid];t=[];now=datetime.now()
    js=["mardi","vendredi"]if jid=="euromillions"else["lundi","mercredi","samedi"]
    for i in range(nb):
        b=sorted(random.sample(range(1,jeu["boules_max"]+1),5))
        e=sorted(random.sample(range(1,jeu["etoiles_max"]+1),2))if jeu["etoiles_max"]else[]
        d={"date":(now-timedelta(days=i*3.5)).date(),"boule_1":b[0],"boule_2":b[1],"boule_3":b[2],"boule_4":b[3],"boule_5":b[4],"jour":js[i%len(js)],"mois":(now-timedelta(days=i*3.5)).month}
        if e:d["etoile_1"]=e[0];d["etoile_2"]=e[1]
        t.append(d)
    return pd.DataFrame(t).sort_values("date",ascending=False).reset_index(drop=True)

# ============================================================
# STATS ENGINE V5
# ============================================================
@st.cache_data
def calc_stats(df_json, jid, jour_f=None):
    df=pd.read_json(io.StringIO(df_json));df["date"]=pd.to_datetime(df["date"]).dt.date
    if jour_f and jour_f!="tous"and"jour"in df.columns:
        df=df[df["jour"].str.lower()==jour_f.lower()].reset_index(drop=True)
    jeu=JEUX[jid];stats={};cols=[f"boule_{i}"for i in range(1,6)]
    an=[];paires=Counter()
    for c in cols:an.extend(df[c].tolist())
    df20=df.head(20);n20=[]
    for c in cols:n20.extend(df20[c].tolist())
    d12=datetime.now().date()-timedelta(days=365);df12=df[df["date"]>=d12];n12=[]
    for c in cols:n12.extend(df12[c].tolist())
    d3=datetime.now().date()-timedelta(days=90);df3=df[df["date"]>=d3];n3=[]
    for c in cols:n3.extend(df3[c].tolist())
    fa,f20,f12,f3=Counter(an),Counter(n20),Counter(n12),Counter(n3)

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
        ft=(len(df12)*5)/jeu["boules_max"];fn=(f12.get(n,0)/max(ft,1))*50
        ep=max(0,30-(ec*2));ch=min(100,max(0,.40*fo+.35*fn+.25*ep))
        rr=(ec/ex*100)if ex>0 else 0
        if em>0:z_ec=(ec-em)/max(es,1);pb=min(99,max(1,50+z_ec*15))
        else:pb=50
        f_p1=f3.get(n,0);f_p2=f12.get(n,0)-f3.get(n,0)
        t1=f_p1/max(len(df3),1)*100;t2=f_p2/max(len(df12)-len(df3),1)*100
        tend="↗️"if t1>t2*1.3 else("↘️"if t1<t2*0.7 else"→")
        # NOUVEAU : Retard prédit (estimation du prochain tirage)
        retard_predit = max(0, round(em - ec))  # Tirages restants estimés
        stats[n]={"numero":n,"ecart":ec,"ecart_moy":round(em,1),"ecart_max":ex,"ecart_std":round(es,1),
            "freq_tot":fa.get(n,0),"f20":f20.get(n,0),"f12m":f12.get(n,0),"f3m":f3.get(n,0),
            "chaleur":round(ch,1),"dern":str(dern)if dern else"—","ratio_rec":round(rr,1),
            "proba":round(pb,1),"tend":tend,"term":n%10,"diz":(n-1)//10,
            "retard_predit":retard_predit}

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
            se[n]={"numero":n,"ecart":ec,"freq_tot":fe.get(n,0),"f20":fe20.get(n,0)}

    for _,r in df.iterrows():
        bs=sorted([int(r[c])for c in cols])
        for i in range(len(bs)):
            for j in range(i+1,len(bs)):paires[(bs[i],bs[j])]+=1

    # Analyse structurelle
    analyses=[]
    for _,r in df.iterrows():
        bs=[int(r[c])for c in cols]
        analyses.append({"pairs":sum(1 for b in bs if b%2==0),"bas":sum(1 for b in bs if b<=25),
            "somme":sum(bs),"terms_diff":len(set(b%10 for b in bs)),"diz_diff":len(set((b-1)//10 for b in bs))})

    sommes=[a["somme"]for a in analyses]
    po={"somme_moy":round(np.mean(sommes),1),"somme_q1":round(np.percentile(sommes,25),1),
        "somme_q3":round(np.percentile(sommes,75),1),
        "pairs_moy":round(np.mean([a["pairs"]for a in analyses]),1),
        "bas_moy":round(np.mean([a["bas"]for a in analyses]),1),
        "terms_moy":round(np.mean([a["terms_diff"]for a in analyses]),1),
        "diz_moy":round(np.mean([a["diz_diff"]for a in analyses]),1)}

    # NOUVEAU : Analyse saisonnière
    saison={}
    if "mois" in df.columns:
        for mois in range(1,13):
            dfm=df[df.get("mois",pd.Series())==mois] if "mois" in df.columns else pd.DataFrame()
            if len(dfm)>0:
                nm=[]
                for c in cols:nm.extend(dfm[c].tolist())
                fm=Counter(nm)
                top3=fm.most_common(5)
                saison[mois]={"nb_tirages":len(dfm),"top":top3}

    # Terminaisons et dizaines
    term_all=Counter(n%10 for n in an);term_20=Counter(n%10 for n in n20)
    diz_all=Counter((n-1)//10 for n in an);diz_20=Counter((n-1)//10 for n in n20)

    return {"boules":stats,"etoiles":se,"paires":paires.most_common(30),
        "term_all":dict(term_all),"term_20":dict(term_20),
        "diz_all":dict(diz_all),"diz_20":dict(diz_20),
        "analyses":analyses,"profil":po,"saison":saison,
        "nb_tirages":len(df),
        "date_1":str(df.iloc[-1]["date"])if len(df)>0 else"—",
        "date_n":str(df.iloc[0]["date"])if len(df)>0 else"—"}


# ============================================================
# SCORE V5 — 10 CRITÈRES
# ============================================================
def score_v5(gr,et,stats,jid):
    jeu=JEUX[jid];sc={};po=stats.get("profil",{})
    np2=sum(1 for n in gr if n%2==0)
    sc["⚖️ Parité"]=15 if abs(np2-po.get("pairs_moy",2.5))<=0.5 else(10 if abs(np2-po.get("pairs_moy",2.5))<=1.5 else 5)
    dz=Counter((n-1)//10 for n in gr)
    sc["📊 Dizaines"]=12 if len(dz)>=round(po.get("diz_moy",4)) else(8 if len(dz)>=round(po.get("diz_moy",4))-1 else 4)
    s=sum(gr);q1=po.get("somme_q1",90);q3=po.get("somme_q3",160)
    sc["➕ Somme"]=15 if q1<=s<=q3 else(10 if jeu["somme_min"]<=s<=jeu["somme_max"]else 3)
    ecs=[stats["boules"][n]["ecart"]for n in gr if n in stats["boules"]]
    sc["🔀 Diversité"]=(10 if float(np.std(ecs))>5 else(7 if float(np.std(ecs))>3 else 4))if len(set(ecs))>1 else 4
    g=sorted(gr);hs=any(g[i+1]==g[i]+1 and g[i+2]==g[i]+2 for i in range(len(g)-2))
    sc["🚫 Suite"]=2 if hs else 8
    if et and len(et)==2:ec=abs(et[0]-et[1]);sc["⭐ Étoiles"]=8 if ec>=3 else(5 if ec>=2 else 2)
    else:sc["⭐ Étoiles"]=8
    terms=set(n%10 for n in gr)
    sc["🔢 Terms"]=8 if len(terms)>=round(po.get("terms_moy",4)) else(5 if len(terms)>=round(po.get("terms_moy",4))-1 else 2)
    nb_bas=sum(1 for n in gr if n<=jeu["boules_max"]//2)
    sc["⬆️⬇️ B/H"]=8 if abs(nb_bas-po.get("bas_moy",2.5))<=0.5 else(5 if abs(nb_bas-po.get("bas_moy",2.5))<=1.5 else 2)
    chs=[stats["boules"][n]["chaleur"]for n in gr if n in stats["boules"]]
    mc=np.mean(chs)if chs else 50
    sc["🌡️ Chaleur"]=8 if 35<=mc<=65 else(5 if 20<=mc<=80 else 2)
    pbs=[stats["boules"][n]["proba"]for n in gr if n in stats["boules"]]
    mp=np.mean(pbs)if pbs else 50
    sc["📊 Proba"]=8 if mp>=55 else(5 if mp>=45 else 2)
    return{"total":sum(sc.values()),"detail":sc,"max":100}


# ============================================================
# GENERATOR V5
# ============================================================
def gen_grille(jid,stats,mode="aleatoire",fp=False,fs=False,fd=False,fa=False,
               chasseur=0,forces=None,ee=0,plafond="aucun",
               f_term=False,f_bh=False,f_ac=False,
               pw_ch=50,pw_ec=50,pw_pr=50,mt=2000):
    jeu=JEUX[jid]
    for t in range(mt):
        if mode=="optimal":
            ns=list(stats["boules"].keys())
            sc_c=[(pw_ch/100)*stats["boules"][n]["chaleur"]+(pw_ec/100)*min(100,stats["boules"][n]["ecart"]*8)+(pw_pr/100)*stats["boules"][n]["proba"]for n in ns]
            sc_c=[s**1.5+1 for s in sc_c];tp=sum(sc_c)
            pool=list(np.random.choice(ns,size=min(25,len(ns)),replace=False,p=[s/tp for s in sc_c]))
        elif mode=="contrarian":pool=sorted(stats["boules"],key=lambda x:stats["boules"][x]["freq_tot"])[:20]
        elif mode=="probabiliste":pool=sorted(stats["boules"],key=lambda x:stats["boules"][x]["proba"],reverse=True)[:20]
        elif mode=="tendance":
            pool=[n for n in stats["boules"]if stats["boules"][n]["tend"]=="↗️"]
            if len(pool)<10:pool+=sorted(stats["boules"],key=lambda x:stats["boules"][x]["chaleur"],reverse=True)[:20]
            pool=pool[:25]
        elif mode=="retard":
            # NOUVEAU : Mode Retard Prédit — numéros dont le retard prédit est 0 ou négatif
            pool=sorted(stats["boules"],key=lambda x:stats["boules"][x]["retard_predit"])[:20]
        elif mode=="chaud":pool=sorted(stats["boules"],key=lambda x:stats["boules"][x]["chaleur"],reverse=True)[:20]
        elif mode=="froid":pool=sorted(stats["boules"],key=lambda x:stats["boules"][x]["ecart"],reverse=True)[:20]
        elif mode=="top":pool=sorted(stats["boules"],key=lambda x:stats["boules"][x]["f12m"],reverse=True)[:15]
        elif mode=="hybride":
            ns=list(stats["boules"].keys());pw=[stats["boules"][n]["chaleur"]**1.5+5 for n in ns]
            tp=sum(pw);pool=list(np.random.choice(ns,size=min(25,len(ns)),replace=False,p=[p/tp for p in pw]))
        else:pool=list(range(1,jeu["boules_max"]+1))

        if plafond=="moins_40":pool=[n for n in pool if n<40]
        if chasseur>0:
            pf=[n for n in pool if stats["boules"][n]["ecart"]>=chasseur]
            if len(pf)>=5:pool=pf
        fo=[f for f in(forces or[])if 1<=f<=jeu["boules_max"]]
        di=[n for n in pool if n not in fo];mq=5-len(fo)
        if mq>len(di):di=[n for n in range(1,jeu["boules_max"]+1)if n not in fo]
        ch=random.sample(di,min(mq,len(di)))if mq>0 else[]
        gr=sorted(fo+ch)[:5]
        if plafond=="force_40"and not any(n>=40 for n in gr):
            s40=[n for n in range(40,jeu["boules_max"]+1)if n not in gr]
            nf=[n for n in gr if n not in fo]
            if s40 and nf:rm=min(nf,key=lambda x:stats["boules"][x]["chaleur"]);gr.remove(rm);gr.append(random.choice(s40));gr=sorted(gr)
        et=[]
        if jeu["nb_etoiles"]and jeu["etoiles_max"]:
            for _ in range(100):
                et=sorted(random.sample(range(1,jeu["etoiles_max"]+1),jeu["nb_etoiles"]))
                if ee>0 and len(et)==2 and abs(et[0]-et[1])>=ee:break
                elif ee==0:break
        v=True
        if fp:np2=sum(1 for n in gr if n%2==0);v=v and 0<np2<5
        if fs:v=v and jeu["somme_min"]<=sum(gr)<=jeu["somme_max"]
        if fd:v=v and max(Counter((n-1)//10 for n in gr).values())<=3
        if fa:gs=sorted(gr);v=v and not any(gs[i+1]==gs[i]+1 and gs[i+2]==gs[i]+2 for i in range(len(gs)-2))
        if f_term:v=v and len(set(n%10 for n in gr))>=4
        if f_bh:nb_b=sum(1 for n in gr if n<=jeu["boules_max"]//2);v=v and 1<=nb_b<=4
        if v:return{"grille":gr,"etoiles":et,"score":score_v5(gr,et,stats,jid),"t":t+1,"mode":mode}
    gr=sorted(random.sample(range(1,jeu["boules_max"]+1),5))
    et=sorted(random.sample(range(1,jeu["etoiles_max"]+1),2))if jeu["etoiles_max"]else[]
    return{"grille":gr,"etoiles":et,"score":score_v5(gr,et,stats,jid),"t":mt,"mode":"fallback"}

def backtest(df,jid,stats,mode,nt=50,gpt=1):
    jeu=JEUX[jid];cols=[f"boule_{i}"for i in range(1,6)]
    res={str(i):0 for i in range(6)};tm=0;tg=0;gt={0:0,1:0,2:0,3:4,4:50,5:5000};hist=[]
    for idx in range(min(nt,len(df))):
        row=df.iloc[idx];bt=set(int(row[c])for c in cols)
        for _ in range(gpt):
            r=gen_grille(jid,stats,mode=mode);nb=len(set(r["grille"])&bt)
            res[str(nb)]+=1;tm+=jeu["prix"];g=gt.get(nb,0);tg+=g
            if nb>=3:hist.append({"date":str(row["date"]),"grille":r["grille"],"tirage":sorted(bt),"bons":nb,"gain":g})
    return{"resultats":res,"mise":round(tm,2),"gains":round(tg,2),"bilan":round(tg-tm,2),"nb":nt*gpt,"hist":hist}

def reducteur(nums,t=5):
    from itertools import combinations
    if len(nums)<=t:return[sorted(nums)]
    combs=list(combinations(nums,t));random.shuffle(combs)
    gr=[];co=set()
    for c in combs:
        if set(c)-co or not gr:gr.append(sorted(c));co|=set(c)
        if co==set(nums)and len(gr)>=3:break
        if len(gr)>=12:break
    return gr

def html_grille(gr,et,stats,jid):
    h="<div class='grille-container'>"
    for b in gr:
        ch=stats["boules"][b]["chaleur"]
        bg="linear-gradient(135deg,#dc2626,#ef4444)"if ch>=60 else("linear-gradient(135deg,#1e40af,#3b82f6)"if ch>=40 else"linear-gradient(135deg,#1e3a5f,#475569)")
        h+=f"<span style='background:{bg};color:white;border-radius:50%;width:65px;height:65px;display:inline-flex;align-items:center;justify-content:center;font-size:22px;font-weight:bold;margin:5px;box-shadow:0 4px 12px rgba(0,0,0,0.3);'>{b}</span>"
    if et:
        h+="<span style='margin:0 15px;font-size:28px;color:#94a3b8;'>|</span>"
        for e in et:h+=f"<span class='etoile'>⭐{e}</span>"
    h+="</div>";return h

def show_score(sc):
    ev="⭐"*max(1,min(5,(sc["total"]-20)//15+1))
    sc_c="#22c55e"if sc["total"]>=70 else("#f59e0b"if sc["total"]>=50 else"#ef4444")
    c1,c2=st.columns([1,2])
    with c1:st.markdown(f"<div style='text-align:center;'><div style='font-size:3rem;font-weight:800;color:{sc_c};'>{sc['total']}</div><div style='color:#64748b;'>/ {sc['max']} {ev}</div></div>",unsafe_allow_html=True)
    with c2:
        mx={"⚖️ Parité":15,"📊 Dizaines":12,"➕ Somme":15,"🔀 Diversité":10,"🚫 Suite":8,"⭐ Étoiles":8,"🔢 Terms":8,"⬆️⬇️ B/H":8,"🌡️ Chaleur":8,"📊 Proba":8}
        for cr,pt in sc["detail"].items():
            m=mx.get(cr,8);pct=pt/m if m else 0
            cl="#22c55e"if pct>=.7 else("#f59e0b"if pct>=.4 else"#ef4444")
            bar="█"*int(pct*10)+"░"*(10-int(pct*10))
            st.markdown(f"<span style='font-size:.85rem;'>`{cr}` <span style='color:{cl};font-family:monospace;'>{bar}</span> **{pt}/{m}**</span>",unsafe_allow_html=True)


# ============================================================
# 🔮 AUTO-SUGGESTION — NOUVEAU
# ============================================================
def auto_suggestion(stats, jeu_id):
    """Analyse les données et recommande la meilleure stratégie."""
    jeu = JEUX[jeu_id]
    recos = []

    # Combien de numéros sont en tendance hausse ?
    nb_hausse = sum(1 for s in stats["boules"].values() if s["tend"] == "↗️")
    nb_baisse = sum(1 for s in stats["boules"].values() if s["tend"] == "↘️")

    if nb_hausse > jeu["boules_max"] * 0.25:
        recos.append({"mode": "tendance", "raison": f"{nb_hausse} numéros en hausse (> 25%)", "confiance": 80})

    # Combien de numéros ont un écart proche du record ?
    nb_record = sum(1 for s in stats["boules"].values() if s["ratio_rec"] >= 80)
    if nb_record >= 5:
        recos.append({"mode": "retard", "raison": f"{nb_record} numéros à ≥80% de leur record", "confiance": 75})

    # Moyenne de probabilité
    moy_proba = np.mean([s["proba"] for s in stats["boules"].values()])
    if moy_proba > 55:
        recos.append({"mode": "probabiliste", "raison": f"Proba moyenne élevée ({moy_proba:.1f}%)", "confiance": 70})

    # Écart moyen global vs attendu
    moy_ecart = np.mean([s["ecart"] for s in stats["boules"].values()])
    moy_ecart_attendu = jeu["boules_max"] / 5
    if moy_ecart > moy_ecart_attendu * 1.2:
        recos.append({"mode": "froid", "raison": f"Écart moyen élevé ({moy_ecart:.1f} vs attendu {moy_ecart_attendu:.1f})", "confiance": 65})
    else:
        recos.append({"mode": "chaud", "raison": f"Écart moyen normal → favoriser les chauds", "confiance": 60})

    # Toujours ajouter optimal comme option
    recos.append({"mode": "optimal", "raison": "Compromis intelligent entre tous les critères", "confiance": 70})

    # Trier par confiance
    recos.sort(key=lambda x: x["confiance"], reverse=True)
    return recos


# ============================================================
# INTERFACE V5
# ============================================================
def main():
    st.sidebar.markdown("<div style='text-align:center;'><h1 style='font-size:2rem;'>🎱 Smart-Loto</h1><p style='color:#64748b;'>V5.0 Ultimate</p></div>",unsafe_allow_html=True)
    st.sidebar.markdown("---")
    jeu_id=st.sidebar.selectbox("🎮",["euromillions","loto"],format_func=lambda x:f"{JEUX[x]['emoji']} {JEUX[x]['nom']}")
    jeu=JEUX[jeu_id]
    st.sidebar.markdown("---")
    up=st.sidebar.file_uploader(f"📤 CSV",type=["csv","txt"])
    reel=False;dbg={}
    if up:
        df,dbg=detecter_et_charger_csv(up,jeu_id)
        if df is not None and len(df)>0:reel=True;st.sidebar.success(f"✅ {len(df)} tirages")
        else:st.sidebar.error("❌");df=gen_simul(jeu_id)
    else:df=gen_simul(jeu_id);st.sidebar.info("💡 Importe CSV")
    if"gg"not in st.session_state:st.session_state.gg=[]

    st.sidebar.markdown("---")
    page=st.sidebar.radio("📑",[
        "🏠 Dashboard","🎯 Générateur Pro","📊 Stats",
        "🔮 Auto-Suggestion","📆 Saisonnier","📈 Tendance Glissante",
        "⏳ Retard Prédit","💰 Budget","📱 Checker",
        "🎰 Monte Carlo","🔗 Couverture",
        "🆚 Comparateur","🧪 Backtest","🧮 Réducteur",
        "🏆 Hall of Fame","🔍 Debug","ℹ️ Info"])
    st.sidebar.caption("⚠️ Pas de garantie\n🛡️ 09 74 75 13 13")
    stats=calc_stats(df.to_json(),jeu_id)
    bdg="🟢"if reel else"🟡"

    # ═══════════════════
    # DASHBOARD
    # ═══════════════════
    if page=="🏠 Dashboard":
        st.markdown("<div class='main-header'>🏠 Dashboard</div>",unsafe_allow_html=True)
        st.markdown(f"<div class='sub-header'>{jeu['nom']} — {bdg} — {stats['nb_tirages']} tirages</div>",unsafe_allow_html=True)
        d=df.iloc[0];bs=[int(d[f"boule_{i}"])for i in range(1,6)]
        et_d=[int(d[f"etoile_{i}"])for i in range(1,jeu["nb_etoiles"]+1)]if jeu["nb_etoiles"]and"etoile_1"in df.columns else[]
        st.subheader(f"🎱 Dernier — {d['date']}")
        st.markdown(html_grille(bs,et_d,stats,jeu_id),unsafe_allow_html=True)

        # Auto-suggestion rapide
        recos=auto_suggestion(stats,jeu_id)
        if recos:
            best=recos[0]
            st.markdown(f"<div class='reco-card'>🔮 <b>Recommandation :</b> Mode <b>{best['mode'].upper()}</b> — {best['raison']} (confiance {best['confiance']}%)</div>",unsafe_allow_html=True)

        c1,c2=st.columns(2)
        with c1:
            st.subheader("🔥 Top 10 Chauds")
            ch=sorted(stats["boules"].values(),key=lambda x:x["chaleur"],reverse=True)[:10]
            st.dataframe(pd.DataFrame(ch)[["numero","chaleur","f20","ecart","tend","proba"]].rename(columns={"numero":"N°","chaleur":"🌡️","f20":"F20","ecart":"Éc.","tend":"📈","proba":"P%"}),hide_index=True,use_container_width=True)
        with c2:
            st.subheader("⏳ Top 10 Retard")
            rt=sorted(stats["boules"].values(),key=lambda x:x["retard_predit"])[:10]
            st.dataframe(pd.DataFrame(rt)[["numero","retard_predit","ecart","ecart_moy","proba"]].rename(columns={"numero":"N°","retard_predit":"⏳ Retard","ecart":"Éc.","ecart_moy":"Moy","proba":"P%"}),hide_index=True,use_container_width=True)

    # ═══════════════════
    # GÉNÉRATEUR PRO
    # ═══════════════════
    elif page=="🎯 Générateur Pro":
        st.markdown("<div class='main-header'>🎯 Générateur Pro</div>",unsafe_allow_html=True)
        c1,c2,c3=st.columns(3)
        with c1:
            mode=st.selectbox("Mode",["aleatoire","chaud","froid","top","hybride","optimal","probabiliste","tendance","retard","contrarian"],
                format_func=lambda x:{"aleatoire":"🎲 Aléatoire","chaud":"🔥 Chauds","froid":"🧊 Froids","top":"⭐ Top","hybride":"🧠 Hybride","optimal":"🏆 Optimal","probabiliste":"📊 Proba","tendance":"📈 Tendance","retard":"⏳ Retard Prédit","contrarian":"🔄 Contrarian"}[x])
            if mode=="optimal":
                pw_ch=st.slider("🌡️ Chaleur",0,100,50);pw_ec=st.slider("📏 Écart",0,100,50);pw_pr=st.slider("📊 Proba",0,100,50)
            else:pw_ch=pw_ec=pw_pr=50
        with c2:
            fi=st.text_input("🔒 Forcés",placeholder="7,14")
            forces=[int(n.strip())for n in fi.split(",")if n.strip().isdigit()and 1<=int(n.strip())<=jeu["boules_max"]][:3]if fi else[]
            chasseur=st.slider("🎯 Écart min",0,30,0)
            plafond=st.selectbox("🔝",["aucun","moins_40","force_40"],format_func=lambda x:{"aucun":"—","moins_40":"<40","force_40":"≥40"}[x])
            ee=st.slider("⭐ Éc.ét.",0,8,2)if jeu["nb_etoiles"]else 0
            nbg=st.selectbox("Nb",[1,3,5,10],index=1)
        with c3:
            fpa=st.checkbox("⚖️ Parité",True);fso=st.checkbox("➕ Somme",True)
            fdi=st.checkbox("📊 Dizaines",True);fan=st.checkbox("🚫 Suite",True)
            ftm=st.checkbox("🔢 Terminaisons",False);fbh=st.checkbox("⬆️⬇️ Bas/Hauts",False)

        if st.button("🎱 GÉNÉRER",type="primary",use_container_width=True):
            ag=[]
            for gi in range(nbg):
                r=gen_grille(jeu_id,stats,mode,fpa,fso,fdi,fan,chasseur,forces,ee,plafond,ftm,fbh,False,pw_ch,pw_ec,pw_pr)
                ag.append(r);st.markdown(f"#### G{gi+1}/{nbg}")
                st.markdown(html_grille(r["grille"],r["etoiles"],stats,jeu_id),unsafe_allow_html=True)
                show_score(r["score"]);st.markdown("---")
            st.session_state.gg.extend([{"g":r["grille"],"e":r["etoiles"],"s":r["score"]["total"],"m":mode,"t":datetime.now().strftime("%H:%M")}for r in ag])
            st.subheader("📱 Buraliste")
            for i,r in enumerate(ag):
                gs=" — ".join(str(n)for n in r["grille"])
                es=f" | ⭐{' — '.join(str(e)for e in r['etoiles'])}"if r["etoiles"]else""
                st.markdown(f"<div style='text-align:center;font-size:28px;font-weight:bold;padding:15px;background:#f8fafc;border-radius:12px;margin:8px 0;'>G{i+1}: {gs}{es}</div>",unsafe_allow_html=True)
            exp="".join(f"G{i+1}: {' - '.join(str(n)for n in r['grille'])}{' | E:'+' - '.join(str(e)for e in r['etoiles'])if r['etoiles']else''} (S:{r['score']['total']})\n"for i,r in enumerate(ag))
            st.download_button("📥",exp,f"grilles-{datetime.now().strftime('%Y%m%d')}.txt")

    # ═══════════════════
    # STATS
    # ═══════════════════
    elif page=="📊 Stats":
        st.markdown("<div class='main-header'>📊 Statistiques</div>",unsafe_allow_html=True)
        nc=10;nr=(jeu["boules_max"]+nc-1)//nc;zd=[];td=[]
        for row in range(nr):
            zr=[];tr=[]
            for col in range(nc):
                n=row*nc+col+1
                if n<=jeu["boules_max"]:s=stats["boules"][n];zr.append(s["chaleur"]);tr.append(f"N°{n}<br>🌡️{s['chaleur']}<br>P:{s['proba']}%<br>Éc:{s['ecart']}<br>{s['tend']}")
                else:zr.append(None);tr.append("")
            zd.append(zr);td.append(tr)
        fh=go.Figure(data=go.Heatmap(z=zd,text=td,hoverinfo="text",colorscale=[[0,"#1e3a5f"],[.5,"#f59e0b"],[1,"#ef4444"]],showscale=True))
        for row in range(nr):
            for col in range(nc):
                n=row*nc+col+1
                if n<=jeu["boules_max"]:fh.add_annotation(x=col,y=row,text=str(n),showarrow=False,font=dict(color="white",size=14))
        fh.update_layout(height=350,margin=dict(l=20,r=20,t=20,b=20),xaxis=dict(showticklabels=False),yaxis=dict(showticklabels=False))
        st.plotly_chart(fh,use_container_width=True)

        tri=st.selectbox("Tri",["🌡️","Écart","P%","F20","⏳ Retard","% Record"])
        cm={"🌡️":"chaleur","Écart":"ecart","P%":"proba","F20":"f20","⏳ Retard":"retard_predit","% Record":"ratio_rec"}
        dfc=pd.DataFrame([{"N°":n,"🌡️":stats["boules"][n]["chaleur"],"Éc.":stats["boules"][n]["ecart"],
            "Moy":stats["boules"][n]["ecart_moy"],"Max":stats["boules"][n]["ecart_max"],
            "P%":stats["boules"][n]["proba"],"📈":stats["boules"][n]["tend"],
            "F20":stats["boules"][n]["f20"],"F12m":stats["boules"][n]["f12m"],
            "⏳":stats["boules"][n]["retard_predit"],"%Rec":stats["boules"][n]["ratio_rec"],
            "Term":stats["boules"][n]["term"],"Diz":stats["boules"][n]["diz"]+1
            }for n in range(1,jeu["boules_max"]+1)])
        st.dataframe(dfc.sort_values(cm.get(tri,"chaleur"),ascending=(tri in["Écart","⏳ Retard"])),hide_index=True,use_container_width=True,height=500)

    # ═══════════════════
    # 🔮 AUTO-SUGGESTION — NOUVEAU
    # ═══════════════════
    elif page=="🔮 Auto-Suggestion":
        st.markdown("<div class='main-header'>🔮 Auto-Suggestion</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>L'outil analyse les données et te recommande la meilleure stratégie</div>",unsafe_allow_html=True)

        recos=auto_suggestion(stats,jeu_id)
        for i,r in enumerate(recos):
            emoji={"tendance":"📈","retard":"⏳","probabiliste":"📊","froid":"🧊","chaud":"🔥","optimal":"🏆"}.get(r["mode"],"🎯")
            conf_color="#22c55e"if r["confiance"]>=75 else("#f59e0b"if r["confiance"]>=60 else"#3b82f6")
            medal="🥇"if i==0 else("🥈"if i==1 else"🥉"if i==2 else f"#{i+1}")
            st.markdown(f"""
            <div class='reco-card' style='border-color:{conf_color};'>
            <span style='font-size:1.5rem;'>{medal} {emoji} Mode <b>{r['mode'].upper()}</b></span><br>
            <b>Raison :</b> {r['raison']}<br>
            <b>Confiance :</b> <span style='color:{conf_color};font-weight:bold;'>{r['confiance']}%</span>
            </div>""",unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🎱 Générer avec la meilleure suggestion",type="primary",use_container_width=True):
            best=recos[0]["mode"]
            for i in range(3):
                r=gen_grille(jeu_id,stats,best,True,True,True,True)
                st.markdown(f"#### G{i+1} (mode {best})")
                st.markdown(html_grille(r["grille"],r["etoiles"],stats,jeu_id),unsafe_allow_html=True)
                show_score(r["score"]);st.markdown("---")

    # ═══════════════════
    # 📆 SAISONNIER — NOUVEAU
    # ═══════════════════
    elif page=="📆 Saisonnier":
        st.markdown("<div class='main-header'>📆 Analyse Saisonnière</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Quels numéros sont favorisés selon le mois ?</div>",unsafe_allow_html=True)

        mois_noms={1:"Janvier",2:"Février",3:"Mars",4:"Avril",5:"Mai",6:"Juin",
                   7:"Juillet",8:"Août",9:"Septembre",10:"Octobre",11:"Novembre",12:"Décembre"}

        if stats["saison"]:
            mois_choisi=st.selectbox("Mois",list(stats["saison"].keys()),format_func=lambda x:mois_noms.get(x,f"Mois {x}"))
            if mois_choisi in stats["saison"]:
                sm=stats["saison"][mois_choisi]
                st.info(f"📅 {mois_noms.get(mois_choisi,'')} : {sm['nb_tirages']} tirages dans l'historique")
                st.subheader(f"🔥 Numéros stars de {mois_noms.get(mois_choisi,'')}")
                for n,freq in sm["top"]:
                    st.markdown(f"**N°{n}** — sorti **{freq} fois** en {mois_noms.get(mois_choisi,'')}")

                # Comparaison tous les mois pour un numéro
                st.subheader("📊 Profil mensuel d'un numéro")
                num_s=st.number_input("Numéro",1,jeu["boules_max"],7)
                cols_b=[f"boule_{i}"for i in range(1,6)]
                mois_freq={}
                for m in range(1,13):
                    if "mois" in df.columns:
                        dfm=df[df["mois"]==m]
                        count=0
                        for _,r in dfm.iterrows():
                            if num_s in[int(r[c])for c in cols_b]:count+=1
                        mois_freq[mois_noms.get(m,"")]=count

                if mois_freq:
                    fig_m=go.Figure(go.Bar(x=list(mois_freq.keys()),y=list(mois_freq.values()),
                        marker_color=["#ef4444"if v==max(mois_freq.values())else"#3b82f6"for v in mois_freq.values()]))
                    fig_m.update_layout(height=350,title=f"N°{num_s} — Sorties par mois")
                    st.plotly_chart(fig_m,use_container_width=True)
        else:
            st.warning("Données saisonnières insuffisantes")

    # ═══════════════════
    # 📈 TENDANCE GLISSANTE — NOUVEAU
    # ═══════════════════
    elif page=="📈 Tendance Glissante":
        st.markdown("<div class='main-header'>📈 Tendance Glissante</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Moving Average — visualise l'évolution dans le temps</div>",unsafe_allow_html=True)

        num_t=st.number_input("Numéro à analyser",1,jeu["boules_max"],7)
        fenetre=st.slider("Fenêtre glissante (tirages)",10,100,30)
        cols_b=[f"boule_{i}"for i in range(1,6)]

        # Calculer la fréquence glissante
        presences=[]
        for idx,row in df.iterrows():
            p=1 if num_t in[int(row[c])for c in cols_b]else 0
            presences.append({"idx":idx,"date":row["date"],"present":p})

        if presences:
            dfp=pd.DataFrame(presences)
            dfp["ma"]=dfp["present"].rolling(window=fenetre,min_periods=1).mean()*100
            dfp["date"]=pd.to_datetime(dfp["date"])

            fig_ma=go.Figure()
            fig_ma.add_trace(go.Scatter(x=dfp["date"],y=dfp["ma"],mode="lines",name=f"MA {fenetre}",
                line=dict(color="#3b82f6",width=2)))
            freq_theorique=5/jeu["boules_max"]*100
            fig_ma.add_hline(y=freq_theorique,line_dash="dash",line_color="#ef4444",
                annotation_text=f"Théorique: {freq_theorique:.1f}%")
            fig_ma.update_layout(height=400,title=f"N°{num_t} — Fréquence glissante ({fenetre} tirages)",
                xaxis_title="Date",yaxis_title="Fréquence (%)")
            st.plotly_chart(fig_ma,use_container_width=True)

            # Interprétation
            last_ma=dfp["ma"].iloc[0]
            if last_ma>freq_theorique*1.3:
                st.markdown(f"<div class='success-card'>🔥 Le N°{num_t} est <b>au-dessus</b> de sa fréquence théorique ({last_ma:.1f}% vs {freq_theorique:.1f}%) → En forme !</div>",unsafe_allow_html=True)
            elif last_ma<freq_theorique*0.7:
                st.markdown(f"<div class='alert-card'>🧊 Le N°{num_t} est <b>en-dessous</b> de sa fréquence théorique ({last_ma:.1f}% vs {freq_theorique:.1f}%) → Candidat retour ?</div>",unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='insight-card'>→ Le N°{num_t} est dans la norme ({last_ma:.1f}% vs {freq_theorique:.1f}%)</div>",unsafe_allow_html=True)

    # ═══════════════════
    # ⏳ RETARD PRÉDIT — NOUVEAU
    # ═══════════════════
    elif page=="⏳ Retard Prédit":
        st.markdown("<div class='main-header'>⏳ Retard Prédit</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Estimation du nombre de tirages avant la prochaine sortie</div>",unsafe_allow_html=True)

        # Tableau des retards
        retards=sorted(stats["boules"].values(),key=lambda x:x["retard_predit"])
        
        st.subheader("🔴 Retard ≤ 0 (\"en retard\")")
        en_retard=[s for s in retards if s["retard_predit"]<=0]
        if en_retard:
            for s in en_retard:
                st.markdown(f"🔴 **N°{s['numero']}** — Écart: {s['ecart']} (moy: {s['ecart_moy']}) — **\"en retard\" de {abs(s['retard_predit'])} tirages** — P={s['proba']}%")
        else:
            st.info("Aucun numéro en retard")

        st.subheader("🟡 Retard 1-3 (\"bientôt attendu\")")
        bientot=[s for s in retards if 1<=s["retard_predit"]<=3]
        for s in bientot:
            st.markdown(f"🟡 **N°{s['numero']}** — Encore ~{s['retard_predit']} tirages estimés — Écart: {s['ecart']}/{s['ecart_moy']}")

        st.subheader("🟢 Retard > 3 (\"pas encore attendu\")")
        pas_encore=[s for s in retards if s["retard_predit"]>3][:10]
        for s in pas_encore:
            st.markdown(f"🟢 N°{s['numero']} — ~{s['retard_predit']} tirages restants — Écart: {s['ecart']}/{s['ecart_moy']}")

        st.markdown("---")
        st.markdown("<div class='insight-card'>💡 Le <b>retard prédit</b> = écart moyen − écart actuel. Si négatif, le numéro a dépassé son écart moyen historique. <b>Ce n'est pas une prédiction fiable</b> — chaque tirage est indépendant.</div>",unsafe_allow_html=True)

        if st.button("🎯 Grille avec les numéros en retard",type="primary"):
            r=gen_grille(jeu_id,stats,"retard",True,True,True,True)
            st.markdown(html_grille(r["grille"],r["etoiles"],stats,jeu_id),unsafe_allow_html=True)
            show_score(r["score"])

    # ═══════════════════
    # 💰 BUDGET — NOUVEAU
    # ═══════════════════
    elif page=="💰 Budget":
        st.markdown("<div class='main-header'>💰 Planificateur Budget</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Optimise tes grilles selon ton budget</div>",unsafe_allow_html=True)

        budget=st.number_input("💶 Ton budget (€)",min_value=jeu["prix"],max_value=100.0,value=10.0,step=jeu["prix"])
        nb_possible=int(budget/jeu["prix"])
        st.info(f"Avec **{budget}€**, tu peux jouer **{nb_possible} grilles** à {jeu['prix']}€")

        strategie=st.selectbox("Stratégie de répartition",[
            "🎯 Toutes identiques (même mode)",
            "🔀 Mix diversifié (plusieurs modes)",
            "🏆 Optimisation maximale"])

        if st.button("💰 PLANIFIER",type="primary",use_container_width=True):
            grilles=[]
            if strategie.startswith("🎯"):
                mode_budget=st.session_state.get("last_mode","optimal")
                for _ in range(nb_possible):
                    r=gen_grille(jeu_id,stats,mode_budget,True,True,True,True)
                    grilles.append(r)
            elif strategie.startswith("🔀"):
                modes=["chaud","froid","probabiliste","tendance","optimal"]
                for i in range(nb_possible):
                    m=modes[i%len(modes)]
                    r=gen_grille(jeu_id,stats,m,True,True,True,True)
                    grilles.append(r)
            else:
                # Top score
                candidates=[]
                for _ in range(nb_possible*5):
                    r=gen_grille(jeu_id,stats,"optimal",True,True,True,True)
                    candidates.append(r)
                candidates.sort(key=lambda x:x["score"]["total"],reverse=True)
                grilles=candidates[:nb_possible]

            st.subheader(f"📋 {len(grilles)} grilles pour {budget}€")

            # Analyse de couverture
            tous_nums=set()
            for r in grilles:tous_nums|=set(r["grille"])
            couverture=len(tous_nums)/jeu["boules_max"]*100

            c1,c2,c3=st.columns(3)
            c1.metric("Grilles",len(grilles))
            c2.metric("Couverture",f"{couverture:.0f}%",f"{len(tous_nums)}/{jeu['boules_max']} numéros")
            c3.metric("Score moyen",f"{np.mean([r['score']['total']for r in grilles]):.0f}/100")

            for i,r in enumerate(grilles):
                gs=" — ".join(str(n)for n in r["grille"])
                es=f" | ⭐{' — '.join(str(e)for e in r['etoiles'])}"if r["etoiles"]else""
                st.markdown(f"**G{i+1}** `{gs}{es}` — Score: {r['score']['total']} — Mode: {r['mode']}")

    # ═══════════════════
    # 📱 CHECKER — NOUVEAU
    # ═══════════════════
    elif page=="📱 Checker":
        st.markdown("<div class='main-header'>📱 Checker de Résultat</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Entre le tirage du soir et vérifie toutes tes grilles</div>",unsafe_allow_html=True)

        ti=st.text_input("🎱 Numéros du tirage (5 numéros)",placeholder="3, 17, 28, 34, 45")
        ei=""
        if jeu["nb_etoiles"]:
            ei=st.text_input("⭐ Étoiles",placeholder="2, 11")

        if ti:
            tirage=sorted(set(int(n.strip())for n in ti.split(",")if n.strip().isdigit()))
            etoiles_t=sorted(set(int(n.strip())for n in ei.split(",")if n.strip().isdigit()))if ei else[]

            if len(tirage)==5:
                st.markdown(html_grille(tirage,etoiles_t,stats,jeu_id),unsafe_allow_html=True)

                if st.session_state.gg:
                    st.subheader(f"📋 Vérification de {len(st.session_state.gg)} grilles sauvegardées")
                    resultats=[]
                    for i,g in enumerate(st.session_state.gg):
                        communs=set(g["g"])&set(tirage)
                        etoiles_ok=set(g.get("e",[]))&set(etoiles_t)if etoiles_t else set()
                        resultats.append({"idx":i+1,"grille":g["g"],"bons":len(communs),
                            "communs":sorted(communs),"etoiles_ok":len(etoiles_ok),"mode":g["m"]})

                    resultats.sort(key=lambda x:x["bons"],reverse=True)

                    for r in resultats:
                        if r["bons"]>=4:emoji="🎉🎉"
                        elif r["bons"]==3:emoji="🎉"
                        elif r["bons"]==2:emoji="👍"
                        else:emoji="—"
                        e_str=f" + {r['etoiles_ok']}⭐"if etoiles_t else""
                        st.markdown(f"{emoji} **G{r['idx']}** `{r['grille']}` → **{r['bons']}/5 bons** {list(r['communs'])}{e_str} ({r['mode']})")

                    best=max(resultats,key=lambda x:x["bons"])
                    if best["bons"]>=3:
                        st.balloons()
                        st.markdown(f"<div class='success-card'>🎉 Meilleur résultat : <b>{best['bons']}/5</b> avec la grille G{best['idx']} !</div>",unsafe_allow_html=True)
                else:
                    st.info("Aucune grille sauvegardée. Génère des grilles d'abord !")
            else:
                st.warning(f"5 numéros requis ({len(tirage)} saisis)")

    # ═══════════════════
    # 🎰 MONTE CARLO — NOUVEAU
    # ═══════════════════
    elif page=="🎰 Monte Carlo":
        st.markdown("<div class='main-header'>🎰 Simulation Monte Carlo</div>",unsafe_allow_html=True)
        st.markdown("<div class='sub-header'>Simule des milliers de tirages pour évaluer une stratégie</div>",unsafe_allow_html=True)

        mode_mc=st.selectbox("Stratégie",["aleatoire","chaud","optimal","probabiliste","retard"])
        nb_sim=st.selectbox("Simulations",[100,500,1000,5000],index=1)
        budget_mc=st.number_input("Budget total (€)",10.0,1000.0,50.0,step=10.0)
        nb_grilles_mc=int(budget_mc/jeu["prix"])

        if st.button("🎰 SIMULER",type="primary",use_container_width=True):
            with st.spinner(f"⏳ {nb_sim} simulations..."):
                bilans=[]
                meilleur_rang=[]
                for sim in range(nb_sim):
                    grilles_sim=[gen_grille(jeu_id,stats,mode_mc)for _ in range(nb_grilles_mc)]
                    # Simuler un tirage aléatoire
                    tirage_sim=sorted(random.sample(range(1,jeu["boules_max"]+1),5))
                    best_match=0
                    for g in grilles_sim:
                        match=len(set(g["grille"])&set(tirage_sim))
                        best_match=max(best_match,match)
                    gt={0:0,1:0,2:0,3:4,4:50,5:5000}
                    gain=gt.get(best_match,0)
                    bilans.append(gain-budget_mc)
                    meilleur_rang.append(best_match)

            st.subheader("📊 Résultats")
            c1,c2,c3,c4=st.columns(4)
            c1.metric("Simulations",nb_sim)
            c2.metric("Bilan moyen",f"{np.mean(bilans):+.2f}€")
            c3.metric("Meilleur",f"{max(bilans):+.2f}€")
            c4.metric("Pire",f"{min(bilans):+.2f}€")

            dist_rangs=Counter(meilleur_rang)
            fig_mc=go.Figure(go.Bar(x=[f"{k} bons"for k in sorted(dist_rangs)],y=[dist_rangs[k]for k in sorted(dist_rangs)],
                marker_color=["#ef4444","#f97316","#f59e0b","#84cc16","#22c55e","#15803d"]))
            fig_mc.update_layout(height=350,title="Meilleur résultat par simulation")
            st.plotly_chart(fig_mc,use_container_width=True)

            fig_hist=go.Figure(go.Histogram(x=bilans,nbinsx=50,marker_color="#3b82f6"))
            fig_hist.add_vline(x=0,line_color="red",line_dash="dash")
            fig_hist.update_layout(height=300,title="Distribution des bilans",xaxis_title="€")
            st.plotly_chart(fig_hist,use_container_width=True)

            pct_positif=sum(1 for b in bilans if b>0)/len(bilans)*100
            st.markdown(f"<div class='insight-card'>📊 **{pct_positif:.1f}%** des simulations sont positives. En moyenne, tu {'gagnes' if np.mean(bilans)>0 else 'perds'} **{abs(np.mean(bilans)):.2f}€** par session.</div>",unsafe_allow_html=True)

    # ═══════════════════
    # 🔗 COUVERTURE — NOUVEAU
    # ═══════════════════
    elif page=="🔗 Couverture":
        st.markdown("<div class='main-header'>🔗 Couverture Multi-Grilles</div>",unsafe_allow_html=True)

        if st.session_state.gg:
            grilles=[g["g"]for g in st.session_state.gg]
            tous=set()
            for g in grilles:tous|=set(g)

            st.metric("Grilles générées",len(grilles))
            st.metric("Numéros couverts",f"{len(tous)}/{jeu['boules_max']}",f"{len(tous)/jeu['boules_max']*100:.0f}%")

            # Fréquence de chaque numéro dans les grilles
            freq_grilles=Counter()
            for g in grilles:
                for n in g:freq_grilles[n]+=1

            # Heatmap de couverture
            nc=10;nr=(jeu["boules_max"]+nc-1)//nc;zd=[]
            for row in range(nr):
                zr=[]
                for col in range(nc):
                    n=row*nc+col+1
                    if n<=jeu["boules_max"]:zr.append(freq_grilles.get(n,0))
                    else:zr.append(None)
                zd.append(zr)
            fh=go.Figure(data=go.Heatmap(z=zd,colorscale=[[0,"#f8fafc"],[.5,"#3b82f6"],[1,"#1e3a5f"]],showscale=True))
            for row in range(nr):
                for col in range(nc):
                    n=row*nc+col+1
                    if n<=jeu["boules_max"]:
                        color="white"if freq_grilles.get(n,0)>0 else"#94a3b8"
                        fh.add_annotation(x=col,y=row,text=str(n),showarrow=False,font=dict(color=color,size=14))
            fh.update_layout(height=350,title="Couverture des numéros",margin=dict(l=20,r=20,t=40,b=20),xaxis=dict(showticklabels=False),yaxis=dict(showticklabels=False))
            st.plotly_chart(fh,use_container_width=True)

            # Trous
            manquants=sorted(set(range(1,jeu["boules_max"]+1))-tous)
            if manquants:
                st.warning(f"⚠️ {len(manquants)} numéros non couverts : {manquants[:20]}{'...'if len(manquants)>20 else''}")
        else:
            st.info("Génère des grilles d'abord !")

    # ═══════════════════
    # COMPARATEUR
    # ═══════════════════
    elif page=="🆚 Comparateur":
        st.markdown("<div class='main-header'>🆚 Comparateur</div>",unsafe_allow_html=True)
        nbt=st.selectbox("Tirages",[20,50,100],index=1)
        if st.button("🆚 GO",type="primary",use_container_width=True):
            with st.spinner("⏳..."):
                comp={}
                for m in["aleatoire","chaud","froid","optimal","probabiliste","tendance","retard"]:
                    comp[m]=backtest(df,jeu_id,stats,m,nbt)
            cd=[{"Mode":m,"Misé":f"{r['mise']}€","Gagné":f"{r['gains']}€","Bilan":f"{r['bilan']:+.2f}€",
                "≥3":sum(r["resultats"][str(i)]for i in range(3,6))}for m,r in comp.items()]
            st.dataframe(pd.DataFrame(cd),hide_index=True,use_container_width=True)

    # ═══════════════════
    # BACKTEST
    # ═══════════════════
    elif page=="🧪 Backtest":
        st.markdown("<div class='main-header'>🧪 Backtest</div>",unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1:m=st.selectbox("Mode",["aleatoire","chaud","froid","optimal","probabiliste","tendance","retard"])
        with c2:nt=st.selectbox("Tirages",[20,50,100,200],index=1)
        if st.button("🚀",type="primary",use_container_width=True):
            with st.spinner("⏳"):rb=backtest(df,jeu_id,stats,m,nt)
            c1,c2,c3=st.columns(3);c1.metric("💰",f"{rb['mise']}€");c2.metric("🏆",f"{rb['gains']}€");c3.metric("📈",f"{rb['bilan']:+.2f}€")
            res=rb["resultats"]
            fig=go.Figure(go.Bar(x=[f"{k}"for k in sorted(res)],y=[res[k]for k in sorted(res)],marker_color=["#ef4444","#f97316","#f59e0b","#84cc16","#22c55e","#15803d"]))
            fig.update_layout(height=300);st.plotly_chart(fig,use_container_width=True)
            for h in rb["hist"][:10]:st.markdown(f"📅 **{h['date']}** — `{h['grille']}` vs `{h['tirage']}` — **{h['bons']}** — {h['gain']}€")

    # ═══════════════════
    # RÉDUCTEUR
    # ═══════════════════
    elif page=="🧮 Réducteur":
        st.markdown("<div class='main-header'>🧮 Réducteur</div>",unsafe_allow_html=True)
        ni=st.text_input("🔢 Numéros (6-15)",placeholder="3,7,14,19,23,28,34,41")
        if ni:
            nums=sorted(set(int(n.strip())for n in ni.split(",")if n.strip().isdigit()and 1<=int(n.strip())<=jeu["boules_max"]))
            if len(nums)>=6:
                if st.button("🧮 GO",type="primary",use_container_width=True):
                    grs=reducteur(nums)
                    st.info(f"💰 {len(grs)}×{jeu['prix']}€ = **{len(grs)*jeu['prix']:.2f}€**")
                    for i,g in enumerate(grs):st.markdown(f"<div class='grille-container'><b>G{i+1}</b>&nbsp;&nbsp;{'&nbsp;&nbsp;'.join(f'<span class=\"boule\">{b}</span>'for b in g)}</div>",unsafe_allow_html=True)

    # ═══════════════════
    # HALL OF FAME
    # ═══════════════════
    elif page=="🏆 Hall of Fame":
        st.markdown("<div class='main-header'>🏆 Hall of Fame</div>",unsafe_allow_html=True)
        if st.session_state.gg:
            sg=sorted(st.session_state.gg,key=lambda x:x["s"],reverse=True)
            st.metric("Total",len(sg));st.metric("Top",f"{sg[0]['s']}/100")
            for i,g in enumerate(sg[:20]):
                md="🥇"if i==0 else("🥈"if i==1 else("🥉"if i==2 else f"#{i+1}"))
                gs=" — ".join(str(n)for n in g["g"])
                es=f" | ⭐{' — '.join(str(e)for e in g['e'])}"if g["e"]else""
                st.markdown(f"{md} **{g['s']}/100** — `{gs}{es}` — {g['m']} — {g['t']}")
            if st.button("🗑️"):st.session_state.gg=[];st.rerun()
        else:st.info("Génère des grilles !")

    # ═══════════════════
    # DEBUG
    # ═══════════════════
    elif page=="🔍 Debug":
        st.markdown("<div class='main-header'>🔍 Debug</div>",unsafe_allow_html=True)
        if dbg:
            if dbg.get("succes"):st.success(f"✅ {dbg.get('nb_tirages','?')}")
            else:st.error(dbg.get("erreur","?"))
            if"colonnes"in dbg:
                for i,c in enumerate(dbg["colonnes"][:15]):st.markdown(f"`{i}` → **{c}**")
            if"mapping"in dbg:m=dbg["mapping"];st.success(f"📅{m['date']} 🎱{m['boules']} ⭐{m['etoiles']}")
        st.dataframe(df.head(10),use_container_width=True)

    # ═══════════════════
    # INFO
    # ═══════════════════
    elif page=="ℹ️ Info":
        st.markdown("<div class='main-header'>ℹ️ V5.0</div>",unsafe_allow_html=True)
        st.markdown(f"""
## Nouveautés V5.0

| Module | Description |
|---|---|
| 🔮 **Auto-Suggestion** | L'outil recommande la meilleure stratégie |
| 📆 **Saisonnier** | Analyse par mois/saison |
| 📈 **Tendance Glissante** | Moving average visuelle |
| ⏳ **Retard Prédit** | Estimation prochaine sortie |
| 💰 **Budget** | Optimise selon ton budget |
| 📱 **Checker** | Vérifie tes grilles vs résultat |
| 🎰 **Monte Carlo** | Simulation de milliers de tirages |
| 🔗 **Couverture** | Analyse visuelle des trous |
| ⏳ **Mode Retard** | Génère avec les numéros "en retard" |

**Total : 10 modes × 10 filtres × 10 critères × 17 pages**

{bdg} | {stats['nb_tirages']} tirages

⚠️ Aucune garantie de gain | 🛡️ 09 74 75 13 13
        """)

    st.markdown("<div class='footer-disclaimer'>⚠️ Outil d'analyse — Aucune garantie — 🛡️ <a href='https://www.joueurs-info-service.fr/'>JIS</a> 09 74 75 13 13</div>",unsafe_allow_html=True)

if __name__=="__main__":
    main()
