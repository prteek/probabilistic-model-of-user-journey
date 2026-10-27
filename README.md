# probabilistic-model-of-user-journey

Predicting an app's daily, weekly and monthly active users with a Markov chain over user states (new, current,
reactivated, resurrected, at risk, dormant), following Duolingo's growth model, tested on six held-out months.
Written up as the blog post
[How Well Does a Markov Chain Predict Active Users?](https://huggingface.co/blog/prteek/probabilistic-model-of-user-journey) on Hugging Face.

**Blog:** https://huggingface.co/blog/prteek/probabilistic-model-of-user-journey · **App:** https://huggingface.co/spaces/prteek/user-journey-what-if · **Data:** https://huggingface.co/datasets/prteek/user-journey-dau

```
user_journey/          shared package
  states.py            one state per user per day from dau_data.csv (DuckDB); python -m user_journey.states
  model.py             transition matrix, daily state counts, DAU / WAU / MAU forecast
dau_data.csv           simulated daily activity of 51,480 users (published as the dataset)
blog/                  Quarto write-up -> markdown for the Hugging Face article editor
  index.qmd            the blog post; renders to probabilistic-model-of-user-journey.md, figures to assets/
  _hf-markdown.lua     writes inline maths as \\( ... \\) for the article editor
  states.png           the state diagram (hand-drawn); thumbnail.png, the article's cover image
space/                 what-if Gradio app replaying the test period: app.py, Space card, requirements, baseline.json
                       (from precompute.py)
dataset/README.md      the dataset card
publish.sh             upload the activity records and the dataset card, or the Space
wait_for_space.py      wait until the Space runs its latest commit (used by CI)
tests/                 the state rules, transition matrix, forecast and app
```

## Common tasks

```bash
uv sync                                                      # package + app + blog + dev groups
uv run pytest -q

QUARTO_PYTHON=.venv/bin/python quarto render blog/index.qmd  # blog markdown + assets/ figures (~25 s)
uv run python -m user_journey.states                         # states.parquet (32 million rows, seconds)
uv run python space/precompute.py                            # space/baseline.json (the app's data)
uv run python space/app.py                                   # app on http://127.0.0.1:7860
```

The post builds the states from `dau_data.csv` on every render, so it needs nothing beyond this repository.

## Notes

- **The write-up is a blog post in Python.** It was ported from R on 2026-10-27 and reproduces the R results: the
  DuckDB states query gives exactly the 32,111,109 rows of the `states.parquet` the old `prepare_states.r` built, and
  the transition matrix matches the R one to 7 decimal places.
- **The post tests the transitions, not sign-ups.** The transition matrix is estimated on 2022-05-01 to 2023-04-30
  and the chain is run over the last six months of data (2023-05-01 to 2023-10-31) from the actual state counts on
  the last training day, adding the actual new users each day. The original negative binomial model of new users was
  dropped, so the error is down to the transitions alone.
- **Expected counts, not whole users.** The forecast keeps the chain's expected counts; the R version rounded every
  state down to whole users each day, which biased DAU low (by about 3 points over six months).
- **The states table is not published.** It used to be on the dataset (225 MB) because the R code took a long
  time and 2.5 GB to build it; the DuckDB query rebuilds it in seconds, so it was removed on 2026-10-27.

Pushes to `main` publish to Hugging Face with the `HF_TOKEN` repository secret: `publish-dataset.yml` when
`dau_data.csv`, the card or `publish.sh` change, and `publish-space.yml` when the app or `user_journey/model.py`
change (it runs the tests, uploads, and waits until the Space runs the new commit).
