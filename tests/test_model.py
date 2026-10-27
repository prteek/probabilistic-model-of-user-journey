import duckdb
import numpy as np
import pandas as pd

from user_journey.model import STATE_NAMES, forecast, transition_matrix


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
    state0 = pd.Series({"new": 10, "current": 100, "dormant": 50})
    new_users = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=2), "predicted": [5.7, 3.2]})
    out = forecast(m, state0, new_users)
    assert out.loc[0, "current"] == 110 and out.loc[0, "new"] == 5
    assert out.loc[1, "current"] == 115 and out.loc[1, "new"] == 3
    assert out.loc[1, "dau"] == 118 and out.loc[1, "mau"] == 118
