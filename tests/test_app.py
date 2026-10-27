import importlib.util
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location("app", Path(__file__).parents[1] / "space/app.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

BASELINE_LEVELS = [round(app.baseline_percent(f, t), 3) for f, t, *_ in app.LEVERS]  # what the sliders hold
TEST_LEVELS = [round(app.baseline_percent(f, t, app.M_TEST), 3) for f, t, *_ in app.LEVERS]


def test_baseline_matrix_rows_sum_to_one():
    assert np.allclose(app.M.sum(axis=1), 1)


def test_projection_covers_the_test_period_only():
    assert app.BASE.index.equals(app.ACTUAL.index)
    assert str(app.BASE.index[0].date()) == app.BASELINE["test"][0]
    assert str(app.BASE.index[-1].date()) == app.BASELINE["test"][1]


def test_unchanged_sliders_give_the_baseline():
    scen = app.project(app.scenario_matrix(BASELINE_LEVELS))
    assert np.allclose(app.BASE[["dau", "wau", "mau"]], scen[["dau", "wau", "mau"]], rtol=1e-4)
    assert "Move a slider" in app.run(*BASELINE_LEVELS)[0]


def test_test_period_transitions_move_the_scenario_towards_the_actual_numbers():
    scen = app.project(app.scenario_matrix(TEST_LEVELS))
    for col in ("dau", "mau"):
        base_error = abs(app.BASE[col] - app.ACTUAL[col]).mean()
        scen_error = abs(scen[col] - app.ACTUAL[col]).mean()
        assert scen_error < base_error
    assert "With the levers as set" in app.run(*TEST_LEVELS)[0]
