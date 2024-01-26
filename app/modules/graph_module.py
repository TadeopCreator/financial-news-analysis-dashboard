import json
import plotly
import plotly_express as px
import plotly.graph_objects as go
from google.cloud import firestore
import pandas as pd
from datetime import datetime, timedelta

top_10_assets_pie_json = {}  # top_10_assets_pie_json holds the pie chart data for the top 10 assets.
top_winners_per_asset_icicle_json = {}  # top_winners_per_asset_icicle_json holds the icicle chart data 
# for the top winners per
average_sentiment_score_per_asset_bars_json = {}  # average_sentiment_score_per_asset_bars_json holds the bar chart data
asset_distribution_per_type_json = {}  # asset_distribution_per_type_json holds the bar chart data for the asset distribution per type.

# balances_graph_json holds each balance graph for portfolio page.
balances_graph_json = {
    1: None,
    2: None,
    3: None,
    4: None,
    5: None,
    6: None,
    7: None,
    8: None,
    9: None,
    10: None,
    11: None,
    12: None
}


def pie_main_symbols_graph(): 
    global top_10_assets_pie_json

    if top_10_assets_pie_json:
        return top_10_assets_pie_json
       
    orders_list = []
    labels = []
    values = []

    db = firestore.Client(project='financial-news-analysis-410223')
    # Get top 10 orders with major pl_percent
    orders = db.collection("orders").order_by('pl_percent', direction=firestore.Query.DESCENDING).limit(10).stream()    
    
    for order in orders:
        orders_list.append(order.to_dict())

    for order in orders_list:
        labels.append(order['ticker'])
        values.append(order['pl_percent'])
    
    colors = ['#994D1C', '#E48F45', '#ED7D31', '#FFE6B3', '#FFD699', '#FFC27F', '#F5CCA0', '#FFB966', '#FFA54D', '#FF9933', '#FF8800']

    # Create a Pie chart with specified colors
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3, marker=dict(colors=colors))])
    fig.update_traces(textposition='inside', textfont_size=18)        

    graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    top_10_assets_pie_json = graph
    
    return graph

def bar_graph(sentiment_values):
    global average_sentiment_score_per_asset_bars_json

    if average_sentiment_score_per_asset_bars_json:
        return average_sentiment_score_per_asset_bars_json
    
    assets=['Equity', 'Index', 'Forex', 'ETF', 'Crypto', 'Mutual Fund', 'Ecn Quote', 'Undefined']

    # Colores
    colores = ['green' if valor >= 0 else 'crimson' for valor in sentiment_values]

    # Crear figura
    fig = go.Figure()

    # Añadir barras
    fig.add_trace(go.Bar(
        x=assets,
        y=sentiment_values,
        marker_color=colores
    ))

    # Diseño de la gráfica
    fig.update_layout(        
        xaxis=dict(title='Assets'),
        yaxis=dict(title='Avg. Sentiment Score [%]')
    )

    # Change the bar mode
    fig.update_layout(barmode='group')
    fig.update_xaxes(title='')
    fig.update_traces(textposition='inside', textfont_size=18)    

    graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    average_sentiment_score_per_asset_bars_json = graph

    return graph

def pie_assets_distribution_graph(distribution_values):
    global asset_distribution_per_type_json

    if asset_distribution_per_type_json:
        return asset_distribution_per_type_json

    assets = ['Equity', 'Index', 'Forex', 'ETF', 'Crypto', 'Mutual Fund', 'Ecn Quote', 'Undefined']
    colors = ['#ED7D31', '#FFE6B3', '#FFD699', '#FFC27F', '#F5CCA0', '#FFB966', '#FFA54D', '#FF9933', '#FF8800']

    # Crear figura de pastel
    fig = go.Figure(data=[go.Pie(labels=assets, values=distribution_values, marker=dict(colors=colors))])

    # Diseño de la gráfica    
    fig.update_traces(textposition='inside', textfont_size=18)    

    graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    asset_distribution_per_type_json = graph
    
    return graph

