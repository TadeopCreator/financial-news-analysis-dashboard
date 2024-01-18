import json
import plotly
import plotly_express as px
import plotly.graph_objects as go
from flask import Flask, render_template, request
from google.cloud import firestore
from datetime import datetime, timedelta

news_list = []  # news_list is a global list variable that will hold the news articles 
# retrieved from the database for the current page.

selected_new_index = -1  # selected_new_index holds the index of the currently selected news article in the news_list.

selected_new_info = {}  # selected_new_info holds information about the currently selected news article.

selected_page = 1  # Sets the global selected_page variable to 1. This will be the default page
# shown on the index page if no specific page is requested.

top_10_assets_pie_json = {}  # top_10_assets_pie_json holds the pie chart data for the top 10 assets.
top_winners_per_asset_icicle_json = {}  # top_winners_per_asset_icicle_json holds the icicle chart data 
# for the top winners per
average_sentiment_score_per_asset_bars_json = {}  # average_sentiment_score_per_asset_bars_json holds the bar chart data
asset_distribution_per_type_json = {}  # asset_distribution_per_type_json holds the bar chart data for the asset distribution per type.


app = Flask(__name__)

def round_filter(value, decimals=0):
    # Rounds a number to the given number of decimal places.    
    try:
        value = round(float(value), decimals)*100
        value = round(value, decimals)        
        return value
    except (ValueError, TypeError):
        return value

app.jinja_env.filters['round'] = round_filter

@app.route('/')
def index():
    # Retrieves the selected page of news articles from the database
    # and renders the index template. 
    #
    # Sets the global selected_page variable based on url parameter.
    # Defaults to 1 if no page provided. Limits to 1-5.    
    global news_list, selected_page

    page = int(request.args.get('page', 1))
    if page < 1:
        page = 1

    if page > 5:
        page = 5

    selected_page = page

    news_list = []    

    return render_template('index.html', current_page=selected_page)


@app.route('/get_orders', methods=['GET'])
def get_orders():
    # Retrieves the 10 most recent orders from Firestore.    
    # Orders the results by descending date and limits to 10 documents.
    # Converts each document to a dictionary and stores in a list.
    # Returns the list of order dictionaries.
    db = firestore.Client(project='financial-news-analysis-410223')
    orders = db.collection("orders").order_by('date', direction=firestore.Query.DESCENDING).limit(10).stream()

    orders_list = []
    
    for order in orders:
        orders_list.append(order.to_dict())

    return orders_list


@app.route('/get_news', methods=['GET'])
def get_news():
    # Retrieves news articles from Firestore based on the selected page 
    # and returns them as a list of news (dictionaries).
    # Orders articles by descending publish time. 
    # Offsets results by 20 per page and limits to 20 articles per page.
    global selected_page

    db = firestore.Client(project='financial-news-analysis-410223')
    if selected_page != 1:
        docs = db.collection("news").order_by('time_published', direction=firestore.Query.DESCENDING).offset(20*(selected_page-1)).limit(20).stream()
    else:
        docs = db.collection("news").order_by('time_published', direction=firestore.Query.DESCENDING).limit(20).stream()

    for doc in docs:
        news_list.append(doc.to_dict())

    # Aquí devuelves las noticias como JSON o datos procesados
    return news_list


@app.route('/new/<int:index>')
def new(index):
    # Returns a specific news article based on index
    #
    # Loads the global news_list and finds the article at the 
    # index passed in. Stores the index and article in globals
    # to share with the template. Renders the new.html template
    # passing the article as context.
    global news_list, selected_new_index, selected_new_info
    selected_new_index = index-1

    if (news_list):
        selected_new_info = news_list[selected_new_index]
    
    return render_template('new.html', new=selected_new_info)

@app.route('/callback_graph_1', methods=['POST', 'GET'])
def cb_graph_1():
    return pie_main_symbols_graph()

