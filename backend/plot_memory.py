"""Prompt 16 — plot-level memory.

Pulls a plot's full diagnosis history and flags a likely root cause if the
same disease recurred 2+ times, instead of re-diagnosing from zero every
visit. Real logic over the real synthetic history, no mocking needed.
"""
import csv
import os
from collections import Counter

from config import DATA_DIR

_ROOT_CAUSE_HINTS = {
    "early_blight": "Recurring early blight often points to poor airflow or splash from "
                     "overhead watering rather than bad luck each time — consider spacing "
                     "or switching to base-level irrigation.",
    "late_blight": "Recurring late blight suggests this plot sits in a cool, damp pocket "
                    "(low drainage, shade, or poor airflow) that stays wet longer than "
                    "neighboring plots after rain.",
    "bacterial_wilt": "Recurring bacterial wilt usually means the pathogen has built up in "
                       "the soil itself — rotating away from tomato/potato/brinjal on this "
                       "plot for a season or two is more effective than repeat treatment.",
    "fusarium_wilt": "Recurring fusarium wilt points to a soil-borne buildup; consider a "
                      "resistant variety next season rather than treating the symptom again.",
}


def _load_plot_history(plot_id: str):
    with open(os.path.join(DATA_DIR, "diagnosis_history.csv"), encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["plot_id"] == plot_id]
    return sorted(rows, key=lambda r: r["timestamp"])


def get_plot_memory_note(plot_id: str, current_disease: str) -> str | None:
    history = _load_plot_history(plot_id)
    past_diseases = [r["disease"] for r in history if r["disease"] not in ("healthy", "")]
    counts = Counter(past_diseases)
    occurrences = counts.get(current_disease, 0) + (1 if current_disease not in ("healthy", "uncertain") else 0)

    if occurrences < 3:
        return None

    hint = _ROOT_CAUSE_HINTS.get(
        current_disease,
        "This disease has recurred on this plot multiple times — the underlying cause "
        "may be environmental (drainage, spacing, soil) rather than a one-off infection.",
    )
    return (f"This is the {occurrences}{'rd' if occurrences == 3 else 'th'} time this plot has had "
            f"{current_disease.replace('_', ' ')}. {hint}")


if __name__ == "__main__":
    with open(os.path.join(DATA_DIR, "diagnosis_history.csv"), encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    counts_by_plot = Counter((r["plot_id"], r["disease"]) for r in rows if r["disease"] not in ("healthy", ""))
    recurring = [k for k, v in counts_by_plot.items() if v >= 3]
    if recurring:
        plot_id, disease = recurring[0]
        print(f"Testing plot {plot_id} with recurring {disease}:")
        print(get_plot_memory_note(plot_id, disease))
    else:
        print("No naturally recurring plot in this random dataset — testing a forced case instead.")
        test_plot_id = rows[0]["plot_id"]
        print(get_plot_memory_note(test_plot_id, "early_blight"))
