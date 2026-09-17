import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analytics.statistics import calc_entropy, get_geometry_score
from core.config import PROFILS
from optimization.portfolio import generate_portfolio
from validation.backtest import summarize_backtest, walk_forward_backtest


def draw_radar_card(grille, stats_b, jeu):
    """Radar descriptif d'une grille. Ce n'est pas une probabilité de gain."""

    if not grille:
        return go.Figure()

    recent = float(
        np.clip(
            np.mean(
                [
                    stats_b[n]["momentum"]
                    for n in grille
                ]
            )
            / 2.0,
            0,
            1,
        )
    )

    anti = (
        sum(
            1
            for n in grille
            if n > 31
        )
        / len(grille)
    )

    entropy = float(
        np.clip(
            calc_entropy(
                grille,
                jeu["b_max"],
            )
            / 3.0,
            0,
            1,
        )
    )

    geo = float(
        np.clip(
            get_geometry_score(
                grille
            )
            / 10.0,
            0,
            1,
        )
    )

    evens = sum(
        1
        for n in grille
        if n % 2 == 0
    )

    parity = (
        1.0
        if evens in (2, 3)
        else max(
            0.0,
            1.0
            - abs(
                evens - 2.5
            )
            / 2.5,
        )
    )

    vals = [
        recent,
        anti,
        entropy,
        geo,
        parity,
        recent,
    ]

    axes = [
        "MOMENTUM",
        "ANTI-PARTAGE",
        "ENTROPIE",
        "GÉO",
        "PARITÉ",
        "MOMENTUM",
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=vals,
            theta=axes,
            fill="toself",
            line=dict(
                color="#fbbf24",
                width=2,
            ),
            fillcolor="rgba(251,191,36,0.35)",
            hovertemplate=(
                "%{theta}: %{r:.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=False,
                range=[0, 1],
            ),
        ),
        showlegend=False,
        height=245,
        margin=dict(
            l=35,
            r=35,
            t=25,
            b=25,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            color="white",
            size=11,
        ),
    )

    return fig


def _balls_html(
    balls,
    extras,
):
    """
    HTML compact.

    Évite que Streamlit interprète
    le HTML comme un bloc de code.
    """

    balls_html = "".join(
        f'<div class="boule">{int(n)}</div>'
        for n in balls
    )

    extras_html = "".join(
        f'<div class="etoile">{int(n)}</div>'
        for n in extras
    )

    return (
        '<div style="'
        'display:flex;'
        'justify-content:center;'
        'align-items:center;'
        'flex-wrap:wrap;'
        'margin:6px 0 14px 0;'
        '">'
        f"{balls_html}"
        '<div style="'
        'width:2px;'
        'height:35px;'
        'background:#334155;'
        'margin:0 15px;'
        '"></div>'
        f"{extras_html}"
        "</div>"
    )


def _mini_grid_html(
    grid,
    max_number,
):
    cells = "".join(
        (
            '<div class="mini-cell active"></div>'
            if n in grid
            else '<div class="mini-cell"></div>'
        )
        for n in range(
            1,
            max_number + 1,
        )
    )

    return (
        '<div class="mini-grid">'
        f"{cells}"
        "</div>"
    )


