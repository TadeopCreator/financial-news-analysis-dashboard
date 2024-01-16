import os
import requests
import ccxt
import yfinance as yf
from datetime import datetime, date, timedelta
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

        news_count = 0
        total_assets = 0
        total_equity = 0
        total_index = 0
        total_forex = 0
        total_etf = 0
        total_crypto = 0
        total_mutualfund = 0
        total_ecnquote = 0
        total_undefined = 0

        diff_avg_risk = 0
        diff_avg_sentiment_score = 0

        diff_sentiment_equity = 0
        diff_sentiment_index = 0
        diff_sentiment_forex = 0
        diff_sentiment_etf = 0
        diff_sentiment_crypto = 0
        diff_sentiment_mutualfund = 0
        diff_sentiment_ecnquote = 0
        diff_sentiment_undefined = 0

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
        # Count the number of valid symbols in the article, a valid symbol is a symbol that has a name, price and exchange
        valid_symbols = 0
        
        # If there is no assets, don't save the article
        if not selected_new_info['ticker_sentiment']:
            print('No assets')
        else:
            # For calculate average risk whitin assets in the new
            risk_avg = 0

            for asset in selected_new_info['ticker_sentiment']:
                ticker = asset['ticker']
                print("Current ticker: " + ticker)

                try:
                    # If the asset is a CRYPTO
                    if asset['type'] == 'CRYPTO':
                        exchange = ccxt.bitget()
                        
                        symbol = ticker + '/USDT'
                        fetch_ticker = exchange.fetch_ticker(symbol)

                        asset['name'] = ticker
                        asset['price'] = fetch_ticker['ask']
                        asset['exchange'] = "Binance"
                        asset['risk'] = 10
                        total_crypto += 1              
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

                        if 'quoteType' in ticker_info.info:
                            asset['type'] = ticker_info.info['quoteType']                        

                        if 'exchange' in ticker_info.info:
                            asset['exchange'] = ticker_info.info['exchange']
                        else:
                            asset['exchange'] = "Unknown"

                        if 'overallRisk' in ticker_info.info:
                            asset['risk'] = ticker_info.info['overallRisk']
                        else:
                            asset['risk'] = 5

                        if asset['type'] == 'STOCK/ETF/INDEX':
                            total_undefined += 1
                            diff_sentiment_undefined += float(asset['ticker_sentiment_score'])
                        elif asset['type'] == 'EQUITY':
                            total_equity += 1
                            diff_sentiment_equity += float(asset['ticker_sentiment_score'])
                        elif asset['type'] == 'INDEX':
                            total_index += 1
                            diff_sentiment_index += float(asset['ticker_sentiment_score'])
                        elif asset['type'] == 'FOREX':
                            total_forex += 1
                            diff_sentiment_forex += float(asset['ticker_sentiment_score'])
                        elif asset['type'] == 'ETF':
                            total_etf += 1
                            diff_sentiment_etf += float(asset['ticker_sentiment_score'])
                        elif asset['type'] == 'CRYPTO':
                            total_crypto += 1
                            diff_sentiment_crypto += float(asset['ticker_sentiment_score'])
                        elif asset['type'] == 'MUTUALFUND':
                            total_mutualfund += 1
                            diff_sentiment_mutualfund += float(asset['ticker_sentiment_score'])
                        elif asset['type'] == 'ECNQUOTE':
                            total_ecnquote += 1
                            diff_sentiment_ecnquote += float(asset['ticker_sentiment_score'])
                        else:                    
                            total_undefined += 1
                            diff_sentiment_undefined += float(asset['ticker_sentiment_score'])
                    
                    risk_avg += asset['risk']
                    valid_symbols += 1                    
                except Exception as e:
                    # Delete current asset from seleted new info
                    selected_new_info['ticker_sentiment'].remove(asset)
                    # Print error                    
                    print('yfinance/ccxt error: ' + str(e))

        # If there are at list 1 valid symbol                       
        if valid_symbols > 0:
            # Count the number of assets in the new
            total_assets += valid_symbols
            # Calculate average risk whitin assets in the new
            risk_avg = risk_avg / valid_symbols
            selected_new_info['risk_avg'] = risk_avg
            diff_avg_risk += risk_avg

            diff_avg_sentiment_score += float(selected_new_info['overall_sentiment_score'])

            timestamp = selected_new_info['time_published']
            datetime_obj = datetime.strptime(timestamp, '%Y%m%dT%H%M%S')
            selected_new_info['time_published'] = datetime_obj

            db = firestore.Client(project='financial-news-analysis-410223')

            db.collection("news").document().set(selected_new_info)

            news_count += 1

            print("Saved into Firestore")

            # Count the number of valid news
            counter += 1

            if counter > NEWS_AMOUNT:
                print("News loaded")
                break
        else:
            print('No valid symbols')
    
    # Incrementar el valor del campo news-total-count de la coleccion insights del documento insights-data con el total de las noticias
    insights_doc = db.collection("insights").document("insights-data")
    # Actualizaciones DIARIAS
    # Actualizacion de totales
    insights_doc.update({"news_total_count": firestore.Increment(news_count)})
    insights_doc.update({"total_assets": firestore.Increment(total_assets)})
    insights_doc.update({"total_equity": firestore.Increment(total_equity)})
    insights_doc.update({"total_index": firestore.Increment(total_index)})
    insights_doc.update({"total_forex": firestore.Increment(total_forex)})
    insights_doc.update({"total_etf": firestore.Increment(total_etf)})
    insights_doc.update({"total_crypto": firestore.Increment(total_crypto)})
    insights_doc.update({"total_mutualfund": firestore.Increment(total_mutualfund)})
    insights_doc.update({"total_ecnquote": firestore.Increment(total_ecnquote)})
    insights_doc.update({"total_undefined": firestore.Increment(total_undefined)})

    # Actualizacion de temporales
    insights_doc.update({"temp_last_week_avg_risk": firestore.Increment(diff_avg_risk)})
    insights_doc.update({"temp_last_week_avg_sentiment_score": firestore.Increment(diff_avg_sentiment_score)})    
    insights_doc.update({"temp_last_week_total_assets": firestore.Increment(total_assets)})
    insights_doc.update({"temp_last_week_type_equity_count": firestore.Increment(total_equity)})
    insights_doc.update({"temp_last_week_type_index_count": firestore.Increment(total_index)})
    insights_doc.update({"temp_last_week_type_forex_count": firestore.Increment(total_forex)})
    insights_doc.update({"temp_last_week_type_etf_count": firestore.Increment(total_etf)})
    insights_doc.update({"temp_last_week_type_crypto_count": firestore.Increment(total_crypto)})
    insights_doc.update({"temp_last_week_type_mutualfund_count": firestore.Increment(total_mutualfund)})
    insights_doc.update({"temp_last_week_type_ecnquote_count": firestore.Increment(total_ecnquote)})
    insights_doc.update({"temp_last_week_type_undefined_count": firestore.Increment(total_undefined)})
    insights_doc.update({"temp_last_week_avg_sentiment_equity": firestore.Increment(diff_sentiment_equity)})
    insights_doc.update({"temp_last_week_avg_sentiment_index": firestore.Increment(diff_sentiment_index)})
    insights_doc.update({"temp_last_week_avg_sentiment_forex": firestore.Increment(diff_sentiment_forex)})
    insights_doc.update({"temp_last_week_avg_sentiment_etf": firestore.Increment(diff_sentiment_etf)})
    insights_doc.update({"temp_last_week_avg_sentiment_crypto": firestore.Increment(diff_sentiment_crypto)})
    insights_doc.update({"temp_last_week_avg_sentiment_mutualfund": firestore.Increment(diff_sentiment_mutualfund)})
    insights_doc.update({"temp_last_week_avg_sentiment_ecnquote": firestore.Increment(diff_sentiment_ecnquote)})
    insights_doc.update({"temp_last_week_avg_sentiment_undefined": firestore.Increment(diff_sentiment_undefined)})
        
    insights_dict = insights_doc.get().to_dict()
    day_of_week = insights_dict['day_of_week']
    
    if day_of_week == 5:
        insights_doc.update({"day_of_week": 1})
    else:
        insights_doc.update({"day_of_week": firestore.Increment(1)})

    # Si el dia de la semana tiene el numero 4 quiere decir que hoy le sumamos 1 y ahora es 5
    # Es hora de actualizar los valores semanales
    if day_of_week == 4:
        # Actualizaciones SEMANALES
        # Recupero el documento insights con las ultimas actualizaciones
        insights_doc_recover = db.collection("insights").document("insights-data")
        insights_dict_recover = insights_doc_recover.get().to_dict()

        # 100 es la cantidad de noticias analizadas a la semana

        temp_last_week_avg_risk = (float(insights_dict_recover['temp_last_week_avg_risk']))/100
        temp_last_week_avg_sentiment_score = (float(insights_dict_recover['temp_last_week_avg_sentiment_score']))/100

        insights_doc_recover.update({"last_week_avg_risk": temp_last_week_avg_risk})
        insights_doc_recover.update({"last_week_avg_sentiment_score": temp_last_week_avg_sentiment_score})
        # Reseteo temporales
        insights_doc_recover.update({"temp_last_week_avg_risk": 0})
        insights_doc_recover.update({"temp_last_week_avg_sentiment_score": 0})

        temp_last_week_total_assets = float(insights_dict_recover['temp_last_week_total_assets'])
        temp_last_week_type_equity_count = float(insights_dict_recover['temp_last_week_type_equity_count'])
        temp_last_week_type_index_count = float(insights_dict_recover['temp_last_week_type_index_count'])
        temp_last_week_type_forex_count = float(insights_dict_recover['temp_last_week_type_forex_count'])
        temp_last_week_type_etf_count = float(insights_dict_recover['temp_last_week_type_etf_count'])
        temp_last_week_type_crypto_count = float(insights_dict_recover['temp_last_week_type_crypto_count'])
        temp_last_week_type_mutualfund_count = float(insights_dict_recover['temp_last_week_type_mutualfund_count'])
        temp_last_week_type_ecnquote_count = float(insights_dict_recover['temp_last_week_type_ecnquote_count'])
        temp_last_week_type_undefined_count = float(insights_dict_recover['temp_last_week_type_undefined_count'])

        insights_doc_recover.update({"last_week_total_assets": temp_last_week_total_assets})
        insights_doc_recover.update({"last_week_type_equity_count": temp_last_week_type_equity_count})
        insights_doc_recover.update({"last_week_type_index_count": temp_last_week_type_index_count})
        insights_doc_recover.update({"last_week_type_forex_count": temp_last_week_type_forex_count})
        insights_doc_recover.update({"last_week_type_etf_count": temp_last_week_type_etf_count})
        insights_doc_recover.update({"last_week_type_crypto_count": temp_last_week_type_crypto_count})
        insights_doc_recover.update({"last_week_type_mutualfund_count": temp_last_week_type_mutualfund_count})
        insights_doc_recover.update({"last_week_type_ecnquote_count": temp_last_week_type_ecnquote_count})
        insights_doc_recover.update({"last_week_type_undefined_count": temp_last_week_type_undefined_count})
        # Reseteo temporales
        insights_doc_recover.update({"temp_last_week_total_assets": 0})
        insights_doc_recover.update({"temp_last_week_type_equity_count": 0})
        insights_doc_recover.update({"temp_last_week_type_index_count": 0})
        insights_doc_recover.update({"temp_last_week_type_forex_count": 0})
        insights_doc_recover.update({"temp_last_week_type_etf_count": 0})
        insights_doc_recover.update({"temp_last_week_type_crypto_count": 0})
        insights_doc_recover.update({"temp_last_week_type_mutualfund_count": 0})
        insights_doc_recover.update({"temp_last_week_type_ecnquote_count": 0})
        insights_doc_recover.update({"temp_last_week_type_undefined_count": 0})
        
        # Proteger para no dividir por 0
        if insights_dict_recover['temp_last_week_type_equity_count'] == 0:
            temp_last_week_avg_sentiment_equity = 0
        else:
            temp_last_week_avg_sentiment_equity = (float(insights_dict_recover['temp_last_week_avg_sentiment_equity']))/float(insights_dict_recover['temp_last_week_type_equity_count'])
        
        if insights_dict_recover['temp_last_week_type_index_count'] == 0:
            temp_last_week_avg_sentiment_index = 0
        else:
            temp_last_week_avg_sentiment_index = (float(insights_dict_recover['temp_last_week_avg_sentiment_index']))/float(insights_dict_recover['temp_last_week_type_index_count'])
        
        if insights_dict_recover['temp_last_week_type_forex_count'] == 0:
            temp_last_week_avg_sentiment_forex = 0
        else:
            temp_last_week_avg_sentiment_forex = (float(insights_dict_recover['temp_last_week_avg_sentiment_forex']))/float(insights_dict_recover['temp_last_week_type_forex_count'])
        
        if insights_dict_recover['temp_last_week_type_etf_count'] == 0:
            temp_last_week_avg_sentiment_etf = 0
        else:
            temp_last_week_avg_sentiment_etf = (float(insights_dict_recover['temp_last_week_avg_sentiment_etf']))/float(insights_dict_recover['temp_last_week_type_etf_count'])

        if insights_dict_recover['temp_last_week_type_crypto_count'] == 0:
            temp_last_week_avg_sentiment_crypto = 0
        else:
            temp_last_week_avg_sentiment_crypto = (float(insights_dict_recover['temp_last_week_avg_sentiment_crypto']))/float(insights_dict_recover['temp_last_week_type_crypto_count'])
        
        if insights_dict_recover['temp_last_week_type_mutualfund_count'] == 0:
            temp_last_week_avg_sentiment_mutualfund = 0
        else:
            temp_last_week_avg_sentiment_mutualfund = (float(insights_dict_recover['temp_last_week_avg_sentiment_mutualfund']))/float(insights_dict_recover['temp_last_week_type_mutualfund_count'])

        if insights_dict_recover['temp_last_week_type_ecnquote_count'] == 0:
            temp_last_week_avg_sentiment_ecnquote = 0
        else:
            temp_last_week_avg_sentiment_ecnquote = (float(insights_dict_recover['temp_last_week_avg_sentiment_ecnquote']))/float(insights_dict_recover['temp_last_week_type_ecnquote_count'])
        
        if insights_dict_recover['temp_last_week_type_undefined_count'] == 0:
            temp_last_week_avg_sentiment_undefined = 0
        else:
            temp_last_week_avg_sentiment_undefined = (float(insights_dict_recover['temp_last_week_avg_sentiment_undefined']))/float(insights_dict_recover['temp_last_week_type_undefined_count'])
            
        insights_doc_recover.update({"last_week_avg_sentiment_equity": temp_last_week_avg_sentiment_equity})
        insights_doc_recover.update({"last_week_avg_sentiment_index": temp_last_week_avg_sentiment_index})
        insights_doc_recover.update({"last_week_avg_sentiment_forex": temp_last_week_avg_sentiment_forex})
        insights_doc_recover.update({"last_week_avg_sentiment_etf": temp_last_week_avg_sentiment_etf})
        insights_doc_recover.update({"last_week_avg_sentiment_crypto": temp_last_week_avg_sentiment_crypto})
        insights_doc_recover.update({"last_week_avg_sentiment_mutualfund": temp_last_week_avg_sentiment_mutualfund})
        insights_doc_recover.update({"last_week_avg_sentiment_ecnquote": temp_last_week_avg_sentiment_ecnquote})
        insights_doc_recover.update({"last_week_avg_sentiment_undefined": temp_last_week_avg_sentiment_undefined})
        # Reseteo temporales
        insights_doc_recover.update({"temp_last_week_avg_sentiment_equity": 0})
        insights_doc_recover.update({"temp_last_week_avg_sentiment_index": 0})
        insights_doc_recover.update({"temp_last_week_avg_sentiment_forex": 0})
        insights_doc_recover.update({"temp_last_week_avg_sentiment_etf": 0})
        insights_doc_recover.update({"temp_last_week_avg_sentiment_crypto": 0})
        insights_doc_recover.update({"temp_last_week_avg_sentiment_mutualfund": 0})
        insights_doc_recover.update({"temp_last_week_avg_sentiment_ecnquote": 0})
        insights_doc_recover.update({"temp_last_week_avg_sentiment_undefined": 0})

    # Set orders, wallets and balances
    today = datetime.combine(date.today(), datetime.min.time())

    # If it is Monday today, checking if was friday...
    if day_of_week == 5:        
        initial_day = today - timedelta(days=3)
        last_day = today - timedelta(days=2)
    else:
        initial_day = today - timedelta(days=1)
        last_day = today

    news = db.collection("news").where("time_published", ">=", initial_day).where("time_published", "<", last_day).stream()

    tickers_dict = {}  # Used for save the current price of processed assets
    # Wallets for each strategy
    all_orders = []
    order_imdex = 0
    wallet_high_sentiment_day_no_short_low_risk = []
    wallet_low_sentiment_day_no_short_low_risk = []
    wallet_high_sentiment_day_with_short_low_risk = []
    wallet_low_sentiment_day_with_short_low_risk = []

    wallet_high_sentiment_day_no_short_mid_risk = []
    wallet_low_sentiment_day_no_short_mid_risk = []
    wallet_high_sentiment_day_with_short_mid_risk = []
    wallet_low_sentiment_day_with_short_mid_risk = []

    wallet_high_sentiment_day_no_short_all_risk = []
    wallet_low_sentiment_day_no_short_all_risk = []
    wallet_high_sentiment_day_with_short_all_risk = []
    wallet_low_sentiment_day_with_short_all_risk = []

    for new in news:        
        new_dict = new.to_dict()                

        # For each ticker in the new
        if 'ticker_sentiment' in new_dict:
            for ticker in new_dict['ticker_sentiment']:                
                try:                    
                    if abs(float(ticker['ticker_sentiment_score'])) >= 0.25:                                                                
                        pl_absolute = 0
                        pl_percent = 0
                        order = {}

                        # If the asset is a CRYPTO
                        if ticker['type'] == 'CRYPTO':
                            if ticker['ticker'] in tickers_dict.keys():                                
                                current_price = tickers_dict[ticker['ticker']]
                            else:
                                exchange = ccxt.bitget()                                                        
                                symbol = ticker['ticker'] + '/USDT'
                                fetch_ticker = exchange.fetch_ticker(symbol)                                
                                current_price = float(fetch_ticker['ask'])
                                tickers_dict[ticker['ticker']] = current_price

                            old_price = float(ticker['price'])
                            sentiment = float(ticker['ticker_sentiment_score'])

                            if sentiment > 0:
                                # Long
                                pl_absolute = current_price - old_price
                                order['direction'] = 0
                            else:
                                # Short
                                pl_absolute = old_price - current_price
                                order['direction'] = 1
                            
                            pl_percent = (pl_absolute/current_price)*100
                            order['pl_absolute'] = round(pl_absolute, 4)
                            order['pl_percent'] = round(pl_percent, 4)                      
                        else:
                            if ticker['ticker'] in tickers_dict.keys():                                
                                current_price = tickers_dict[ticker['ticker']]
                            else:
                                ticker_info = yf.Ticker(ticker['ticker'])                        
                                current_price = float(ticker_info.info['currentPrice'])
                                tickers_dict[ticker['ticker']] = current_price
                            
                            old_price = float(ticker['price'])
                            sentiment = float(ticker['ticker_sentiment_score'])

                            if sentiment > 0:
                                # Long
                                pl_absolute = current_price - old_price
                                order['direction'] = 0
                            else:
                                # Short
                                pl_absolute = old_price - current_price
                                order['direction'] = 1
                            
                            pl_percent = (pl_absolute/current_price)*100
                            order['pl_absolute'] = round(pl_absolute, 4)
                            order['pl_percent'] = round(pl_percent, 4)                            

                        order['ticker'] = ticker['ticker']
                        order['exchange'] = ticker['exchange']
                        order['type'] = ticker['type']
                        order['risk'] = ticker['risk']
                        order['price'] = current_price
                        order['date'] = new_dict['time_published']
                        order['new_ref'] = new.id
                        order['term'] = 'DAY'
                        order['sentiment_score'] = float(ticker['ticker_sentiment_score'])

                        all_orders.append(order)

                        # Save order
                        db.collection("orders").document().set(order)
                        print("Save order")

                        if float(ticker['ticker_sentiment_score']) >= 0.6:
                            # High sentiment
                            if order['direction'] == 0:
                                # If is a long
                                wallet_high_sentiment_day_no_short_all_risk.append(order_imdex)
                                wallet_high_sentiment_day_with_short_all_risk.append(order_imdex)

                                if float(order['risk']) <= 6 and float(order['risk']) > 3:
                                    # Mid risk
                                    wallet_high_sentiment_day_no_short_mid_risk.append(order_imdex)
                                    wallet_high_sentiment_day_with_short_mid_risk.append(order_imdex)
                                elif float(order['risk']) <= 3:
                                    # Low risk
                                    wallet_high_sentiment_day_no_short_low_risk.append(order_imdex)
                                    wallet_high_sentiment_day_with_short_low_risk.append(order_imdex)
                            else:
                                # Is a short
                                wallet_high_sentiment_day_with_short_all_risk.append(order_imdex)

                                if float(order['risk']) <= 6 and float(order['risk']) > 3:
                                    # Mid risk                                    
                                    wallet_high_sentiment_day_with_short_mid_risk.append(order_imdex)
                                elif float(order['risk']) <= 3:
                                    # Low risk                                    
                                    wallet_high_sentiment_day_with_short_low_risk.append(order_imdex)
                        else:
                            # Low sentiment, from 0.25                       
                            if order['direction'] == 0:
                                # If is a long
                                wallet_low_sentiment_day_no_short_all_risk.append(order_imdex)
                                wallet_low_sentiment_day_with_short_all_risk.append(order_imdex)

                                if float(order['risk']) <= 6 and float(order['risk']) > 3:
                                    # Mid risk
                                    wallet_low_sentiment_day_no_short_mid_risk.append(order_imdex)
                                    wallet_low_sentiment_day_with_short_mid_risk.append(order_imdex)
                                elif float(order['risk']) <= 3:
                                    # Low risk
                                    wallet_low_sentiment_day_no_short_low_risk.append(order_imdex)
                                    wallet_low_sentiment_day_with_short_low_risk.append(order_imdex)
                            else:
                                # Is a short
                                wallet_low_sentiment_day_with_short_all_risk.append(order_imdex)

                                if float(order['risk']) <= 6 and float(order['risk']) > 3:
                                    # Mid risk                                    
                                    wallet_low_sentiment_day_with_short_mid_risk.append(order_imdex)
                                elif float(order['risk']) <= 3:
                                    # Low risk                                    
                                    wallet_low_sentiment_day_with_short_low_risk.append(order_imdex)

                        order_imdex += 1
                except Exception as e:
                    # Print error               
                    print('yfinance/ccxt error: ' + str(e))
    
    # Iterate each list
    ###############################################################################
    balance = {}
    balance['date'] = datetime.utcnow()
    acc_per = 0
    for order_i in wallet_high_sentiment_day_no_short_all_risk:
        acc_per += round(float(all_orders[order_i]['pl_percent'])/100.0, 8)  # Divided by 100 because is 1% the operation
        # in relation with all the capital    
    
    balance['balance'] = 100.0 + acc_per

    wallet = db.collection("wallets/wallets-cointainer/high-sentiment-day-no-short-all-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    for w in wallet:
        w_dict = w.to_dict
        balance['balance'] = float(w_dict['balance']) + acc_per
        
    db.collection("wallets/wallets-cointainer/high-sentiment-day-no-short-all-risk").document().set(balance)

    ###############################################################################
    acc_per = 0    
    for order_i in wallet_high_sentiment_day_no_short_mid_risk:
        acc_per += round(float(all_orders[order_i]['pl_percent'])/100.0, 8)  # Divided by 100 because is 1% the operation
        # in relation with all the capital    
    
    balance['balance'] = 100.0 + acc_per

    wallet = db.collection("wallets/wallets-cointainer/high-sentiment-day-no-short-mid-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    for w in wallet:
        w_dict = w.to_dict
        balance['balance'] = float(w_dict['balance']) + acc_per
        
    db.collection("wallets/wallets-cointainer/high-sentiment-day-no-short-mid-risk").document().set(balance)

    ###############################################################################
    acc_per = 0    
    for order_i in wallet_high_sentiment_day_no_short_low_risk:
        acc_per += round(float(all_orders[order_i]['pl_percent'])/100.0, 8)  # Divided by 100 because is 1% the operation
        # in relation with all the capital    
    
    balance['balance'] = 100.0 + acc_per

    wallet = db.collection("wallets/wallets-cointainer/high-sentiment-day-no-short-low-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    for w in wallet:
        w_dict = w.to_dict
        balance['balance'] = float(w_dict['balance']) + acc_per
        
    db.collection("wallets/wallets-cointainer/high-sentiment-day-no-short-low-risk").document().set(balance)
    
    ###############################################################################
    acc_per = 0    
    for order_i in wallet_high_sentiment_day_with_short_all_risk:
        acc_per += round(float(all_orders[order_i]['pl_percent'])/100.0, 8)  # Divided by 100 because is 1% the operation
        # in relation with all the capital    
    
    balance['balance'] = 100.0 + acc_per

    wallet = db.collection("wallets/wallets-cointainer/high-sentiment-day-with-short-all-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    for w in wallet:
        w_dict = w.to_dict
        balance['balance'] = float(w_dict['balance']) + acc_per
        
    db.collection("wallets/wallets-cointainer/high-sentiment-day-no-short-all-risk").document().set(balance)

    ###############################################################################
    acc_per = 0    
    for order_i in wallet_high_sentiment_day_with_short_mid_risk:
        acc_per += round(float(all_orders[order_i]['pl_percent'])/100.0, 8)  # Divided by 100 because is 1% the operation
        # in relation with all the capital    
    
    balance['balance'] = 100.0 + acc_per

    wallet = db.collection("wallets/wallets-cointainer/high-sentiment-day-with-short-mid-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    for w in wallet:
        w_dict = w.to_dict
        balance['balance'] = float(w_dict['balance']) + acc_per
        
    db.collection("wallets/wallets-cointainer/high-sentiment-day-no-short-mid-risk").document().set(balance)

    ###############################################################################
    acc_per = 0    
    for order_i in wallet_high_sentiment_day_with_short_low_risk:
        acc_per += round(float(all_orders[order_i]['pl_percent'])/100.0, 8)  # Divided by 100 because is 1% the operation
        # in relation with all the capital    
    
    balance['balance'] = 100.0 + acc_per

    wallet = db.collection("wallets/wallets-cointainer/high-sentiment-day-with-short-low-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    for w in wallet:
        w_dict = w.to_dict
        balance['balance'] = float(w_dict['balance']) + acc_per
        
    db.collection("wallets/wallets-cointainer/high-sentiment-day-no-short-low-risk").document().set(balance)

    #################################### LOW SENTIMENT ####################################

    ###############################################################################
    acc_per = 0 
    for order_i in wallet_low_sentiment_day_no_short_all_risk:
        acc_per += round(float(all_orders[order_i]['pl_percent'])/100.0, 8)  # Divided by 100 because is 1% the operation
        # in relation with all the capital    
    
    balance['balance'] = 100.0 + acc_per

    wallet = db.collection("wallets/wallets-cointainer/low-sentiment-day-no-short-all-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    for w in wallet:
        w_dict = w.to_dict
        balance['balance'] = float(w_dict['balance']) + acc_per
        
    db.collection("wallets/wallets-cointainer/low-sentiment-day-no-short-all-risk").document().set(balance)

    ###############################################################################
    acc_per = 0    
    for order_i in wallet_low_sentiment_day_no_short_mid_risk:
        acc_per += round(float(all_orders[order_i]['pl_percent'])/100.0, 8)  # Divided by 100 because is 1% the operation
        # in relation with all the capital    
    
    balance['balance'] = 100.0 + acc_per

    wallet = db.collection("wallets/wallets-cointainer/low-sentiment-day-no-short-mid-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    for w in wallet:
        w_dict = w.to_dict
        balance['balance'] = float(w_dict['balance']) + acc_per
        
    db.collection("wallets/wallets-cointainer/low-sentiment-day-no-short-mid-risk").document().set(balance)

    ###############################################################################
    acc_per = 0    
    for order_i in wallet_low_sentiment_day_no_short_low_risk:
        acc_per += round(float(all_orders[order_i]['pl_percent'])/100.0, 8)  # Divided by 100 because is 1% the operation
        # in relation with all the capital    
    
    balance['balance'] = 100.0 + acc_per

    wallet = db.collection("wallets/wallets-cointainer/low-sentiment-day-no-short-low-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    for w in wallet:
        w_dict = w.to_dict
        balance['balance'] = float(w_dict['balance']) + acc_per
        
    db.collection("wallets/wallets-cointainer/low-sentiment-day-no-short-low-risk").document().set(balance)
    
    ###############################################################################
    acc_per = 0    
    for order_i in wallet_low_sentiment_day_with_short_all_risk:
        acc_per += round(float(all_orders[order_i]['pl_percent'])/100.0, 8)  # Divided by 100 because is 1% the operation
        # in relation with all the capital    
    
    balance['balance'] = 100.0 + acc_per

    wallet = db.collection("wallets/wallets-cointainer/low-sentiment-day-with-short-all-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    for w in wallet:
        w_dict = w.to_dict
        balance['balance'] = float(w_dict['balance']) + acc_per
        
    db.collection("wallets/wallets-cointainer/low-sentiment-day-no-short-all-risk").document().set(balance)

    ###############################################################################
    acc_per = 0    
    for order_i in wallet_low_sentiment_day_with_short_mid_risk:
        acc_per += round(float(all_orders[order_i]['pl_percent'])/100.0, 8)  # Divided by 100 because is 1% the operation
        # in relation with all the capital    
    
    balance['balance'] = 100.0 + acc_per

    wallet = db.collection("wallets/wallets-cointainer/low-sentiment-day-with-short-mid-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    for w in wallet:
        w_dict = w.to_dict
        balance['balance'] = float(w_dict['balance']) + acc_per
        
    db.collection("wallets/wallets-cointainer/low-sentiment-day-no-short-mid-risk").document().set(balance)

    ###############################################################################
    acc_per = 0    
    for order_i in wallet_low_sentiment_day_with_short_low_risk:
        acc_per += round(float(all_orders[order_i]['pl_percent'])/100.0, 8)  # Divided by 100 because is 1% the operation
        # in relation with all the capital    
    
    balance['balance'] = 100.0 + acc_per

    wallet = db.collection("wallets/wallets-cointainer/low-sentiment-day-with-short-low-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    for w in wallet:
        w_dict = w.to_dict
        balance['balance'] = float(w_dict['balance']) + acc_per
        
    db.collection("wallets/wallets-cointainer/low-sentiment-day-no-short-low-risk").document().set(balance)

    print("No errors")
