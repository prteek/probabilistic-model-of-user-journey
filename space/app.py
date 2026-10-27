"""Gradio app: what happens to daily, weekly and monthly active users if retention changes?

Users are in one of seven states each day and move between them with the probabilities of a transition matrix,
estimated on the last year of a simulated app's activity (baseline.json, from precompute.py). The sliders change the
transitions a product team can act on; the chain is run forward with and without the change. Method: the blog post
"How Well Does a Markov Chain Predict Active Users?" (BLOG_URL).
"""
import json
from pathlib import Path

import gradio as gr
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from user_journey.model import STATE_NAMES, forecast, with_transition

pio.templates.default = "ggplot2"

BLOG_URL = "https://huggingface.co/blog/prteek/probabilistic-model-of-user-journey"
BASELINE = json.loads(Path(__file__).with_name("baseline.json").read_text())
M = pd.DataFrame(BASELINE["matrix"], index=BASELINE["states"], columns=BASELINE["states"])
STATE0 = pd.Series(BASELINE["state0"], index=BASELINE["states"])
HISTORY = pd.DataFrame(BASELINE["history"]).assign(date=lambda d: pd.to_datetime(d["date"]))
START = pd.Timestamp(BASELINE["last_day"]) + pd.Timedelta(days=1)

# the transitions a product team can act on: (from, to, label, slider maximum in %, slider step in %)
LEVERS = [
    ("new", "current", "New users who come back on day 2", 100, 0.5),
    ("current", "current", "Current users who are active again the next day", 99.5, 0.1),
    ("at_risk_wau", "current", "At-risk weekly users who return each day", 40, 0.1),
    ("at_risk_mau", "reactivated", "At-risk monthly users who return each day", 5, 0.02),
    ("dormant", "resurrected", "Dormant users who return each day", 0.5, 0.002),
]
METRICS = [("dau", "Daily active users"), ("wau", "Weekly active users"), ("mau", "Monthly active users")]
COLOURS = {"history": "#999999", "baseline": "#333333", "scenario": "#F8766D"}


def baseline_percent(state_from, state_to) -> float:
    return float(100 * M.loc[state_from, state_to])  # a plain float: gradio sends numpy floats back as strings


def scenario_matrix(levels) -> pd.DataFrame:
    m = M
    for (state_from, state_to, *_), level in zip(LEVERS, levels):
        m = with_transition(m, state_from, state_to, float(level) / 100)
    return m


def project(m, new_users_per_day, days) -> pd.DataFrame:
    dates = pd.date_range(START, periods=int(days))
    return forecast(m, STATE0, pd.Series(float(new_users_per_day), index=dates))


def summary(base, scen, days, levels) -> str:
    end = f"{base.index[-1]:%-d %B %Y}"
    rows = ["| | baseline | scenario | difference |", "|---|---:|---:|---:|"]
    for col, label in METRICS:
        b, s = base[col].iloc[-1], scen[col].iloc[-1]
        rows.append(f"| {label} | {b:,.0f} | {s:,.0f} | {s - b:+,.0f} ({(s - b) / b:+.1%}) |")
    # a slider counts as moved when it is more than half a step from its baseline value (the slider rounds it)
    changed = [label for (f, t, label, _, step), lv in zip(LEVERS, levels) if abs(lv - baseline_percent(f, t)) > step / 2]
    head = (f"**After {int(days)} days ({end})**, with the levers as set:" if changed
            else f"**After {int(days)} days ({end}).** Move a slider to see how a change in retention plays out.")
    return head + "\n\n" + "\n".join(rows)



def figure(base, scen) -> go.Figure:
    fig = make_subplots(rows=1, cols=3, subplot_titles=[label for _, label in METRICS], horizontal_spacing=0.07)
    for i, (col, _) in enumerate(METRICS, start=1):
        first = i == 1
        fig.add_trace(go.Scatter(x=HISTORY["date"], y=HISTORY[col], mode="lines", name="data",
                                 line=dict(color=COLOURS["history"], width=1), showlegend=first), row=1, col=i)
        fig.add_trace(go.Scatter(x=base.index, y=base[col], mode="lines", name="baseline (no change)",
                                 line=dict(color=COLOURS["baseline"], width=2, dash="dash"), showlegend=first),
                      row=1, col=i)
        fig.add_trace(go.Scatter(x=scen.index, y=scen[col], mode="lines", name="scenario",
                                 line=dict(color=COLOURS["scenario"], width=2.5), showlegend=first), row=1, col=i)
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=40, b=10), legend=dict(orientation="h", y=-0.15, x=0),
                      hovermode="x unified")
    return fig


def run(new_users_per_day, days, *levels):
    if new_users_per_day is None or new_users_per_day < 0:
        return "New users per day can't be negative.", None
    base = project(M, new_users_per_day, days)
    scen = project(scenario_matrix(levels), new_users_per_day, days)
    return summary(base, scen, days, levels), figure(base, scen)


with gr.Blocks(title="User journey what-if") as demo:
    gr.Markdown(
        "# What if retention changed?\n"
        "Every user of an app is in one of seven states each day (new, current, reactivated, resurrected, at risk, "
        "dormant), and moves between states with probabilities estimated from a year of activity. Move the sliders "
        "to change the transitions a product team can act on, such as onboarding, reminders or win-back campaigns, "
        "and see what happens to daily, weekly and monthly active users. The dashed line is the baseline with "
        f"nothing changed. Method: [How Well Does a Markov Chain Predict Active Users?]({BLOG_URL})."
    )
    with gr.Row():
        with gr.Column(scale=2):
            sliders = [
                gr.Slider(0, top, value=round(baseline_percent(f, t), 3), step=step,
                          label=f"{label} (%, now {baseline_percent(f, t):.{max(1, -int(np.floor(np.log10(step))))}f})")
                for f, t, label, top, step in LEVERS
            ]
        with gr.Column(scale=1):
            new_users = gr.Number(BASELINE["new_users_per_day"], label="New users per day", minimum=0)
            days = gr.Slider(30, 365, value=180, step=5, label="Days ahead")
            reset = gr.Button("Reset to baseline")
            gr.Markdown(
                f"New users per day starts at the average of the last 90 days of data. They come from outside the "
                f"chain, so they are an input here, not a prediction. The transitions were estimated on "
                f"{BASELINE['window'][0]} to {BASELINE['window'][1]}."
            )
    result = gr.Markdown()
    plot = gr.Plot(show_label=False)
    gr.Markdown(
        "When a slider changes one transition, the other transitions out of the same state shrink in proportion, so "
        "the probabilities still add up to 1. The data is a simulated activity log of 51,480 users based on a real "
        "SaaS app: [prteek/user-journey-dau](https://huggingface.co/datasets/prteek/user-journey-dau)."
    )

    inputs = [new_users, days, *sliders]
    reset.click(lambda: [round(baseline_percent(f, t), 3) for f, t, *_ in LEVERS], None, sliders)
    gr.on([c.change for c in inputs], run, inputs, [result, plot], trigger_mode="always_last")
    demo.load(run, inputs, [result, plot])

if __name__ == "__main__":
    demo.launch()
