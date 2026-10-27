---
title: User Journey What-If
emoji: 📈
colorFrom: red
colorTo: gray
sdk: gradio
sdk_version: 6.30.0
python_version: "3.12"
app_file: app.py
pinned: false
license: cc-by-4.0
short_description: What happens to active users if retention changes?
datasets:
  - prteek/user-journey-dau
---

Interactive companion to the blog post [How Well Does a Markov Chain Predict Active Users?](https://huggingface.co/blog/prteek/probabilistic-model-of-user-journey) on Hugging Face. Every user of an app is in one of seven states each day (new, current, reactivated, resurrected, at risk, dormant) and moves between states with probabilities estimated from a year of activity. Change the transitions a product team can act on, such as day-2 retention of new users, reminders to at-risk users or win-back campaigns, and see how daily, weekly and monthly active users respond.

Code: [github.com/prteek/probabilistic-model-of-user-journey](https://github.com/prteek/probabilistic-model-of-user-journey) · Data: [prteek/user-journey-dau](https://huggingface.co/datasets/prteek/user-journey-dau), a simulated activity log of 51,480 users based on a real SaaS app.
