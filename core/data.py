# ============================================================
# SMART-LOTO V38/V39
# DATA MANAGEMENT
# ============================================================


import pandas as pd
import io



# ============================================================
# Lecture CSV
# ============================================================


def load_csv(uploaded_file):


    if uploaded_file is None:

        return None



    attempts = [

        {
            "sep": None,
            "engine": "python",
            "encoding": "utf-8-sig"
        },

        {
            "sep": ";",
            "engine": "python",
            "encoding": "utf-8-sig"
        },

        {
            "sep": ",",
            "engine": "python",
            "encoding": "utf-8-sig"
        }

    ]



    last_error = None



    for options in attempts:

        try:

            df = pd.read_csv(
                io.BytesIO(
                    uploaded_file.getvalue()
                ),
                **options
            )


            if df.shape[1] > 1:

                return df


        except Exception as exc:

            last_error = exc



    raise ValueError(
        f"Impossible de lire le fichier CSV : {last_error}"
    )



# ============================================================
# Nettoyage archive
# ============================================================


def clean_archive(df):


    df = df.copy()



    df = df.dropna()



    return df



# ============================================================
# Validation tirage
# ============================================================


def validate_draw(numbers, max_value):


    numbers = list(numbers)



    if len(numbers) != len(set(numbers)):

        return False



    for n in numbers:

        if n < 1 or n > max_value:

            return False



    return True
