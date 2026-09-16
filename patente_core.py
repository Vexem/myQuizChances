import math
from pathlib import Path

import numpy as np
import pandas as pd

PASSING_ERROR_LIMIT = 3


def load_excel_groups(file_name):
    path = Path(file_name)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_name}")

    frame = pd.read_excel(path, header=None)
    if frame.empty:
        raise ValueError("The Excel file is empty.")
    if frame.shape[1] < 2:
        raise ValueError("The Excel file must contain a date column and result columns.")

    groups = []
    for _, row in frame.iterrows():
        if row.empty:
            continue
        try:
            test_date = pd.to_datetime(row.iloc[0])
        except (TypeError, ValueError):
            continue

        errors = []
        for value in row.iloc[1:]:
            if pd.isna(value):
                continue
            try:
                errors.append(float(value))
            except (TypeError, ValueError):
                continue
        if errors:
            groups.append({"date": test_date, "errors": errors})

    if not groups:
        raise ValueError("No numeric test results were found in the Excel file.")
    return groups


def flatten_recent_events(groups, row_limit):
    ordered_groups = sorted(groups, key=lambda item: item["date"])
    recent_groups = ordered_groups[-row_limit:]
    return [
        {"date": group["date"], "errors": float(error)}
        for group in recent_groups
        for error in group["errors"]
    ]


def poisson_cdf_at_limit(expected_errors):
    probability = 0.0
    for error_count in range(PASSING_ERROR_LIMIT + 1):
        probability += (math.exp(-expected_errors) * expected_errors ** error_count) / math.factorial(error_count)
    return min(100.0, probability * 100)


def analyze_events(events, half_life_days):
    if not events:
        raise ValueError("There are no results to analyze.")
    if half_life_days <= 0:
        raise ValueError("Half-life must be greater than zero.")

    ordered_events = sorted(events, key=lambda item: item["date"])
    reference_date = ordered_events[-1]["date"]
    decay_rate = math.log(2) / half_life_days
    weights = []
    errors = []
    for event in ordered_events:
        days_since_test = max(0, (reference_date - event["date"]).days)
        weights.append(math.exp(-decay_rate * days_since_test))
        errors.append(float(event["errors"]))

    normalized_weights = np.array(weights, dtype=float) / np.sum(weights)
    error_values = np.array(errors, dtype=float)
    expected_errors = float(np.sum(error_values * normalized_weights))
    passed_tests = int(sum(error <= PASSING_ERROR_LIMIT for error in error_values))
    return {
        "tests_analyzed": len(error_values),
        "reference_date": reference_date.strftime("%d/%m/%Y"),
        "half_life": half_life_days,
        "expected_errors": expected_errors,
        "passed_tests": passed_tests,
        "historical_percentage": (passed_tests / len(error_values)) * 100,
        "predicted_probability": poisson_cdf_at_limit(expected_errors),
    }


def normalize_records(records):
    events = []
    for record in records:
        test_date = pd.to_datetime(record["date"])
        errors = float(record["errors"])
        if errors < 0:
            raise ValueError("The number of errors cannot be negative.")
        events.append({"date": test_date, "errors": errors})
    return events


def analyze_records(records, half_life_days=7.0):
    try:
        return analyze_events(normalize_records(records), half_life_days)
    except Exception as error:
        return f"Analysis error: {error}"


def analyze_records_with_anxiety(records, half_life_days, anxiety_factor):
    try:
        base_result = analyze_events(normalize_records(records), half_life_days)
        base_expected_errors = base_result["expected_errors"]
        stress_expected_errors = base_expected_errors * anxiety_factor
        return {
            "tests_analyzed": base_result["tests_analyzed"],
            "reference_date": base_result["reference_date"],
            "base_expected_errors": base_expected_errors,
            "stress_expected_errors": stress_expected_errors,
            "base_probability": poisson_cdf_at_limit(base_expected_errors),
            "stress_probability": poisson_cdf_at_limit(stress_expected_errors),
        }
    except Exception as error:
        return f"Analysis error: {error}"


def error_distribution_from_records(records):
    distribution = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    for record in normalize_records(records):
        error_count = int(record["errors"])
        distribution[min(error_count, 4)] += 1
    return distribution


def analyze_excel(file_name, row_limit=9999, half_life_days=7.0):
    try:
        events = flatten_recent_events(load_excel_groups(file_name), row_limit)
        return analyze_events(events, half_life_days)
    except Exception as error:
        return f"Analysis error: {error}"


def error_distribution_from_excel(file_name, row_limit=50):
    events = flatten_recent_events(load_excel_groups(file_name), row_limit)
    return error_distribution_from_records(
        [{"date": event["date"], "errors": event["errors"]} for event in events]
    )


def analyze_excel_with_anxiety(file_name, row_limit, half_life_days, anxiety_factor):
    try:
        events = flatten_recent_events(load_excel_groups(file_name), row_limit)
        records = [{"date": event["date"], "errors": event["errors"]} for event in events]
        return analyze_records_with_anxiety(records, half_life_days, anxiety_factor)
    except Exception as error:
        return f"Analysis error: {error}"
