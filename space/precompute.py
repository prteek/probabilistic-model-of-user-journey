"""Write space/baseline.json, everything the what-if app needs. The app replays the blog post's test: the transition
matrix of the training year, the state counts on its last day, and for the six test months the actual new users per
day and the actual daily, weekly and monthly active users. The transitions of the test period are included too, so
the app can show how they changed.

Run: uv run python space/precompute.py
"""
import json
from pathlib import Path

import duckdb

from user_journey.model import STATE_NAMES, state_counts, transition_matrix, with_active_totals
from user_journey.states import states

OUT = Path(__file__).with_name("baseline.json")
TRAIN = ("2022-05-01", "2023-04-30")  # as in the blog post
TEST = ("2023-05-01", "2023-10-31")
HISTORY_START = "2023-01-01"  # training data shown before the test period


def series(df):
    return {"date": [f"{d:%Y-%m-%d}" for d in df.index], **{c: df[c].round(1).tolist() for c in df.columns}}


con = duckdb.connect()
con.execute("SET enable_progress_bar = false")
s = states(con)
counts = with_active_totals(state_counts(s))

baseline = {
    "train": TRAIN,
    "test": TEST,
    "states": STATE_NAMES,
    "matrix": transition_matrix(s, *TRAIN).round(8).values.tolist(),
    "test_matrix": transition_matrix(s, *TEST).round(8).values.tolist(),
    "state0": counts.loc[TRAIN[1], STATE_NAMES].tolist(),
    "history": series(counts.loc[HISTORY_START:TRAIN[1], ["dau", "wau", "mau"]]),
    "test_period": series(counts.loc[TEST[0]:TEST[1], ["new", "dau", "wau", "mau"]]),
}
OUT.write_text(json.dumps(baseline, indent=1) + "\n")
print(f"wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} kB)")
