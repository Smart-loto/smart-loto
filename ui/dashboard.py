import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from analytics.bayesian import (
    bayesian_rank,
    beta_binomial_summary,
)

from analytics.statistics import (
    normal_two_sided_p,
    pair_analysis,
    stats_frame,
    theoretical_sum_stats,
)

from analytics.windows import (
    window_frequency_frame,
)


def render_dashboard(
    df,
    jeu,
    stats_b,
    stats_e,
):
    st.markdown(
        (
            "<div class='main-header'>"
            f"Evidence Dashboard — {jeu['nom']} V39"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    mu_sum, var_sum = (
        theoretical_sum_stats(
            jeu
        )
    )

    real_mean_sum = float(
        df[
            "total_sum"
        ].mean()
    )

    se_mean = (
        math.sqrt(
            var_sum
            / len(df)
        )
        if len(df)
        else 0.0
    )

    z_mean = (
        (
            real_mean_sum
            - mu_sum
        )
        / se_mean
        if se_mean > 0
        else 0.0
    )

    p_mean = normal_two_sided_p(
        z_mean
    )

    anomalies = sum(
        1
        for s in stats_b.values()
        if s["q"] < 0.05
    )

    c1, c2, c3, c4 = st.columns(
        4
    )

    c1.metric(
        "Archive",
        f"{len(df)} tirages",
    )

    c2.metric(
        "Somme moyenne",
        f"{real_mean_sum:.2f}",
        delta=(
            f"théorie "
            f"{mu_sum:.2f}"
        ),
    )

    c3.metric(
        "Z moyenne des sommes",
        f"{z_mean:.2f}",
        delta=(
            f"p≈{p_mean:.3f}"
        ),
    )

    c4.metric(
        "Anomalies FDR 5%",
        str(anomalies),
        delta=(
            "à examiner"
            if anomalies
            else "aucune détectée"
        ),
    )

    st.caption(
        "Les écarts de fréquence, "
        "retards et scores sont descriptifs. "
        "Ils ne rendent pas le prochain "
        "tirage prédictible."
    )

    analyses = [
        (
            "BOULES",
            stats_b,
            jeu["b_max"],
            jeu["nb_b"],
        ),
        (
            jeu[
                "extra_label"
            ].upper(),
            stats_e,
            jeu["e_max"],
            jeu["nb_e"],
        ),
    ]

    for (
        title,
        s_dict,
        mx,
        picks,
    ) in analyses:

        st.subheader(
            f"Analyse fréquentielle — {title}"
        )

        x = list(
            range(
                1,
                mx + 1,
            )
        )

        y_recent = [
            s_dict[n]["vel"]
            for n in x
        ]

        y_archive = [
            s_dict[n]["heat"]
            for n in x
        ]

        expected_pct = (
            100
            * picks
            / mx
        )

        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[
                0.68,
                0.32,
            ],
        )

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y_recent,
                mode="lines+markers",
                name="Récent",
                line=dict(
                    color="#fbbf24",
                    width=2,
                ),
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y_archive,
                mode="lines",
                name="Archive",
                line=dict(
                    color="#60a5fa",
                    width=1.6,
                ),
            ),
            row=1,
            col=1,
        )

        fig.add_hline(
            y=expected_pct,
            line_dash="dash",
            line_color="#94a3b8",
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Heatmap(
                z=[
                    [
                        s_dict[n]["z"]
                        for n in x
                    ]
                ],
                x=x,
                colorscale="RdBu",
                zmid=0,
                showscale=False,
            ),
            row=2,
            col=1,
        )

        fig.update_layout(
            height=390,
            paper_bgcolor=(
                "rgba(0,0,0,0)"
            ),
            font=dict(
                color="white"
            ),
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10,
            ),
        )

        fig.update_xaxes(
            dtick=(
                5
                if mx > 20
                else 1
            ),
            range=[
                0.5,
                mx + 0.5,
            ],
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )


