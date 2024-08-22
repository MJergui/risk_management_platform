from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import yfinance as yf
from scipy.stats import norm

app = Flask(__name__)

def calculate_historical_var(returns, confidence_level):
    # edge case - empty values 
    if returns.size == 0:
        return None
    if confidence_level == 1.0:
        return np.max(returns)
    if confidence_level == 0.0:
        return np.min(returns)
    var = np.percentile(returns, (1 - confidence_level) * 100)
    return var

def calculate_variance_covariance_var(returns, confidence_level): #normal distribution
    if returns.size == 0:
        return None
    # edge cases: extreme confidence levels (like 0% and 100%) 
    # previously z_score was returning -inf when the confidence level is 100%
    if confidence_level == 1.0:
        return np.max(returns)
    if confidence_level == 0.0:
        return np.min(returns)
    
    mean = returns.mean()
    std_dev = returns.std()
    z_score = norm.ppf(1 - confidence_level) # formular for left tail (loss threshold) of the distribution.
    var = mean - z_score * std_dev
    return var

def calculate_monte_carlo_var(returns, confidence_level, num_simulations=10000):
    if returns.size == 0:
        return None
    if confidence_level == 1.0:
        return np.max(returns)
    if confidence_level == 0.0:
        return np.min(returns)
    mean = returns.mean()
    std_dev = returns.std()
    simulated_returns = np.random.normal(mean, std_dev, num_simulations)
    var = np.percentile(simulated_returns, (1 - confidence_level) * 100)
    return var

@app.route('/', methods=['GET', 'POST'])
def index():
    var = None
    error = None
    if request.method == 'POST':
        tickers = request.form['tickers'].split(',')
        weights = list(map(float, request.form['weights'].split(',')))
        confidence_level = float(request.form['confidence_level'])
        start_date = request.form['start_date']
        method = request.form['method']

        try:
            # Fetch historical data
            data = yf.download(tickers, start=start_date)['Adj Close']

            if data.empty:
                error = "No data available for the given tickers and date range."
                return render_template('index.html', error=error)

            returns = data.pct_change().dropna()

            if returns.empty:
                error = "No returns data available after processing. Check the tickers and date range."
                return render_template('index.html', error=error)

            portfolio_returns = returns.dot(weights)

            # Calculate VaR based on selected method
            if method == 'historical':
                var = calculate_historical_var(portfolio_returns, confidence_level)
            elif method == 'var_cov':
                var = calculate_variance_covariance_var(portfolio_returns, confidence_level)
            elif method == 'monte_carlo':
                var = calculate_monte_carlo_var(portfolio_returns, confidence_level)

            return render_template('index.html', var=var, tickers=tickers, weights=weights, method=method)

        except Exception as e:
            error = str(e)

    return render_template('index.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)
