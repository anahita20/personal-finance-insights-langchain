import pandas as pd
from prophet import Prophet
from copy import deepcopy


def enrich_with_forecast_and_anomalies(
    data,
    date_key="date",
    value_keys=("income", "expense"),
    granularity="daily",
    horizon=7
):

    base_df = pd.DataFrame(data)
    base_df = _parse_dates(base_df, date_key, granularity)

    freq = "D" if granularity == "daily" else "W"
    enriched = deepcopy(data)

    # Anomaly detection (historical only)
    for key in value_keys:
        anomaly_mask = _detect_anomalies(base_df, key)

        for i, is_anomaly in enumerate(anomaly_mask):
            if is_anomaly:
                enriched[i].setdefault("anomaly", {})[key] = True

    # Forecasting (per metric)
    forecasts = {}
    forecast_dates = None

    for key in value_keys:
        fcast = _forecast_single_series(base_df, key, horizon, freq)
        forecasts[key] = fcast["yhat"].values
        forecast_dates = fcast["ds"].values

    # Append forecast points
    for i in range(horizon):
        point = {
            date_key: pd.to_datetime(forecast_dates[i]).strftime("%Y-%m-%d"),
            "isForecast": True
        }
        for key in value_keys:
            point[key] = round(float(forecasts[key][i]), 2)

        enriched.append(point)

    return enriched


# Helpers
def _parse_dates(df, date_key, granularity):
    if granularity == "daily":
        df["ds"] = pd.to_datetime(df[date_key])
    elif granularity == "weekly":
        # "2024-48" → Monday of that ISO week
        df["ds"] = pd.to_datetime(df[date_key] + "-1", format="%Y-%W-%w")
    else:
        raise ValueError("Unsupported granularity")
    return df


def _forecast_single_series(df, value_key, horizon, freq):
    prophet_df = df[["ds", value_key]].rename(columns={value_key: "y"})

    model = Prophet()
    model.fit(prophet_df)

    future = model.make_future_dataframe(periods=horizon, freq=freq)
    forecast = model.predict(future)

    return forecast.tail(horizon)


def _detect_anomalies(df, value_key, z_thresh=3.0):
    mean = df[value_key].mean()
    std = df[value_key].std()

    if std == 0 or pd.isna(std):
        return [False] * len(df)

    z = (df[value_key] - mean) / std
    return z.abs() > z_thresh
