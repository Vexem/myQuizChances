import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from patente_core import (
    analizza_predizione_patente,
    analizza_predizione_patente_con_stress,
    distribuzione_errori,
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

        self.default_file = Path(__file__).resolve().parent / "SCHEMA TEST PATENTE.xlsx"
        self.language = "it"
        self.translations = {
            "it": {
                "title": "Analisi probabilistica esame patente", "base": "Base", "stress": "Con ansia", "english": "English",
                "file": "File Excel da analizzare", "file_help": "Inserisci il file con i risultati dei test. La prima colonna deve contenere la data e le seguenti i punteggi di errore.", "browse": "Sfoglia",
                "tests": "Numero di test da considerare", "tests_help": "Più alto è il numero, più lo storico è ampio. Il valore indica quanti test recenti includere.",
                "half": "Emivita in giorni", "half_help": "Indica dopo quanti giorni un test vecchio perde metà della sua rilevanza. Valori bassi privilegiano i test recenti.",
                "anxiety": "Moltiplicatore ansia", "anxiety_help": "1.0 indica condizioni normali; valori superiori simulano un peggioramento delle prestazioni sotto stress.",
                "calculate": "Calcola probabilità", "calculate_stress": "Calcola con ansia", "waiting": "In attesa dei risultati", "start": "Avvia un'analisi per visualizzare una stima.",
                "chart": "Distribuzione degli errori negli ultimi test", "errors": "Numero di errori", "occurrences": "Occorrenze", "no_chart": "Nessun grafico disponibile per questo file.",
                "error": "Analisi non disponibile", "normal": "Scenario tranquillo", "stress_scenario": "Scenario ansia", "updated": "Aggiornato al", "analyzed": "Analizzati",
            },
            "en": {
                "title": "Driving test probability analysis", "base": "Standard", "stress": "With anxiety", "english": "Italiano",
                "file": "Excel file to analyze", "file_help": "Choose the file with your test results. The first column must contain dates and the following columns error scores.", "browse": "Browse",
                "tests": "Number of tests to include", "tests_help": "A higher number gives a broader history. This is the number of recent tests included.",
                "half": "Half-life in days", "half_help": "After this many days, an old test has half its relevance. Lower values favor recent tests.",
                "anxiety": "Anxiety multiplier", "anxiety_help": "1.0 means normal conditions; higher values simulate performance loss under stress.",
                "calculate": "Calculate probability", "calculate_stress": "Calculate with anxiety", "waiting": "Waiting for results", "start": "Run an analysis to see an estimate.",
                "chart": "Error distribution in recent tests", "errors": "Number of errors", "occurrences": "Occurrences", "no_chart": "No chart is available for this file.",
                "error": "Analysis unavailable", "normal": "Calm scenario", "stress_scenario": "Anxiety scenario", "updated": "Updated on", "analyzed": "Analyzed",
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
        prefix = "base" if mode == "base" else "stress"
        title_widget = getattr(self, f"{prefix}_result_title")
        probability_widget = getattr(self, f"{prefix}_result_probability")
        details_widget = getattr(self, f"{prefix}_result_details")
        if not isinstance(result, dict):
            title_widget.configure(text=self.t("error"), fg="#fca5a5")
            probability_widget.configure(text="Errore", fg="#fca5a5")
            details_widget.configure(text=str(result))
            return
        if mode == "base":
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

    def _build_base_tab(self):
        frame = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(frame, text=self.t("base"))

        self.path_var = tk.StringVar(value=str(self.default_file))
        self.n_test_var = tk.DoubleVar(value=50)
        self.half_life_var = tk.DoubleVar(value=7)

        self._field_block(
            frame,
            self.t("file"), self.t("file_help"),
            self.path_var,
            row=0,
            width=68,
            button=ttk.Button(frame, text=self.t("browse"), command=self._choose_file),
        )

        self._slider_block(
            frame,
            self.t("tests"), self.t("tests_help"),
            self.n_test_var,
            row=3,
            minimum=5,
            maximum=200,
            formatter=lambda value: f"{float(value):.0f}",
        )

        self._slider_block(
            frame,
            self.t("half"), self.t("half_help"),
            self.half_life_var,
            row=6,
            minimum=1,
            maximum=30,
            formatter=lambda value: f"{float(value):.0f} giorni",
        )

        ttk.Button(frame, text=self.t("calculate"), command=self._run_base_analysis).grid(row=10, column=0, sticky="w", pady=(18, 10))
        self._result_panel(frame, 11, "base")

        self.base_chart = tk.Frame(frame, bg="#111827", height=220)
        self.base_chart.grid(row=11, column=2, rowspan=2, sticky="nsew", padx=(12, 0), pady=(12, 0))

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(11, weight=1)

    def _build_stress_tab(self):
        frame = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(frame, text=self.t("stress"))

        self.stress_path_var = tk.StringVar(value=str(self.default_file))
        self.stress_n_var = tk.DoubleVar(value=50)
        self.stress_half_var = tk.DoubleVar(value=7)
        self.stress_factor_var = tk.DoubleVar(value=1.2)

        self._field_block(
            frame,
            self.t("file"), self.t("file_help"),
            self.stress_path_var,
            row=0,
            width=68,
            button=ttk.Button(frame, text=self.t("browse"), command=lambda: self._choose_file("stress")),
        )

        self._slider_block(
            frame,
            self.t("tests"), self.t("tests_help"),
            self.stress_n_var,
            row=3,
            minimum=5,
            maximum=200,
            formatter=lambda value: f"{float(value):.0f}",
        )

        self._slider_block(
            frame,
            self.t("half"), self.t("half_help"),
            self.stress_half_var,
            row=6,
            minimum=1,
            maximum=30,
            formatter=lambda value: f"{float(value):.0f} giorni",
        )

        self._slider_block(
            frame,
            self.t("anxiety"), self.t("anxiety_help"),
            self.stress_factor_var,
            row=9,
            minimum=1,
            maximum=2,
            formatter=lambda value: f"{float(value):.1f}x",
            step=0.1,
        )

        ttk.Button(frame, text=self.t("calculate_stress"), command=self._run_stress_analysis).grid(row=13, column=0, sticky="w", pady=(18, 10))
        self._result_panel(frame, 14, "stress")

        self.stress_chart = tk.Frame(frame, bg="#111827", height=220)
        self.stress_chart.grid(row=14, column=2, rowspan=2, sticky="nsew", padx=(12, 0), pady=(12, 0))

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(14, weight=1)

    def _choose_file(self, target="base"):
        file_types = [("Excel", "*.xlsx"), ("Excel legacy", "*.xls"), ("Tutti i file", "*.*")]
        selected = filedialog.askopenfilename(filetypes=file_types)
        if selected:
            if target == "stress":
                self.stress_path_var.set(selected)
            else:
                self.path_var.set(selected)

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

    def _show_distribution_chart(self, container, nome_file, n_test):
        self._clear_chart(container)
        try:
            distribuzione = distribuzione_errori(nome_file, n_test)
            labels = ["0", "1", "2", "3", "4+"]
            values = [distribuzione.get(0, 0), distribuzione.get(1, 0), distribuzione.get(2, 0), distribuzione.get(3, 0), distribuzione.get(4, 0)]

            fig = Figure(figsize=(4.8, 2.2), dpi=100, facecolor="#111827")
            ax = fig.add_subplot(111)
            ax.set_facecolor("#111827")
            ax.bar(labels, values, color=["#38bdf8", "#60a5fa", "#a78bfa", "#fbbf24", "#f87171"])
            ax.set_title(self.t("chart"), color="#e2e8f0", fontsize=10, pad=8)
            ax.set_xlabel(self.t("errors"), color="#cbd5e1", fontsize=8)
            ax.set_ylabel(self.t("occurrences"), color="#cbd5e1", fontsize=8)
            ax.tick_params(colors="#cbd5e1", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#475569")
            ax.set_axisbelow(True)
            ax.grid(axis="y", linestyle="--", color="#475569", alpha=0.45)
            fig.tight_layout(pad=1.2)

            canvas = FigureCanvasTkAgg(fig, master=container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        except Exception:
            label = ttk.Label(container, text=self.t("no_chart"), foreground="#fca5a5")
            label.pack(padx=12, pady=12)

    def _run_base_analysis(self):
        try:
            nome_file = self.path_var.get().strip()
            n_test = int(self.n_test_var.get() or 50)
            emivita = float(self.half_life_var.get() or 7.0)
            if not nome_file:
                raise ValueError("Seleziona un file Excel.")
            result = analizza_predizione_patente(nome_file, n_test_da_analizzare=n_test, emivita_giorni=emivita)
            self._display_result(result, "base")
            self._show_distribution_chart(self.base_chart, nome_file, n_test)
        except Exception as exc:
            messagebox.showerror("Errore", str(exc))
            self._display_result(f"Errore: {exc}", "base")
            self._clear_chart(self.base_chart)

    def _run_stress_analysis(self):
        try:
            nome_file = self.stress_path_var.get().strip()
            n_test = int(self.stress_n_var.get() or 50)
            emivita = float(self.stress_half_var.get() or 7.0)
            ansia = float(self.stress_factor_var.get() or 1.2)
            if not nome_file:
                raise ValueError("Seleziona un file Excel.")
            result = analizza_predizione_patente_con_stress(nome_file, n_test, emivita, ansia)
            self._display_result(result, "stress")
            self._show_distribution_chart(self.stress_chart, nome_file, n_test)
        except Exception as exc:
            messagebox.showerror("Errore", str(exc))
            self._display_result(f"Errore: {exc}", "stress")
            self._clear_chart(self.stress_chart)


if __name__ == "__main__":
    os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")
    app = PatentApp()
    app.mainloop()
