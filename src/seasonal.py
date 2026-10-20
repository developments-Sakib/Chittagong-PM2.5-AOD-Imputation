from src.config import HOUR_COLS, SEASONS


def assign_season(month):
    if 6 <= month <= 9:
        return "Monsoon"
    elif month in [10, 11, 12, 1]:
        return "Winter"
    else:
        return "Summer"


def add_season(df):
    df = df.copy()
    df["Season"] = df["Date"].dt.month.apply(assign_season)
    df["Daily_PM2.5_Avg"] = df[HOUR_COLS].mean(axis=1)
    return df


def hourly_ratios(df):
    # average PM2.5 of each hour divided by the average of the whole day, per season
    profiles = df.groupby("Season")[HOUR_COLS].mean().reindex(SEASONS)
    return profiles.div(profiles.mean(axis=1), axis=0)
