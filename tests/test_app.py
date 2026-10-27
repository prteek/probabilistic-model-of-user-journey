import importlib.util
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location("app", Path(__file__).parents[1] / "space/app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

BASELINE_LEVELS = [app.baseline_percent(f, t) for f, t, *_ in app.LEVERS]


def test_baseline_matrix_rows_sum_to_one():
    assert np.allclose(app.M.sum(axis=1), 1)


def test_unchanged_sliders_give_the_baseline():
    base = app.project(app.M, 25, 60)
    scen = app.project(app.scenario_matrix(BASELINE_LEVELS), 25, 60)
    assert np.allclose(base[["dau", "wau", "mau"]], scen[["dau", "wau", "mau"]])


def test_better_retention_of_new_users_raises_active_users():
    levels = list(BASELINE_LEVELS)
    levels[0] = 70  # new -> current
    base = app.project(app.M, 25, 180)
    scen = app.project(app.scenario_matrix(levels), 25, 180)
    assert (scen["dau"].iloc[-1] > base["dau"].iloc[-1]) and (scen["mau"].iloc[-1] > base["mau"].iloc[-1])


def test_run_returns_a_summary_and_a_figure():
    text, fig = app.run(25, 90, *BASELINE_LEVELS)
    assert "Daily active users" in text and fig is not None
    assert app.run(-1, 90, *BASELINE_LEVELS)[0].startswith("New users per day can't")


def test_summary_says_when_nothing_has_changed():
    rounded = [round(x, 3) for x in BASELINE_LEVELS]  # what the sliders hold
    assert "Move a slider" in app.run(25, 90, *rounded)[0]
    moved = list(rounded)
    moved[2] += 5
    assert "with the levers as set" in app.run(25, 90, *moved)[0]
