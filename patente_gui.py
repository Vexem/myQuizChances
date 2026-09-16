import os
import calendar
import tkinter as tk
from datetime import date
from pathlib import Path
from tkinter import messagebox, ttk

from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from patente_core import (
    analizza_predizione_records,
    analizza_predizione_records_con_stress,
    distribuzione_errori_records,
)


class PatentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Analisi Patente")
        self.geometry("900x680")
        self.minsize(850, 620)
        self.configure(bg="#0b1220")
        self._center_window()
        self.after(100, self._focus_window)

        self.records = []
        self.language = "it"
        self.translations = {
            "it": {
                "title": "Analisi probabilistica esame patente", "entry": "Inserisci risultati", "base": "Base", "stress": "Con ansia", "english": "English",
                "tests": "Numero di test da considerare", "tests_help": "Più alto è il numero, più lo storico è ampio. Il valore indica quanti test recenti includere.",
                "half": "Emivita in giorni", "half_help": "Indica dopo quanti giorni un test vecchio perde metà della sua rilevanza. Valori bassi privilegiano i test recenti.",
                "anxiety": "Moltiplicatore ansia", "anxiety_help": "1.0 indica condizioni normali; valori superiori simulano un peggioramento delle prestazioni sotto stress.",
                "calculate": "Calcola probabilità", "calculate_stress": "Calcola con ansia", "waiting": "In attesa dei risultati", "start": "Avvia un'analisi per visualizzare una stima.",
                "chart": "Distribuzione degli errori negli ultimi test", "errors": "Numero di errori", "occurrences": "Occorrenze", "no_chart": "Nessun grafico disponibile per questo file.",
                "error": "Analisi non disponibile", "normal": "Scenario tranquillo", "stress_scenario": "Scenario ansia", "updated": "Aggiornato al", "analyzed": "Analizzati",
                "entry_date": "Data del test", "entry_errors": "Errori commessi", "add": "Aggiungi risultato", "remove": "Rimuovi selezionato", "clear": "Svuota elenco", "analyze_entries": "Analizza risultati inseriti", "entry_help": "I risultati restano nell'app durante questa sessione e non richiedono file esterni.", "saved_results": "Risultati inseriti", "no_entries": "Inserisci almeno un risultato.",
                "today": "Oggi", "previous_month": "Mese precedente", "next_month": "Mese successivo", "calendar": "Apri calendario",
                "session_help": "Queste analisi usano i risultati inseriti nella scheda Inserisci risultati.", "session_count": "risultati disponibili", "go_to_entry": "Vai a Inserisci risultati",
            },
            "en": {
                "title": "Driving test probability analysis", "entry": "Enter results", "base": "Standard", "stress": "With anxiety", "english": "Italiano",
                "tests": "Number of tests to include", "tests_help": "A higher number gives a broader history. This is the number of recent tests included.",
                "half": "Half-life in days", "half_help": "After this many days, an old test has half its relevance. Lower values favor recent tests.",
                "anxiety": "Anxiety multiplier", "anxiety_help": "1.0 means normal conditions; higher values simulate performance loss under stress.",
                "calculate": "Calculate probability", "calculate_stress": "Calculate with anxiety", "waiting": "Waiting for results", "start": "Run an analysis to see an estimate.",
                "chart": "Error distribution in recent tests", "errors": "Number of errors", "occurrences": "Occurrences", "no_chart": "No chart is available for this file.",
                "error": "Analysis unavailable", "normal": "Calm scenario", "stress_scenario": "Anxiety scenario", "updated": "Updated on", "analyzed": "Analyzed",
                "entry_date": "Test date", "entry_errors": "Mistakes made", "add": "Add result", "remove": "Remove selected", "clear": "Clear list", "analyze_entries": "Analyze entered results", "entry_help": "Results stay inside the app during this session and do not require external files.", "saved_results": "Entered results", "no_entries": "Add at least one result.",
                "today": "Today", "previous_month": "Previous month", "next_month": "Next month", "calendar": "Open calendar",
                "session_help": "These analyses use the results entered in the Enter results tab.", "session_count": "results available", "go_to_entry": "Go to Enter results",
            },
        }
        self._apply_theme()

        self.container = ttk.Frame(self, padding=18)
        self.container.pack(fill="both", expand=True)
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(1, weight=1)
        container = self.container

        self.header_bar = ttk.Frame(container)
        self.header_bar.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        self.header_bar.columnconfigure(0, weight=1)

        self.header = ttk.Label(
            self.header_bar,
            text=self.t("title"),
            font=("Segoe UI", 18, "bold"),
            foreground="#e2e8f0",
            background="#0b1220",
        )
        self.header.grid(row=0, column=0, sticky="w")

        self._build_language_selector()

        self.notebook = ttk.Notebook(container)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        self._build_entry_tab()
        self._build_base_tab()
        self._build_stress_tab()

    def t(self, key):
        return self.translations[self.language][key]

    def _build_language_selector(self):
        assets = Path(__file__).resolve().parent / "assets"
        self.flag_images = {
            "it": ImageTk.PhotoImage(Image.open(assets / "italy.png").resize((28, 28), Image.Resampling.LANCZOS)),
            "en": ImageTk.PhotoImage(Image.open(assets / "uk.png").resize((28, 28), Image.Resampling.LANCZOS)),
        }
        self.language_selector = tk.Menubutton(
            self.header_bar,
            image=self.flag_images[self.language],
            bg="#0b1220",
            activebackground="#162033",
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=4,
            pady=2,
            cursor="hand2",
        )
        self.language_selector.grid(row=0, column=1, sticky="e")
        self.language_menu = tk.Menu(
            self.language_selector,
            tearoff=False,
            bg="#111c31",
            activebackground="#263653",
            activeforeground="#ffffff",
            borderwidth=0,
            relief="flat",
        )
        self.language_menu.add_command(image=self.flag_images["it"], command=lambda: self._switch_language("it"))
        self.language_menu.add_command(image=self.flag_images["en"], command=lambda: self._switch_language("en"))
        self.language_selector.configure(menu=self.language_menu)

    def _switch_language(self, language):
        self.language = language
        self.header.configure(text=self.t("title"))
        self.notebook.destroy()
        self.language_selector.destroy()
        self.notebook = ttk.Notebook(self.container)
        self.notebook.grid(row=1, column=0, sticky="nsew")
        self._build_language_selector()
        self._build_entry_tab()
        self._build_base_tab()
        self._build_stress_tab()

    def _center_window(self):
        self.update_idletasks()
        width = 900
        height = 680
        left = max(0, (self.winfo_screenwidth() - width) // 2)
        top = max(0, (self.winfo_screenheight() - height) // 2)
        self.geometry(f"{width}x{height}+{left}+{top}")

    def _focus_window(self):
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()
        self.after(700, lambda: self.attributes("-topmost", False))

    def _apply_theme(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#0b1220")
        style.configure("TLabel", background="#0b1220", foreground="#dfe7f5")
        style.configure("TNotebook", background="#0b1220", borderwidth=0, tabmargins=(0, 0, 0, 0))
        style.configure("TNotebook.Tab", background="#162033", foreground="#94a3b8", padding=(16, 8), borderwidth=0)
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#38bdf8"), ("active", "#263653")],
            foreground=[("selected", "#07111f"), ("active", "#e2e8f0")],
            padding=[("selected", (19, 10)), ("active", (17, 9))],
        )
        style.configure("TEntry", fieldbackground="#101a2c", foreground="#f8fafc")
        style.map("TEntry", fieldbackground=[("readonly", "#101a2c")])
        style.configure("TButton", background="#38bdf8", foreground="#0f172a", padding=(12, 8), font=("Segoe UI", 10, "bold"))
        style.map("TButton", background=[("active", "#7dd3fc")], foreground=[("active", "#0f172a")])
        style.configure("Info.TLabel", background="#111827", foreground="#a5f3fc", font=("Segoe UI", 9))
        style.configure("Result.TLabel", background="#111827", foreground="#f8fafc", font=("Segoe UI", 10))
        style.configure("Value.TLabel", background="#0f172a", foreground="#67e8f9", font=("Segoe UI", 12, "bold"))
        style.configure("Scale.TLabel", background="#0b1220", foreground="#64748b", font=("Segoe UI", 8))
        style.configure("Horizontal.TScale", troughcolor="#263653", background="#38bdf8", lightcolor="#38bdf8", darkcolor="#38bdf8", borderwidth=0)

    def _field_block(self, parent, label_text, help_text, variable, row, width=60, button=None):
        ttk.Label(parent, text=label_text, font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w", pady=(12, 4))
        ttk.Label(parent, text=help_text, style="Info.TLabel", wraplength=760).grid(row=row + 1, column=0, sticky="w", pady=(0, 8))
        entry = ttk.Entry(parent, textvariable=variable, width=width)
        entry.grid(row=row + 2, column=0, sticky="ew", padx=(0, 10))
        if button is not None:
            button.grid(row=row + 2, column=1, sticky="w")
        parent.columnconfigure(0, weight=1)

    def _slider_block(self, parent, label_text, help_text, variable, row, minimum, maximum, formatter=str, step=1):
        ttk.Label(parent, text=label_text, font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w", pady=(12, 4))
        value_label = ttk.Label(parent, text=formatter(variable.get()), style="Value.TLabel", width=10, anchor="e")
        value_label.grid(row=row, column=1, sticky="e", pady=(12, 4))
        ttk.Label(parent, text=help_text, style="Info.TLabel", wraplength=760).grid(row=row + 1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        def update_value(raw_value):
            snapped = round(float(raw_value) / step) * step
            variable.set(snapped)
            value_label.configure(text=formatter(snapped))

        slider = tk.Scale(
            parent,
            from_=minimum,
            to=maximum,
            resolution=step,
            variable=variable,
            orient="horizontal",
            command=update_value,
            showvalue=False,
            bg="#0b1220",
            fg="#94a3b8",
            troughcolor="#263653",
            activebackground="#7dd3fc",
            highlightthickness=0,
            bd=0,
            sliderlength=24,
            width=16,
        )
        slider.grid(row=row + 2, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        ttk.Label(parent, text=formatter(minimum), style="Scale.TLabel").grid(row=row + 3, column=0, sticky="w")
        ttk.Label(parent, text=formatter(maximum), style="Scale.TLabel").grid(row=row + 3, column=1, sticky="e")
        parent.columnconfigure(0, weight=1)

    def _result_panel(self, parent, row, prefix):
        panel = tk.Frame(parent, bg="#111c31", highlightbackground="#263653", highlightthickness=1)
        panel.grid(row=row, column=0, columnspan=2, sticky="nsew", pady=(12, 8))
        setattr(self, f"{prefix}_result_title", tk.Label(panel, text=self.t("waiting"), bg="#111c31", fg="#94a3b8", font=("Segoe UI", 10, "bold")))
        getattr(self, f"{prefix}_result_title").pack(anchor="w", padx=18, pady=(14, 0))
        setattr(self, f"{prefix}_result_probability", tk.Label(panel, text="--", bg="#111c31", fg="#67e8f9", font=("Segoe UI", 30, "bold")))
        getattr(self, f"{prefix}_result_probability").pack(anchor="w", padx=18, pady=(0, 8))
        setattr(self, f"{prefix}_result_details", tk.Label(panel, text=self.t("start"), justify="left", anchor="w", bg="#111c31", fg="#dbeafe", font=("Segoe UI", 10), wraplength=760))
        getattr(self, f"{prefix}_result_details").pack(fill="x", padx=18, pady=(0, 16))

    def _display_result(self, result, mode="base"):
        prefix = mode if mode in ("base", "entry") else "stress"
        title_widget = getattr(self, f"{prefix}_result_title")
        probability_widget = getattr(self, f"{prefix}_result_probability")
        details_widget = getattr(self, f"{prefix}_result_details")
        if not isinstance(result, dict):
            title_widget.configure(text=self.t("error"), fg="#fca5a5")
            probability_widget.configure(text="Errore", fg="#fca5a5")
            details_widget.configure(text=str(result))
            return
        if mode in ("base", "entry"):
            probability = result["prob_predittiva"]
            title = "Probabilità stimata di promozione" if self.language == "it" else "Estimated passing probability"
            details = (f"{result['test_superati']} test su {result['test_analizzati']} entro la soglia di 3 errori\n"
                       f"Errori attesi: {result['lambda_atteso']:.2f}  |  Storico positivo: {result['perc_storica']:.1f}%\n"
                       f"{self.t('updated')} {result['data_riferimento']}  |  Emivita: {result['emivita']:.0f} giorni") if self.language == "it" else (f"{result['test_superati']} of {result['test_analizzati']} tests within the 3-error threshold\n"
                       f"Expected errors: {result['lambda_atteso']:.2f}  |  Positive history: {result['perc_storica']:.1f}%\n"
                       f"{self.t('updated')} {result['data_riferimento']}  |  Half-life: {result['emivita']:.0f} days")
        else:
            probability = result["prob_stress"]
            title = "Probabilità stimata in condizioni di ansia" if self.language == "it" else "Estimated probability under anxiety"
            details = (f"Scenario tranquillo: {result['prob_base']:.1f}%  |  Scenario ansia: {result['prob_stress']:.1f}%\n"
                       f"Errori attesi: {result['lambda_base']:.2f}  ->  sotto stress: {result['lambda_stress']:.2f}\n"
                       f"Analizzati {result['test_analizzati']} test, aggiornati al {result['data_rif']}") if self.language == "it" else (f"Calm scenario: {result['prob_base']:.1f}%  |  Anxiety scenario: {result['prob_stress']:.1f}%\n"
                       f"Expected errors: {result['lambda_base']:.2f}  ->  under stress: {result['lambda_stress']:.2f}\n"
                       f"{self.t('analyzed')} {result['test_analizzati']} tests, {self.t('updated').lower()} {result['data_rif']}")
        color = "#86efac" if probability >= 70 else "#fbbf24" if probability >= 50 else "#fca5a5"
        title_widget.configure(text=title, fg="#cbd5e1")
        probability_widget.configure(text=f"{probability:.1f}%", fg=color)
        details_widget.configure(text=details)

    def _build_entry_tab(self):
        frame = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(frame, text=self.t("entry"))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(5, weight=1)

        self.entry_date_var = tk.StringVar(value=date.today().isoformat())
        self.entry_errors_var = tk.DoubleVar(value=0)
        self.entry_half_life_var = tk.DoubleVar(value=7)

        ttk.Label(frame, text=self.t("entry_help"), style="Info.TLabel", wraplength=760).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        ttk.Label(frame, text=self.t("entry_date"), font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=(4, 4))
        ttk.Label(frame, text="YYYY-MM-DD", style="Info.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 8))
        date_controls = ttk.Frame(frame)
        date_controls.grid(row=3, column=0, sticky="w")
        self.entry_date_display = ttk.Entry(date_controls, textvariable=self.entry_date_var, state="readonly", width=18)
        self.entry_date_display.pack(side="left", padx=(0, 8))
        self.calendar_button = ttk.Button(date_controls, text="📅", width=3, command=self._open_date_picker)
        self.calendar_button.pack(side="left")
        self._slider_block(frame, self.t("entry_errors"), "0 = nessun errore; 12 = molti errori.", self.entry_errors_var, row=4, minimum=0, maximum=12, formatter=lambda value: f"{float(value):.0f}")

        actions = ttk.Frame(frame)
        actions.grid(row=8, column=0, sticky="w", pady=(14, 8))
        ttk.Button(actions, text=self.t("add"), command=self._add_record).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text=self.t("remove"), command=self._remove_record).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text=self.t("clear"), command=self._clear_records).pack(side="left")

        self.entry_tree = ttk.Treeview(frame, columns=("date", "errors"), show="headings", height=6)
        self.entry_tree.heading("date", text=self.t("entry_date"))
        self.entry_tree.heading("errors", text=self.t("entry_errors"))
        self.entry_tree.column("date", width=150, anchor="center")
        self.entry_tree.column("errors", width=150, anchor="center")
        self.entry_tree.grid(row=9, column=0, sticky="nsew", pady=(0, 10))
        self._refresh_record_list()

        ttk.Button(frame, text=self.t("analyze_entries"), command=self._run_entry_analysis).grid(row=10, column=0, sticky="w", pady=(4, 8))
        self._result_panel(frame, 11, "entry")
        self.entry_chart = tk.Frame(frame, bg="#111827", height=180)
        self.entry_chart.grid(row=12, column=0, sticky="nsew", pady=(4, 0))
        frame.rowconfigure(11, weight=1)

    def _refresh_record_list(self):
        if not hasattr(self, "entry_tree"):
            return
        for item in self.entry_tree.get_children():
            self.entry_tree.delete(item)
        for record in sorted(self.records, key=lambda value: value["data"]):
            self.entry_tree.insert("", "end", values=(record["data"], int(record["errori"])))
        self._update_session_labels()

    def _open_date_picker(self):
        if hasattr(self, "date_picker") and self.date_picker.winfo_exists():
            self.date_picker.focus_force()
            return

        try:
            selected_date = date.fromisoformat(self.entry_date_var.get())
        except ValueError:
            selected_date = date.today()

        self.calendar_year = selected_date.year
        self.calendar_month = selected_date.month
        self.calendar_selected = selected_date
        self.date_picker = tk.Toplevel(self)
        self.date_picker.title(self.t("entry_date"))
        self.date_picker.configure(bg="#0b1220")
        self.date_picker.resizable(False, False)
        self.date_picker.transient(self)
        self.date_picker.grab_set()

        header = tk.Frame(self.date_picker, bg="#111c31")
        header.pack(fill="x", padx=10, pady=(10, 6))
        tk.Button(header, text="‹", command=lambda: self._change_calendar_month(-1), bg="#111c31", fg="#67e8f9", activebackground="#263653", activeforeground="#ffffff", relief="flat", bd=0, font=("Segoe UI", 15, "bold"), width=3).pack(side="left")
        self.calendar_title = tk.Label(header, bg="#111c31", fg="#f8fafc", font=("Segoe UI", 10, "bold"), width=18)
        self.calendar_title.pack(side="left", expand=True)
        tk.Button(header, text="›", command=lambda: self._change_calendar_month(1), bg="#111c31", fg="#67e8f9", activebackground="#263653", activeforeground="#ffffff", relief="flat", bd=0, font=("Segoe UI", 15, "bold"), width=3).pack(side="right")

        self.calendar_grid = tk.Frame(self.date_picker, bg="#0b1220")
        self.calendar_grid.pack(padx=10, pady=(0, 6))
        ttk.Button(self.date_picker, text=self.t("today"), command=lambda: self._select_calendar_date(date.today())).pack(pady=(0, 10))
        self._render_calendar()

    def _change_calendar_month(self, offset):
        month_index = self.calendar_year * 12 + self.calendar_month - 1 + offset
        self.calendar_year, month_zero = divmod(month_index, 12)
        self.calendar_month = month_zero + 1
        self._render_calendar()

    def _select_calendar_date(self, selected_date):
        self.entry_date_var.set(selected_date.isoformat())
        if hasattr(self, "date_picker") and self.date_picker.winfo_exists():
            self.date_picker.grab_release()
            self.date_picker.destroy()

    def _render_calendar(self):
        for child in self.calendar_grid.winfo_children():
            child.destroy()
        month_names = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        if self.language == "en":
            month_names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        self.calendar_title.configure(text=f"{month_names[self.calendar_month - 1]} {self.calendar_year}")
        weekdays = ["L", "M", "M", "G", "V", "S", "D"] if self.language == "it" else ["M", "T", "W", "T", "F", "S", "S"]
        for column, weekday in enumerate(weekdays):
            tk.Label(self.calendar_grid, text=weekday, bg="#0b1220", fg="#64748b", font=("Segoe UI", 8, "bold"), width=4).grid(row=0, column=column, pady=(0, 4))
        month_days = calendar.monthrange(self.calendar_year, self.calendar_month)[1]
        first_weekday = date(self.calendar_year, self.calendar_month, 1).weekday()
        for day_number in range(1, month_days + 1):
            position = first_weekday + day_number - 1
            row, column = divmod(position, 7)
            current = date(self.calendar_year, self.calendar_month, day_number)
            selected = current == self.calendar_selected
            button = tk.Button(self.calendar_grid, text=str(day_number), command=lambda value=current: self._select_calendar_date(value), width=4, relief="flat", bd=0, bg="#38bdf8" if selected else "#162033", fg="#07111f" if selected else "#dbeafe", activebackground="#7dd3fc", activeforeground="#07111f", font=("Segoe UI", 9, "bold" if selected else "normal"))
            button.grid(row=row + 1, column=column, padx=1, pady=1)

    def _selected_records(self, count):
        records = sorted(self.records, key=lambda value: value["data"])
        return records[-int(count):]

    def _add_record(self):
        try:
            data = self.entry_date_var.get().strip()
            parsed_date = date.fromisoformat(data)
            errors = int(self.entry_errors_var.get())
            if errors < 0:
                raise ValueError("Il numero di errori non può essere negativo.")
            self.records.append({"data": parsed_date.isoformat(), "errori": errors})
            self._refresh_record_list()
        except ValueError as error:
            messagebox.showerror("Errore", str(error))

    def _remove_record(self):
        selected = self.entry_tree.selection()
        if not selected:
            return
        values = self.entry_tree.item(selected[0], "values")
        self.records.remove({"data": values[0], "errori": int(values[1])})
        self._refresh_record_list()

    def _clear_records(self):
        self.records.clear()
        self._refresh_record_list()

    def _run_entry_analysis(self):
        try:
            if not self.records:
                raise ValueError(self.t("no_entries"))
            result = analizza_predizione_records(self.records, emivita_giorni=7)
            self._display_result(result, "entry")
            self._show_records_chart(self.entry_chart, self.records)
        except Exception as error:
            messagebox.showerror("Errore", str(error))
            self._display_result(f"Errore: {error}", "entry")

    def _build_base_tab(self):
        frame = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(frame, text=self.t("base"))

        self.n_test_var = tk.DoubleVar(value=50)
        self.half_life_var = tk.DoubleVar(value=7)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(2, weight=1)
        ttk.Label(frame, text=self.t("session_help"), style="Info.TLabel", wraplength=760).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        self.base_session_label = ttk.Label(frame, text="", style="Value.TLabel")
        self.base_session_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))
        self._update_session_labels()

        self._slider_block(
            frame,
            self.t("tests"), self.t("tests_help"),
            self.n_test_var,
            row=2,
            minimum=5,
            maximum=200,
            formatter=lambda value: f"{float(value):.0f}",
        )

        self._slider_block(
            frame,
            self.t("half"), self.t("half_help"),
            self.half_life_var,
            row=5,
            minimum=1,
            maximum=30,
            formatter=lambda value: f"{float(value):.0f} giorni",
        )

        ttk.Button(frame, text=self.t("calculate"), command=self._run_base_analysis).grid(row=9, column=0, sticky="w", pady=(14, 8))
        self._result_panel(frame, 10, "base")

        self.base_chart = tk.Frame(frame, bg="#111827", height=180)
        self.base_chart.grid(row=10, column=2, rowspan=2, sticky="nsew", padx=(12, 0), pady=(12, 0))

        frame.rowconfigure(10, weight=1)

    def _build_stress_tab(self):
        frame = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(frame, text=self.t("stress"))

        self.stress_n_var = tk.DoubleVar(value=50)
        self.stress_half_var = tk.DoubleVar(value=7)
        self.stress_factor_var = tk.DoubleVar(value=1.2)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(2, weight=1)
        ttk.Label(frame, text=self.t("session_help"), style="Info.TLabel", wraplength=760).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        self.stress_session_label = ttk.Label(frame, text="", style="Value.TLabel")
        self.stress_session_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))
        self._update_session_labels()

        self._slider_block(
            frame,
            self.t("tests"), self.t("tests_help"),
            self.stress_n_var,
            row=2,
            minimum=5,
            maximum=200,
            formatter=lambda value: f"{float(value):.0f}",
        )

        self._slider_block(
            frame,
            self.t("half"), self.t("half_help"),
            self.stress_half_var,
            row=5,
            minimum=1,
            maximum=30,
            formatter=lambda value: f"{float(value):.0f} giorni",
        )

        self._slider_block(
            frame,
            self.t("anxiety"), self.t("anxiety_help"),
            self.stress_factor_var,
            row=8,
            minimum=1,
            maximum=2,
            formatter=lambda value: f"{float(value):.1f}x",
            step=0.1,
        )

        ttk.Button(frame, text=self.t("calculate_stress"), command=self._run_stress_analysis).grid(row=12, column=0, sticky="w", pady=(14, 8))
        self._result_panel(frame, 13, "stress")

        self.stress_chart = tk.Frame(frame, bg="#111827", height=180)
        self.stress_chart.grid(row=13, column=2, rowspan=2, sticky="nsew", padx=(12, 0), pady=(12, 0))

        frame.rowconfigure(13, weight=1)

    def _update_session_labels(self):
        if hasattr(self, "base_session_label") and self.base_session_label.winfo_exists():
            self.base_session_label.configure(text=f"{len(self.records)} {self.t('session_count')}")
        if hasattr(self, "stress_session_label") and self.stress_session_label.winfo_exists():
            self.stress_session_label.configure(text=f"{len(self.records)} {self.t('session_count')}")

    def _format_result(self, result):
        if isinstance(result, dict):
            text = [
                "RISULTATO ANALISI",
                "=" * 60,
                f"Test analizzati: {result.get('test_analizzati', 0)}",
                f"Data riferimento: {result.get('data_riferimento') or result.get('data_rif', '-')}",
            ]
            if 'emivita' in result:
                text.append(f"Emivita: {result['emivita']} giorni")
            if 'lambda_atteso' in result:
                text.append(f"Lambda atteso: {result['lambda_atteso']:.2f}")
                text.append(f"Storico superati: {result['test_superati']} ({result['perc_storica']:.1f}%)")
                text.append(f"Probabilità di promozione: {result['prob_predittiva']:.1f}%")
            if 'lambda_base' in result:
                text.append(f"Lambda base: {result['lambda_base']:.2f}")
                text.append(f"Lambda stress: {result['lambda_stress']:.2f}")
                text.append(f"Promozione tranquilla: {result['prob_base']:.1f}%")
                text.append(f"Promozione con ansia: {result['prob_stress']:.1f}%")
            return "\n".join(text)
        return str(result)

    def _set_text(self, widget, value):
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, value)
        widget.configure(state="disabled")

    def _clear_chart(self, container):
        for child in container.winfo_children():
            child.destroy()

    def _show_records_chart(self, container, records):
        self._clear_chart(container)
        try:
            distribuzione = distribuzione_errori_records(records)
            labels = ["0", "1", "2", "3", "4+"]
            values = [distribuzione.get(0, 0), distribuzione.get(1, 0), distribuzione.get(2, 0), distribuzione.get(3, 0), distribuzione.get(4, 0)]
            fig = Figure(figsize=(5.8, 2.1), dpi=100, facecolor="#111827")
            ax = fig.add_subplot(111)
            ax.set_facecolor("#111827")
            ax.bar(labels, values, color=["#38bdf8", "#60a5fa", "#a78bfa", "#fbbf24", "#f87171"])
            ax.set_title(self.t("chart"), color="#e2e8f0", fontsize=10, pad=8)
            ax.set_xlabel(self.t("errors"), color="#cbd5e1", fontsize=8)
            ax.set_ylabel(self.t("occurrences"), color="#cbd5e1", fontsize=8)
            ax.tick_params(colors="#cbd5e1", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#475569")
            ax.grid(axis="y", linestyle="--", color="#475569", alpha=0.45)
            fig.tight_layout(pad=1.2)
            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception:
            ttk.Label(container, text=self.t("no_chart"), foreground="#fca5a5").pack(padx=12, pady=12)

    def _run_base_analysis(self):
        try:
            n_test = int(self.n_test_var.get() or 50)
            emivita = float(self.half_life_var.get() or 7.0)
            result = analizza_predizione_records(self._selected_records(n_test), emivita_giorni=emivita)
            self._display_result(result, "base")
            self._show_records_chart(self.base_chart, self._selected_records(n_test))
        except Exception as exc:
            messagebox.showerror("Errore", str(exc))
            self._display_result(f"Errore: {exc}", "base")
            self._clear_chart(self.base_chart)

    def _run_stress_analysis(self):
        try:
            n_test = int(self.stress_n_var.get() or 50)
            emivita = float(self.stress_half_var.get() or 7.0)
            ansia = float(self.stress_factor_var.get() or 1.2)
            result = analizza_predizione_records_con_stress(self._selected_records(n_test), emivita, ansia)
            self._display_result(result, "stress")
            self._show_records_chart(self.stress_chart, self._selected_records(n_test))
        except Exception as exc:
            messagebox.showerror("Errore", str(exc))
            self._display_result(f"Errore: {exc}", "stress")
            self._clear_chart(self.stress_chart)


if __name__ == "__main__":
    os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")
    app = PatentApp()
    app.mainloop()