@app.route('/callback_graph_2', methods=['POST', 'GET'])
def cb_graph_2():
    db = firestore.Client(project='financial-news-analysis-410223')
    docs = db.collection("insights").document("insights-data")

    insights = docs.get()
    
    doc_dict = insights.to_dict()

    sentiment_values = [doc_dict['last_week_avg_sentiment_equity'], 
                        doc_dict['last_week_avg_sentiment_index'], 
                        doc_dict['last_week_avg_sentiment_forex'], 
                        doc_dict['last_week_avg_sentiment_etf'], 
                        doc_dict['last_week_avg_sentiment_crypto'], 
                        doc_dict['last_week_avg_sentiment_mutualfund'],
                        doc_dict['last_week_avg_sentiment_ecnquote'],
                        doc_dict['last_week_avg_sentiment_undefined']]
        
    return bar_graph(sentiment_values)

@app.route('/callback_graph_3', methods=['POST', 'GET'])
def cb_graph_3():
    db = firestore.Client(project='financial-news-analysis-410223')
    docs = db.collection("insights").document("insights-data")

    insights = docs.get()
    doc_dict = insights.to_dict()

    distribution_values = [doc_dict['total_equity'],
                         doc_dict['total_index'],
                         doc_dict['total_forex'],
                         doc_dict['total_etf'],
                         doc_dict['total_crypto'],
                         doc_dict['total_mutualfund'],
                         doc_dict['total_ecnquote'],
                         doc_dict['total_undefined']]
    
    return pie_assets_distribution_graph(distribution_values)

@app.route('/callback_graph_4', methods=['POST', 'GET'])
def cb_graph_4():
    return icicle_main_symbols_graph()

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

@app.route('/get_graphs', methods=['GET'])
def get_graphs():
    # Retrieves insights data from Firestore and generates graphs
    # Parses document into lists of values for graphing
    # Calls functions to generate each graph with data
    # Returns list containing parsed doc and generated graphs
    db = firestore.Client(project='financial-news-analysis-410223')
    docs = db.collection("insights").document("insights-data")

    insights = docs.get()
    
    doc_dict = insights.to_dict()

    sentiment_values = [doc_dict['last_week_avg_sentiment_equity']*100, 
                        doc_dict['last_week_avg_sentiment_index']*100, 
                        doc_dict['last_week_avg_sentiment_forex']*100, 
                        doc_dict['last_week_avg_sentiment_etf']*100, 
                        doc_dict['last_week_avg_sentiment_crypto']*100, 
                        doc_dict['last_week_avg_sentiment_mutualfund']*100,
                        doc_dict['last_week_avg_sentiment_ecnquote']*100,
                        doc_dict['last_week_avg_sentiment_undefined']*100]
        
    distribution_values = [doc_dict['total_equity'],
                         doc_dict['total_index'],
                         doc_dict['total_forex'],
                         doc_dict['total_etf'],
                         doc_dict['total_crypto'],
                         doc_dict['total_mutualfund'],
                         doc_dict['total_ecnquote'],
                         doc_dict['total_undefined']]

    graph1 = pie_main_symbols_graph()
    graph2 = bar_graph(sentiment_values)
    graph3 = pie_assets_distribution_graph(distribution_values)
    graph4 = icicle_main_symbols_graph()

    list_data = [doc_dict, graph1, graph2, graph3, graph4]

    return list_data


@app.route('/news_insights')
def news_insights():
    return render_template('news_insights.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/portfolio')
def portfolio():
    # db = firestore.Client(project='financial-news-analysis-410223')

    # wallet = db.collection("wallets/wallets-cointainer/high-sentiment-day-no-short-all-risk").order_by('date', direction=firestore.Query.DESCENDING).limit(1).stream()
    # for w in wallet:
    #     w_dict = w.to_dict
    #     print(w_dict)
    
    return render_template('portfolio.html')

@app.errorhandler(404)
def page_not_found(e):
    # Handles 404 page not found errors by rendering the 404.html template and returning a 404 status code
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
