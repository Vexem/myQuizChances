import pandas as pd
import numpy as np
import math

def analizza_predizione_patente(nome_file, n_test_da_analizzare=9999, emivita_giorni=7.0):
    try:
        df = pd.read_excel(nome_file)

        if df.shape[1] < 2:
            return "Il file non contiene abbastanza colonne di dati."

        # Assicuriamoci che Pandas capisca che la prima colonna contiene date reali
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])

        # Raggruppiamo ogni singolo test con la sua data di esecuzione
        dati_strutturati = []
        for index, row in df.iterrows():
            data_del_test = row.iloc[0]
            # Iteriamo sui tentativi (dalla seconda colonna in poi)
            for valore in row.iloc[1:]:
                if pd.notna(valore):
                    dati_strutturati.append({'data': data_del_test, 'errori': float(valore)})

        if not dati_strutturati:
            return "Non ci sono test validi nel file."

        # Ordiniamo cronologicamente (dal più vecchio al più recente) e prendiamo gli ultimi 'n'
        dati_strutturati.sort(key=lambda x: x['data'])
        ultimi_test = dati_strutturati[-n_test_da_analizzare:]
        n_effettivo = len(ultimi_test)

        # ---------------------------------------------------------
        # PUNTO 1: DECADIMENTO ESPONENZIALE (MEMORIA E GIORNI)
        # ---------------------------------------------------------
        # Troviamo la data dell'ultimo test per calcolare quanto sono vecchi gli altri
        data_odierna = ultimi_test[-1]['data']
        
        # Calcolo costante di decadimento k in base all'emivita scelta
        k = math.log(2) / emivita_giorni

        pesi = []
        errori = []
        for item in ultimi_test:
            giorni_di_distanza = (data_odierna - item['data']).days
            giorni_di_distanza = max(0, giorni_di_distanza) # Evita errori logici
            
            # Formula del decadimento esponenziale: Peso = e^(-k * giorni_trascorsi)
            peso = math.exp(-k * giorni_di_distanza)
            pesi.append(peso)
            errori.append(item['errori'])

        pesi_norm = np.array(pesi) / np.sum(pesi)
        errori_array = np.array(errori)

        # Lambda è il "Tasso di Errore Atteso", ovvero la nostra Media rigorosamente pesata sul tempo
        lambda_atteso = np.sum(errori_array * pesi_norm)

        # ---------------------------------------------------------
        # PUNTO 2: DISTRIBUZIONE DI POISSON 
        # ---------------------------------------------------------
        # L'esame si passa con 3 o meno errori (0, 1, 2 o 3)
        soglia_errori = 3
        prob_predittiva_poisson = 0.0
        
        # Formula di Poisson: P(X=x) = (e^-lambda * lambda^x) / x!
        # Sommiamo le probabilità individuali di fare 0, 1, 2 e 3 errori
        for x in range(soglia_errori + 1):
            prob_x = (math.exp(-lambda_atteso) * (lambda_atteso**x)) / math.factorial(x)
            prob_predittiva_poisson += prob_x

        prob_predittiva_perc = min(100.0, prob_predittiva_poisson * 100)

        # Calcoli di corredo (Statistica classica)
        test_superati = sum(1 for e in errori_array if e <= soglia_errori)
        perc_storica = (test_superati / n_effettivo) * 100

        return {
            "test_analizzati": n_effettivo,
            "data_riferimento": data_odierna.strftime('%d/%m/%Y'),
            "emivita": emivita_giorni,
            "lambda_atteso": lambda_atteso,
            "test_superati": test_superati,
            "perc_storica": perc_storica,
            "prob_predittiva": prob_predittiva_perc,
        }

    except Exception as e:
        return f"Si è verificato un errore: {e}"

# --- COME UTILIZZARE LO SCRIPT ---
nome_del_file = 'SCHEMA TEST PATENTE.xlsx' 

# Quanti test vuoi guardare in totale? (es. gli ultimi 50)
numero_test = 50 

# Dopo quanti giorni ritieni che un test sia "vecchio la metà"? (es. 7 giorni)
giorni_dimezzamento_memoria = 5.0 

risultati = analizza_predizione_patente(nome_file=nome_del_file, 
                                        n_test_da_analizzare=numero_test, 
                                        emivita_giorni=giorni_dimezzamento_memoria)

# --- STAMPA A SCHERMO ---
if isinstance(risultati, dict):
    sep = "=" * 60
    print(sep)
    print(f"  MODELLO PREDITTIVO AVANZATO (POISSON + TIME DECAY)  ")
    print(sep)
    print(f"Test analizzati    : {risultati['test_analizzati']}")
    print(f"Ultimo test il     : {risultati['data_riferimento']}")
    print(f"Decadimento (metà) : ogni {risultati['emivita']} giorni")
    print("-" * 60)
    print(f"Successi passati   : {risultati['test_superati']} su {risultati['test_analizzati']} ({risultati['perc_storica']:.1f}%)")
    print(f"Errori attesi (λ)  : {risultati['lambda_atteso']:.2f} a scheda")
    print("-" * 60)
    print(f"▶ PROBABILITÀ MATEMATICA DI PATENTE: {risultati['prob_predittiva']:.1f}% ◀")
    print(sep)
else:
    print(risultati)
input("\nPremi INVIO per uscire...")