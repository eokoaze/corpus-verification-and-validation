"""Generate IEEE-style figures from the RGT results."""
import json, statistics as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.size": 8, "axes.labelsize": 8, "legend.fontsize": 7,
    "xtick.labelsize": 7, "ytick.labelsize": 7,
    "figure.dpi": 300, "savefig.dpi": 300, "axes.grid": True,
    "grid.alpha": 0.3, "grid.linewidth": 0.4,
})

RATES = ["0.0", "0.05", "0.1", "0.15", "0.2", "0.3", "0.4", "0.5"]
X = [float(r) for r in RATES]
d = json.load(open("results_both.json"))
sw = json.load(open("smoothing_sweep.json"))

CONTENT = ["foreign", "encoding"]
STRUCT = ["duplicate", "truncate", "boilerplate"]
M = {"foreign": "o", "encoding": "s", "duplicate": "^", "truncate": "v", "boilerplate": "D"}

# ---- Fig 1: dose-response, split by defect class ----------------------------
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6))
for ax, group, lab in [(axes[0], CONTENT, "(a) Content defects"),
                       (axes[1], STRUCT, "(b) Structural defects")]:
    for k in group:
        m = [st.mean(d[k][r]["rgt"]) for r in RATES]
        s = [st.pstdev(d[k][r]["rgt"]) for r in RATES]
        ax.errorbar(X, m, yerr=s, marker=M[k], ms=3, lw=1.2, capsize=2, label=k)
    ax.set_xlabel("Injection rate $r$")
    ax.set_ylabel("JS divergence (bits)")
    ax.set_title(lab, fontsize=8)
    ax.legend(frameon=False)
plt.tight_layout()
plt.savefig("fig_dose_response.pdf", bbox_inches="tight")
print("wrote fig_dose_response.pdf")

# ---- Fig 2: information-theoretic vs frequency baseline on encoding ---------
fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.6))
m = [st.mean(d["encoding"][r]["rgt"]) for r in RATES]
s = [st.pstdev(d["encoding"][r]["rgt"]) for r in RATES]
axes[0].errorbar(X, m, yerr=s, marker="s", ms=3, lw=1.2, capsize=2, color="tab:blue")
axes[0].set_xlabel("Encoding-corruption rate $r$")
axes[0].set_ylabel("JS divergence (bits)")
axes[0].set_title("(a) Information-theoretic measure", fontsize=8)

m = [st.mean(d["encoding"][r]["baseline"]) for r in RATES]
s = [st.pstdev(d["encoding"][r]["baseline"]) for r in RATES]
axes[1].errorbar(X, m, yerr=s, marker="s", ms=3, lw=1.2, capsize=2, color="tab:red")
axes[1].set_xlabel("Encoding-corruption rate $r$")
axes[1].set_ylabel("Mean frequency difference")
axes[1].set_title("(b) Frequency profile (non-monotonic)", fontsize=8)
plt.tight_layout()
plt.savefig("fig_baseline_failure.pdf", bbox_inches="tight")
print("wrote fig_baseline_failure.pdf")

# ---- Fig 3: smoothing -- add-k depends on k, RGT does not -------------------
fig, ax = plt.subplots(figsize=(3.4, 2.5))
ks = sw["encoding"]["ks"]
for name, colour, mk in [("encoding", "tab:blue", "s"), ("foreign", "tab:green", "o")]:
    ax.semilogx(ks, sw[name]["addk_d"], marker=mk, ms=3.5, lw=1.3, color=colour,
                label=f"add-$k$ ({name})")
    ax.axhline(sw[name]["rgt_d"], ls="--", lw=1.3, color=colour, alpha=0.85)
    ax.annotate(f"RGT {sw[name]['rgt_d']:.2f}", xy=(ks[0], sw[name]["rgt_d"]),
                xytext=(0, 3), textcoords="offset points", fontsize=6.5, color=colour)
ax.set_xlabel("Smoothing parameter $k$")
ax.set_ylabel("Effect size $d$ (clean vs. defective)")
ax.legend(frameon=False, loc="lower left")
plt.tight_layout()
plt.savefig("fig_smoothing.pdf", bbox_inches="tight")
print("wrote fig_smoothing.pdf")
