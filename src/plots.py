import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import HOUR_COLS, SEASONS, SEASON_COLORS

GRID = "#e6e6e3"
LABEL = "#6b6b6b"


def style(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=13, fontweight="bold", loc="left")
    ax.set_xlabel(xlabel, fontsize=11, color=LABEL)
    ax.set_ylabel(ylabel, fontsize=11, color=LABEL)
    ax.tick_params(colors=LABEL, labelsize=9)
    ax.grid(axis="y", color=GRID)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(GRID)


def save(fig, path):
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_aod(df, station, path):
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(df["Date"], df["AOD"], color=SEASON_COLORS["Monsoon"], linewidth=0.8)
    style(ax, f"Daily AOD, {station}", "Date", "AOD")
    save(fig, path)


def plot_seasonal_hourly(df, station, path):
    profile = df.groupby("Season")[HOUR_COLS].mean().T
    hours = range(1, 25)

    fig, ax = plt.subplots(figsize=(12, 5))
    w = 0.27
    for i, season in enumerate(SEASONS):
        x = [h + (i - 1) * w for h in hours]
        ax.bar(x, profile[season], width=w - 0.03, color=SEASON_COLORS[season], label=season)
    ax.set_xticks(list(hours))
    ax.legend(frameon=False, ncols=3, loc="lower right", bbox_to_anchor=(1, 1))
    style(ax, f"Hourly average PM2.5 by season, {station}", "Hour of the day", "Average PM2.5 (µg/m³)")
    save(fig, path)


def plot_pm_vs_aod(df, station, path):
    fig, ax = plt.subplots(figsize=(7, 5.5))
    for season in SEASONS:
        s = df[df["Season"] == season]
        ax.scatter(s["AOD"], s["Daily_PM2.5_Avg"], s=14, alpha=0.75, color=SEASON_COLORS[season],
                   edgecolors="white", linewidths=0.4, label=season)
    ax.legend(frameon=False, title="Season")
    ax.grid(axis="x", color=GRID)
    style(ax, f"Daily average PM2.5 vs AOD, {station}", "AOD", "Daily average PM2.5 (µg/m³)")
    save(fig, path)
