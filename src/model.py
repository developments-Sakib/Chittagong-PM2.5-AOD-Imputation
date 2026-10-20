import warnings

import numpy as np
from sklearn.metrics import mean_absolute_percentage_error, r2_score
from statsmodels.tsa.statespace.sarimax import SARIMAX

from src.config import EXOG_COLS, HOUR_COLS, SARIMAX_ORDER


def fit_sarimax(df):
    ts = df.set_index("Date").asfreq("D")
    model = SARIMAX(ts["Daily_PM2.5_Avg"], exog=ts[EXOG_COLS], order=SARIMAX_ORDER)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return model.fit(disp=False)


def transfer(results, df):
    # use the fitted parameters on another station's data (no refitting)
    ts = df.set_index("Date").asfreq("D")
    return results.apply(endog=ts["Daily_PM2.5_Avg"], exog=ts[EXOG_COLS])


def hourly_prediction(results, df, ratios):
    """Daily prediction x seasonal hourly ratio -> predicted PM2.5 for every hour."""
    daily_pred = np.asarray(results.predict())
    factors = ratios.loc[df["Season"].values, HOUR_COLS].values
    pred = daily_pred[:, None] * factors
    return np.clip(pred, 0, None)


def evaluate(df, pred):
    obs = df[HOUR_COLS].values.astype(float)
    mask = ~np.isnan(obs)
    return {
        "r2": r2_score(obs[mask], pred[mask]),
        "mape": mean_absolute_percentage_error(obs[mask], pred[mask]) * 100,
        "n_hours": int(mask.sum()),
    }


def impute(df, pred):
    """Fill only the missing hours. Observed values are kept as they are."""
    df = df.copy()
    missing = df[HOUR_COLS].isna()
    df[HOUR_COLS] = df[HOUR_COLS].where(~missing, pred)
    flags = missing.add_prefix("PM2.5_h").add_suffix("_imputed")
    return df, flags
