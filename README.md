# Analisi Patente

Applicazione desktop per stimare la probabilita di superare l'esame di teoria della patente a partire dallo storico dei quiz. Il progetto include una GUI in italiano e inglese, analisi base, simulazione dello stress, grafico della distribuzione degli errori e packaging Windows.

> La stima e un supporto statistico orientativo, non una garanzia del risultato d'esame.

## Funzionalita

- Analisi probabilistica dello storico dei quiz.
- Peso maggiore ai test recenti tramite decadimento esponenziale.
- Modello di Poisson con soglia di superamento impostata a 3 errori.
- Scenario con ansia tramite moltiplicatore delle difficolta.
- Selezione dei parametri tramite barre interattive.
- Selezione della data tramite calendario popup interno.
- Grafico della distribuzione degli errori.
- Interfaccia in italiano e inglese.
- Selettore lingua con icone delle bandiere.
- Test automatici del motore e dei principali componenti GUI.
- Eseguibile Windows generabile con PyInstaller.
- Inserimento diretto dei risultati nell'app senza caricare file esterni.
- Salvataggio automatico locale dopo ogni modifica.
- Ripristino automatico dei risultati all'avvio.
- Cancellazione manuale di una singola entry o dell'intero elenco.
- Pulsante `x` rosso accanto a ogni entry per la cancellazione diretta.
- Impostazioni ripristinate automaticamente all'avvio successivo.

## Requisiti

- Windows 10 o superiore consigliato.
- Python 3.12 consigliato.
- PowerShell.
- Un file Excel `.xlsx` con lo storico dei quiz.

Le dipendenze principali sono:

- `pandas`
- `numpy`
- `openpyxl`
- `matplotlib`
- `Pillow`
- `pyinstaller` per creare l'eseguibile

## Installazione

Dalla cartella del progetto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pandas numpy openpyxl matplotlib Pillow pyinstaller
```

Se il virtual environment esiste gia, basta attivarlo:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Avvio della GUI

Con il virtual environment attivo:

```powershell
python patente_gui.py
```

In alternativa, senza attivare l'ambiente:

```powershell
.\.venv\Scripts\python.exe patente_gui.py
```

L'applicazione si apre con due schede:

- **Inserisci risultati**: registra i risultati della sessione direttamente nell'app.
- **Impostazioni** / **Settings**: configura numero di test, emivita e valutazione ansia.

La scheda Impostazioni/Settings serve solo a cambiare le impostazioni. Non permette di inserire percorsi o caricare file: usa esclusivamente i risultati aggiunti nella scheda Inserisci risultati.

## Inserimento senza file

La scheda **Inserisci risultati** e una proposta alternativa al caricamento di Excel pensata per essere compatibile anche con una futura app Android:

1. inserisci la data del test;
2. seleziona il numero di errori con la barra interattiva;
3. premi **Aggiungi risultato**;
4. ripeti per tutti i test della sessione;
5. premi **Analizza risultati inseriti** per aprire il report in una finestra popup.

Nella scheda **Impostazioni** / **Settings** puoi scegliere:

- **Senza ansia**: calcolo standard;
- **Con ansia**: calcolo standard e confronto con il moltiplicatore di ansia scelto. Quando e deselezionato, il cursore e le relative indicazioni diventano grigi e non interagibili.

Il pulsante **Analizza risultati inseriti** resta nella scheda Inserisci risultati e apre il report in un popup dedicato.

La data si seleziona dal pulsante calendario: puoi cambiare mese con le frecce, scegliere un giorno oppure usare il pulsante **Oggi**. Il campo mostra il formato italiano `GG/MM/AAAA`; internamente il valore viene normalizzato in `YYYY-MM-DD` per storage e calcoli.

I record sono rappresentati internamente in forma semplice:

```python
{"data": "2026-09-16", "errori": 2}
```

Il motore di analisi riceve una lista di questi record tramite `analizza_predizione_records`. Questo separa l'inserimento dall'analisi: in futuro Android potra sostituire la schermata Tkinter mantenendo lo stesso contratto dati e lo stesso motore statistico. Durante l'esecuzione i record restano in memoria e vengono sincronizzati automaticamente con lo storage locale.

### Persistenza locale

I record non vengono persi chiudendo l'applicazione. Dopo ogni aggiunta, cancellazione singola o svuotamento dell'elenco, l'app salva automaticamente i dati in JSON:

```text
%LOCALAPPDATA%\AnalisiPatente\records.json
```

Il salvataggio usa un file temporaneo e una sostituzione atomica, per evitare di lasciare un archivio parzialmente scritto in caso di interruzione. All'avvio il file viene ricaricato automaticamente. Se il contenuto non e leggibile, l'app mostra un errore e non sovrascrive il file danneggiato.

La cancellazione e sempre esplicita: la `x` rossa accanto a una entry elimina solo quella entry, mentre **Svuota elenco** elimina tutti i risultati salvati.

Anche i parametri della scheda **Impostazioni** / **Settings** vengono salvati automaticamente in:

```text
%LOCALAPPDATA%\AnalisiPatente\settings.json
```

Sono persistiti il numero di test, l'emivita, la modalita ansia e il relativo moltiplicatore. Non serve un pulsante Salva.

## Utilizzo della GUI

### Formato Excel compatibile del motore

Il caricamento Excel resta disponibile nelle API del motore per compatibilita e test, ma non fa parte del flusso principale della GUI. Il file deve avere una struttura a righe:

| Data | Quiz 1 | Quiz 2 | Quiz 3 |
|---|---:|---:|---:|
| 2026-05-01 | 2 | 1 | 4 |
| 2026-05-02 | 0 | 3 | 1 |

- La prima colonna contiene la data del gruppo di test.
- Le colonne successive contengono il numero di errori.
- Le celle vuote e i valori non numerici vengono ignorati.
- Le righe con date non valide vengono ignorate.
- Il dataset di compatibilita incluso nel progetto e `SCHEMA TEST PATENTE.xlsx`.

### Parametri

#### Numero di test

Definisce quante righe recenti considerare. Un valore maggiore usa uno storico piu ampio e generalmente produce una stima piu stabile.

#### Emivita in giorni

Indica dopo quanti giorni il peso statistico di un test si dimezza:

- valore basso: privilegia molto i test recenti;
- valore alto: conserva piu influenza dello storico;
- il valore mostrato nella GUI e espresso in giorni interi.

#### Moltiplicatore ansia

Disponibile nella scheda **Impostazioni** / **Settings** quando viene selezionato **Con ansia**:

- `1.0`: condizioni normali;
- `1.2`: stress moderato;
- `1.5`: stress elevato.

Il moltiplicatore aumenta il numero di errori attesi nel modello di stress.

## Modello statistico

### Decadimento temporale

Per ogni test viene calcolato un peso in base alla distanza dall'ultimo test:

```text
peso = exp(-k * giorni trascorsi)
k = ln(2) / emivita
```

I pesi vengono normalizzati e usati per calcolare la media pesata degli errori, indicata nel risultato come `lambda`.

### Distribuzione di Poisson

La probabilita stimata di superamento e la probabilita di ottenere da 0 a 3 errori secondo una distribuzione di Poisson:

```text
P(X <= 3) = P(0) + P(1) + P(2) + P(3)
P(X = x) = exp(-lambda) * lambda^x / x!
```

La soglia di 3 errori e definita in `SOGLIA_ERRORI` dentro `patente_core.py`.

### Interpretazione

- **Probabilita predittiva**: stima matematica basata sul valore `lambda` recente.
- **Percentuale storica**: quota di test con 3 errori o meno.
- **Errori attesi**: media pesata degli errori.
- **Scenario ansia**: stessa stima dopo aver moltiplicato gli errori attesi per il fattore scelto.

Il modello non considera fattori come stanchezza reale, difficolta specifica delle domande, condizioni dell'esame o cambiamenti nel metodo di studio.

## Struttura del progetto

```text
patente_gui.py             Interfaccia desktop Tkinter
patente_core.py            Calcoli, record in memoria, Excel e distribuzione errori
patente_storage.py         Persistenza locale atomica dei record
test_patente_core.py       Suite di test automatici
AnalisiPatente.spec        Configurazione PyInstaller
SCHEMA TEST PATENTE.xlsx   Dataset Excel predefinito
assets/italy.png           Icona lingua italiana
assets/uk.png              Icona lingua inglese
.gitignore                 File esclusi dal versionamento
```

## Test

Esegui la suite completa usando lo stesso ambiente della GUI:

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

La suite verifica:

- risultati dell'analisi base;
- applicazione del limite ai test recenti;
- celle non valide e righe non valide;
- file mancanti e dataset privi di punteggi;
- distribuzione degli errori, inclusa la categoria `4+`;
- modello con ansia;
- gestione dell'emivita non valida;
- presenza degli slider GUI;
- menu lingua e cambio italiano/inglese.
- salvataggio e caricamento dei record;
- archivio mancante o corrotto;
- persistenza dopo riavvio dell'app;
- cancellazione di una singola entry;
- popup dei risultati e modalita ansia.

Controllo sintattico:

```powershell
.\.venv\Scripts\python.exe -m py_compile patente_core.py patente_gui.py
```

## Creazione dell'eseguibile Windows

Per una build con cartella di distribuzione:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --name AnalisiPatente --add-data "assets;assets" --add-data "SCHEMA TEST PATENTE.xlsx;." patente_gui.py
```

