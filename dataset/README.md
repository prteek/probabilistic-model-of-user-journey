---
license: cc-by-4.0
language:
  - en
pretty_name: Simulated daily active users of an app
tags:
  - time-series
  - user-behaviour
  - retention
  - markov-chain
  - tabular
size_categories:
  - 100K<n<1M
configs:
  - config_name: default
    data_files: dau_data.csv
---

# Simulated daily active users of an app

667,236 records of daily user activity in an app: 51,480 users active between 1 October 2020 and 31 October 2023.
Each row is one day on which one user was active. The data is **simulated**, based on historical activity data of a
SaaS app; it contains no real users.

It is the data behind the blog post
[Forecasting Daily Active Users with a Markov Chain](https://huggingface.co/blog/prteek/probabilistic-model-of-user-journey) on
Hugging Face, which places users in seven states each day (new, current, reactivated, resurrected, at-risk weekly active,
at-risk monthly active, dormant) following Duolingo's growth model, estimates a Markov chain of transitions between
them, and forecasts daily, weekly and monthly active users.
Code: [github.com/prteek/probabilistic-model-of-user-journey](https://github.com/prteek/probabilistic-model-of-user-journey).

## Activity records (`dau_data.csv`)

| column | content |
|---|---|
| `user_id` | anonymous user id (UUID) |
| `date` | a day on which the user was active (2020-10-01 to 2023-10-31) |
| `registration_date` | the day the user registered (2020-04-20 to 2023-10-31) |

Days without a row for a user are days on which the user was inactive.

## User states, derived

The states used in the blog post (one row per user per day, 32,111,109 rows) are not stored here: a single DuckDB
query builds them from the activity records in a few seconds. It is `user_journey/states.py` in the code repository:

```python
import duckdb
from user_journey.states import states

states(duckdb.connect(), "dau_data.csv").write_parquet("states.parquet")
```

| column | content |
|---|---|
| `user_id` | anonymous user id (UUID) |
| `date` | the day (2020-10-01 to 2023-10-31) |
| `is_active` | whether the user was active that day (true on the 667,236 days in the activity records) |
| `state` | the user's state that day (below) |
| `registration_date` | the day the user registered |

| state | meaning | rows |
|---|---|---:|
| `new` | active for the first time | 50,175 |
| `current` | active today and in the past week | 585,129 |
| `reactivated` | active today, last active in the past month but not the past week | 16,847 |
| `resurrected` | active today, last active more than 30 days ago | 15,085 |
| `at_risk_wau` | not active today, active in the past week | 604,449 |
| `at_risk_mau` | active in the past month but not the past week | 1,683,057 |
| `dormant` | inactive for at least 30 days | 29,156,367 |
