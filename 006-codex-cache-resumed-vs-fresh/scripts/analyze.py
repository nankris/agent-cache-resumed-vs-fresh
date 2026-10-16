#!/usr/bin/env python3
"""#006 adapted: same 14 packages, one per turn.
  fresh   = a new `codex exec` per package (this repo, results/runs.csv)
  resumed = one session continued with `codex exec resume` (the `default` arm of #012, copied to
            results/resumed_from_012.csv; identical config, same runs, not re-run)
Outputs results/summary.csv, results/per_turn.csv, results/chart.png."""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fresh = pd.read_csv(os.path.join(HERE, "results", "runs.csv"))
fresh["arm"] = "fresh exec per task"
res = pd.read_csv(os.path.join(HERE, "results", "resumed_from_012.csv"))
res["arm"] = "one resumed session"
df = pd.concat([fresh, res], ignore_index=True)
df["turn"] = df.groupby(["arm", "rep"]).cumcount() + 1
cols = ["input_tokens", "cached_input_tokens", "uncached_input_tokens", "output_tokens", "total_tokens", "est_cost_usd",
        "model_calls", "wall_s"]
chains = df.groupby(["arm", "rep"]).agg({**{c: "sum" for c in cols}, "passed": "sum", "subtests_passed": "last",
                                         "turn": "max"}).reset_index()
chains["cache_share"] = (chains.cached_input_tokens / chains.input_tokens).round(4)
chains.to_csv(os.path.join(HERE, "results", "summary.csv"), index=False)
print(chains.to_string())
arm = chains.groupby("arm").agg(chains=("rep", "count"), turns=("turn", "mean"), turns_passed=("passed", "mean"),
                                total_tokens=("total_tokens", "mean"), cached=("cached_input_tokens", "mean"),
                                uncached=("uncached_input_tokens", "mean"), output=("output_tokens", "mean"),
                                cache_share=("cache_share", "mean"), cost_mean=("est_cost_usd", "mean"),
                                cost_min=("est_cost_usd", "min"), cost_max=("est_cost_usd", "max"))
arm.round(4).to_csv(os.path.join(HERE, "results", "summary_by_arm.csv"))
print(arm.round(4).to_string())
df[["arm", "rep", "turn", "task", "passed", "input_tokens", "cached_input_tokens", "uncached_input_tokens",
    "output_tokens", "est_cost_usd", "peak_context_tokens"]].to_csv(os.path.join(HERE, "results", "per_turn.csv"), index=False)

c = {"fresh exec per task": "#dd8452", "one resumed session": "#4c72b0"}
fig, ax = plt.subplots(1, 3, figsize=(16, 4.8))
for (a, rep), g in df.groupby(["arm", "rep"]):
    ls = {1: "-", 2: ":", 3: "--", 4: "-."}.get(int(rep), "-")
    ax[0].plot(g.turn, g.input_tokens / 1000, ls, marker="o", ms=3, color=c[a], label=f"{a} r{rep}")
    ax[1].plot(g.turn, g.uncached_input_tokens / 1000, ls, marker="o", ms=3, color=c[a], label=f"{a} r{rep}")
ax[0].set_title("Input tokens per turn (K), incl. cache reads", fontsize=10)
ax[1].set_title("Uncached input tokens per turn (K)", fontsize=10)
for a_ in ax[:2]:
    a_.set_xlabel("turn (one package per turn)")
    a_.grid(alpha=0.3)
    a_.legend(fontsize=7)
arms = list(arm.index)
x = range(len(arms))
w = 0.38
ax[2].bar([i - w / 2 for i in x], arm.cached / 1000, w, color="#8fbcd4", label="cached input (K)")
ax[2].bar([i + w / 2 for i in x], (arm.uncached + arm.output) / 1000, w, color="#e3a07a", label="uncached input + output (K)")
for i, a_ in enumerate(arms):
    ax[2].text(i, arm.cached.max() / 1000 * 1.02, f"${arm.cost_mean[a_]:.3f} / 14 tasks\ncache share {arm.cache_share[a_]:.0%}",
               ha="center", fontsize=8)
ax[2].set_xticks(list(x))
ax[2].set_xticklabels(arms, fontsize=9)
ax[2].set_ylim(0, arm.cached.max() / 1000 * 1.25)
ax[2].set_title("Tokens for all 14 tasks (mean of chains)", fontsize=10)
ax[2].legend(fontsize=8, loc="center")
ax[2].grid(axis="y", alpha=0.3)
fig.suptitle("Codex 0.162.1 (gpt-6.1-sol): 14 small fixes as 14 fresh `codex exec` runs vs one `codex exec resume` session", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(HERE, "results", "chart.png"), dpi=130)
print("wrote chart")
