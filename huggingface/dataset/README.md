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

It is the data behind the paper
[Probabilistic Model of User Journey](https://www.alphaxiv.org/abs/2610.probabilistic-model-of-user-journey) on
alphaXiv, which places users in seven states each day (new, current, reactivated, resurrected, at-risk weekly active,
at-risk monthly active, dormant) following Duolingo's growth model, estimates a Markov chain of transitions between them, and forecasts daily, weekly and
monthly active users. Code: [github.com/prteek/probabilistic-model-of-user-journey](https://github.com/prteek/probabilistic-model-of-user-journey).

## Columns

| column | content |
|---|---|
| `user_id` | anonymous user id (UUID) |
| `date` | a day on which the user was active (2020-10-01 to 2023-10-31) |
| `registration_date` | the day the user registered (2020-04-20 to 2023-10-31) |

Days without a row for a user are days on which the user was inactive. The paper's code expands these records into
one state per user per day (`prepare_states.r` in the code repository; about 2.5 GB as CSV).
