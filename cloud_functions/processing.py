import os
import requests
import ccxt
import yfinance as yf
from datetime import datetime
from google.cloud import firestore
from dotenv import load_dotenv

NEWS_AMOUNT = 20

news_list = []

def processing():
    global news_list
    news_list = []

    load_dotenv()

    try:        
        p_k = os.environ['ALPHAVANTAGE_API']

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
        counter += 1

        if counter > NEWS_AMOUNT:
            break

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
                        asset['name'] = ticker_info.info['shortName']
                        asset['price'] = ticker_info.info['currentPrice']
                        asset['exchange'] = ticker_info.info['exchange']

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
        else:
            print('No valid symbols')