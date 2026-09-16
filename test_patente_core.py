import os
import tempfile
import tkinter as tk
import unittest
from contextlib import contextmanager
from pathlib import Path
from tkinter import ttk

import pandas as pd

from patente_core import (
    analyze_excel,
    analyze_excel_with_anxiety,
    analyze_records,
    analyze_records_with_anxiety,
    error_distribution_from_excel,
    error_distribution_from_records,
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
            result = analyze_excel(path, row_limit=10, half_life_days=7)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['tests_analyzed'], 12)
        self.assertEqual(result['passed_tests'], 12)
        self.assertEqual(result['reference_date'], '04/01/2024')
        self.assertGreaterEqual(result['predicted_probability'], 0)
        self.assertLessEqual(result['predicted_probability'], 100)
        self.assertGreater(result['expected_errors'], 0)

    def test_test_limit_is_applied_by_date_row(self):
        with self.create_workbook([
            ['2024-01-01', 0, 0],
            ['2024-01-02', 5, 5],
            ['2024-01-03', 1, 1],
        ]) as path:
            result = analyze_excel(path, row_limit=1, half_life_days=7)

        self.assertEqual(result['tests_analyzed'], 2)
        self.assertEqual(result['passed_tests'], 2)

    def test_invalid_cells_and_rows_are_ignored(self):
        with self.create_workbook([
            ['not a date', 2, 2],
            ['2024-01-01', 'bad', 2, None],
            ['2024-01-02', 1, '3'],
        ]) as path:
            result = analyze_excel(path, row_limit=50, half_life_days=7)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['tests_analyzed'], 3)

    def test_missing_file_returns_readable_error(self):
        result = analyze_excel('missing-file.xlsx')
        self.assertIsInstance(result, str)
        self.assertIn('File not found', result)

    def test_empty_or_non_numeric_file_returns_error(self):
        with self.create_workbook([
            ['2024-01-01', 'no score'],
        ]) as path:
            result = analyze_excel(path)

        self.assertIsInstance(result, str)
        self.assertIn('numeric test results', result)

    def test_distribution_groups_four_or_more_errors(self):
        with self.create_workbook([
            ['2024-01-01', 0, 1, 2, 3, 4, 7],
        ]) as path:
            result = error_distribution_from_excel(path, row_limit=10)

        self.assertEqual(result, {0: 1, 1: 1, 2: 1, 3: 1, 4: 2})

    def test_stress_prediction_has_expected_keys(self):
        with self.create_workbook([
            ['2024-01-01', 2, 3, 4],
            ['2024-01-02', 1, 2, 3],
            ['2024-01-03', 3, 4, 2],
        ]) as path:
            result = analyze_excel_with_anxiety(path, 10, 7.0, 1.2)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['tests_analyzed'], 9)
        self.assertGreater(result['stress_expected_errors'], result['base_expected_errors'])
        self.assertLess(result['stress_probability'], result['base_probability'])
        self.assertLessEqual(result['stress_probability'], 100)

    def test_invalid_half_life_is_reported(self):
        with self.create_workbook([
            ['2024-01-01', 1, 2],
        ]) as path:
            result = analyze_excel(path, half_life_days=0)

        self.assertIsInstance(result, str)
        self.assertIn('analysis error', result.lower())

    def test_in_memory_records_match_file_style_analysis(self):
        records = [
            {"date": "2024-01-01", "errors": 2},
            {"date": "2024-01-02", "errors": 0},
            {"date": "2024-01-03", "errors": 4},
        ]
        result = analyze_records(records, half_life_days=7)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['tests_analyzed'], 3)
        self.assertEqual(result['reference_date'], '03/01/2024')

    def test_in_memory_stress_and_distribution(self):
        records = [
            {"date": "2024-01-01", "errors": 0},
            {"date": "2024-01-02", "errors": 4},
        ]
        stress = analyze_records_with_anxiety(records, 7, 1.2)
        distribution = error_distribution_from_records(records)

        self.assertLess(stress['stress_probability'], stress['base_probability'])
        self.assertEqual(distribution, {0: 1, 1: 0, 2: 0, 3: 0, 4: 1})

    def test_storage_round_trip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "records.json"
            records = [{"date": "2026-09-16", "errors": 2}]
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
            save_records([{"date": "2026-09-16", "errors": 1}], path)
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
        self.app.notebook.select(1)
        self.app.language_menu.invoke(1)
        self.app.update_idletasks()
        self.assertEqual(self.app.language, 'en')
        self.assertEqual(self.app.notebook.tab(0, 'text'), 'Enter results')
        self.assertEqual(self.app.notebook.tab(1, 'text'), 'Settings')
        self.assertEqual(self.app.notebook.index(self.app.notebook.select()), 1)

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
        records = [{"date": "2026-09-16", "errors": 1}]
        self.app.records.extend(records)
        self.app._open_entry_analysis()
        self.app.update_idletasks()
        self.assertEqual(self.app.popup_result_title.cget('text'), 'Probabilità stimata di superamento')
        self.assertEqual(self.app.notebook.index('end'), 2)
        self.app.popup_result_title.winfo_toplevel().destroy()

    def test_anxiety_mode_opens_comparison_popup(self):
        self.app.records.append({"date": "2026-09-16", "errors": 1})
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
        self.assertEqual(load_records(self.storage_path), [{"date": "2026-09-16", "errors": 2}])

        delete_button = next(child for child in self.app.records_list_frame.winfo_children()[1].winfo_children() if isinstance(child, tk.Button))
        delete_button.invoke()
        self.assertEqual(load_records(self.storage_path), [])

    def test_gui_reloads_saved_records(self):
        save_records([{"date": "2026-09-15", "errors": 1}], self.storage_path)
        self.app.destroy()
        self.app = __import__('patente_gui', fromlist=['PatentApp']).PatentApp(storage_path=self.storage_path, settings_path=self.settings_path)
        self.app.update_idletasks()
        self.assertEqual(self.app.records, [{"date": "2026-09-15", "errors": 1}])

    def test_gui_clear_all_is_persistent(self):
        self.app.records.append({"date": "2026-09-15", "errors": 1})
        self.app._persist_records()
        self.app._clear_records()
        self.assertEqual(load_records(self.storage_path), [])

    def test_record_list_scrolls_after_fifteen_entries(self):
        self.app.records = [{"date": f"2026-09-{day:02d}", "errors": day % 7} for day in range(1, 11)]
        self.app._refresh_record_list()
        self.app.update_idletasks()
        self.assertFalse(self.app.records_scrollbar.winfo_ismapped())

        self.app.records = [{"date": f"2026-09-{day:02d}", "errors": day % 7} for day in range(1, 17)]
        self.app._refresh_record_list()
        self.app.update_idletasks()
        bounds = self.app.records_canvas.bbox("all")
        self.assertIsNotNone(bounds)
        self.assertGreater(bounds[3] - bounds[1], self.app.records_canvas.winfo_height())
        self.assertTrue(self.app.records_scrollbar.winfo_ismapped())
        visible_text = [child.cget("text") for child in self.app.records_list_frame.winfo_children()[0].winfo_children()]
        self.assertNotIn("Rimuovi selezionato", visible_text)

    def test_graphics_keep_analysis_button_visible_at_startup(self):
        self.app.records = [{"date": f"2026-09-{day:02d}", "errors": 2} for day in range(1, 11)]
        self.app._refresh_record_list()
        tab = self.app.notebook.nametowidget(self.app.notebook.tabs()[0])
        content = tab.winfo_children()[0]
        analyze_button = next(widget for widget in content.winfo_children() if isinstance(widget, ttk.Button) and widget.cget("text") == self.app.t("analyze_entries"))
        self.app.update_idletasks()
        self.assertTrue(analyze_button.winfo_ismapped())
        self.assertLess(analyze_button.winfo_rooty() + analyze_button.winfo_height(), self.app.winfo_rooty() + self.app.winfo_height())
        self.assertGreaterEqual(self.app.winfo_height(), 820)

    def test_graphics_use_dark_scrollbar_and_red_delete_buttons(self):
        self.app.records = [{"date": f"2026-09-{day:02d}", "errors": 2} for day in range(1, 4)]
        self.app._refresh_record_list()
        rows = self.app.records_list_frame.winfo_children()[1:]
        delete_buttons = [row.winfo_children()[-1] for row in rows]
        self.assertEqual(len(delete_buttons), 3)
        self.assertTrue(all(button.cget("bg") == "#ef4444" for button in delete_buttons))
        self.assertEqual(self.app.tk.call("ttk::style", "lookup", "Dark.Vertical.TScrollbar", "-background"), "#263653")

    def test_graphics_center_tab_content(self):
        self.app.update_idletasks()
        tab = self.app.notebook.nametowidget(self.app.notebook.tabs()[0])
        content = tab.winfo_children()[0]
        tab_center = tab.winfo_rootx() + tab.winfo_width() / 2
        content_center = content.winfo_rootx() + content.winfo_width() / 2
        self.assertLess(abs(tab_center - content_center), 2)

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
