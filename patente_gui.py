import os
import calendar
import tkinter as tk
from datetime import date, datetime
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
from patente_storage import StorageError, get_storage_path, load_records, load_settings, save_records, save_settings


class PatentApp(tk.Tk):
    def __init__(self, storage_path=None, settings_path=None):
        super().__init__()
        self.title("Analisi Patente")
        self.geometry("1100x760")
        self.minsize(1000, 700)
        self.configure(bg="#0b1220")
        self._center_window()
        self.after(100, self._focus_window)

        self.storage_path = Path(storage_path) if storage_path is not None else get_storage_path()
        self.settings_path = Path(settings_path) if settings_path is not None else get_storage_path(file_name="settings.json")
        self.storage_error = None
        try:
            self.records = load_records(self.storage_path)
        except StorageError as error:
            self.records = []
            self.storage_error = error
        self.settings_error = None
        try:
            self.saved_settings = load_settings(self.settings_path)
        except StorageError as error:
            self.saved_settings = load_settings(Path("__missing_settings__.json"))
            self.settings_error = error
        self.language = "it"
        self.translations = {
            "it": {
                "title": "Analisi probabilistica esame patente", "entry": "Inserisci risultati", "settings": "Impostazioni", "english": "English",
                "tests": "Numero di test da considerare", "tests_help": "Più alto è il numero, più lo storico è ampio. Il valore indica quanti test recenti includere.",
                "half": "Emivita in giorni", "half_help": "Indica dopo quanti giorni un test vecchio perde metà della sua rilevanza. Valori bassi privilegiano i test recenti.",
                "anxiety": "Moltiplicatore ansia", "anxiety_help": "1.0 indica condizioni normali; valori superiori simulano un peggioramento delle prestazioni sotto stress.",
                "waiting": "In attesa dei risultati", "start": "Avvia un'analisi per visualizzare una stima.",
                "chart": "Distribuzione degli errori negli ultimi test", "errors": "Numero di errori", "occurrences": "Occorrenze", "no_chart": "Nessun grafico disponibile per questo file.",
                "error": "Analisi non disponibile", "normal": "Scenario tranquillo", "stress_scenario": "Scenario ansia", "updated": "Aggiornato al", "analyzed": "Analizzati",
                "entry_date": "Data del test", "entry_errors": "Errori commessi", "add": "Aggiungi risultato", "remove": "Rimuovi selezionato", "clear": "Svuota elenco", "analyze_entries": "Analizza risultati inseriti", "entry_help": "I risultati restano nell'app durante questa sessione e non richiedono file esterni.", "no_entries": "Inserisci almeno un risultato.",
                "today": "Oggi", "previous_month": "Mese precedente", "next_month": "Mese successivo", "calendar": "Apri calendario",
                "session_help": "Queste analisi usano i risultati inseriti nella scheda Inserisci risultati.", "session_count": "risultati disponibili", "go_to_entry": "Vai a Inserisci risultati",
                "analysis_mode": "Valutazione ansia", "without_anxiety": "Senza ansia", "with_anxiety": "Con ansia", "close": "Chiudi", "report": "Report analisi", "storage_error": "Impossibile leggere o salvare i risultati locali.",
            },
            "en": {
                "title": "Driving test probability analysis", "entry": "Enter results", "settings": "Settings", "english": "Italiano",
                "tests": "Number of tests to include", "tests_help": "A higher number gives a broader history. This is the number of recent tests included.",
                "half": "Half-life in days", "half_help": "After this many days, an old test has half its relevance. Lower values favor recent tests.",
                "anxiety": "Anxiety multiplier", "anxiety_help": "1.0 means normal conditions; higher values simulate performance loss under stress.",
                "waiting": "Waiting for results", "start": "Run an analysis to see an estimate.",
                "chart": "Error distribution in recent tests", "errors": "Number of errors", "occurrences": "Occurrences", "no_chart": "No chart is available for this file.",
                "error": "Analysis unavailable", "normal": "Calm scenario", "stress_scenario": "Anxiety scenario", "updated": "Updated on", "analyzed": "Analyzed",
                "entry_date": "Test date", "entry_errors": "Mistakes made", "add": "Add result", "remove": "Remove selected", "clear": "Clear list", "analyze_entries": "Analyze entered results", "entry_help": "Results stay inside the app during this session and do not require external files.", "no_entries": "Add at least one result.",
                "today": "Today", "previous_month": "Previous month", "next_month": "Next month", "calendar": "Open calendar",
                "session_help": "These analyses use the results entered in the Enter results tab.", "session_count": "results available", "go_to_entry": "Go to Enter results",
                "analysis_mode": "Anxiety evaluation", "without_anxiety": "Without anxiety", "with_anxiety": "With anxiety", "close": "Close", "report": "Analysis report", "storage_error": "Unable to read or save local results.",
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
        if self.storage_error is not None or self.settings_error is not None:
            self.after_idle(self._show_storage_error)

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

    def _show_storage_error(self):
        error = self.storage_error or self.settings_error
        messagebox.showerror(self.t("storage_error"), str(error))

    def _persist_records(self):
        try:
            save_records(self.records, self.storage_path)
            return True
        except StorageError as error:
            messagebox.showerror(self.t("storage_error"), str(error))
            return False

    def _persist_settings(self):
        try:
            save_settings(self._current_settings(), self.settings_path)
            return True
        except StorageError as error:
            messagebox.showerror(self.t("storage_error"), str(error))
            return False

    def _current_settings(self):
        return {
            "test_count": int(self.n_test_var.get()),
            "half_life": float(self.half_life_var.get()),
            "anxiety_mode": self.analysis_mode_var.get(),
            "anxiety_factor": float(self.anxiety_factor_var.get()),
        }

    def _center_window(self):
        self.update_idletasks()
        width = 1100
        height = 760
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
        style.configure("Treeview", background="#111c31", foreground="#dbeafe", fieldbackground="#111c31", rowheight=27, borderwidth=0, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#1e293b", foreground="#e2e8f0", relief="flat", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#38bdf8")], foreground=[("selected", "#07111f")])
        style.configure("Dark.Vertical.TScrollbar", troughcolor="#0b1220", background="#263653", bordercolor="#0b1220", arrowcolor="#67e8f9", relief="flat", width=12)
        style.map("Dark.Vertical.TScrollbar", background=[("active", "#38bdf8")])

    def _slider_block(self, parent, label_text, help_text, variable, row, minimum, maximum, formatter=str, step=1):
        ttk.Label(parent, text=label_text, font=("Segoe UI", 10, "bold")).grid(row=row, column=0, sticky="w", pady=(12, 4))
        value_label = ttk.Label(parent, text=formatter(variable.get()), style="Value.TLabel", width=10, anchor="e")
        value_label.grid(row=row, column=1, sticky="e", pady=(12, 4))
        ttk.Label(parent, text=help_text, style="Info.TLabel", wraplength=760).grid(row=row + 1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        def update_value(raw_value):
            snapped = round(float(raw_value) / step) * step
            variable.set(snapped)
            value_label.configure(text=formatter(snapped))
            if hasattr(self, "n_test_var") and hasattr(self, "analysis_mode_var"):
                self._persist_settings()

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
        variable.trace_add("write", lambda *_: self._persist_settings() if hasattr(self, "n_test_var") and hasattr(self, "analysis_mode_var") else None)
        parent.columnconfigure(0, weight=1)

    def _result_panel(self, parent, row, prefix):
        panel = tk.Frame(parent, height=135, bg="#111c31", highlightbackground="#263653", highlightthickness=1)
        panel.grid(row=row, column=0, columnspan=2, sticky="nsew", pady=(12, 8))
        panel.grid_propagate(False)
        setattr(self, f"{prefix}_result_title", tk.Label(panel, text=self.t("waiting"), bg="#111c31", fg="#94a3b8", font=("Segoe UI", 10, "bold")))
        getattr(self, f"{prefix}_result_title").pack(anchor="w", padx=18, pady=(14, 0))
        setattr(self, f"{prefix}_result_probability", tk.Label(panel, text="--", bg="#111c31", fg="#67e8f9", font=("Segoe UI", 30, "bold")))
        getattr(self, f"{prefix}_result_probability").pack(anchor="w", padx=18, pady=(0, 8))
        setattr(self, f"{prefix}_result_details", tk.Label(panel, text=self.t("start"), justify="left", anchor="w", bg="#111c31", fg="#dbeafe", font=("Segoe UI", 10), wraplength=760))
        getattr(self, f"{prefix}_result_details").pack(fill="x", padx=18, pady=(0, 16))

    def _display_result(self, result, mode="base"):
        is_popup = mode.startswith("popup_")
        is_stress = mode in ("stress", "popup_stress")
        prefix = "popup" if is_popup else ("stress" if is_stress else mode)
        title_widget = getattr(self, f"{prefix}_result_title")
        probability_widget = getattr(self, f"{prefix}_result_probability")
        details_widget = getattr(self, f"{prefix}_result_details")
        if not isinstance(result, dict):
            title_widget.configure(text=self.t("error"), fg="#fca5a5")
            probability_widget.configure(text="Errore", fg="#fca5a5")
            details_widget.configure(text=str(result))
            return
        if not is_stress:
            probability = result["prob_predittiva"]
            title = "Probabilità stimata di superamento" if self.language == "it" else "Estimated passing probability"
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
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=self.t("entry"))
        frame = ttk.Frame(tab, padding=16)
        frame.place(relx=0.5, rely=0.02, relwidth=0.78, anchor="n")
        frame.columnconfigure(0, weight=1)

        self.entry_date_var = tk.StringVar(value=date.today().strftime("%d/%m/%Y"))
        self.entry_errors_var = tk.DoubleVar(value=0)

        ttk.Label(frame, text=self.t("entry_help"), style="Info.TLabel", wraplength=760).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
        ttk.Label(frame, text=self.t("entry_date"), font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky="w", pady=(4, 4))
        date_controls = ttk.Frame(frame)
        date_controls.grid(row=2, column=0, sticky="w", pady=(0, 8))
        self.entry_date_display = ttk.Entry(date_controls, textvariable=self.entry_date_var, state="readonly", width=18)
        self.entry_date_display.pack(side="left", padx=(0, 8))
        self.calendar_button = ttk.Button(date_controls, text="📅", width=3, command=self._open_date_picker)
        self.calendar_button.pack(side="left")
        self._slider_block(frame, self.t("entry_errors"), "0 = nessun errore; 12 = molti errori.", self.entry_errors_var, row=3, minimum=0, maximum=12, formatter=lambda value: f"{float(value):.0f}")

        actions = ttk.Frame(frame)
        actions.grid(row=7, column=0, sticky="w", pady=(14, 8))
        ttk.Button(actions, text=self.t("add"), command=self._add_record).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text=self.t("clear"), command=self._clear_records).pack(side="left")

        list_container = ttk.Frame(frame)
        list_container.grid(row=8, column=0, sticky="ew", pady=(0, 10))
        list_container.columnconfigure(0, weight=1)
        self.records_canvas = tk.Canvas(list_container, bg="#0b1220", highlightthickness=0, height=300)
        self.records_canvas.grid(row=0, column=0, sticky="ew")
        self.records_scrollbar = ttk.Scrollbar(list_container, orient="vertical", style="Dark.Vertical.TScrollbar", command=self.records_canvas.yview)
        self.records_scrollbar.grid(row=0, column=1, sticky="ns")
        self.records_canvas.configure(yscrollcommand=self.records_scrollbar.set)
        self.records_list_frame = ttk.Frame(self.records_canvas)
        self.records_window = self.records_canvas.create_window((0, 0), window=self.records_list_frame, anchor="nw")
        self.records_list_frame.bind("<Configure>", lambda _event: self.records_canvas.configure(scrollregion=self.records_canvas.bbox("all")))
        self.records_canvas.bind("<Configure>", lambda event: self.records_canvas.itemconfigure(self.records_window, width=event.width))
        self._refresh_record_list()

        ttk.Button(frame, text=self.t("analyze_entries"), command=self._open_entry_analysis).grid(row=9, column=0, sticky="w", pady=(4, 8))

    def _refresh_record_list(self):
        if not hasattr(self, "records_list_frame"):
            return
        for child in self.records_list_frame.winfo_children():
            child.destroy()
        header = ttk.Frame(self.records_list_frame)
        header.pack(fill="x")
        ttk.Label(header, text=self.t("entry_date"), style="Scale.TLabel", width=24).pack(side="left", padx=(8, 0))
        ttk.Label(header, text=self.t("entry_errors"), style="Scale.TLabel", width=18).pack(side="left")
        for record in sorted(self.records, key=lambda value: value["data"]):
            row = tk.Frame(self.records_list_frame, bg="#111c31")
            row.pack(fill="x", pady=1)
            display_date = date.fromisoformat(record["data"]).strftime("%d/%m/%Y")
            tk.Label(row, text=display_date, bg="#111c31", fg="#dbeafe", width=24, anchor="w", padx=8, font=("Segoe UI", 9)).pack(side="left")
            tk.Label(row, text=str(int(record["errori"])), bg="#111c31", fg="#dbeafe", width=18, anchor="w", font=("Segoe UI", 9)).pack(side="left")
            tk.Button(row, text="×", command=lambda item=record: self._remove_record(item), bg="#ef4444", fg="#ffffff", activebackground="#f87171", activeforeground="#ffffff", relief="flat", bd=0, width=3, font=("Segoe UI", 10, "bold"), cursor="hand2").pack(side="right", padx=6)
        self.records_canvas.configure(scrollregion=self.records_canvas.bbox("all"))
        if len(self.records) > 10:
            self.records_scrollbar.grid()
        else:
            self.records_scrollbar.grid_remove()
        self._update_session_labels()

    def _open_date_picker(self):
        if hasattr(self, "date_picker") and self.date_picker.winfo_exists():
            self.date_picker.focus_force()
            return

        try:
            selected_date = datetime.strptime(self.entry_date_var.get(), "%d/%m/%Y").date()
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
        self.date_picker.update_idletasks()
        popup_width = self.date_picker.winfo_reqwidth()
        popup_height = self.date_picker.winfo_reqheight()
        left = self.winfo_rootx() + (self.winfo_width() - popup_width) // 2
        top = self.winfo_rooty() + (self.winfo_height() - popup_height) // 2
        self.date_picker.geometry(f"{popup_width}x{popup_height}+{max(0, left)}+{max(0, top)}")
        self.date_picker.update_idletasks()
        target_center_x = self.winfo_rootx() + self.winfo_width() / 2
        target_center_y = self.winfo_rooty() + self.winfo_height() / 2
        popup_center_x = self.date_picker.winfo_rootx() + self.date_picker.winfo_width() / 2
        popup_center_y = self.date_picker.winfo_rooty() + self.date_picker.winfo_height() / 2
        corrected_left = self.date_picker.winfo_x() + round(target_center_x - popup_center_x)
        corrected_top = self.date_picker.winfo_y() + round(target_center_y - popup_center_y)
        self.date_picker.geometry(f"+{max(0, corrected_left)}+{max(0, corrected_top)}")

    def _change_calendar_month(self, offset):
        month_index = self.calendar_year * 12 + self.calendar_month - 1 + offset
        self.calendar_year, month_zero = divmod(month_index, 12)
        self.calendar_month = month_zero + 1
        self._render_calendar()

    def _select_calendar_date(self, selected_date):
        self.entry_date_var.set(selected_date.strftime("%d/%m/%Y"))
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
            parsed_date = datetime.strptime(data, "%d/%m/%Y").date()
            errors = int(self.entry_errors_var.get())
            if errors < 0:
                raise ValueError("Il numero di errori non può essere negativo.")
            record = {"data": parsed_date.isoformat(), "errori": errors}
            self.records.append(record)
            if not self._persist_records():
                self.records.pop()
                return
            self._refresh_record_list()
        except ValueError as error:
            messagebox.showerror("Errore", str(error))

    def _remove_record(self, record):
        self.records.remove(record)
        if not self._persist_records():
            self.records.append(record)
            return
        self._refresh_record_list()

    def _clear_records(self):
        previous_records = self.records[:]
        self.records.clear()
        if not self._persist_records():
            self.records.extend(previous_records)
            return
        self._refresh_record_list()

    def _open_entry_analysis(self):
        self._run_unified_analysis()

    def _build_base_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text=self.t("settings"))
        frame = ttk.Frame(tab, padding=16)
        frame.place(relx=0.5, rely=0.02, relwidth=0.78, anchor="n")

        self.n_test_var = tk.DoubleVar(value=self.saved_settings["test_count"])
        self.half_life_var = tk.DoubleVar(value=self.saved_settings["half_life"])
        self.anxiety_factor_var = tk.DoubleVar(value=self.saved_settings["anxiety_factor"])
        self.analysis_mode_var = tk.StringVar(value=self.saved_settings["anxiety_mode"])
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

        ttk.Label(frame, text=self.t("analysis_mode"), font=("Segoe UI", 10, "bold")).grid(row=8, column=0, sticky="w", pady=(12, 4))
        mode_frame = ttk.Frame(frame)
        mode_frame.grid(row=9, column=0, sticky="w", pady=(0, 4))
        self.anxiety_without_radio = tk.Radiobutton(mode_frame, text=self.t("without_anxiety"), variable=self.analysis_mode_var, value="base", command=self._toggle_anxiety_slider, bg="#0b1220", fg="#dbeafe", activebackground="#0b1220", activeforeground="#67e8f9", selectcolor="#162033", font=("Segoe UI", 9))
        self.anxiety_without_radio.pack(side="left", padx=(0, 18))
        self.anxiety_with_radio = tk.Radiobutton(mode_frame, text=self.t("with_anxiety"), variable=self.analysis_mode_var, value="stress", command=self._toggle_anxiety_slider, bg="#0b1220", fg="#dbeafe", activebackground="#0b1220", activeforeground="#67e8f9", selectcolor="#162033", font=("Segoe UI", 9))
        self.anxiety_with_radio.pack(side="left")
        self.anxiety_slider_frame = ttk.Frame(frame)
        self.anxiety_slider_frame.grid(row=10, column=0, sticky="ew")
        self._slider_block(self.anxiety_slider_frame, self.t("anxiety"), self.t("anxiety_help"), self.anxiety_factor_var, row=0, minimum=1, maximum=2, formatter=lambda value: f"{float(value):.1f}x", step=0.1)
        self._toggle_anxiety_slider()


    def _update_session_labels(self):
        if hasattr(self, "base_session_label") and self.base_session_label.winfo_exists():
            self.base_session_label.configure(text=f"{len(self.records)} {self.t('session_count')}")

    def _toggle_anxiety_slider(self):
        if not hasattr(self, "anxiety_slider_frame"):
            return
        state = "normal" if self.analysis_mode_var.get() == "stress" else "disabled"
        foreground = "#dbeafe" if state == "normal" else "#475569"
        value_foreground = "#67e8f9" if state == "normal" else "#475569"
        for widget in self.anxiety_slider_frame.winfo_children():
            if isinstance(widget, (tk.Scale, ttk.Scale)):
                widget.configure(state=state)
            elif isinstance(widget, ttk.Label):
                widget.configure(foreground=value_foreground if widget.cget("style") == "Value.TLabel" else foreground)
        if hasattr(self, "n_test_var"):
            self._persist_settings()

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

    def _open_analysis_popup(self, records, emivita_giorni, anxiety_enabled, anxiety_factor=1.2):
        try:
            if anxiety_enabled:
                result = analizza_predizione_records_con_stress(records, emivita_giorni, anxiety_factor)
                mode = "popup_stress"
            else:
                result = analizza_predizione_records(records, emivita_giorni=emivita_giorni)
                mode = "popup_base"
            popup = tk.Toplevel(self)
            popup.title(self.t("report"))
            popup.configure(bg="#0b1220")
            popup.transient(self)
            popup.resizable(False, False)
            popup_frame = ttk.Frame(popup, padding=14)
            popup_frame.pack(fill="both", expand=True)
            self._result_panel(popup_frame, 0, "popup")
            chart = tk.Frame(popup_frame, bg="#111827", height=210)
            chart.grid(row=1, column=0, sticky="nsew", pady=(4, 8))
            self._display_result(result, mode)
            self._show_records_chart(chart, records)
            ttk.Button(popup_frame, text=self.t("close"), command=popup.destroy).grid(row=2, column=0, sticky="e")
            popup.update_idletasks()
            width, height = popup.winfo_reqwidth(), popup.winfo_reqheight()
            left = self.winfo_rootx() + (self.winfo_width() - width) // 2
            top = self.winfo_rooty() + (self.winfo_height() - height) // 2
            popup.geometry(f"{width}x{height}+{max(0, left)}+{max(0, top)}")
            popup.grab_set()
        except Exception as exc:
            messagebox.showerror("Errore", str(exc))
            return None

    def _run_unified_analysis(self):
        try:
            n_test = int(self.n_test_var.get() or 50)
            emivita = float(self.half_life_var.get() or 7.0)
            records = self._selected_records(n_test)
            if not records:
                raise ValueError(self.t("no_entries"))
            self._open_analysis_popup(records, emivita, self.analysis_mode_var.get() == "stress", float(self.anxiety_factor_var.get()))
        except Exception as exc:
            messagebox.showerror("Errore", str(exc))


if __name__ == "__main__":
    os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")
    app = PatentApp()
    app.mainloop()
