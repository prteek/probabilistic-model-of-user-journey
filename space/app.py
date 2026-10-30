"""Gradio app: what would have happened to daily, weekly and monthly active users if retention had been different?

Users are in one of seven states each day and move between them with the probabilities of a transition matrix. The
app replays the blog post's test (baseline.json, from precompute.py): the matrix of the training year is run over the
six held-out months, with the actual new users each day. The sliders change the transitions a product team can act
on, and the actual numbers show what really happened. Method: the blog post
"How Well Does a Markov Chain Predict Active Users?" (BLOG_URL).
"""
import json
from pathlib import Path

import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from user_journey.model import forecast, with_transition

pio.templates.default = "ggplot2"

BLOG_URL = "https://huggingface.co/blog/prteek/probabilistic-model-of-user-journey"
BASELINE = json.loads(Path(__file__).with_name("baseline.json").read_text())
STATES = BASELINE["states"]
M = pd.DataFrame(BASELINE["matrix"], index=STATES, columns=STATES)
M_TEST = pd.DataFrame(BASELINE["test_matrix"], index=STATES, columns=STATES)
STATE0 = pd.Series(BASELINE["state0"], index=STATES)
HISTORY = pd.DataFrame(BASELINE["history"]).assign(date=lambda d: pd.to_datetime(d["date"]))
ACTUAL = pd.DataFrame(BASELINE["test_period"]).assign(date=lambda d: pd.to_datetime(d["date"])).set_index("date")
TEST_END = f"{ACTUAL.index[-1]:%-d %B %Y}"

# the transitions a product team can act on: (from, to, label, slider maximum in %, slider step in %)
LEVERS = [
    ("new", "current", "New users who come back on day 2", 100, 0.5),
    ("current", "current", "Current users who are active again the next day", 99.5, 0.1),
    ("at_risk_wau", "current", "At-risk weekly users who return each day", 40, 0.1),
    ("at_risk_mau", "reactivated", "At-risk monthly users who return each day", 5, 0.02),
    ("dormant", "resurrected", "Dormant users who return each day", 0.5, 0.002),
]
METRICS = [("dau", "Daily active users"), ("wau", "Weekly active users"), ("mau", "Monthly active users")]
COLOURS = {"history": "#999999", "actual": "#000000", "baseline": "#555555", "scenario": "#F8766D"}


def baseline_percent(state_from, state_to, m=M) -> float:
    return float(100 * m.loc[state_from, state_to])  # a plain float: gradio sends numpy floats back as strings


def decimals(step) -> int:
    return len(f"{step:g}".partition(".")[2]) or 1


def moved(lever, level) -> bool:
    """Whether a slider is off its baseline value, which it holds rounded to its step."""
    state_from, state_to, _, _, step = lever
    return abs(float(level) - baseline_percent(state_from, state_to)) > step / 2


def scenario_matrix(levels) -> pd.DataFrame:
    m = M
    for lever, level in zip(LEVERS, levels):
        if moved(lever, level):  # an untouched slider keeps the exact baseline value, not its rounded one
            m = with_transition(m, lever[0], lever[1], float(level) / 100)
    return m


def project(m) -> pd.DataFrame:
    """The chain over the test period from the last training day, with the actual new users each day."""
    return forecast(m, STATE0, ACTUAL["new"])


BASE = project(M)


def summary(scen, levels) -> str:
    rows = [f"| on {TEST_END} | actual | baseline | scenario | scenario − baseline |", "|---|---:|---:|---:|---:|"]
    for col, label in METRICS:
        a, b, s = ACTUAL[col].iloc[-1], BASE[col].iloc[-1], scen[col].iloc[-1]
        rows.append(f"| {label} | {a:,.0f} | {b:,.0f} | {s:,.0f} | {s - b:+,.0f} ({(s - b) / b:+.1%}) |")
    head = ("**With the levers as set.**" if any(moved(lever, lv) for lever, lv in zip(LEVERS, levels))
            else "**Baseline: the training year's transitions.** Move a slider to see how a change in retention "
                 "would have played out.")
    return head + "\n\n" + "\n".join(rows)


