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
short_description: What if retention had been different? A Markov chain what-if
datasets:
  - prteek/user-journey-dau
---

Interactive companion to the blog post [How Well Does a Markov Chain Predict Active Users?](https://huggingface.co/blog/prteek/probabilistic-model-of-user-journey) on Hugging Face. Every user of an app is in one of seven states each day (new, current, reactivated, resurrected, at risk, dormant) and moves between states with probabilities estimated from a year of activity. The app replays the post's test: the training year's transitions run over six held-out months with the actual new users each day, shown against what actually happened. Change the transitions a product team can act on, such as day-2 retention of new users, reminders to at-risk users or win-back campaigns, and see how daily, weekly and monthly active users would have responded, or set them to the values measured in the test period to see how much of the gap to the actual numbers the change in behaviour explains.

Code: [github.com/prteek/probabilistic-model-of-user-journey](https://github.com/prteek/probabilistic-model-of-user-journey) · Data: [prteek/user-journey-dau](https://huggingface.co/datasets/prteek/user-journey-dau), a simulated activity log of 51,480 users based on a real SaaS app, from Vladimir Kukushkin's [Modeling DAU with Markov chain](https://towardsdatascience.com/modeling-dau-with-markov-chain-640ea4fddeb4/) (Towards Data Science), the work this builds on.
