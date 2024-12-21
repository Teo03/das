import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import ta

def calculate_technical_indicators(df: pd.DataFrame, periods: List[int] = [1, 5, 20]) -> Dict[str, pd.DataFrame]:
    """Calculate technical indicators for different time periods.
    
    Args:
        df: DataFrame with columns ['date', 'close_price', 'volume', 'high', 'low']
        periods: List of periods to calculate indicators for [1-day, 1-week, 1-month]
    
    Returns:
        Dictionary containing DataFrames with calculated indicators
    """
    results = {}
    
    # Convert Decimal columns to float
    numeric_columns = ['close_price', 'high', 'low', 'volume']
    for col in numeric_columns:
        df[col] = df[col].astype(float)
    
    for period in periods:
        # Moving Averages
        df[f'sma_{period}'] = ta.trend.sma_indicator(df['close_price'], window=period)
        df[f'ema_{period}'] = ta.trend.ema_indicator(df['close_price'], window=period)
        df[f'wma_{period}'] = df['close_price'].rolling(window=period).apply(
            lambda x: np.sum(x * np.arange(1, len(x) + 1)) / np.sum(np.arange(1, len(x) + 1))
        )
        
        # Calculate TEMA manually
        ema1 = ta.trend.ema_indicator(df['close_price'], window=period)
        ema2 = ta.trend.ema_indicator(ema1, window=period)
        ema3 = ta.trend.ema_indicator(ema2, window=period)
        df[f'tema_{period}'] = 3 * ema1 - 3 * ema2 + ema3
        
        df[f'kama_{period}'] = ta.momentum.kama(df['close_price'], window=period)
        
        # Oscillators
        df[f'rsi_{period}'] = ta.momentum.rsi(df['close_price'], window=period)
        df[f'stoch_{period}'] = ta.momentum.stoch(df['high'], df['low'], df['close_price'], window=period)
        df[f'cci_{period}'] = ta.trend.cci(df['high'], df['low'], df['close_price'], window=period)
        df[f'macd_{period}'] = ta.trend.macd_diff(df['close_price'], window_slow=period*2, window_fast=period)
        df[f'willr_{period}'] = ta.momentum.williams_r(df['high'], df['low'], df['close_price'], lbp=period)
        
        results[period] = df.copy()
    
    return results

def generate_signals(indicators_df: pd.DataFrame, period: int) -> pd.DataFrame:
    """Generate trading signals based on technical indicators.
    
    Args:
        indicators_df: DataFrame with calculated technical indicators
        period: Time period for the indicators
    
    Returns:
        DataFrame with trading signals
    """
    signals = pd.DataFrame(index=indicators_df.index)
    
    # Moving Average Signals
    signals[f'sma_signal_{period}'] = np.where(
        indicators_df['close_price'] > indicators_df[f'sma_{period}'], 'BUY', 'SELL'
    )
    signals[f'ema_signal_{period}'] = np.where(
        indicators_df['close_price'] > indicators_df[f'ema_{period}'], 'BUY', 'SELL'
    )
    signals[f'wma_signal_{period}'] = np.where(
        indicators_df['close_price'] > indicators_df[f'wma_{period}'], 'BUY', 'SELL'
    )
    signals[f'tema_signal_{period}'] = np.where(
        indicators_df['close_price'] > indicators_df[f'tema_{period}'], 'BUY', 'SELL'
    )
    signals[f'kama_signal_{period}'] = np.where(
        indicators_df['close_price'] > indicators_df[f'kama_{period}'], 'BUY', 'SELL'
    )
    
    # Oscillator Signals
    signals[f'rsi_signal_{period}'] = np.where(
        indicators_df[f'rsi_{period}'] > 70, 'SELL',
        np.where(indicators_df[f'rsi_{period}'] < 30, 'BUY', 'HOLD')
    )
    signals[f'stoch_signal_{period}'] = np.where(
        indicators_df[f'stoch_{period}'] > 80, 'SELL',
        np.where(indicators_df[f'stoch_{period}'] < 20, 'BUY', 'HOLD')
    )
    signals[f'cci_signal_{period}'] = np.where(
        indicators_df[f'cci_{period}'] > 100, 'SELL',
        np.where(indicators_df[f'cci_{period}'] < -100, 'BUY', 'HOLD')
    )
    signals[f'macd_signal_{period}'] = np.where(
        indicators_df[f'macd_{period}'] > 0, 'BUY',
        np.where(indicators_df[f'macd_{period}'] < 0, 'SELL', 'HOLD')
    )
    signals[f'willr_signal_{period}'] = np.where(
        indicators_df[f'willr_{period}'] > -20, 'SELL',
        np.where(indicators_df[f'willr_{period}'] < -80, 'BUY', 'HOLD')
    )
    
    return signals

def get_consensus_signal(signals: pd.DataFrame, period: int) -> str:
    """Get consensus signal based on all indicators.
    
    Args:
        signals: DataFrame with trading signals
        period: Time period for the indicators
    
    Returns:
        Consensus signal (BUY, SELL, or HOLD)
    """
    period_signals = signals[[col for col in signals.columns if str(period) in col]]
    buy_count = (period_signals == 'BUY').sum().sum()
    sell_count = (period_signals == 'SELL').sum().sum()
    
    if buy_count > sell_count and buy_count > len(period_signals.columns) / 3:
        return 'BUY'
    elif sell_count > buy_count and sell_count > len(period_signals.columns) / 3:
        return 'SELL'
    return 'HOLD'