import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

def run_xgboost_forecast(df: pd.DataFrame, date_col: str, target_col: str, horizon_days: int, cross_val: bool = True) -> tuple[pd.DataFrame, dict, XGBRegressor, pd.DataFrame, list[str]]:
    """
    Fits XGBoost regressor using autoregressive lags and rolling average features.
    Why: Handles complex non-linear trends and interaction effects on structured timelines.
    """
    df_sorted = df.sort_values(date_col).copy()
    
    series_df = pd.DataFrame({
        'date': pd.to_datetime(df_sorted[date_col]),
        'y': df_sorted[target_col].astype(float)
    })

    # Resample to daily frequency to ensure regular lags
    series_df = series_df.set_index('date').resample('D').sum().reset_index()

    # Feature engineering helper
    def create_features(data: pd.DataFrame) -> pd.DataFrame:
        df_feat = data.copy()
        n = len(df_feat)
        # Fallback lags defensively for tiny datasets
        df_feat['lag_1'] = df_feat['y'].shift(1).fillna(0.0)
        df_feat['lag_7'] = df_feat['y'].shift(min(7, max(1, n - 1))).fillna(0.0)
        df_feat['lag_14'] = df_feat['y'].shift(min(14, max(1, n - 1))).fillna(0.0)
        df_feat['rolling_mean_7'] = df_feat['y'].shift(1).rolling(window=min(7, max(1, n - 1)), min_periods=1).mean().fillna(0.0)
        return df_feat

    df_features = create_features(series_df)
    
    X = df_features.drop(columns=['date', 'y'])
    y = df_features['y']

    try:
        # Fit full model
        xgb_full = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1)
        xgb_full.fit(X, y)
        hist_pred = xgb_full.predict(X)

        # Calculate MAE and RMSE comparing actuals vs in-sample predictions
        mae = float(mean_absolute_error(y, hist_pred))
        rmse = float(np.sqrt(mean_squared_error(y, hist_pred)))
    except Exception as e:
        raise ValueError(f"XGBoost forecast model training or diagnostics evaluation failed: {str(e)}")

    # Recursive multi-step forecasting
    last_date = series_df['date'].max()
    current_df = series_df.copy()

    future_features_list = []
    for i in range(horizon_days):
        next_date = last_date + pd.Timedelta(days=i + 1)
        next_row = pd.DataFrame({'date': [next_date], 'y': [np.nan]})
        current_df = pd.concat([current_df, next_row], ignore_index=True)
        
        temp_feat = create_features(current_df)
        last_row = temp_feat.iloc[[-1]].drop(columns=['date', 'y'])
        
        pred = float(xgb_full.predict(last_row)[0])
        current_df.loc[current_df['date'] == next_date, 'y'] = pred
        future_features_list.append(last_row)

    future_rows = current_df.iloc[-horizon_days:].copy()
    X_future = pd.concat(future_features_list, ignore_index=True)

    # Calculate intervals based on residuals standard deviation
    residuals = y.to_numpy() - hist_pred
    std_resid = float(np.std(residuals)) if len(residuals) > 1 else max(1.0, float(np.std(y)))

    out_df = pd.DataFrame({
        'date': future_rows['date'].dt.strftime('%Y-%m-%d'),
        'yhat': future_rows['y'].astype(float),
        'yhat_lower': (future_rows['y'] - 1.96 * std_resid).astype(float),
        'yhat_upper': (future_rows['y'] + 1.96 * std_resid).astype(float)
    })

    metrics = {"mae": mae, "rmse": rmse}
    return out_df, metrics, xgb_full, X_future, X.columns.tolist()
