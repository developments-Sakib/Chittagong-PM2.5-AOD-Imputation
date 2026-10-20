# Study period
START_DATE = "2014-01-01"
END_DATE = "2021-12-31"

HOUR_COLS = [str(h) for h in range(1, 25)]
EXOG_COLS = ["AOD", "Temperature", "Rain"]

SARIMAX_ORDER = (1, 0, 1)

SEASONS = ["Summer", "Monsoon", "Winter"]
SEASON_COLORS = {"Summer": "#eb6834", "Monsoon": "#2a78d6", "Winter": "#1baf7a"}

# sheet = sheet name in the DoE CAMS workbook, aod_col = column in the AOD file
STATIONS = {
    "agrabad": {"name": "Agrabad", "sheet": "Agrabad Chittagong", "aod_col": "Agrabad"},
    "khulshi": {"name": "Khulshi", "sheet": "TV st-Chittagong", "aod_col": "Khulshi"},
}
