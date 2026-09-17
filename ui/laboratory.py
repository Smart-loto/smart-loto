import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from analytics.statistics import (
    calc_entropy,
    get_geometry_score,
)

from core.config import PROFILS

from optimization.portfolio import (
    generate_portfolio,
)

from validation.backtest import (
    summarize_backtest,
    walk_forward_backtest,
)


def draw_radar_card(
    grille,
    stats_b,
    jeu,
):
    recent = np.mean(
        [
            stats_b[n]["momentum"]
            for n in grille
        ]
    )

    recent = float(
        np.clip(
            recent / 2.0,
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
        if evens in (
            2,
            3,
        )
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
            line_color="#fbbf24",
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=False,
                range=[
                    0,
                    1,
                ],
            )
        ),
        showlegend=False,
        height=210,
        margin=dict(
            l=30,
            r=30,
            t=20,
            b=20,
        ),
        paper_bgcolor=(
            "rgba(0,0,0,0)"
        ),
        font=dict(
            color="white"
        ),
    )

    return fig


def _show_portfolio(
    portfolio,
    stats_b,
    jeu,
):
    for i, item in enumerate(
        portfolio,
        start=1,
    ):
        g = item[
            "balls"
        ]

        et = item[
            "extras"
        ]

        st.markdown(
            '<div class="result-card">',
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<b>Grille {i}</b>",
            unsafe_allow_html=True,
        )

        b_h = "".join(
            [
                f'<div class="boule">{b}</div>'
                for b in g
            ]
        )

        e_h = "".join(
            [
                f'<div class="etoile">{e}</div>'
                for e in et
            ]
        )

        st.markdown(
            (
                '<div style="display:flex;'
                'justify-content:center;'
                'align-items:center;'
                'flex-wrap:wrap;'
                'margin-bottom:12px;">'
                f'{b_h}'
                '<div style="width:2px;'
                'height:35px;'
                'background:#334155;'
                'margin:0 15px;"></div>'
                f'{e_h}'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        ca1, ca2 = st.columns(
            [
                1,
                1.1,
            ]
        )

        with ca1:
            st.plotly_chart(
                draw_radar_card(
                    g,
                    stats_b,
                    jeu,
                ),
                use_container_width=True,
            )

        with ca2:
            sab = sum(
                1
                for n in g
                if n > 31
            )

            evens = sum(
                1
                for n in g
                if n % 2 == 0
            )

            mini = " ".join(
                [
                    (
                        "<div class='mini-cell "
                        f"{'active' if n in g else ''}"
                        "'></div>"
                    )
                    for n in range(
                        1,
                        jeu["b_max"] + 1,
                    )
                ]
            )

            st.markdown(
                f"""
                <div style="
                    display:grid;
                    grid-template-columns:1fr 1fr;
                    gap:12px;
                ">
                    <div>
                        <small class="metric-title">
                            Somme
                        </small><br>
                        <b class="metric-value">
                            {sum(g)}
                        </b>
                    </div>

                    <div>
                        <small class="metric-title">
                            Score stratégie
                        </small><br>
                        <b class="metric-value">
                            {item['score']:.0f}/100
                        </b>
                    </div>

                    <div>
                        <small class="metric-title">
                            Pair / Impair
                        </small><br>
                        <b class="metric-value">
                            {evens}/{len(g)-evens}
                        </b>
                    </div>

                    <div>
                        <small class="metric-title">
                            N° &gt; 31
                        </small><br>
                        <b class="metric-value">
                            {sab}/{len(g)}
                        </b>
                    </div>

                    <div style="grid-column:1 / span 2">
                        <small class="metric-title">
                            Ticket
                        </small><br>
                        <div class="mini-grid">
                            {mini}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.caption(
            "Le score stratégie mesure "
            "l'alignement avec le profil choisi ; "
            "ce n'est pas une probabilité de gain."
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )


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

    c1, c2 = st.columns(
        [
            1,
            2.5,
        ]
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

    with c1:
        prof = st.selectbox(
            "Stratégie",
            list(
                PROFILS.keys()
            ),
        )

        st.caption(
            PROFILS[prof]
        )

        nb = st.slider(
            "Grilles",
            1,
            12,
            4,
        )

        strength = (
            st.slider(
                "Force de la pondération",
                0,
                100,
                75,
                5,
            )
            / 100
        )

        diversify = st.checkbox(
            "Diversification du portefeuille",
            value=True,
        )

        max_overlap = st.slider(
            "Recouvrement max "
            "entre deux grilles",
            0,
            4,
            2,
            disabled=not diversify,
        )

        seed = st.number_input(
            "Graine reproductible",
            min_value=0,
            max_value=2_147_483_647,
            value=20260917,
            step=1,
        )

        with st.expander(
            "Filtres combinatoires"
        ):
            f_sum = st.slider(
                "Somme des numéros",
                min_sum,
                max_sum,
                jeu["sum_range"],
            )

            f_par = st.checkbox(
                "Parité équilibrée "
                "(2/3 ou 3/2)",
                value=True,
            )

            excl = st.multiselect(
                "Bannir des numéros",
                range(
                    1,
                    jeu["b_max"] + 1,
                ),
            )

        btn = st.button(
            "CALCULER LE PORTEFEUILLE",
            type="primary",
            use_container_width=True,
        )

    with c2:
        if btn:
            try:
                state_key = (
                    f"v39_portfolio_"
                    f"{jeu['nom']}"
                )

                st.session_state[
                    state_key
                ] = generate_portfolio(
                    jeu=jeu,
                    stats_b=stats_b,
                    stats_e=stats_e,
                    profile=prof,
                    nb_grids=nb,
                    strength=strength,
                    diversify=diversify,
                    sum_filter=f_sum,
                    parity_balanced=f_par,
                    exclusions=excl,
                    max_overlap=max_overlap,
                    seed=seed,
                )

            except Exception as exc:
                st.error(
                    str(exc)
                )

        state_key = (
            f"v39_portfolio_"
            f"{jeu['nom']}"
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
        "Chaque tirage testé est simulé "
        "comme s'il était encore inconnu : "
        "le moteur n'utilise que les tirages "
        "plus anciens. La baseline aléatoire "
        "reçoit les mêmes filtres combinatoires."
    )

    min_train = max(
        40,
        int(recent_window) + 10,
    )

    max_depth = max(
        1,
        min(
            100,
            len(df)
            - min_train,
        ),
    )

    if max_depth < 5:
        st.warning(
            f"Il faut au moins "
            f"{min_train + 5} tirages "
            "pour un backtest utile "
            "avec cette fenêtre récente."
        )
        return

    col1, col2 = st.columns(
        [
            1,
            2.2,
        ]
    )

    with col1:
        prof_t = st.selectbox(
            "Stratégie",
            list(
                PROFILS.keys()
            ),
            key="bt_prof",
        )

        depth = st.slider(
            "Tirages testés",
            5,
            max_depth,
            min(
                40,
                max_depth,
            ),
        )

        tickets = st.slider(
            "Tickets par tirage",
            1,
            10,
            3,
        )

        strength_t = (
            st.slider(
                "Force pondération",
                0,
                100,
                75,
                5,
                key="bt_strength",
            )
            / 100
        )

        use_sum = st.checkbox(
            "Appliquer la plage de somme",
            value=True,
        )

        use_par = st.checkbox(
            "Appliquer la parité équilibrée",
            value=True,
        )

        seed_t = st.number_input(
            "Graine backtest",
            min_value=0,
            max_value=2_147_483_647,
            value=39039,
            step=1,
        )

        run = st.button(
            "LANCER LE BACKTEST",
            type="primary",
            use_container_width=True,
        )

    with col2:
        if run:
            with st.spinner(
                "Backtest walk-forward..."
            ):
                try:
                    bt = (
                        walk_forward_backtest(
                            df=df,
                            jid=jid,
                            profile=prof_t,
                            depth=depth,
                            tickets_per_draw=tickets,
                            recent_window=recent_window,
                            strength=strength_t,
                            use_sum_filter=use_sum,
                            use_parity=use_par,
                            seed=seed_t,
                        )
                    )

                except Exception as exc:
                    st.error(
                        "Backtest interrompu : "
                        f"{exc}"
                    )

                    bt = pd.DataFrame()

            state_key = (
                f"v39_backtest_{jid}"
            )

            st.session_state[
                state_key
            ] = bt

        state_key = (
            f"v39_backtest_{jid}"
        )

        bt = st.session_state.get(
            state_key
        )

        if (
            isinstance(
                bt,
                pd.DataFrame,
            )
            and not bt.empty
        ):
            summary = (
                summarize_backtest(
                    bt
                )
            )

            m1, m2, m3, m4 = (
                st.columns(4)
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

            counts = pd.DataFrame(
                {
                    "Hits": list(
                        range(
                            jeu["nb_b"] + 1
                        )
                    ),
                    "Stratégie": [
                        (
                            bt["strat_b"]
                            == i
                        ).sum()
                        for i in range(
                            jeu["nb_b"] + 1
                        )
                    ],
                    "Aléatoire": [
                        (
                            bt["random_b"]
                            == i
                        ).sum()
                        for i in range(
                            jeu["nb_b"] + 1
                        )
                    ],
                }
            )

            fig = go.Figure()

            fig.add_trace(
                go.Bar(
                    x=counts["Hits"],
                    y=counts[
                        "Stratégie"
                    ],
                    name="Stratégie",
                )
            )

            fig.add_trace(
                go.Bar(
                    x=counts["Hits"],
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
                font=dict(
                    color="white"
                ),
                xaxis_title=(
                    "Nombre de boules trouvées "
                    "— meilleur ticket"
                ),
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

            st.caption(
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

            with st.expander(
                "Voir les résultats bruts"
            ):
                st.dataframe(
                    bt,
                    use_container_width=True,
                    hide_index=True,
                )
