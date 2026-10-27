# probabilistic-model-of-user-journey

Forecasting an app's daily, weekly and monthly active users with a Markov chain over user states (new, current,
reactivated, resurrected, at risk, dormant), following Duolingo's growth model, and exploring how campaigns that move
at-risk users back to active change the forecast. Written up as the paper
[Probabilistic Model of User Journey](https://www.alphaxiv.org/abs/2610.probabilistic-model-of-user-journey) on
alphaXiv.

**Data:** https://huggingface.co/datasets/prteek/user-journey-dau

```
index.qmd            the paper (R, knitr)
_quarto.yml          PDF format; renders to _output/probabilistic-model-of-user-journey.pdf
_freeze/             frozen results of the paper's code (tracked)
dau_data.csv         simulated daily activity of 51,480 users (published as the dataset)
prepare_states.r     expands dau_data.csv into one state per user per day: states.csv (~2.5 GB, not in git)
helpers.r            functions used by the paper
huggingface/         dataset card and publish.sh
renv.lock, renv/     R package versions (renv)
references.bib, states.png, count_estimation.png, _wide-tables.lua
```

## Common tasks

```bash
Rscript -e 'renv::restore()'                       # once: install the R packages
QUARTO_R=/opt/homebrew/bin/Rscript quarto render   # paper PDF from the frozen results
huggingface/publish.sh "message"                   # publish dau_data.csv and the card (CI does this on push)
```

Re-running the paper's code needs `states.csv`, one state per user per day (~2.5 GB). Rather than building it with
`Rscript prepare_states.r`, download the ready-made table from the dataset and convert it:

```bash
hf download prteek/user-journey-dau states.parquet --repo-type dataset --local-dir .
duckdb -c "COPY (FROM 'states.parquet') TO 'states.csv'"
```

After changing `prepare_states.r`, rebuild `states.csv` and publish it with `huggingface/publish.sh "message" states`.

Rendering reuses `_freeze/` until a code chunk changes. A push to `main` that changes `dau_data.csv` or the card
publishes the dataset (`.github/workflows/publish-dataset.yml`, using the `HF_TOKEN` repository secret).
