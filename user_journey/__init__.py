"""A Markov chain over user states for forecasting daily, weekly and monthly active users.

- states: one state per user per day from the activity records (data/dau_data.csv), with DuckDB
- model: transition matrix, daily state counts and the DAU / WAU / MAU forecast
"""
