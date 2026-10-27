import duckdb
import pandas as pd

from user_journey.states import states


def states_of(tmp_path, active_days, registration="2024-01-01", other_user_until="2024-03-31"):
    """States of user `u` active on `active_days`; a second user stretches the data to `other_user_until`."""
    rows = [("u", d, registration) for d in active_days] + [("v", other_user_until, other_user_until)]
    path = tmp_path / "dau.csv"
    pd.DataFrame(rows, columns=["user_id", "date", "registration_date"]).to_csv(path, index=False)
    df = states(duckdb.connect(), path).filter("user_id = 'u'").order("date").df()
    return dict(zip(df["date"].dt.strftime("%Y-%m-%d"), df["state"]))


def test_state_rules(tmp_path):
    s = states_of(tmp_path, ["2024-01-01", "2024-01-02", "2024-01-12", "2024-02-20"])
    assert s["2024-01-01"] == "new"
    assert s["2024-01-02"] == "current"
    assert s["2024-01-03"] == "at_risk_wau"      # 1 day since last active
    assert s["2024-01-08"] == "at_risk_wau"      # 6 days
    assert s["2024-01-09"] == "at_risk_mau"      # 7 days
    assert s["2024-01-12"] == "reactivated"      # active again after 10 days
    assert s["2024-02-11"] == "at_risk_mau"      # 30 days
    assert s["2024-02-12"] == "dormant"          # 31 days
    assert s["2024-02-20"] == "resurrected"      # active again after 39 days
    assert s["2024-03-31"] == "dormant"          # rows run to the end of the data


def test_rows_start_at_first_active_day(tmp_path):
    # registered before the data starts: the first row is the first active day, not the registration day
    s = states_of(tmp_path, ["2024-01-05", "2024-01-06"], registration="2023-12-01")
    assert min(s) == "2024-01-05"
    assert s["2024-01-05"] == "current"