def _show_portfolio(
    portfolio,
    stats_b,
    jeu,
):
    """
    Affichage du portefeuille.

    Les métriques utilisent les
    composants Streamlit natifs.
    """

    if not portfolio:
        st.info(
            "Aucune grille à afficher."
        )
        return

    for i, item in enumerate(
        portfolio,
        start=1,
    ):

        g = [
            int(n)
            for n in item.get(
                "balls",
                [],
            )
        ]

        extras = [
            int(n)
            for n in item.get(
                "extras",
                [],
            )
        ]

        if not g:
            continue

        st.markdown(
            f"### Grille {i}"
        )

        st.markdown(
            _balls_html(
                g,
                extras,
            ),
            unsafe_allow_html=True,
        )

        left, right = st.columns(
            [
                1.05,
                1.15,
            ],
            gap="large",
        )

        # ------------------------------------
        # Radar
        # ------------------------------------

        with left:

            st.plotly_chart(
                draw_radar_card(
                    g,
                    stats_b,
                    jeu,
                ),
                use_container_width=True,
                key=(
                    f"v39_radar_"
                    f"{jeu['nom']}_"
                    f"{i}"
                ),
            )

        # ------------------------------------
        # Métriques
        # ------------------------------------

        with right:

            evens = sum(
                1
                for n in g
                if n % 2 == 0
            )

            above_31 = sum(
                1
                for n in g
                if n > 31
            )

            m1, m2 = st.columns(
                2
            )

            m3, m4 = st.columns(
                2
            )

            m1.metric(
                "Somme",
                str(
                    sum(g)
                ),
            )

            m2.metric(
                "Score stratégie",
                (
                    f"{float(item.get('score', 0.0)):.0f}"
                    "/100"
                ),
            )

            m3.metric(
                "Pair / Impair",
                (
                    f"{evens}/"
                    f"{len(g) - evens}"
                ),
            )

            m4.metric(
                "N° > 31",
                (
                    f"{above_31}/"
                    f"{len(g)}"
                ),
            )

            st.caption(
                "Ticket"
            )

            st.markdown(
                _mini_grid_html(
                    set(g),
                    jeu["b_max"],
                ),
                unsafe_allow_html=True,
            )

        st.caption(
            "Le score stratégie mesure "
            "l'alignement avec le profil choisi ; "
            "ce n'est pas une probabilité de gain."
        )

        st.divider()


