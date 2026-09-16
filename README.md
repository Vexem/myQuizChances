# Driving Test Probability Analysis

A desktop application for estimating driving-theory test performance from a quiz history. The application provides Italian and English UI localization, in-app result entry, optional anxiety analysis, charts, automatic local persistence, and Windows packaging.

> The result is an indicative statistical estimate, not a guarantee of the exam outcome.

## Features

- Time-weighted probability analysis.
- Greater relevance for recent tests through exponential decay.
- Poisson model with a three-error passing threshold.
- Optional anxiety multiplier and normal-versus-stress comparison.
- Interactive parameter sliders.
- In-app calendar date picker.
- Scrollable result list with a red delete button per entry.
- Italian and English interface.
- Flag-based language selector.
- Popup analysis report with chart.
- Automatic record and settings persistence.
- Full unit and GUI presentation test suite.
- Windows executable packaging with PyInstaller.

## Requirements

- Windows 10 or newer recommended.
- Python 3.12 recommended.
- PowerShell.
- Python packages: `pandas`, `numpy`, `openpyxl`, `matplotlib`, and `Pillow`.
- `pyinstaller` is required only to build the executable.

## Installation

From the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pandas numpy openpyxl matplotlib Pillow pyinstaller
```

## Run the application

```powershell
.\.venv\Scripts\python.exe patente_gui.py
```

The application has two tabs:

- **Inserisci risultati / Enter results**: enter and manage quiz results.
- **Impostazioni / Settings**: configure the analysis parameters.

## Entering results

1. Select a date with the calendar button.
2. Set the error count with the slider.
3. Press **Aggiungi risultato / Add result**.
4. Repeat for every completed quiz.
5. Press **Analizza risultati inseriti / Analyze entered results**.

The report opens in a centered popup and does not add permanent widgets to the main window.

The visible date format is `DD/MM/YYYY`. Dates are normalized internally to `YYYY-MM-DD` for sorting, storage, and analysis.

Each record is represented internally as:

```python
{"date": "2026-09-16", "errors": 2}
```

The red `x` button next to a record removes only that record. **Svuota elenco / Clear list** removes all records.

When more than ten records are present, the list becomes scrollable.

## Automatic persistence

Records are saved immediately after every addition, single deletion, or clear-all operation. Settings are saved immediately after every slider or anxiety-mode change.

On Windows, the default files are stored outside the repository:

```text
%LOCALAPPDATA%\AnalisiPatente\records.json
%LOCALAPPDATA%\AnalisiPatente\settings.json
```

The storage layer writes through temporary files and atomic replacement to avoid truncated files after an interrupted write. Existing legacy record keys are migrated when read. Corrupt data is reported without silently overwriting the source file.

## Settings

The Settings tab controls:

- **Number of tests**: how many recent date groups are considered.
- **Half-life**: after how many days an old result has half the weight of a recent result.
- **Without anxiety**: uses the standard probability model.
- **With anxiety**: enables the anxiety multiplier and shows the normal-versus-stress comparison.

Settings are restored automatically on the next application start. No Save button is required.

## Statistical model

For each result, the application calculates a time-decay weight:

```text
weight = exp(-decay_rate * days_since_test)
decay_rate = ln(2) / half_life
```

The weighted average error count is the expected error value. The predicted passing probability is the Poisson cumulative probability from zero through three errors:

```text
P(X <= 3) = P(0) + P(1) + P(2) + P(3)
P(X = x) = exp(-lambda) * lambda^x / x!
```

The anxiety scenario multiplies the expected error value before calculating the second probability.

The model does not account for fatigue, question difficulty, exam conditions, or changes in study habits.

## Excel compatibility API

The main GUI does not require external files. Excel support remains available in the core API for compatibility and tests. The expected layout is:

| Date | Quiz 1 | Quiz 2 | Quiz 3 |
|---|---:|---:|---:|
| 2026-05-01 | 2 | 1 | 4 |
| 2026-05-02 | 0 | 3 | 1 |

The first column contains dates. Subsequent columns contain error counts. Blank and non-numeric cells are ignored.

The bundled `SCHEMA TEST PATENTE.xlsx` file is a compatibility dataset, not a requirement for the GUI.

## Project structure

```text
patente_gui.py             Tkinter desktop interface
patente_core.py            English statistical core and Excel compatibility API
patente_storage.py         Atomic local records and settings persistence
test_patente_core.py       Core, storage, GUI, and presentation tests
AnalisiPatente.spec        PyInstaller configuration
SCHEMA TEST PATENTE.xlsx   Compatibility dataset
assets/italy.png           Italian language icon
assets/uk.png              English language icon
.gitignore                 Ignored generated and local files
```

## Tests

Run the complete suite with:

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

The suite covers:

- Excel and in-memory analysis;
- invalid and missing input;
- anxiety calculations;
- record and settings storage round trips;
- corrupt storage and invalid schemas;
- persistence after application restart;
- single-record deletion and clear-all behavior;
- date picker selection;
- language switching;
- anxiety control states;
- popup reports;
- tab centering;
- startup button visibility;
- red delete-button styling;
- scrollbar threshold and presentation geometry.

Compile checks:

```powershell
.\.venv\Scripts\python.exe -m py_compile patente_core.py patente_gui.py patente_storage.py
```

## Build the Windows executable

For a single executable:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name AnalisiPatente --add-data "assets;assets" --add-data "SCHEMA TEST PATENTE.xlsx;." patente_gui.py
```

The output is created at:

```text
dist/AnalisiPatente.exe
```

Generated `build/` and `dist/` folders are excluded from Git.

## Git workflow

```powershell
git status --short --branch
git add -A
git commit -m "describe the change"
git push origin feature/in-app-results-entry
```

Remote repository:

```text
https://github.com/Vexem/myQuizChances
```

## Troubleshooting

### `ModuleNotFoundError`

Use the project virtual environment explicitly:

```powershell
.\.venv\Scripts\python.exe patente_gui.py
```

### The window is not visible

Check whether it opened behind another window. The application centers itself and briefly brings the window to the foreground.

### The saved data cannot be read

The application reports the storage error without silently overwriting the source file. Inspect the files under `%LOCALAPPDATA%\AnalisiPatente` before removing anything.

### The chart does not appear

Verify Matplotlib in the project environment:

```powershell
.\.venv\Scripts\python.exe -c "import matplotlib; print(matplotlib.__version__)"
```

## Data and privacy

Local records are stored outside the repository. Do not publish personal quiz history or other sensitive data to a remote repository.
