import pandas as pd
import numpy as np
import logging
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Suppress Prophet logs to keep console clean
logging.getLogger('prophet').setLevel(logging.WARNING)

def run_prophet_forecast(df: pd.DataFrame, date_col: str, target_col: str, horizon_days: int, cross_val: bool = True) -> tuple[pd.DataFrame, dict]:
    """
    Fits Prophet forecasting model over df timeline, computing MAE/RMSE metrics dynamically.
    Why: Evaluates model error by comparing historical actuals to training set predictions.
    """
    df_sorted = df.sort_values(date_col).copy()
    
    prophet_df = pd.DataFrame({
        'ds': pd.to_datetime(df_sorted[date_col]),
        'y': df_sorted[target_col].astype(float)
    })

    try:
        # Fit on all records for future projection and dynamic diagnostics evaluation
        m_full = Prophet(yearly_seasonality=False, daily_seasonality=False)
        m_full.fit(prophet_df)

        # Generate predictions for the historical period (training data)
        hist_forecast = m_full.predict(prophet_df[['ds']])
        
        # Calculate MAE and RMSE comparing actuals vs in-sample predictions
        mae = float(mean_absolute_error(prophet_df['y'], hist_forecast['yhat']))
        rmse = float(np.sqrt(mean_squared_error(prophet_df['y'], hist_forecast['yhat'])))
    except Exception as e:
        raise ValueError(f"Prophet forecast model training or diagnostics evaluation failed: {str(e)}")

    # Forecast future period
    future = m_full.make_future_dataframe(periods=horizon_days)
    forecast = m_full.predict(future)

    future_forecast = forecast.iloc[-horizon_days:].copy()
    out_df = pd.DataFrame({
        'date': future_forecast['ds'].dt.strftime('%Y-%m-%d'),
        'yhat': future_forecast['yhat'].astype(float),
        'yhat_lower': future_forecast['yhat_lower'].astype(float),
        'yhat_upper': future_forecast['yhat_upper'].astype(float)
    })

    metrics = {"mae": mae, "rmse": rmse}
    return out_df, metrics