def figure(scen) -> go.Figure:
    fig = make_subplots(rows=1, cols=3, subplot_titles=[label for _, label in METRICS], horizontal_spacing=0.07)
    for i, (col, _) in enumerate(METRICS, start=1):
        first = i == 1
        lines = [
            (HISTORY["date"], HISTORY[col], "training data", dict(color=COLOURS["history"], width=1)),
            (ACTUAL.index, ACTUAL[col], "actual", dict(color=COLOURS["actual"], width=1)),
            (BASE.index, BASE[col], "baseline (training-year transitions)",
             dict(color=COLOURS["baseline"], width=2, dash="dash")),
            (scen.index, scen[col], "scenario", dict(color=COLOURS["scenario"], width=2.5)),
        ]
        for x, y, name, line in lines:
            fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=name, line=line, showlegend=first), row=1, col=i)
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.15, x=0),
                      hovermode="x unified")
    return fig


def run(*levels):
    scen = project(scenario_matrix(levels))
    return summary(scen, levels), figure(scen)


def slider_label(state_from, state_to, label, step) -> str:
    d = decimals(step)
    return (f"{label} (%; training year {baseline_percent(state_from, state_to):.{d}f}, "
            f"test period {baseline_percent(state_from, state_to, M_TEST):.{d}f})")


with gr.Blocks(title="User journey what-if") as demo:
    gr.Markdown(
        "# What if retention had been different?\n"
        "Every user of an app is in one of seven states each day (new, current, reactivated, resurrected, at risk, "
        "dormant) and moves between states with probabilities estimated from a year of activity, "
        f"{BASELINE['train'][0]} to {BASELINE['train'][1]}. Run over the next six months with the actual new users "
        "each day, they give the dashed baseline; the black line is what actually happened. Move the sliders to "
        "change the transitions a product team can act on, such as onboarding, reminders or win-back campaigns, and "
        "see how daily, weekly and monthly active users would have responded. Each slider also shows the value "
        "measured in the test period: setting them there shows how much of the gap to the actual numbers the "
        f"change in behaviour explains. Method: [How Well Does a Markov Chain Predict Active Users?]({BLOG_URL})."
    )
    with gr.Row():
        with gr.Column(scale=3):
            sliders = [
                gr.Slider(0, top, value=round(baseline_percent(f, t), 3), step=step, label=slider_label(f, t, label, step))
                for f, t, label, top, step in LEVERS
            ]
        with gr.Column(scale=1):
            reset = gr.Button("Reset to the training year")
            to_test = gr.Button("Set to the test period")
            gr.Markdown(
                "New users come from outside the chain, so the actual number each day is used throughout. When a "
                "slider changes one transition, the other transitions out of the same state shrink in proportion, "
                "so the probabilities still add up to 1."
            )
    result = gr.Markdown()
    plot = gr.Plot(show_label=False)
    gr.Markdown(
        "The data is a simulated activity log of 51,480 users based on a real SaaS app: "
        "[prteek/user-journey-dau](https://huggingface.co/datasets/prteek/user-journey-dau), from Vladimir "
        "Kukushkin's [Modeling DAU with Markov chain](https://towardsdatascience.com/modeling-dau-with-markov-chain-640ea4fddeb4/) "
        "(Towards Data Science), the work this builds on."
    )

    reset.click(lambda: [round(baseline_percent(f, t), 3) for f, t, *_ in LEVERS], None, sliders)
    to_test.click(lambda: [round(baseline_percent(f, t, M_TEST), 3) for f, t, *_ in LEVERS], None, sliders)
    gr.on([s.change for s in sliders], run, sliders, [result, plot], trigger_mode="always_last")
    demo.load(run, sliders, [result, plot])

if __name__ == "__main__":
    demo.launch()
