import os
import tempfile
import tkinter as tk
import unittest
from contextlib import contextmanager

import pandas as pd

from patente_core import (
    analizza_predizione_patente,
    analizza_predizione_records,
    analizza_predizione_records_con_stress,
    analizza_predizione_patente_con_stress,
    distribuzione_errori,
    distribuzione_errori_records,
)


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


class PatentGuiTestCase(unittest.TestCase):
    def setUp(self):
        try:
            from patente_gui import PatentApp
            self.app = PatentApp()
        except tk.TclError as error:
            self.skipTest(f'GUI non disponibile in questo ambiente: {error}')

    def tearDown(self):
        if getattr(self, 'app', None) is not None:
            self.app.destroy()

    def test_gui_has_parameter_sliders_and_language_menu(self):
        widgets = []

        def visit(parent):
            for child in parent.winfo_children():
                widgets.append(child)
                visit(child)

        visit(self.app)
        scales = [widget for widget in widgets if isinstance(widget, tk.Scale)]
        self.assertEqual(len(scales), 6)
        self.assertEqual(scales[-1].cget('resolution'), 0.1)
        self.assertEqual(self.app.language_menu.index('end') + 1, 2)

    def test_gui_language_menu_switches_tabs(self):
        self.app.language_menu.invoke(1)
        self.app.update_idletasks()
        self.assertEqual(self.app.language, 'en')
        self.assertEqual(self.app.notebook.tab(0, 'text'), 'Enter results')
        self.assertEqual(self.app.notebook.tab(1, 'text'), 'Standard')
        self.assertEqual(self.app.notebook.tab(2, 'text'), 'With anxiety')

    def test_gui_date_picker_selects_date(self):
        from datetime import date

        self.app._open_date_picker()
        self.app.update_idletasks()
        self.assertTrue(self.app.date_picker.winfo_exists())
        self.assertLess(abs(self.app.date_picker.winfo_rootx() + self.app.date_picker.winfo_width() / 2 - (self.app.winfo_rootx() + self.app.winfo_width() / 2)), 2)
        self.assertLess(abs(self.app.date_picker.winfo_rooty() + self.app.date_picker.winfo_height() / 2 - (self.app.winfo_rooty() + self.app.winfo_height() / 2)), 2)
        self.app._select_calendar_date(date(2026, 9, 20))
        self.assertEqual(self.app.entry_date_var.get(), '2026-09-20')

    def test_gui_uses_correct_result_wording(self):
        records = [{"data": "2026-09-16", "errori": 1}]
        self.app.records.extend(records)
        self.app._run_entry_analysis()
        self.assertEqual(self.app.entry_result_title.cget('text'), 'Probabilità stimata di superamento')


if __name__ == '__main__':
    unittest.main()
