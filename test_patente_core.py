import os
import tempfile
import tkinter as tk
import unittest
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from patente_core import (
    analizza_predizione_patente,
    analizza_predizione_records,
    analizza_predizione_records_con_stress,
    analizza_predizione_patente_con_stress,
    distribuzione_errori,
    distribuzione_errori_records,
)
from patente_storage import StorageError, load_records, load_settings, save_records, save_settings


class PatentCoreTestCase(unittest.TestCase):
    @contextmanager
    def create_workbook(self, rows):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test.xlsx')
            df = pd.DataFrame(rows)
            df.to_excel(path, index=False, header=False)
            yield path

    def test_simple_prediction_returns_complete_metrics(self):
        with self.create_workbook([
            ['2024-01-01', 1, 2, 3],
            ['2024-01-02', 0, 1, 2],
            ['2024-01-03', 2, 3, 1],
            ['2024-01-04', 1, 0, 2],
        ]) as path:
            result = analizza_predizione_patente(path, n_test_da_analizzare=10, emivita_giorni=7)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['test_analizzati'], 12)
        self.assertEqual(result['test_superati'], 12)
        self.assertEqual(result['data_riferimento'], '04/01/2024')
        self.assertGreaterEqual(result['prob_predittiva'], 0)
        self.assertLessEqual(result['prob_predittiva'], 100)
        self.assertGreater(result['lambda_atteso'], 0)

    def test_test_limit_is_applied_by_date_row(self):
        with self.create_workbook([
            ['2024-01-01', 0, 0],
            ['2024-01-02', 5, 5],
            ['2024-01-03', 1, 1],
        ]) as path:
            result = analizza_predizione_patente(path, n_test_da_analizzare=1, emivita_giorni=7)

        self.assertEqual(result['test_analizzati'], 2)
        self.assertEqual(result['test_superati'], 2)

    def test_invalid_cells_and_rows_are_ignored(self):
        with self.create_workbook([
            ['not a date', 2, 2],
            ['2024-01-01', 'bad', 2, None],
            ['2024-01-02', 1, '3'],
        ]) as path:
            result = analizza_predizione_patente(path, n_test_da_analizzare=50, emivita_giorni=7)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['test_analizzati'], 3)

    def test_missing_file_returns_readable_error(self):
        result = analizza_predizione_patente('missing-file.xlsx')
        self.assertIsInstance(result, str)
        self.assertIn('File non trovato', result)

    def test_empty_or_non_numeric_file_returns_error(self):
        with self.create_workbook([
            ['2024-01-01', 'no score'],
        ]) as path:
            result = analizza_predizione_patente(path)

        self.assertIsInstance(result, str)
        self.assertIn('dati numerici', result)

    def test_distribution_groups_four_or_more_errors(self):
        with self.create_workbook([
            ['2024-01-01', 0, 1, 2, 3, 4, 7],
        ]) as path:
            result = distribuzione_errori(path, n_test_da_analizzare=10)

        self.assertEqual(result, {0: 1, 1: 1, 2: 1, 3: 1, 4: 2})

    def test_stress_prediction_has_expected_keys(self):
        with self.create_workbook([
            ['2024-01-01', 2, 3, 4],
            ['2024-01-02', 1, 2, 3],
            ['2024-01-03', 3, 4, 2],
        ]) as path:
            result = analizza_predizione_patente_con_stress(path, 10, 7.0, 1.2)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['test_analizzati'], 9)
        self.assertGreater(result['lambda_stress'], result['lambda_base'])
        self.assertLess(result['prob_stress'], result['prob_base'])
        self.assertLessEqual(result['prob_stress'], 100)

    def test_invalid_half_life_is_reported(self):
        with self.create_workbook([
            ['2024-01-01', 1, 2],
        ]) as path:
            result = analizza_predizione_patente(path, emivita_giorni=0)

        self.assertIsInstance(result, str)
        self.assertIn('errore', result.lower())

    def test_in_memory_records_match_file_style_analysis(self):
        records = [
            {"data": "2024-01-01", "errori": 2},
            {"data": "2024-01-02", "errori": 0},
            {"data": "2024-01-03", "errori": 4},
        ]
        result = analizza_predizione_records(records, emivita_giorni=7)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['test_analizzati'], 3)
        self.assertEqual(result['data_riferimento'], '03/01/2024')

    def test_in_memory_stress_and_distribution(self):
        records = [
            {"data": "2024-01-01", "errori": 0},
            {"data": "2024-01-02", "errori": 4},
        ]
        stress = analizza_predizione_records_con_stress(records, 7, 1.2)
        distribution = distribuzione_errori_records(records)

        self.assertLess(stress['prob_stress'], stress['prob_base'])
        self.assertEqual(distribution, {0: 1, 1: 0, 2: 0, 3: 0, 4: 1})

    def test_storage_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "records.json"
            records = [{"data": "2026-09-16", "errori": 2}]
            save_records(records, path)
            self.assertEqual(load_records(path), records)

    def test_storage_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertEqual(load_records(Path(tmpdir) / "missing.json"), [])

    def test_storage_rejects_corrupt_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "records.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(StorageError):
                load_records(path)

    def test_storage_rejects_invalid_record_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "records.json"
            save_records([{"data": "2026-09-16", "errori": 1}], path)
            path.write_text("[{\"wrong\": 1}]", encoding="utf-8")
            with self.assertRaises(StorageError):
                load_records(path)

    def test_settings_round_trip_and_defaults(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "settings.json"
            defaults = load_settings(path)
            save_settings({"test_count": 80, "half_life": 14, "anxiety_mode": "stress", "anxiety_factor": 1.5}, path)
            loaded = load_settings(path)
        self.assertEqual(defaults["test_count"], 50)
        self.assertEqual(loaded["test_count"], 80)
        self.assertEqual(loaded["anxiety_mode"], "stress")


class PatentGuiTestCase(unittest.TestCase):
    def setUp(self):
        try:
            from patente_gui import PatentApp
            self.storage_directory = tempfile.TemporaryDirectory()
            self.storage_path = Path(self.storage_directory.name) / "records.json"
            self.settings_path = Path(self.storage_directory.name) / "settings.json"
            self.app = PatentApp(storage_path=self.storage_path, settings_path=self.settings_path)
        except tk.TclError as error:
            self.skipTest(f'GUI non disponibile in questo ambiente: {error}')

    def tearDown(self):
        if getattr(self, 'app', None) is not None:
            self.app.destroy()
        if getattr(self, 'storage_directory', None) is not None:
            self.storage_directory.cleanup()

    def test_gui_has_parameter_sliders_and_language_menu(self):
        widgets = []

        def visit(parent):
            for child in parent.winfo_children():
                widgets.append(child)
                visit(child)

        visit(self.app)
        scales = [widget for widget in widgets if isinstance(widget, tk.Scale)]
        self.assertEqual(len(scales), 4)
        self.assertEqual(scales[-1].cget('resolution'), 0.1)
        self.assertEqual(self.app.language_menu.index('end') + 1, 2)

    def test_gui_language_menu_switches_tabs(self):
        self.app.language_menu.invoke(1)
        self.app.update_idletasks()
        self.assertEqual(self.app.language, 'en')
        self.assertEqual(self.app.notebook.tab(0, 'text'), 'Enter results')
        self.assertEqual(self.app.notebook.tab(1, 'text'), 'Settings')

    def test_gui_date_picker_selects_date(self):
        from datetime import date

        self.app._open_date_picker()
        self.app.update_idletasks()
        self.assertTrue(self.app.date_picker.winfo_exists())
        self.assertLess(abs(self.app.date_picker.winfo_rootx() + self.app.date_picker.winfo_width() / 2 - (self.app.winfo_rootx() + self.app.winfo_width() / 2)), 2)
        self.assertLess(abs(self.app.date_picker.winfo_rooty() + self.app.date_picker.winfo_height() / 2 - (self.app.winfo_rooty() + self.app.winfo_height() / 2)), 2)
        self.app._select_calendar_date(date(2026, 9, 20))
        self.assertEqual(self.app.entry_date_var.get(), '20/09/2026')

    def test_gui_uses_correct_result_wording(self):
        records = [{"data": "2026-09-16", "errori": 1}]
        self.app.records.extend(records)
        self.app._open_entry_analysis()
        self.app.update_idletasks()
        self.assertEqual(self.app.popup_result_title.cget('text'), 'Probabilità stimata di superamento')
        self.assertEqual(self.app.notebook.index('end'), 2)
        self.app.popup_result_title.winfo_toplevel().destroy()

    def test_anxiety_mode_opens_comparison_popup(self):
        self.app.records.append({"data": "2026-09-16", "errori": 1})
        self.app.analysis_mode_var.set('stress')
        self.app._toggle_anxiety_slider()
        self.app._run_unified_analysis()
        self.app.update_idletasks()
        self.assertEqual(self.app.popup_result_title.cget('text'), 'Probabilità stimata in condizioni di ansia')
        self.app.popup_result_title.winfo_toplevel().destroy()

    def test_settings_disables_anxiety_controls_by_default(self):
        anxiety_scales = [widget for widget in self.app.anxiety_slider_frame.winfo_children() if isinstance(widget, tk.Scale)]
        self.assertEqual(len(anxiety_scales), 1)
        self.assertEqual(anxiety_scales[0].cget('state'), 'disabled')
        self.app.analysis_mode_var.set('stress')
        self.app._toggle_anxiety_slider()
        self.assertEqual(anxiety_scales[0].cget('state'), 'normal')

    def test_gui_persists_and_deletes_single_record(self):
        self.app.entry_date_var.set('16/09/2026')
        self.app.entry_errors_var.set(2)
        self.app._add_record()
        self.assertEqual(load_records(self.storage_path), [{"data": "2026-09-16", "errori": 2}])

        delete_button = next(child for child in self.app.records_list_frame.winfo_children()[1].winfo_children() if isinstance(child, tk.Button))
        delete_button.invoke()
        self.assertEqual(load_records(self.storage_path), [])

    def test_gui_reloads_saved_records(self):
        save_records([{"data": "2026-09-15", "errori": 1}], self.storage_path)
        self.app.destroy()
        self.app = __import__('patente_gui', fromlist=['PatentApp']).PatentApp(storage_path=self.storage_path, settings_path=self.settings_path)
        self.app.update_idletasks()
        self.assertEqual(self.app.records, [{"data": "2026-09-15", "errori": 1}])

    def test_gui_clear_all_is_persistent(self):
        self.app.records.append({"data": "2026-09-15", "errori": 1})
        self.app._persist_records()
        self.app._clear_records()
        self.assertEqual(load_records(self.storage_path), [])

    def test_record_list_scrolls_after_fifteen_entries(self):
        self.app.records = [{"data": f"2026-09-{day:02d}", "errori": day % 7} for day in range(1, 11)]
        self.app._refresh_record_list()
        self.app.update_idletasks()
        self.assertFalse(self.app.records_scrollbar.winfo_ismapped())

        self.app.records = [{"data": f"2026-09-{day:02d}", "errori": day % 7} for day in range(1, 17)]
        self.app._refresh_record_list()
        self.app.update_idletasks()
        bounds = self.app.records_canvas.bbox("all")
        self.assertIsNotNone(bounds)
        self.assertGreater(bounds[3] - bounds[1], self.app.records_canvas.winfo_height())
        self.assertTrue(self.app.records_scrollbar.winfo_ismapped())
        visible_text = [child.cget("text") for child in self.app.records_list_frame.winfo_children()[0].winfo_children()]
        self.assertNotIn("Rimuovi selezionato", visible_text)

    def test_gui_persists_settings_for_next_start(self):
        self.app.n_test_var.set(80)
        self.app.half_life_var.set(14)
        self.app.analysis_mode_var.set('stress')
        self.app._toggle_anxiety_slider()
        self.app.anxiety_factor_var.set(1.5)
        self.app.destroy()
        self.app = __import__('patente_gui', fromlist=['PatentApp']).PatentApp(storage_path=self.storage_path, settings_path=self.settings_path)
        self.app.update_idletasks()
        self.assertEqual(int(self.app.n_test_var.get()), 80)
        self.assertEqual(float(self.app.half_life_var.get()), 14)
        self.assertEqual(self.app.analysis_mode_var.get(), 'stress')
        self.assertAlmostEqual(float(self.app.anxiety_factor_var.get()), 1.5)


if __name__ == '__main__':
    unittest.main()
