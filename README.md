# probabilistic-model-of-user-journey

Forecasting an app's daily, weekly and monthly active users with a Markov chain over user states (new, current,
reactivated, resurrected, at risk, dormant), following Duolingo's growth model. Written up as the blog post
[Forecasting Daily Active Users with a Markov Chain](https://huggingface.co/blog/prteek/probabilistic-model-of-user-journey) on Hugging Face.

**Blog:** https://huggingface.co/blog/prteek/probabilistic-model-of-user-journey · **Data:** https://huggingface.co/datasets/prteek/user-journey-dau

```
user_journey/          shared package
  states.py            one state per user per day from dau_data.csv (DuckDB); python -m user_journey.states
  model.py             transition matrix, new-user count model (negative binomial), DAU / WAU / MAU forecast
dau_data.csv           simulated daily activity of 51,480 users (published as the dataset)
blog/                  Quarto write-up -> markdown for the Hugging Face article editor
  index.qmd            the blog post; renders to probabilistic-model-of-user-journey.md, figures to assets/
  _hf-markdown.lua     writes inline maths as \\( ... \\) for the article editor
  states.png           the state diagram (hand-drawn); thumbnail.png, the article's cover image
dataset/README.md      the dataset card
publish.sh             upload the activity records and the dataset card
tests/                 the state rules, transition matrix and forecast
```

## Common tasks

```bash
uv sync                                                      # package + blog + dev groups
uv run pytest -q

QUARTO_PYTHON=.venv/bin/python quarto render blog/index.qmd  # blog markdown + assets/ figures (~25 s)
uv run python -m user_journey.states                         # states.parquet (32 million rows, seconds)
```

The post builds the states from `dau_data.csv` on every render, so it needs nothing beyond this repository.

## Notes

- **The write-up is a blog post in Python.** It replaced the alphaXiv paper (R, PDF build, frozen results) on
  2026-10-27. The Python port reproduces the R results: the DuckDB states query gives exactly the 32,111,109 rows of
  the `states.parquet` the old `prepare_states.r` built, the transition matrix matches the paper to
  7 decimal places, and the negative binomial new-user model gives the same fit (theta 9.31) and predictions as
  `MASS::glm.nb`; its 95% intervals are about 1% wider, since statsmodels estimates the dispersion jointly.
- **The states table is not published.** It used to be on the dataset (225 MB) because the R code took a long
  time and 2.5 GB to build it; the DuckDB query rebuilds it in seconds, so it was removed on 2026-10-27.
- **The new-user forecast is the weak link.** The `year * bs(week_of_year)` interaction extrapolates the seasonal
  shape into 2024, so the January spike becomes a broad hump; the post says so and treats the forecast as a scenario.

A push to `main` that changes `dau_data.csv`, the card or `publish.sh` publishes the dataset
(`.github/workflows/publish-dataset.yml`, using the `HF_TOKEN` repository secret).
