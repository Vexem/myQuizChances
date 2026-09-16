import pandas as pd
import numpy as np
import math
import os

def analizza_predizione_patente_con_stress(nome_file, n_test_da_analizzare, emivita_giorni, moltiplicatore_ansia):
    try:
        # Caricamento dati dal file Excel[cite: 2]
        df = pd.read_excel(nome_file)

        if df.shape[1] < 2:
            return "Errore: Il file Excel deve avere almeno due colonne (Data e Test)[cite: 2]."

        # Converte la prima colonna in formato Data[cite: 2]
        df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])

        dati_strutturati = []
        for index, row in df.iterrows():
            data_del_test = row.iloc[0]
            # Estrae i punteggi (errori) ignorando le celle vuote nelle colonne successive[cite: 2]
            for valore in row.iloc[1:]:
                if pd.notna(valore) and isinstance(valore, (int, float)):
                    dati_strutturati.append({'data': data_del_test, 'errori': float(valore)})

        if not dati_strutturati:
            return "Errore: Non ho trovato punteggi numerici nel file."

        dati_strutturati.sort(key=lambda x: x['data'])
        ultimi_test = dati_strutturati[-n_test_da_analizzare:]
        n_effettivo = len(ultimi_test)

        data_odierna = ultimi_test[-1]['data']
        k_decay = math.log(2) / emivita_giorni

        pesi = []
        errori = []
        for item in ultimi_test:
            diff_giorni = max(0, (data_odierna - item['data']).days)
            peso = math.exp(-k_decay * diff_giorni)
            pesi.append(peso)
            errori.append(item['errori'])

        pesi_norm = np.array(pesi) / np.sum(pesi)
        lambda_base = np.sum(np.array(errori) * pesi_norm)
        lambda_stress = lambda_base * moltiplicatore_ansia

        def poisson_cdf_3(lam):
            prob = 0.0
            for x in range(4):
                prob += (math.exp(-lam) * (lam**x)) / math.factorial(x)
            return min(100.0, prob * 100)

        return {
            "test_analizzati": n_effettivo,
            "data_rif": data_odierna.strftime('%d/%m/%Y'),
            "lambda_base": lambda_base,
            "lambda_stress": lambda_stress,
            "prob_base": poisson_cdf_3(lambda_base),
            "prob_stress": poisson_cdf_3(lambda_stress)
        }
    except Exception as e:
        return f"Errore durante il calcolo: {e}"

if __name__ == "__main__":
    file_target = 'SCHEMA TEST PATENTE.xlsx' #[cite: 2]

    while True:
        # Pulisce un po' la schermata a ogni giro
        print("\n" + "="*65)
        print("      PREVISIONE ESAME PATENTE - ANALISI PROFESSIONALE      ")
        print("="*65)
        
        if not os.path.exists(file_target):
            print(f"\nERRORE FATALE: Il file '{file_target}' non è nella cartella!")
            print("Assicurati che l'Excel e questo programma siano insieme.")
            input("\nPremi INVIO per uscire...")
            break

        try:
            # --- PARTE NUOVA E PIÙ CHIARA ---
            print("\n--- IMPOSTAZIONI DI ANALISI ---")
            print("INFO: Il 'Peso del Passato' decide quanto contano i vecchi test.")
            print("      7 = equilibrio, 3 = conta solo l'ultimo periodo, 14 = conta tutto lo storico.")

            n_in = input("\n1. Quanti test vuoi guardare? (Premi Invio per analizzarli TUTTI): ")
            n_val = int(n_in) if n_in.strip() != "" else 9999

            emi_in = input("2. Peso del passato: dopo quanti giorni un errore vale la metà? (Default 7): ")
            emi_val = float(emi_in) if emi_in.strip() != "" else 7.0

            ansia_in = input("3. Ansia da esame: quanto ti senti agitata? (1.0 = calma, 1.5 = panico. Default 1.2): ")
            ansia_val = float(ansia_in) if ansia_in.strip() != "" else 1.2

            res = analizza_predizione_patente_con_stress(file_target, n_val, emi_val, ansia_val)

            if isinstance(res, dict):
                print("\n" + "="*65)
                print(f"REPORT AGGIORNATO AL: {res['data_rif']}")
                print("-"*65)
                print(f"Test analizzati     : {res['test_analizzati']}")
                print(f"Media errori (attesa): {res['lambda_base']:.2f}")
                print(f"Media sotto stress   : {res['lambda_stress']:.2f}")
                print("-"*65)
                print(f"🟢 PROBABILITÀ DI PROMOZIONE (RELAX) : {res['prob_base']:.1f}%")
                print(f"🔴 PROBABILITÀ DI PROMOZIONE (ANSIA) : {res['prob_stress']:.1f}%")
                print("="*65)
            else:
                print(res)

        except ValueError:
            print("\nERRORE: Hai inserito un valore non valido. Usa solo numeri.")

        print("\n" + "-"*65)
        scelta = input("Vuoi fare un'altra analisi? (S/N): ").strip().upper()
        if scelta != 'S':
            print("In bocca al lupo per l'esame! Chiusura in corso...")
            break