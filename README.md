# MSE Stock Market Data Tracker for FINKI DAS Project

A Django web application for tracking and visualizing stock data from the Macedonian Stock Exchange (MSE).

## Project Goal

This application serves as a data aggregator and visualization tool for the Macedonian Stock Exchange, providing:
- Historical stock price data collection and storage
- Real-time market data updates
- Interactive data visualization
- Efficient bulk data processing
- CSV export capabilities for further analysis

## Features

- Fetch and display real-time stock data from MSE
- Historical price data visualization using Chart.js
- Automatic symbol list updates
- Multi-threaded data fetching for improved performance
- Interactive date range selection
- Responsive Bootstrap UI
- CSV data export functionality

## Project Structure

### Core Components

1. **Data Collection Pipeline**
   - `Pipeline` class with modular filters for data processing
   - `WebScraper` utility for MSE data extraction
   - Multi-threaded data fetching for improved performance

2. **Data Models**
   - `Issuer`: Stock symbol and company information
   - `StockPrice`: Historical price data with comprehensive metrics

3. **Management Commands**
   - `get_all_symbols`: Updates available stock symbols
   - `fetch_stock_data_for_symbol`: Fetches data for specific symbols
   - `fetch_all_stock_data`: Bulk historical data collection

4. **Web Interface**
   - Main dashboard with symbol list and search
   - Detailed stock view with interactive charts
   - Date range selection for custom data fetching

### Directory Structure

```
stock_market/
├── core/ # Main application
│ ├── management/ # Custom Django commands
│ ├── migrations/ # Database migrations
│ ├── templates/ # HTML templates
│ ├── models.py # Database models
│ ├── pipeline.py # Data processing pipeline
│ ├── utils.py # Utility functions
│ └── views.py # View controllers
├── stock_market/ # Project settings
└── static/ # Static assets
```

### Key Technologies

- **Backend**: Django 5.1
- **Frontend**: Bootstrap 5.3, Chart.js
- **Data Processing**: Pandas, Selenium
- **Database**: PostgreSQL (production), SQLite (development)
- **Deployment**: Docker, Gunicorn

### Development Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Start development server:
   ```bash
   python manage.py runserver
   ```

### Docker Deployment

Build and run using Docker:

bash
docker build -t mse-tracker .
docker run -p 80:80 mse-tracker


### Data Collection

1. Update symbol list:
   ```bash
   python manage.py get_all_symbols
   ```

2. Fetch historical data:
   ```bash
   python manage.py fetch_all_stock_data --from-year 2000
   ```

### Security Notes

- CSRF protection enabled for all POST requests
- Environment-based configuration
- Secure headers and middleware configuration