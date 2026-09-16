import sqlite3
import json
import os
import sys
from pathlib import Path

# Percorsi del database per diverse piattaforme
DB_PATHS = {
    "win32": r"C:\ProgramData\GOG.com\Galaxy\storage\galaxy-2.0.db",
    "darwin": os.path.expanduser("~/Library/Application Support/GOG.com/Galaxy/storage/galaxy-2.0.db"),
    "linux": os.path.expanduser("~/.local/share/GOG.com/Galaxy/storage/galaxy-2.0.db"),
}

OUTPUT_FILE = "lista_giochi_gog.txt"
DEBUG = True  # Cambia a False per disabilitare i messaggi di debug

def estrai_giochi_gog(db_path=None, output_file=OUTPUT_FILE):
    if db_path is None:
        db_path = DB_PATHS.get(sys.platform, DB_PATHS["win32"])
    
    if not os.path.exists(db_path):
        print(f"Errore: Database non trovato in {db_path}.")
        print(f"Sistema operativo rilevato: {sys.platform}")
        print("Modifica la variabile 'db_path' o il dizionario DB_PATHS se necessario.")
        return

    print(f"🔍 Connessione al database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    titoli_estratti = set()
    righe_elaborate = 0
    errori_parsing = 0

    try:
        cursor.execute("SELECT value FROM GamePieces")
        rows = cursor.fetchall()
        
        if DEBUG:
            print(f"📊 Righe totali in GamePieces: {len(rows)}")
        
        for row in rows:
            righe_elaborate += 1
            try:
                dati = json.loads(row[0])
                
                if 'title' in dati:
                    titolo = dati['title']
                    if titolo:  # Ignora i titoli None o vuoti
                        titoli_estratti.add(titolo)
                        if DEBUG and righe_elaborate % 5000 == 0:  # Mostra ogni 5000 righe
                            print(f"✓ Ultima riga ({righe_elaborate}): {titolo}")
            except (json.JSONDecodeError, TypeError):
                errori_parsing += 1
                continue
                
    except sqlite3.Error as e:
        print(f"❌ Errore SQLite: {e}")
        return
    finally:
        conn.close()

    if DEBUG:
        print(f"📈 Righe elaborate: {righe_elaborate}, Errori parsing: {errori_parsing}")
        print(f"📊 Titoli unici trovati: {len(titoli_estratti)}")

    if not titoli_estratti:
        print("⚠️ Nessun titolo trovato. La struttura del database potrebbe essere stata aggiornata.")
        return

    with open(output_file, "w", encoding="utf-8") as f:
        for titolo in sorted(titoli_estratti):
            f.write(f"{titolo}\n")
            
    print(f"✅ Estrazione completata! Trovati {len(titoli_estratti)} giochi unici.")
    print(f"📄 Salvato in: '{os.path.abspath(output_file)}'")

if __name__ == "__main__":
    estrai_giochi_gog()