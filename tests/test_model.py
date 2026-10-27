import duckdb
import numpy as np
import pandas as pd

from user_journey.model import STATE_NAMES, forecast, state_counts, transition_matrix, with_active_totals, with_transition


def test_transition_matrix_counts_moves_within_users():
    df = pd.DataFrame({
        "user_id": ["a"] * 4 + ["b"] * 3,
        "date": pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"]
                               + ["2024-01-01", "2024-01-02", "2024-01-03"]),
        "state": ["new", "current", "current", "at_risk_wau", "new", "at_risk_wau", "current"],
    })
    m = transition_matrix(duckdb.from_df(df), "2024-01-01", "2024-01-31")
    assert m.loc["new", "current"] == 0.5 and m.loc["new", "at_risk_wau"] == 0.5
    assert m.loc["current", "current"] == 0.5 and m.loc["current", "at_risk_wau"] == 0.5
    assert m.loc["at_risk_wau", "current"] == 1.0
    observed = m.sum(axis=1) > 0
    assert np.allclose(m[observed].sum(axis=1), 1)
    assert list(m.columns) == STATE_NAMES


def test_forecast_moves_counts_and_adds_new_users():
    m = pd.DataFrame(np.eye(len(STATE_NAMES)), index=STATE_NAMES, columns=STATE_NAMES)
    m.loc["new"] = 0.0
    m.loc["new", "current"] = 1.0  # every new user is current the next day
    m.loc["current", "current"], m.loc["current", "at_risk_wau"] = 0.5, 0.5
    state0 = pd.Series({"new": 10, "current": 100, "dormant": 50})
    new_users = pd.Series([5, 3], index=pd.date_range("2024-01-01", periods=2))
    out = forecast(m, state0, new_users)
    # day 1: half of the 100 current stay, the 10 new become current; 5 new users arrive
    assert out.loc["2024-01-01", "current"] == 60 and out.loc["2024-01-01", "new"] == 5
    assert out.loc["2024-01-01", "at_risk_wau"] == 50
    # day 2: expected counts are kept as they are, not rounded
    assert out.loc["2024-01-02", "current"] == 35 and out.loc["2024-01-02", "at_risk_wau"] == 80
    assert out.loc["2024-01-02", "dau"] == 38 and out.loc["2024-01-02", "wau"] == 118
    assert out.loc["2024-01-02", "mau"] == 118


def test_state_counts_and_active_totals():
    df = pd.DataFrame({
        "user_id": ["a", "b", "c"],
        "date": pd.to_datetime(["2024-01-01"] * 3),
        "state": ["current", "at_risk_wau", "at_risk_mau"],
    })
    counts = with_active_totals(state_counts(duckdb.from_df(df)))
    day = counts.loc["2024-01-01"]
    assert (day["dau"], day["wau"], day["mau"]) == (1, 2, 3)


def test_with_transition_keeps_rows_summing_to_one():
    m = pd.DataFrame(0.0, index=STATE_NAMES, columns=STATE_NAMES)
    m.loc["at_risk_wau", ["current", "at_risk_wau", "at_risk_mau"]] = [0.1, 0.6, 0.3]
    out = with_transition(m, "at_risk_wau", "current", 0.3)
    row = out.loc["at_risk_wau"]
    assert row["current"] == 0.3
    # the other 70% keeps the 2:1 split of the original 90%
    assert np.isclose(row["at_risk_wau"], 0.7 * 2 / 3) and np.isclose(row["at_risk_mau"], 0.7 / 3)
    assert np.isclose(row.sum(), 1)
    assert m.loc["at_risk_wau", "current"] == 0.1  # the input is unchanged
