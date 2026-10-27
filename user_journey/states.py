"""One state per user per day, from the activity records.

Every user gets a row for every day from their first active day to the last day of the data. A day's state follows
from whether the user was active that day and how many days earlier they were last active:

- new: the registration day
- current / reactivated / resurrected: active, last active at most 6 / 7 to 30 / more than 30 days earlier
- at_risk_wau / at_risk_mau / dormant: inactive, last active at most 6 / 7 to 30 / more than 30 days earlier

Run `python -m user_journey.states` to write states.parquet (published as the `states` config of the dataset).
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DAU_DATA = ROOT / "dau_data.csv"
STATES = ROOT / "states.parquet"

STATES_SQL = """
with activity as (
    select user_id, cast(date as date) as date, cast(registration_date as date) as registration_date
    from read_csv_auto('{path}')
),
users as (
    select user_id, any_value(registration_date) as registration_date, min(date) as first_active
    from activity
    group by user_id
),
days as (
    select cast(range as date) as date
    from range((select min(date) from activity), (select max(date) from activity) + 1, interval 1 day)
),
user_days as (
    select u.user_id, d.date, u.registration_date, a.date is not null as is_active
    from users u
    join days d on d.date >= greatest(u.registration_date, u.first_active)
    left join activity a on a.user_id = u.user_id and a.date = d.date
),
with_last_active as (
    select *,
        -- the last active day before today; on a user's first row, today
        coalesce(
            max(case when is_active then date end) over (
                partition by user_id order by date rows between unbounded preceding and 1 preceding),
            date) as last_active
    from user_days
)
select user_id, date, is_active,
    case
        when date = registration_date then 'new'
        when is_active and date - last_active <= 6 then 'current'
        when is_active and date - last_active <= 30 then 'reactivated'
        when is_active then 'resurrected'
        when date - last_active <= 6 then 'at_risk_wau'
        when date - last_active <= 30 then 'at_risk_mau'
        else 'dormant'
    end as state,
    registration_date
from with_last_active
"""


def states(con: duckdb.DuckDBPyConnection, dau_data: Path = DAU_DATA) -> duckdb.DuckDBPyRelation:
    """The states table as a DuckDB relation (32 million rows for the full data; query it rather than load it)."""
    return con.sql(STATES_SQL.format(path=dau_data))


if __name__ == "__main__":
    con = duckdb.connect()
    states(con).order("user_id, date").write_parquet(str(STATES), compression="zstd")
    print(f"wrote {STATES}")
