# ============================================================
# SMART-LOTO — VERSION 39 — MODULAR EVIDENCE ENGINE
# ============================================================
#
# Les tirages restent aléatoires et indépendants.
#
# Les scores, fenêtres, pondérations et optimisations
# sont exploratoires et doivent être évalués
# par backtest walk-forward.
# ============================================================

from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Smart-Loto V39 Evidence",
    page_icon="🧬",
    layout="wide",
)


from analytics.statistics import (
    get_full_stats,
)

from core.config import (
    APP_CSS,
    JEUX,
)

from core.data import (
    demo_archive,
    guess_mapping,
    prepare_archive,
    read_raw_csv,
)

from ui.dashboard import (
    render_anomalies,
    render_clusters,
    render_dashboard,
    render_sums,
    render_windows,
)

from ui.laboratory import (
    render_backtest,
    render_generator,
)


def load_archive_from_sidebar(
    jid,
    jeu,
):
    file = st.sidebar.file_uploader(
        "📥 ARCHIVE CSV (optionnel)",
        type="csv",
    )

    recent_window = st.sidebar.slider(
        "Fenêtre récente",
        10,
        100,
        30,
        5,
    )

    source_label = None
    raw = None

    # ----------------------------------------
    # CSV uploadé manuellement
    # ----------------------------------------

    if file is not None:
        raw = read_raw_csv(
            file.getvalue()
        )

        source_label = (
            f"Upload : {file.name}"
        )

    # ----------------------------------------
    # CSV présent dans GitHub
    # ----------------------------------------

    else:
        data_path = Path(
            jeu["data_file"]
        )

        if data_path.exists():
            raw = read_raw_csv(
                data_path.read_bytes()
            )

            source_label = (
                f"GitHub : {data_path.name}"
            )

    # ----------------------------------------
    # Mode démo
    # ----------------------------------------

    if raw is None:
        df = demo_archive(
            jid
        )

        st.sidebar.warning(
            "MODE DÉMO — aucun CSV trouvé "
            "dans data/ et aucun upload fourni"
        )

        return (
            df,
            recent_window,
        )

    # ----------------------------------------
    # Détection colonnes
    # ----------------------------------------

    (
        guessed_b,
        guessed_e,
        guessed_date,
    ) = guess_mapping(
        raw,
        jeu,
    )

    with st.sidebar.expander(
        "🧭 Mapping CSV",
        expanded=False,
    ):
        st.caption(
            "Vérifie les colonnes détectées. "
            "L'index 0 doit devenir le tirage "
            "le plus récent."
        )

        ball_cols = st.multiselect(
            (
                "Colonnes boules "
                f"({jeu['nb_b']})"
            ),
            list(
                raw.columns
            ),
            default=guessed_b,
            max_selections=jeu[
                "nb_b"
            ],
        )

        extra_options = [
            c
            for c in raw.columns
            if c not in ball_cols
        ]

        extra_cols = st.multiselect(
            (
                f"Colonnes "
                f"{jeu['extra_label'].lower()} "
                f"({jeu['nb_e']})"
            ),
            extra_options,
            default=[
                c
                for c in guessed_e
                if c in extra_options
            ],
            max_selections=jeu[
                "nb_e"
            ],
        )

        date_options = [
            "— aucune —"
        ] + list(
            raw.columns
        )

        default_idx = (
            date_options.index(
                guessed_date
            )
            if guessed_date
            in date_options
            else 0
        )

        date_col_choice = (
            st.selectbox(
                "Colonne date",
                date_options,
                index=default_idx,
            )
        )

        row_order = st.radio(
            "Si aucune date exploitable",
            [
                "Plus récent en premier",
                "Plus ancien en premier",
            ],
        )

    date_col = (
        None
        if date_col_choice
        == "— aucune —"
        else date_col_choice
    )

    df, import_info = (
        prepare_archive(
            raw=raw,
            jeu=jeu,
            ball_cols=ball_cols,
            extra_cols=extra_cols,
            date_col=date_col,
            row_order=row_order,
        )
    )

    st.sidebar.success(
        f"{source_label} — "
        f"{import_info['rows_clean']} "
        "tirages valides"
    )

    if import_info[
        "dropped"
    ]:
        st.sidebar.warning(
            f"{import_info['dropped']} "
            "ligne(s) rejetée(s)"
        )

    return (
        df,
        recent_window,
    )


