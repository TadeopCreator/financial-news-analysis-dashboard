import os
import requests
import ccxt
import yfinance as yf
from datetime import datetime
import functions_framework
from google.cloud import firestore

NEWS_AMOUNT = 20

news_list = []

def env_vars():
    return str(os.environ.get("ALPHAVANTAGE_API", "Specified environment variable is not set."))

@functions_framework.cloud_event
def process_recent_news(cloud_event):
    global news_list
    news_list = []

    try:        
        p_k = env_vars()

        url = 'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&limit=20&apikey=' + p_k
        r = requests.get(url)
        data = r.json()

        news = data['feed']

        for n in news:
            if n['title'].startswith("SHAREHOLDER ALERT: "):
                n['title'] = n['title'][len("SHAREHOLDER ALERT: "):]
            
            tickers = n['ticker_sentiment'] or []
            if tickers:
                for t in n['ticker_sentiment']:                    
                    if t['ticker'].startswith("FOREX:"):
                        t['ticker'] = t['ticker'][len("FOREX:"):]
                        t['type'] = "FOREX"
                    elif t['ticker'].startswith("CRYPTO:"):
                        t['ticker'] = t['ticker'][len("CRYPTO:"):]
                        t['type'] = "CRYPTO"
                    else:
                        t['type'] = "STOCK/ETF/INDEX"

            news_list.append(n)
    except Exception as e:
        print("Error when request API: " + e)

    counter = 0

    for selected_new_info in news_list:
        # If there is no assets, don't save the article
        if not selected_new_info['ticker_sentiment']:
            print('No assets error')
        else:
            # Count the number of valid symbols in the article, a valid symbol is a symbol that has a name, price and exchange
            valid_symbols = 0
            # For calculate average risk whitin assets in the new
            risk_avg = 0

            for asset in selected_new_info['ticker_sentiment']:
                ticker = asset['ticker']
                print("Current ticker: " + ticker)

                try:
                    # If the asset is a CRYPTO
                    if asset['type'] == 'CRYPTO':
                        exchange = ccxt.coinbasepro()

                        symbol = ticker + '/USDT'
                        fetch_ticker = exchange.fetch_ticker(symbol)

                        asset['name'] = ticker
                        asset['price'] = fetch_ticker['ask']
                        asset['exchange'] = "Coinbase Pro"
                        asset['risk'] = 10                    
                    else:
                        ticker_info = yf.Ticker(ticker)

                        if 'currentPrice' in ticker_info.info:
                            asset['price'] = ticker_info.info['currentPrice']
                        else:
                            # if ticker dont have current price, not include it
                            continue

                        if 'shortName' in ticker_info.info:
                            asset['name'] = ticker_info.info['shortName']
                        else:
                            asset['name'] = ticker

                        if 'exchange' in ticker_info.info:
                            asset['exchange'] = ticker_info.info['exchange']
                        else:
                            asset['exchange'] = "Unknown"

                        if 'overallRisk' in ticker_info.info:
                            asset['risk'] = ticker_info.info['overallRisk']
                        else:
                            asset['risk'] = 5

                    risk_avg += asset['risk']
                    valid_symbols += 1                    
                except Exception as e:
                    # Delete current asset from seleted new info
                    selected_new_info['ticker_sentiment'].remove(asset)
                    print('yfinance/ccxt error: ' + e)

        # If there are at list 1 valid symbol                       
        if valid_symbols > 0:
            # Calculate average risk whitin assets in the new
            risk_avg = risk_avg / valid_symbols
            selected_new_info['risk_avg'] = risk_avg

            timestamp = selected_new_info['time_published']
            datetime_obj = datetime.strptime(timestamp, '%Y%m%dT%H%M%S')
            selected_new_info['time_published'] = datetime_obj

            db = firestore.Client(project='financial-news-analysis-410223')

            db.collection("news").document().set(selected_new_info)

            print("Saved into Firestore")

            # Count the number of valid news
            counter += 1

            if counter > NEWS_AMOUNT:
                print("News loaded")
                break
        else:
            print('No valid symbols')