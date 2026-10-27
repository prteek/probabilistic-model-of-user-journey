"""Transition matrix, new-user count model and the DAU / WAU / MAU forecast."""
import duckdb
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

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


def new_user_features(dates) -> pd.DataFrame:
    dates = pd.to_datetime(pd.Series(dates))
    return pd.DataFrame({
        "date": dates.values,
        "year": dates.dt.year.values,
        "week_of_year": dates.dt.isocalendar().week.astype(int).values,
        "month": dates.dt.strftime("%b").values,
        "day_of_week": ((dates.dt.dayofweek + 1) % 7 + 1).values,  # 1 = Sunday ... 7 = Saturday
    })


NEW_USER_FORMULA = "new_user_count ~ year * bs(week_of_year, df=4) + C(month) + day_of_week"


def fit_new_users(daily_new_users: pd.DataFrame):
    """Negative binomial regression of daily new-user counts on year, a spline in week of year, month and weekday.

    `daily_new_users` has columns date and new_user_count.
    """
    data = new_user_features(daily_new_users["date"]).assign(new_user_count=daily_new_users["new_user_count"].values)
    return smf.negativebinomial(NEW_USER_FORMULA, data).fit(method="newton", maxiter=200, disp=False)


def predict_new_users(fit, dates) -> pd.DataFrame:
    """Expected new users per day with a 95% interval (on the log scale, transformed back)."""
    data = new_user_features(dates)
    # the formula rebuilds the design matrix with the fit's spline knots and month levels
    eta = fit.get_prediction(data, which="linear").summary_frame(alpha=0.05)
    return data[["date"]].assign(
        predicted=np.exp(eta["predicted"].values),
        lower=np.exp(eta["ci_lower"].values),
        upper=np.exp(eta["ci_upper"].values),
    )


def forecast(m: pd.DataFrame, state0: pd.Series, new_users: pd.DataFrame) -> pd.DataFrame:
    """Expected users in each state on every day of `new_users`, starting from the counts `state0` the day before.

    Each day moves the previous day's counts through the transition matrix, then sets today's new users from
    `new_users` (columns date and predicted). Counts are kept as whole users.
    """
    u = state0.reindex(STATE_NAMES, fill_value=0).to_numpy(float)
    rows = []
    for _, day in new_users.iterrows():
        u = np.floor(m.to_numpy().T @ u)
        u[STATE_NAMES.index("new")] = np.floor(day["predicted"])
        rows.append(u)
    out = pd.DataFrame(rows, columns=STATE_NAMES).assign(date=new_users["date"].values)
    out["dau"] = out[ACTIVE].sum(axis=1)
    out["wau"] = out["dau"] + out["at_risk_wau"]
    out["mau"] = out["wau"] + out["at_risk_mau"]
    return out
