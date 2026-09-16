import math
from pathlib import Path

import numpy as np
import pandas as pd

SOGLIA_ERRORI = 3


def _load_excel_rows(nome_file):
    path = Path(nome_file)
    if not path.exists():
        raise FileNotFoundError(f"File non trovato: {nome_file}")

    df = pd.read_excel(path, header=None)
    if df.empty:
        raise ValueError("Il file Excel è vuoto.")

    if df.shape[1] < 2:
        raise ValueError("Il file Excel deve contenere almeno due colonne: Data e risultati dei test.")

    rows = []
    for _, row in df.iterrows():
        if row.empty:
            continue

        try:
            data_del_test = pd.to_datetime(row.iloc[0])
        except (TypeError, ValueError):
            continue

        valori = []
        for valore in row.iloc[1:]:
            if pd.isna(valore):
                continue
            try:
                numero = float(valore)
            except (TypeError, ValueError):
                continue
            valori.append(numero)

        if not valori:
            continue

        rows.append({"data": data_del_test, "errori": valori})

    if not rows:
        raise ValueError("Non ho trovato dati numerici nel file Excel.")

    return rows


def _estrai_ultimi_test(dati, n_test_da_analizzare):
    dati_ordinati = sorted(dati, key=lambda x: x["data"])
    ultimi_test = dati_ordinati[-n_test_da_analizzare:]
    eventi = []
    for item in ultimi_test:
        for errore in item["errori"]:
            eventi.append({"data": item["data"], "errori": float(errore)})
    return eventi


def _poisson_cdf_3(lam):
    prob = 0.0
    for x in range(SOGLIA_ERRORI + 1):
        prob += (math.exp(-lam) * (lam ** x)) / math.factorial(x)
    return min(100.0, prob * 100)


def analizza_predizione_patente(nome_file, n_test_da_analizzare=9999, emivita_giorni=7.0):
    try:
        dati = _load_excel_rows(nome_file)
        eventi = _estrai_ultimi_test(dati, n_test_da_analizzare)
        if not eventi:
            return "Non ci sono test validi nel file."

        dati_strutturati = sorted(eventi, key=lambda x: x["data"])
        data_odierna = dati_strutturati[-1]["data"]
        k = math.log(2) / emivita_giorni

        pesi = []
        errori = []
        for item in dati_strutturati:
            giorni_di_distanza = max(0, (data_odierna - item["data"]).days)
            peso = math.exp(-k * giorni_di_distanza)
            pesi.append(peso)
            errori.append(item["errori"])

        if not pesi or sum(pesi) == 0:
            return "I pesi calcolati sono tutti nulli. Verifica i dati o il valore dell'emivita."

        pesi_norm = np.array(pesi, dtype=float) / np.sum(pesi)
        errori_array = np.array(errori, dtype=float)
        lambda_atteso = float(np.sum(errori_array * pesi_norm))

        prob_predittiva_poisson = _poisson_cdf_3(lambda_atteso)
        test_superati = int(sum(1 for e in errori_array if e <= SOGLIA_ERRORI))
        perc_storica = (test_superati / len(errori_array)) * 100

        return {
            "test_analizzati": len(errori_array),
            "data_riferimento": data_odierna.strftime("%d/%m/%Y"),
            "emivita": emivita_giorni,
            "lambda_atteso": lambda_atteso,
            "test_superati": test_superati,
            "perc_storica": perc_storica,
            "prob_predittiva": prob_predittiva_poisson,
        }
    except Exception as e:
        return f"Si è verificato un errore: {e}"


def distribuzione_errori(nome_file, n_test_da_analizzare=50):
    dati = _load_excel_rows(nome_file)
    eventi = _estrai_ultimi_test(dati, n_test_da_analizzare)
    distribuzione = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    for item in eventi:
        errore = int(item["errori"])
        if errore >= 4:
            distribuzione[4] += 1
        else:
            distribuzione[errore] = distribuzione.get(errore, 0) + 1
    return distribuzione


def analizza_predizione_patente_con_stress(nome_file, n_test_da_analizzare, emivita_giorni, moltiplicatore_ansia):
    try:
        dati = _load_excel_rows(nome_file)
        eventi = _estrai_ultimi_test(dati, n_test_da_analizzare)
        if not eventi:
            return "Errore: non ho trovato punteggi numerici nel file."

        dati_strutturati = sorted(eventi, key=lambda x: x["data"])
        data_odierna = dati_strutturati[-1]["data"]
        k_decay = math.log(2) / emivita_giorni

        pesi = []
        errori = []
        for item in dati_strutturati:
            diff_giorni = max(0, (data_odierna - item["data"]).days)
            peso = math.exp(-k_decay * diff_giorni)
            pesi.append(peso)
            errori.append(item["errori"])

        pesi_norm = np.array(pesi, dtype=float) / np.sum(pesi)
        lambda_base = float(np.sum(np.array(errori, dtype=float) * pesi_norm))
        lambda_stress = lambda_base * moltiplicatore_ansia

        prob_base = _poisson_cdf_3(lambda_base)
        prob_stress = _poisson_cdf_3(lambda_stress)

        return {
            "test_analizzati": len(errori),
            "data_rif": data_odierna.strftime("%d/%m/%Y"),
            "lambda_base": lambda_base,
            "lambda_stress": lambda_stress,
            "prob_base": prob_base,
            "prob_stress": prob_stress,
        }
    except Exception as e:
        return f"Errore durante il calcolo: {e}"
