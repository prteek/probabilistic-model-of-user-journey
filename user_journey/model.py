"""Transition matrix, daily state counts and the DAU / WAU / MAU forecast."""
import duckdb
import numpy as np
import pandas as pd

STATE_NAMES = ["at_risk_mau", "at_risk_wau", "current", "dormant", "new", "reactivated", "resurrected"]
ACTIVE = ["new", "current", "reactivated", "resurrected"]

TRANSITIONS_SQL = """
with slice as (
    select user_id, date, state
    from states
    where date between '{start}' and '{end}'
),
moves as (
    select state as state_from, lead(state) over (partition by user_id order by date) as state_to
    from slice
)
select state_from, state_to, count(*) as n
from moves
where state_to is not null
group by all
"""


def transition_matrix(states: duckdb.DuckDBPyRelation, start, end) -> pd.DataFrame:
    """Share of users moving from each state (rows) to each state (columns) from one day to the next.

    Estimated from every user's consecutive days between `start` and `end`; each row sums to 1.
    """
    counts = states.query("states", TRANSITIONS_SQL.format(start=start, end=end)).df()
    m = counts.pivot_table(index="state_from", columns="state_to", values="n", aggfunc="sum", fill_value=0)
    m = m.reindex(index=STATE_NAMES, columns=STATE_NAMES, fill_value=0).astype(float)
    return m.div(m.sum(axis=1), axis=0)


def state_counts(states: duckdb.DuckDBPyRelation) -> pd.DataFrame:
    """Number of users in each state on each day (rows: dates, columns: STATE_NAMES)."""
    df = states.aggregate("date, state, count(*) as n").df()
    counts = df.pivot_table(index="date", columns="state", values="n", fill_value=0)
    counts.index = pd.to_datetime(counts.index)
    return counts.reindex(columns=STATE_NAMES, fill_value=0).astype(float)


def with_active_totals(counts: pd.DataFrame) -> pd.DataFrame:
    """Add daily, weekly and monthly active users to a table of state counts."""
    out = counts.copy()
    out["dau"] = out[ACTIVE].sum(axis=1)
    out["wau"] = out["dau"] + out["at_risk_wau"]
    out["mau"] = out["wau"] + out["at_risk_mau"]
    return out


def with_transition(m: pd.DataFrame, state_from: str, state_to: str, p: float) -> pd.DataFrame:
    """A copy of `m` with the probability of `state_from` -> `state_to` set to `p`.

    The other transitions out of `state_from` are scaled in proportion, so the row still sums to 1: a campaign that
    brings more at-risk users back takes them evenly from wherever else they would have gone.
    """
    out = m.copy()
    row = out.loc[state_from].copy()
    rest = 1 - row[state_to]
    others = row.index != state_to
    row[others] = row[others] * (1 - p) / rest if rest > 0 else (1 - p) / others.sum()
    row[state_to] = p
    out.loc[state_from] = row
    return out


def forecast(m: pd.DataFrame, state0: pd.Series, new_users: pd.Series) -> pd.DataFrame:
    """Expected users in each state on every day of `new_users`, starting from the counts `state0` the day before.

    Each day moves the previous day's counts through the transition matrix, then sets the day's new users from
    `new_users` (indexed by date): new users come from outside the chain.
    """
    u = state0.reindex(STATE_NAMES, fill_value=0).to_numpy(float)
    rows = []
    for n_new in new_users.to_numpy(float):
        u = m.to_numpy().T @ u
        u[STATE_NAMES.index("new")] = n_new
        rows.append(u)
    return with_active_totals(pd.DataFrame(rows, columns=STATE_NAMES, index=new_users.index))
