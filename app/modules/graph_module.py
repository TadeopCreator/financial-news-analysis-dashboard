import json
import plotly
import plotly_express as px
import plotly.graph_objects as go
from google.cloud import firestore
from datetime import datetime, timedelta

top_10_assets_pie_json = {}  # top_10_assets_pie_json holds the pie chart data for the top 10 assets.
top_winners_per_asset_icicle_json = {}  # top_winners_per_asset_icicle_json holds the icicle chart data 
# for the top winners per
average_sentiment_score_per_asset_bars_json = {}  # average_sentiment_score_per_asset_bars_json holds the bar chart data
asset_distribution_per_type_json = {}  # asset_distribution_per_type_json holds the bar chart data for the asset distribution per type.

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
    
    colors = ['#363432', '#196774', '#90A19D', '#F0941F', '#EF6024']

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
    fig.update_traces(textposition='inside', textfont_size=18)    

    graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    average_sentiment_score_per_asset_bars_json = graph

    return graph

def pie_assets_distribution_graph(distribution_values):
    global asset_distribution_per_type_json

    if asset_distribution_per_type_json:
        return asset_distribution_per_type_json

    assets = ['Equity', 'Index', 'Forex', 'ETF', 'Crypto', 'Mutual Fund', 'Ecn Quote', 'Undefined']
    colors = ['rgba(50, 171, 96, 0.6)', 'rgb(128, 0, 128)']

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
    last_week_start = today - timedelta(days=(today.weekday() + 7))  # Lunes pasado
    last_week_end = last_week_start + timedelta(days=4)  # Viernes pasado

    db = firestore.Client(project='financial-news-analysis-410223')

    # Get top 10 orders with major pl_percent, from last week
    orders_unsorted = db.collection("orders").where("date", ">=", last_week_start).where("date", "<=", last_week_end).stream()
    
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
    for i, asset in enumerate(assets):
        names.append(asset)
        parents.append("Assets")
        values.append(acc_values_per_type[i])

    fig = px.treemap(
        names=names,
        parents=parents,
        values=values
    )

    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    fig.update_layout(font_family="Roboto")

    graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    top_winners_per_asset_icicle_json = graph
    
    return graph