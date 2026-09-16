# ============================================================
# SMART-LOTO V38
# MULTI WINDOW ANALYSIS
# ============================================================


import pandas as pd



# ============================================================
# Extraction fréquence fenêtre
# ============================================================


def frequency_window(
        df,
        numbers,
        window,
        prefix="b"
):


    if window is None:

        sample = df

    else:

        sample = df.head(window)



    counts = {
        n:0
        for n in numbers
    }



    cols = [
        c for c in sample.columns
        if c.startswith(prefix)
    ]



    for col in cols:

        values = sample[col].values


        for value in values:

            value = int(value)

            if value in counts:

                counts[value]+=1



    return counts



# ============================================================
# Toutes les fenêtres
# ============================================================


def calculate_multi_windows(
        df,
        numbers,
        windows,
        prefix="b"
):


    result = {

        n:{}

        for n in numbers

    }



    for name, size in windows.items():


        frequencies = frequency_window(

            df,

            numbers,

            size,

            prefix

        )



        max_freq = max(
            frequencies.values()
        ) if frequencies else 1



        for n in numbers:


            result[n][name] = {

                "frequency":
                    frequencies[n],

                "normalized":

                    frequencies[n]
                    /
                    max_freq

                    if max_freq

                    else 0

            }



    return result



# ============================================================
# Fusion multi horizons
# ============================================================


def combine_windows(
        window_data,
        weights=None
):


    if weights is None:

        weights = {

            "court_terme":0.40,

            "moyen_terme":0.30,

            "long_terme":0.20,

            "historique":0.10

        }



    scores = {}



    for number, data in window_data.items():


        score = 0



        for name, values in data.items():


            score += (

                values["normalized"]

                *

                weights.get(
                    name,
                    0
                )

            )



        scores[number] = score



    return scores