def render_generator(
    jeu,
    stats_b,
    stats_e,
):

    st.markdown(
        (
            "<div class='main-header'>"
            "Générateur Portfolio V39"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    settings_col, result_col = (
        st.columns(
            [
                1,
                2.5,
            ],
            gap="large",
        )
    )

    min_sum = sum(
        range(
            1,
            jeu["nb_b"] + 1,
        )
    )

    max_sum = sum(
        range(
            jeu["b_max"]
            - jeu["nb_b"]
            + 1,
            jeu["b_max"]
            + 1,
        )
    )

    # ========================================
    # PARAMÈTRES
    # ========================================

    with settings_col:

        profile = st.selectbox(
            "Stratégie",
            list(
                PROFILS.keys()
            ),
            key="generator_profile",
        )

        st.caption(
            PROFILS[
                profile
            ]
        )

        nb_grids = st.slider(
            "Grilles",
            1,
            12,
            4,
            1,
            key="generator_nb_grids",
        )

        strength = (
            st.slider(
                "Force de la pondération",
                0,
                100,
                75,
                5,
                key="generator_strength",
            )
            / 100.0
        )

        diversify = st.checkbox(
            "Diversification du portefeuille",
            value=True,
            key="generator_diversify",
        )

        max_overlap = st.slider(
            (
                "Recouvrement max "
                "entre deux grilles"
            ),
            min_value=0,
            max_value=max(
                0,
                jeu["nb_b"] - 1,
            ),
            value=min(
                2,
                max(
                    0,
                    jeu["nb_b"] - 1,
                ),
            ),
            step=1,
            disabled=not diversify,
            key="generator_max_overlap",
        )

        seed = st.number_input(
            "Graine reproductible",
            min_value=0,
            max_value=2_147_483_647,
            value=20_260_917,
            step=1,
            key="generator_seed",
        )

        with st.expander(
            "Filtres combinatoires",
            expanded=False,
        ):

            sum_filter = st.slider(
                "Somme des numéros",
                min_value=min_sum,
                max_value=max_sum,
                value=tuple(
                    jeu[
                        "sum_range"
                    ]
                ),
                key="generator_sum_filter",
            )

            parity_balanced = (
                st.checkbox(
                    (
                        "Parité équilibrée "
                        "(2/3 ou 3/2)"
                    ),
                    value=True,
                    key="generator_parity",
                )
            )

            exclusions = (
                st.multiselect(
                    "Bannir des numéros",
                    options=list(
                        range(
                            1,
                            jeu[
                                "b_max"
                            ]
                            + 1,
                        )
                    ),
                    key=(
                        "generator_"
                        "exclusions"
                    ),
                )
            )

        calculate = st.button(
            "CALCULER LE PORTEFEUILLE",
            type="primary",
            use_container_width=True,
            key="generator_run",
        )

    state_key = (
        f"v39_portfolio_"
        f"{jeu['nom']}"
    )

    # ========================================
    # RÉSULTATS
    # ========================================

    with result_col:

        if calculate:

            try:

                with st.spinner(
                    (
                        "Génération "
                        "du portefeuille..."
                    )
                ):

                    portfolio = (
                        generate_portfolio(
                            jeu=jeu,
                            stats_b=stats_b,
                            stats_e=stats_e,
                            profile=profile,
                            nb_grids=nb_grids,
                            strength=strength,
                            diversify=diversify,
                            sum_filter=sum_filter,
                            parity_balanced=(
                                parity_balanced
                            ),
                            exclusions=(
                                exclusions
                            ),
                            max_overlap=(
                                max_overlap
                            ),
                            seed=int(
                                seed
                            ),
                        )
                    )

                st.session_state[
                    state_key
                ] = portfolio

            except Exception as exc:

                st.session_state.pop(
                    state_key,
                    None,
                )

                st.error(
                    (
                        "Génération impossible : "
                        f"{exc}"
                    )
                )

        portfolio = (
            st.session_state.get(
                state_key
            )
        )

        if portfolio:

            _show_portfolio(
                portfolio,
                stats_b,
                jeu,
            )

        else:

            st.info(
                (
                    "Configure les paramètres "
                    "puis clique sur "
                    "« CALCULER LE PORTEFEUILLE »."
                )
            )


def render_backtest(
    df,
    jid,
    jeu,
    recent_window,
):

    st.markdown(
        (
            "<div class='main-header'>"
            "Backtest Walk-Forward — V39"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    st.caption(
        (
            "Chaque tirage testé est simulé "
            "comme s'il était encore inconnu : "
            "le moteur n'utilise que les tirages "
            "plus anciens. "
            "La baseline aléatoire reçoit "
            "les mêmes filtres combinatoires."
        )
    )

    min_train = max(
        40,
        int(
            recent_window
        )
        + 10,
    )

    available_depth = (
        len(df)
        - min_train
    )

    if available_depth < 5:

        st.warning(
            (
                f"Il faut au moins "
                f"{min_train + 5} tirages "
                "pour lancer un backtest utile "
                "avec cette fenêtre récente."
            )
        )

        return

    max_depth = min(
        100,
        available_depth,
    )

    settings_col, result_col = (
        st.columns(
            [
                1,
                2.2,
            ],
            gap="large",
        )
    )

    # ========================================
    # PARAMÈTRES BACKTEST
    # ========================================

    with settings_col:

        profile = st.selectbox(
            "Stratégie",
            list(
                PROFILS.keys()
            ),
            key="bt_profile",
        )

        depth = st.slider(
            "Tirages testés",
            5,
            max_depth,
            min(
                40,
                max_depth,
            ),
            1,
            key="bt_depth",
        )

        tickets = st.slider(
            "Tickets par tirage",
            1,
            10,
            3,
            1,
            key="bt_tickets",
        )

        strength = (
            st.slider(
                "Force pondération",
                0,
                100,
                75,
                5,
                key="bt_strength",
            )
            / 100.0
        )

        use_sum = st.checkbox(
            (
                "Appliquer la plage "
                "de somme"
            ),
            value=True,
            key="bt_use_sum",
        )

        use_parity = st.checkbox(
            (
                "Appliquer la parité "
                "équilibrée"
            ),
            value=True,
            key="bt_use_parity",
        )

        seed = st.number_input(
            "Graine backtest",
            min_value=0,
            max_value=2_147_483_647,
            value=39_039,
            step=1,
            key="bt_seed",
        )

        run = st.button(
            "LANCER LE BACKTEST",
            type="primary",
            use_container_width=True,
            key="bt_run",
        )

    state_key = (
        f"v39_backtest_"
        f"{jid}"
    )

    # ========================================
    # RÉSULTATS BACKTEST
    # ========================================

    with result_col:

        if run:

            with st.spinner(
                "Backtest walk-forward..."
            ):

                try:

                    bt = (
                        walk_forward_backtest(
                            df=df,
                            jid=jid,
                            profile=profile,
                            depth=depth,
                            tickets_per_draw=(
                                tickets
                            ),
                            recent_window=(
                                recent_window
                            ),
                            strength=strength,
                            use_sum_filter=(
                                use_sum
                            ),
                            use_parity=(
                                use_parity
                            ),
                            seed=int(
                                seed
                            ),
                        )
                    )

                    st.session_state[
                        state_key
                    ] = bt

                except Exception as exc:

                    st.session_state.pop(
                        state_key,
                        None,
                    )

                    st.error(
                        (
                            "Backtest interrompu : "
                            f"{exc}"
                        )
                    )

        bt = (
            st.session_state.get(
                state_key
            )
        )

        if (
            not isinstance(
                bt,
                pd.DataFrame,
            )
            or bt.empty
        ):

            st.info(
                (
                    "Configure le test puis "
                    "clique sur "
                    "« LANCER LE BACKTEST »."
                )
            )

            return

        summary = (
            summarize_backtest(
                bt
            )
        )

        if not summary:

            st.warning(
                (
                    "Aucun résumé disponible "
                    "pour ce backtest."
                )
            )

            return

        # ------------------------------------
        # KPIs
        # ------------------------------------

        m1, m2, m3, m4 = (
            st.columns(
                4
            )
        )

        m1.metric(
            "Moy. meilleur ticket",
            (
                f"{summary['avg_strategy']:.3f} "
                "boules"
            ),
        )

        m2.metric(
            "Baseline aléatoire",
            (
                f"{summary['avg_random']:.3f} "
                "boules"
            ),
        )

        m3.metric(
            "Delta stratégie",
            (
                f"{summary['delta']:+.3f}"
            ),
            delta=(
                "IC95% "
                f"[{summary['ci_low']:+.2f}; "
                f"{summary['ci_high']:+.2f}]"
            ),
        )

        m4.metric(
            "≥ 3 boules",
            (
                f"{summary['rate3_strategy']:.1f}%"
            ),
            delta=(
                "random "
                f"{summary['rate3_random']:.1f}%"
            ),
        )

        # ------------------------------------
        # DISTRIBUTION DES HITS
        # ------------------------------------

        counts = pd.DataFrame(
            {
                "Hits": list(
                    range(
                        jeu["nb_b"]
                        + 1
                    )
                ),
                "Stratégie": [
                    int(
                        (
                            bt[
                                "strat_b"
                            ]
                            == i
                        ).sum()
                    )
                    for i
                    in range(
                        jeu["nb_b"]
                        + 1
                    )
                ],
                "Aléatoire": [
                    int(
                        (
                            bt[
                                "random_b"
                            ]
                            == i
                        ).sum()
                    )
                    for i
                    in range(
                        jeu["nb_b"]
                        + 1
                    )
                ],
            }
        )

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=counts[
                    "Hits"
                ],
                y=counts[
                    "Stratégie"
                ],
                name="Stratégie",
            )
        )

        fig.add_trace(
            go.Bar(
                x=counts[
                    "Hits"
                ],
                y=counts[
                    "Aléatoire"
                ],
                name="Aléatoire",
            )
        )

        fig.update_layout(
            barmode="group",
            height=380,
            paper_bgcolor=(
                "rgba(0,0,0,0)"
            ),
            plot_bgcolor=(
                "rgba(0,0,0,0)"
            ),
            font=dict(
                color="white"
            ),
            xaxis_title=(
                "Nombre de boules trouvées "
                "— meilleur ticket"
            ),
            yaxis_title=(
                "Nombre de tirages"
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            key=(
                f"v39_bt_chart_"
                f"{jid}"
            ),
        )

        st.caption(
            (
                f"Composante "
                f"{jeu['extra_label'].lower()} "
                "— moyenne stratégie : "
                f"{summary['extra_strategy']:.3f} ; "
                "baseline : "
                f"{summary['extra_random']:.3f}. "
                "Un delta positif sur un petit "
                "échantillon ne suffit pas à "
                "établir un avantage réel."
            )
        )

        with st.expander(
            "Voir les résultats bruts"
        ):

            st.dataframe(
                bt,
                use_container_width=True,
                hide_index=True,
            )