def render_sums(
    df,
    jeu,
):
    st.markdown(
        (
            "<div class='main-header'>"
            "Analyse des Sommes — V39"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    sums = df[
        "total_sum"
    ]

    mu_sum, var_sum = (
        theoretical_sum_stats(
            jeu
        )
    )

    sigma_sum = math.sqrt(
        var_sum
    )

    last_z = (
        (
            float(
                sums.iloc[0]
            )
            - mu_sum
        )
        / sigma_sum
        if (
            sigma_sum > 0
            and len(sums)
        )
        else 0.0
    )

    col1, col2 = st.columns(
        [
            1,
            2.5,
        ]
    )

    with col1:
        st.metric(
            "Moyenne archive",
            f"{sums.mean():.2f}",
        )

        st.metric(
            "Moyenne théorique",
            f"{mu_sum:.2f}",
        )

        st.metric(
            "Z du dernier tirage",
            f"{last_z:.2f}",
        )

        st.info(
            "Le Z-score mesure l'atypicité "
            "de la somme. Une valeur extrême "
            "ne prédit pas un retour à la "
            "moyenne au tirage suivant."
        )

    with col2:
        fig_gauss = go.Figure()

        fig_gauss.add_trace(
            go.Histogram(
                x=sums,
                nbinsx=35,
                marker_color="#fbbf24",
                opacity=0.65,
                name="Archive",
            )
        )

        fig_gauss.add_vline(
            x=mu_sum,
            line_dash="dash",
            line_color="#60a5fa",
            annotation_text=(
                "Moyenne théorique"
            ),
        )

        fig_gauss.update_layout(
            height=360,
            paper_bgcolor=(
                "rgba(0,0,0,0)"
            ),
            font=dict(
                color="white"
            ),
            margin=dict(
                l=10,
                r=10,
                t=20,
                b=10,
            ),
        )

        st.plotly_chart(
            fig_gauss,
            use_container_width=True,
        )

    st.subheader(
        "Tendance chronologique — "
        "100 derniers tirages"
    )

    recent_sums = (
        sums
        .head(100)
        .iloc[::-1]
        .reset_index(
            drop=True
        )
    )

    fig_trend = go.Figure()

    fig_trend.add_trace(
        go.Scatter(
            y=recent_sums,
            mode="lines",
            line=dict(
                color="#64748b"
            ),
            name="Somme",
        )
    )

    fig_trend.add_trace(
        go.Scatter(
            y=recent_sums.rolling(
                window=5
            ).mean(),
            mode="lines",
            line=dict(
                color="#fbbf24",
                width=3,
            ),
            name="Moyenne mobile 5",
        )
    )

    fig_trend.add_hrect(
        y0=jeu[
            "sum_range"
        ][0],
        y1=jeu[
            "sum_range"
        ][1],
        fillcolor="green",
        opacity=0.08,
    )

    fig_trend.update_layout(
        paper_bgcolor=(
            "rgba(0,0,0,0)"
        ),
        font=dict(
            color="white"
        ),
    )

    st.plotly_chart(
        fig_trend,
        use_container_width=True,
    )


def render_anomalies(
    df,
    stats_b,
    stats_e,
    jeu,
):
    st.markdown(
        (
            "<div class='main-header'>"
            "Audit Fréquentiel & Bayésien — V39"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    st.caption(
        "Le volet FDR compare les fréquences "
        "observées aux fréquences marginales "
        "théoriques. Le volet bayésien applique "
        "un lissage Beta-Binomial centré sur "
        "la probabilité théorique."
    )

    (
        tab_b,
        tab_e,
        tab_bayes_b,
        tab_bayes_e,
    ) = st.tabs(
        [
            "Boules — FDR",
            (
                f"{jeu['extra_label']} "
                "— FDR"
            ),
            "Boules — Bayésien",
            (
                f"{jeu['extra_label']} "
                "— Bayésien"
            ),
        ]
    )

    with tab_b:
        table_b = stats_frame(
            stats_b
        )

        table_b[
            "|Z|"
        ] = table_b[
            "Z"
        ].abs()

        st.dataframe(
            table_b.sort_values(
                [
                    "q FDR",
                    "|Z|",
                ],
                ascending=[
                    True,
                    False,
                ],
            ).drop(
                columns="|Z|"
            ),
            use_container_width=True,
            hide_index=True,
        )

    with tab_e:
        table_e = stats_frame(
            stats_e
        )

        table_e[
            "|Z|"
        ] = table_e[
            "Z"
        ].abs()

        st.dataframe(
            table_e.sort_values(
                [
                    "q FDR",
                    "|Z|",
                ],
                ascending=[
                    True,
                    False,
                ],
            ).drop(
                columns="|Z|"
            ),
            use_container_width=True,
            hide_index=True,
        )

    with tab_bayes_b:
        prior_b = st.slider(
            "Force du prior — boules",
            2,
            100,
            20,
            2,
            key="bayes_prior_b",
        )

        bayes_b = (
            beta_binomial_summary(
                df,
                jeu["b_max"],
                jeu["nb_b"],
                prefix="b",
                prior_strength=prior_b,
            )
        )

        st.dataframe(
            bayesian_rank(
                bayes_b
            ).round(3),
            use_container_width=True,
            hide_index=True,
        )

    with tab_bayes_e:
        prior_e = st.slider(
            (
                "Force du prior — "
                f"{jeu['extra_label'].lower()}"
            ),
            2,
            100,
            20,
            2,
            key="bayes_prior_e",
        )

        bayes_e = (
            beta_binomial_summary(
                df,
                jeu["e_max"],
                jeu["nb_e"],
                prefix="e",
                prior_strength=prior_e,
            )
        )

        st.dataframe(
            bayesian_rank(
                bayes_e
            ).round(3),
            use_container_width=True,
            hide_index=True,
        )


def render_windows(
    df,
    jeu,
):
    st.markdown(
        (
            "<div class='main-header'>"
            "Analyse Multi-Fenêtres — V39"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    windows = st.multiselect(
        "Fenêtres à comparer",
        options=[
            10,
            15,
            20,
            30,
            40,
            60,
            80,
            100,
            150,
            200,
        ],
        default=[
            10,
            30,
            60,
            100,
        ],
    )

    if not windows:
        st.warning(
            "Sélectionne au moins "
            "une fenêtre."
        )
        return

    tab_b, tab_e = st.tabs(
        [
            "Boules",
            jeu["extra_label"],
        ]
    )

    analyses = [
        (
            tab_b,
            "b",
            jeu["b_max"],
            jeu["nb_b"],
        ),
        (
            tab_e,
            "e",
            jeu["e_max"],
            jeu["nb_e"],
        ),
    ]

    for (
        tab,
        prefix,
        max_val,
        picks,
    ) in analyses:

        with tab:
            frame = (
                window_frequency_frame(
                    df=df,
                    max_val=max_val,
                    picks_per_draw=picks,
                    prefix=prefix,
                    windows=tuple(
                        windows
                    ),
                )
            )

            if frame.empty:
                st.info(
                    "Aucune donnée exploitable."
                )
                continue

            pct_cols = [
                f"W{w} %"
                for w in windows
            ]

            matrix = frame[
                pct_cols
            ].to_numpy().T

            fig = go.Figure(
                data=go.Heatmap(
                    z=matrix,
                    x=frame["N°"],
                    y=[
                        f"W{w}"
                        for w in windows
                    ],
                    colorscale="Viridis",
                    colorbar=dict(
                        title="Fréq. %"
                    ),
                )
            )

            fig.update_layout(
                height=max(
                    320,
                    90
                    + 65
                    * len(windows),
                ),
                paper_bgcolor=(
                    "rgba(0,0,0,0)"
                ),
                font=dict(
                    color="white"
                ),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            st.dataframe(
                frame.round(3),
                use_container_width=True,
                hide_index=True,
            )


def render_clusters(
    df,
    jeu,
):
    st.markdown(
        (
            "<div class='main-header'>"
            "Cooccurrences & Affinités — V39"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    (
        matrix,
        lift,
        expected_pair,
    ) = pair_analysis(
        df,
        jeu,
    )

    st.caption(
        f"Chaque paire aurait environ "
        f"{expected_pair:.2f} occurrences "
        "attendues sous un tirage uniforme. "
        "Le lift corrige les fréquences "
        "marginales."
    )

    (
        tab1,
        tab2,
        tab3,
    ) = st.tabs(
        [
            "Matrice brute",
            "Lift ajusté",
            "Paires & partenaires",
        ]
    )

    with tab1:
        fig = go.Figure(
            data=go.Heatmap(
                z=matrix,
                colorscale="Inferno",
            )
        )

        fig.update_layout(
            height=650,
            paper_bgcolor=(
                "rgba(0,0,0,0)"
            ),
            font=dict(
                color="white"
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with tab2:
        fig = go.Figure(
            data=go.Heatmap(
                z=lift,
                colorscale="RdBu",
                zmid=1,
            )
        )

        fig.update_layout(
            height=650,
            paper_bgcolor=(
                "rgba(0,0,0,0)"
            ),
            font=dict(
                color="white"
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

    with tab3:
        pairs = []

        for i in range(
            jeu["b_max"]
        ):
            for j in range(
                i + 1,
                jeu["b_max"],
            ):
                if matrix[
                    i,
                    j,
                ] > 0:
                    pairs.append(
                        {
                            "Paire": (
                                f"{i + 1} "
                                f"+ {j + 1}"
                            ),
                            "Occurrences": int(
                                matrix[
                                    i,
                                    j,
                                ]
                            ),
                            "Lift": round(
                                float(
                                    lift[
                                        i,
                                        j,
                                    ]
                                ),
                                2,
                            ),
                        }
                    )

        pairs_df = pd.DataFrame(
            pairs
        )

        c1, c2 = st.columns(
            2
        )

        with c1:
            st.subheader(
                "Top sur-affinités"
            )

            if not pairs_df.empty:
                st.dataframe(
                    pairs_df.sort_values(
                        [
                            "Lift",
                            "Occurrences",
                        ],
                        ascending=[
                            False,
                            False,
                        ],
                    ).head(15),
                    use_container_width=True,
                    hide_index=True,
                )

        with c2:
            st.subheader(
                "Partenaire d'un numéro"
            )

            n_s = st.selectbox(
                "Numéro",
                range(
                    1,
                    jeu["b_max"] + 1,
                ),
            )

            idx = n_s - 1

            partner_rows = [
                {
                    "Partenaire": j + 1,
                    "Occurrences": int(
                        matrix[
                            idx,
                            j,
                        ]
                    ),
                    "Lift": round(
                        float(
                            lift[
                                idx,
                                j,
                            ]
                        ),
                        2,
                    ),
                }
                for j in range(
                    jeu["b_max"]
                )
                if (
                    j != idx
                    and matrix[
                        idx,
                        j,
                    ] > 0
                )
            ]

            if partner_rows:
                partners_df = (
                    pd.DataFrame(
                        partner_rows
                    )
                    .sort_values(
                        [
                            "Lift",
                            "Occurrences",
                        ],
                        ascending=[
                            False,
                            False,
                        ],
                    )
                    .head(12)
                )

                st.dataframe(
                    partners_df,
                    use_container_width=True,
                    hide_index=True,
                )

            else:
                st.info(
                    "Aucun partenaire "
                    "observé dans l'archive."
                )

        st.caption(
            "Une cooccurrence élevée est "
            "descriptive : elle ne démontre "
            "pas une dépendance exploitable "
            "sur les tirages futurs."
        )
