import numpy as np
import pandas as pd


def window_frequency_frame(
    df,
    max_val,
    picks_per_draw,
    prefix="b",
    windows=(10, 30, 60, 100),
):
    """
    Compare les fréquences observées
    sur plusieurs fenêtres récentes.

    Convention :
    index 0 = tirage le plus récent.
    """

    cols = [
        c
        for c in df.columns
        if c.startswith(prefix)
    ]

    if (
        not cols
        or len(df) == 0
    ):
        return pd.DataFrame()

    matrix = df[
        cols
    ].to_numpy(
        dtype=int
    )

    theoretical_pct = (
        100
        * picks_per_draw
        / max_val
    )

    rows = []

    for n in range(
        1,
        max_val + 1,
    ):
        row = {
            "N°": n,
            "Théorie %": theoretical_pct,
        }

        for window in windows:
            w = max(
                1,
                min(
                    int(window),
                    len(df),
                ),
            )

            pres = np.any(
                matrix[:w] == n,
                axis=1,
            )

            rate = float(
                pres.mean()
                * 100
            )

            row[
                f"W{window} %"
            ] = rate

            row[
                f"W{window} / théorie"
            ] = (
                rate
                / theoretical_pct
                if theoretical_pct > 0
                else 1.0
            )

        rows.append(row)

    return pd.DataFrame(
        rows
    )


def window_signal(
    df,
    max_val,
    picks_per_draw,
    prefix="b",
    short_window=15,
    long_window=60,
):
    """
    Signal descriptif
    court / long.
    """

    frame = window_frequency_frame(
        df=df,
        max_val=max_val,
        picks_per_draw=picks_per_draw,
        prefix=prefix,
        windows=(
            short_window,
            long_window,
        ),
    )

    if frame.empty:
        return frame

    short_col = (
        f"W{short_window} %"
    )

    long_col = (
        f"W{long_window} %"
    )

    denom = frame[
        long_col
    ].replace(
        0,
        np.nan,
    )

    frame[
        "Ratio court/long"
    ] = (
        frame[short_col]
        / denom
    ).fillna(
        1.0
    )

    frame[
        "Delta points"
    ] = (
        frame[short_col]
        - frame[long_col]
    )

    return frame