def icicle_main_symbols_graph():
    """Generates an icicle graph showing the top gainers per asset type from the past week.
    
    Fetches orders from the past week, accumulates percent gain by asset type, 
    then renders an icicle graph with the top symbols and asset types.
    
    Returns:
        A JSON string containing the icicle graph.
    """
    global top_winners_per_asset_icicle_json

    if top_winners_per_asset_icicle_json:
        return top_winners_per_asset_icicle_json
    
    last_week_orders = []
    names = ["Assets"]
    parents = [""]
    values = [100]

    today = datetime.now()
    last_week_start = today - timedelta(days=(today.weekday() + 7))  # Last Monday
    last_week_end = last_week_start + timedelta(days=4)  # Last Friday

    db = firestore.Client(project='financial-news-analysis-410223')

    # Get top 10 orders with major pl_percent, from last week
    orders_unsorted = db.collection("orders").where("date", ">=", last_week_start).where("date", "<=", last_week_end).stream()    

    for order in orders_unsorted:
        last_week_orders.append(order.to_dict())

    if not last_week_orders:
        orders_unsorted = db.collection("orders").order_by('date', direction=firestore.Query.DESCENDING).limit(20).stream()

        for order in orders_unsorted:
            last_week_orders.append(order.to_dict())


    # Sort last_week_orders list in descending order by the pl_percent field in each order
    last_week_orders.sort(key=lambda x: x['pl_percent'], reverse=True)

    # Accumulate pl_percent per asset type in a new list
    acc_values_per_type = [0, 0, 0, 0, 0, 0, 0, 0]  # First save on EQUITY, then INDEX and so on

    # Dictionary of assets with index from 0 to 7 as value
    assets_dict = {'EQUITY': 0, 'INDEX': 1, 'FOREX': 2, 'ETF': 3, 'CRYPTO': 4, 'MUTUALFUND': 5, 'ECNQUOTE': 6, 'UNDEFINED': 7}

    for order in last_week_orders:
        # If ticker exist on the parents list accumulate pl_percent at that position
        if order['ticker'] in names:
            t = order['ticker']         
            values[names.index(f'{t}')] += order['pl_percent']
        else:
            names.append(order['ticker'])
            values.append(order['pl_percent'])
            parents.append(order['type'])

        acc_values_per_type[assets_dict[order['type']]] += order['pl_percent']

    assets = ['EQUITY', 'INDEX', 'FOREX', 'ETF', 'CRYPTO', 'MUTUALFUND', 'ECNQUOTE', 'UNDEFINED']
    parent_assets = ['Assets'] * len(assets)

    colors = ['#994D1C', '#E48F45', '#ED7D31', '#FFE6B3', '#FFD699', '#FFC27F', '#F5CCA0', '#FFB966', '#FFA54D', '#FF9933', '#FF8800']

    names[1:1] = assets
    parents[1:1] = parent_assets
    values[0] = sum(values[1:9])

    for i in range(len(assets)):
        values.append(acc_values_per_type[i])

    fig = px.treemap(
        names=names,
        parents=parents,
        values=values,
        color=values,
        color_continuous_scale=colors 
    )

    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    fig.update_layout(font_family="Roboto")

    graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    top_winners_per_asset_icicle_json = graph
    
    return graph


def balance_graph(balance_number):
    global balances_graph_json

    if balances_graph_json[balance_number]:
        return balances_graph_json[balance_number]

    db = firestore.Client(project='financial-news-analysis-410223')

    if balance_number == 1:
        wallet = db.collection("wallets/wallets-cointainer/high-sentiment-day-no-short-all-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(5).stream()
    elif balance_number == 2:
        wallet = db.collection("wallets/wallets-cointainer/high-sentiment-day-no-short-mid-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(5).stream()
    elif balance_number == 3:
        wallet = db.collection("wallets/wallets-cointainer/high-sentiment-day-no-short-low-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(5).stream()
    elif balance_number == 4:
        wallet = db.collection("wallets/wallets-cointainer/high-sentiment-day-with-short-all-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(5).stream()
    elif balance_number == 5:
        wallet = db.collection("wallets/wallets-cointainer/high-sentiment-day-with-short-mid-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(5).stream()
    elif balance_number == 6:
        wallet = db.collection("wallets/wallets-cointainer/high-sentiment-day-with-short-low-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(5).stream()
    elif balance_number == 7:
        wallet = db.collection("wallets/wallets-cointainer/low-sentiment-day-no-short-all-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(5).stream()
    elif balance_number == 8:
        wallet = db.collection("wallets/wallets-cointainer/low-sentiment-day-no-short-mid-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(5).stream()
    elif balance_number == 9:
        wallet = db.collection("wallets/wallets-cointainer/low-sentiment-day-no-short-low-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(5).stream()
    elif balance_number == 10:
        wallet = db.collection("wallets/wallets-cointainer/low-sentiment-day-with-short-all-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(5).stream()
    elif balance_number == 11:
        wallet = db.collection("wallets/wallets-cointainer/low-sentiment-day-with-short-mid-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(5).stream()
    elif balance_number == 12:
        wallet = db.collection("wallets/wallets-cointainer/low-sentiment-day-with-short-low-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(5).stream()
    else:
        return
    
    dates = []
    balance = []

    for w in wallet:
        w_dict = w.to_dict()
        balance.append(w_dict['balance'])
        dates.append(w_dict['date'].strftime("%m-%d"))

    column_name = 'Balance [%]'
    data = {'Date': dates}
    data[column_name] = [ b for b in balance ]

    # Create a DataFrame
    df = pd.DataFrame(data)

    fig = px.area(df, x='Date', y="Balance [%]")
    fig.update_xaxes(title='')
    fig.update_xaxes(minor=dict(ticks="inside"))
    fig.update_traces(line_shape='linear', line=dict(color='orange'))

    graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    balances_graph_json[balance_number] = graph
    
    return graph