Per un singolo file `.exe`:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name AnalisiPatente --add-data "assets;assets" --add-data "SCHEMA TEST PATENTE.xlsx;." patente_gui.py
```

Il risultato viene creato in:

```text
dist/AnalisiPatente.exe
```

`build/` e `dist/` sono artefatti generati e sono esclusi da Git.

## Git e sviluppo

Verifica lo stato:

```powershell
git status --short --branch
```

Esegui test e compilazione prima di un commit:

```powershell
.\.venv\Scripts\python.exe -m unittest -q
.\.venv\Scripts\python.exe -m py_compile patente_core.py patente_gui.py
```

Commit consigliato:

```powershell
git add -A
git commit -m "docs: add project documentation"
git push origin main
```

Repository remoto attuale:

```text
https://github.com/Vexem/myQuizChances
```

## Risoluzione problemi

### `ModuleNotFoundError`

Il comando e stato eseguito con un interprete diverso dal virtual environment. Usa sempre:

```powershell
.\.venv\Scripts\python.exe patente_gui.py
```

### La finestra non compare

Controlla che il processo non sia gia aperto dietro VS Code o in un altro desktop virtuale. La GUI centra la finestra e la porta temporaneamente in primo piano all'avvio.

### Il grafico non appare

Verifica che `matplotlib` sia installato nel venv:

```powershell
.\.venv\Scripts\python.exe -c "import matplotlib; print(matplotlib.__version__)"
```

### Il file Excel non viene letto

Controlla che:

- il file esista;
- sia un `.xlsx` leggibile;
- la prima colonna contenga date valide;
- almeno una colonna successiva contenga numeri.

## Licenza e dati

Il repository contiene dataset Excel locali usati per il funzionamento e la verifica dell'applicazione. Verifica di avere il diritto di condividere eventuali dati reali prima di pubblicarli su un repository remoto.
