import numpy as np
import pandas as pd

from src.config import START_DATE, END_DATE, HOUR_COLS


def load_aod(path, aod_col):
    aod = pd.read_csv(path, encoding="utf-8-sig")
    aod = aod[["Time", aod_col]].rename(columns={"Time": "Date", aod_col: "AOD"})
    aod["Date"] = pd.to_datetime(aod["Date"], format="%d-%m-%Y")
    return aod


def get_hour(time_str):
    try:
        return int(str(time_str).split(":")[0])
    except ValueError:
        return np.nan


def single_value(values):
    # If two records give different PM2.5 for the same hour we can't tell which
    # one is right, so the hour is left missing instead of averaging them.
    values = values.dropna().unique()
    return values[0] if len(values) == 1 else np.nan


def load_cams(excel_path, sheet):
    """Read one station sheet from the DoE CAMS workbook and pivot to one row per day."""
    df = pd.read_excel(excel_path, sheet_name=sheet, skiprows=1)
    df = df[["Date", "Time", "PM2.5", "Temperature", "Rain"]].copy()

    df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")
    df = df.dropna(subset=["Date"])
    # some dates come with a time attached, drop it so each day is one row
    df["Date"] = df["Date"].dt.normalize()
    df = df[(df["Date"] >= START_DATE) & (df["Date"] <= END_DATE)]

    df["Hour"] = df["Time"].apply(get_hour)
    for col in ["PM2.5", "Temperature", "Rain"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    pm = df.pivot_table(index="Date", columns="Hour", values="PM2.5", aggfunc=single_value)
    pm = pm.reindex(columns=range(1, 25))
    pm.columns = HOUR_COLS

    weather = df.groupby("Date")[["Temperature", "Rain"]].mean()
    return pm.join(weather, how="outer").reset_index()


def load_daily(path):
    """Read a daily csv (Date, 1..24, Temperature, Rain)."""
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"], format="mixed").dt.normalize()

    g = df.groupby("Date")
    pm = g[HOUR_COLS].agg(single_value)
    weather = g[["Temperature", "Rain"]].mean()
    return pm.join(weather).reset_index()


def merge_with_aod(aod, daily):
    # full calendar so every day 2014-2021 appears once
    days = pd.DataFrame({"Date": pd.date_range(START_DATE, END_DATE, freq="D")})
    df = days.merge(aod, on="Date", how="left").merge(daily, on="Date", how="left")
    return df[["Date", "AOD"] + HOUR_COLS + ["Temperature", "Rain"]]


def fill_exog(df):
    """Fill gaps in AOD/temperature (linear interpolation) and rain (0).

    Also returns which cells were filled.
    """
    df = df.copy()
    flags = pd.DataFrame({"Date": df["Date"]})

    for col in ["AOD", "Temperature"]:
        flags[col + "_filled"] = df[col].isna()
        df[col] = df[col].interpolate(method="linear").bfill().ffill()

    flags["Rain_filled"] = df["Rain"].isna()
    df["Rain"] = df["Rain"].fillna(0)
    return df, flags
