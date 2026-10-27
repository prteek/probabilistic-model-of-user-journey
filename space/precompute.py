"""Write space/baseline.json, everything the what-if app needs: the transition matrix of the last year of data, the
state counts on the last day, recent daily, weekly and monthly active users, and recent new users per day.

Run: uv run python space/precompute.py
"""
import json
from pathlib import Path

import duckdb

from user_journey.model import STATE_NAMES, state_counts, transition_matrix, with_active_totals
from user_journey.states import states

OUT = Path(__file__).with_name("baseline.json")
WINDOW = ("2022-11-01", "2023-10-31")  # the matrix reflects the last year of behaviour
HISTORY_DAYS = 180  # shown before the projection
NEW_USER_DAYS = 90  # the default new users per day is their recent average

con = duckdb.connect()
con.execute("SET enable_progress_bar = false")
s = states(con)
m = transition_matrix(s, *WINDOW)
counts = with_active_totals(state_counts(s))
last = counts.index.max()
history = counts.iloc[-HISTORY_DAYS:]

baseline = {
    "window": WINDOW,
    "last_day": f"{last:%Y-%m-%d}",
    "states": STATE_NAMES,
    "matrix": m.round(8).values.tolist(),
    "state0": counts.loc[last, STATE_NAMES].tolist(),
    "new_users_per_day": round(float(counts["new"].iloc[-NEW_USER_DAYS:].mean()), 1),
    "history": {
        "date": [f"{d:%Y-%m-%d}" for d in history.index],
        **{col: history[col].tolist() for col in ("dau", "wau", "mau")},
    },
}
OUT.write_text(json.dumps(baseline, indent=1) + "\n")
print(f"wrote {OUT} ({OUT.stat().st_size / 1e3:.0f} kB)")