def main():
    st.markdown(
        APP_CSS,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(
        (
            "<h1 style='"
            "color:#fbbf24;"
            "text-align:center;"
            "'>"
            "🧬 SMART-LOTO V39"
            "</h1>"
        ),
        unsafe_allow_html=True,
    )

    st.sidebar.caption(
        "Evidence Engine modulaire — "
        "analyse descriptive + "
        "stratégies testables"
    )

    # ----------------------------------------
    # Jeu
    # ----------------------------------------

    jid = st.sidebar.selectbox(
        "JEU",
        list(
            JEUX.keys()
        ),
        format_func=lambda x: (
            JEUX[x]["nom"]
        ),
    )

    jeu = JEUX[jid]

    # ----------------------------------------
    # Données
    # ----------------------------------------

    try:
        df, recent_window = (
            load_archive_from_sidebar(
                jid,
                jeu,
            )
        )

    except Exception as exc:
        st.error(
            f"Import impossible : {exc}"
        )
        st.stop()

    # ----------------------------------------
    # Colonnes calculées
    # ----------------------------------------

    bcols = [
        f"b{i}"
        for i in range(
            1,
            jeu["nb_b"] + 1,
        )
    ]

    df = df.copy()

    df[
        "total_sum"
    ] = df[
        bcols
    ].sum(
        axis=1
    )

    # ----------------------------------------
    # Statistiques
    # ----------------------------------------

    stats_b = get_full_stats(
        df,
        jeu["b_max"],
        jeu["nb_b"],
        "b",
        recent_window,
    )

    stats_e = get_full_stats(
        df,
        jeu["e_max"],
        jeu["nb_e"],
        "e",
        recent_window,
    )

    # ----------------------------------------
    # Navigation
    # ----------------------------------------

    menu = st.sidebar.radio(
        "NAVIGATION",
        [
            "📊 Dashboard",
            "🎯 Générateur",
            "➕ Sommes",
            "🧬 Anomalies",
            "🪟 Fenêtres",
            "🔗 Clusters",
            "🧪 Backtest",
        ],
    )

    # ----------------------------------------
    # Pages
    # ----------------------------------------

    if menu == "📊 Dashboard":
        render_dashboard(
            df,
            jeu,
            stats_b,
            stats_e,
        )

    elif menu == "🎯 Générateur":
        render_generator(
            jeu,
            stats_b,
            stats_e,
        )

    elif menu == "➕ Sommes":
        render_sums(
            df,
            jeu,
        )

    elif menu == "🧬 Anomalies":
        render_anomalies(
            df,
            stats_b,
            stats_e,
            jeu,
        )

    elif menu == "🪟 Fenêtres":
        render_windows(
            df,
            jeu,
        )

    elif menu == "🔗 Clusters":
        render_clusters(
            df,
            jeu,
        )

    elif menu == "🧪 Backtest":
        render_backtest(
            df,
            jid,
            jeu,
            recent_window,
        )

    # ----------------------------------------
    # Méthodologie
    # ----------------------------------------

    with st.sidebar.expander(
        "ℹ️ Méthodologie"
    ):
        st.write(
            "V39 sépare les données, "
            "statistiques, fenêtres, "
            "analyse bayésienne, scoring, "
            "optimisation, validation "
            "et interface Streamlit."
        )

        st.write(
            "Le backtest est walk-forward "
            "et évite la fuite d'information. "
            "Les profils servent à construire "
            "et comparer des portefeuilles ; "
            "ils ne garantissent pas une "
            "prédiction du prochain tirage."
        )


if __name__ == "__main__":
    main()
