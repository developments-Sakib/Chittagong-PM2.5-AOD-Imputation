"""
Hourly PM2.5 imputation from satellite AOD (Chittagong).

Train SARIMAX on Agrabad, then apply it to Khulshi.

    python main.py                                  # uses data/processed/*.csv
    python main.py --excel "DoE CAMS Air Quality Data.xlsx"
"""
import argparse
import json
import os

from src.config import HOUR_COLS, STATIONS
from src.model import evaluate, fit_sarimax, hourly_prediction, impute, transfer
from src.plots import plot_aod, plot_pm_vs_aod, plot_seasonal_hourly
from src.preprocessing import fill_exog, load_aod, load_cams, load_daily, merge_with_aod
from src.seasonal import add_season, hourly_ratios

AOD_FILE = "data/raw/aod_daily_2014_2021.csv"


def prepare(key, excel=None):
    st = STATIONS[key]
    aod = load_aod(AOD_FILE, st["aod_col"])
    if excel:
        daily = load_cams(excel, st["sheet"])
    else:
        daily = load_daily(f"data/processed/{key}_daily.csv")

    observed = add_season(merge_with_aod(aod, daily))
    filled, exog_flags = fill_exog(observed)
    return observed, add_season(filled), exog_flags


def save_outputs(key, observed, df, pred, exog_flags, out):
    name = STATIONS[key]["name"]
    imputed, pm_flags = impute(df, pred)

    cols = ["Date", "AOD"] + HOUR_COLS + ["Temperature", "Rain"]
    imputed["Date"] = imputed["Date"].dt.strftime("%Y-%m-%d")
    imputed[cols].to_csv(f"{out}/{name}_PM2.5_Imputed_Dataset.csv", index=False)

    flags = exog_flags.join(pm_flags)
    flags["Date"] = flags["Date"].dt.strftime("%Y-%m-%d")
    flags.to_csv(f"{out}/{name}_imputation_flags.csv", index=False)

    # figures use observed data only
    plot_aod(observed, name, f"{out}/figures/{key}_aod.png")
    plot_seasonal_hourly(observed, name, f"{out}/figures/{key}_seasonal_hourly_pm25.png")
    plot_pm_vs_aod(observed, name, f"{out}/figures/{key}_pm25_vs_aod.png")

    return int(pm_flags.values.sum())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--excel", help="DoE CAMS workbook (optional)")
    parser.add_argument("--out", default="results")
    args = parser.parse_args()
    os.makedirs(f"{args.out}/figures", exist_ok=True)

    metrics = {}

    # Agrabad: fit the model
    obs_a, agrabad, flags_a = prepare("agrabad", args.excel)
    results = fit_sarimax(agrabad)
    ratios = hourly_ratios(agrabad)  # from observed hours only

    pred = hourly_prediction(results, agrabad, ratios)
    metrics["Agrabad"] = evaluate(agrabad, pred)
    metrics["Agrabad"]["hours_imputed"] = save_outputs("agrabad", obs_a, agrabad, pred, flags_a, args.out)

    # Khulshi: same parameters and Agrabad's hourly ratios
    obs_k, khulshi, flags_k = prepare("khulshi", args.excel)
    pred = hourly_prediction(transfer(results, khulshi), khulshi, ratios)
    metrics["Khulshi"] = evaluate(khulshi, pred)
    metrics["Khulshi"]["hours_imputed"] = save_outputs("khulshi", obs_k, khulshi, pred, flags_k, args.out)

    metrics["model_parameters"] = results.params.round(4).to_dict()
    with open(f"{args.out}/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(results.summary().tables[1])
    for station in ["Agrabad", "Khulshi"]:
        m = metrics[station]
        print(f"{station}: R2 = {m['r2']:.4f}, MAPE = {m['mape']:.2f}%, "
              f"observed hours = {m['n_hours']}, imputed hours = {m['hours_imputed']}")


if __name__ == "__main__":
    main()
