import json
import plotly
import plotly_express as px
import plotly.graph_objects as go
from flask import Flask, render_template, request
from google.cloud import firestore

news_list = []  # news_list is a global list variable that will hold the news articles 
# retrieved from the database for the current page.

selected_new_index = -1  # selected_new_index holds the index of the currently selected news article in the news_list.

selected_new_info = {}  # selected_new_info holds information about the currently selected news article.

selected_page = 1  # Sets the global selected_page variable to 1. This will be the default page
# shown on the index page if no specific page is requested.


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
def obtener_noticias():
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

# @app.route('/save_new', methods=['POST'])
# def save_new():
#     data = request.form['data']

#     return render_template('new.html', new=selected_new_info, index=selected_new_index, message=data)

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

    proportion_values = [doc_dict['total_equity'],
                         doc_dict['total_index'],
                         doc_dict['total_forex'],
                         doc_dict['total_etf'],
                         doc_dict['total_crypto'],
                         doc_dict['total_mutualfund'],
                         doc_dict['total_ecnquote'],
                         doc_dict['total_undefined']]
    
    return pie_assets_proportion_graph(proportion_values)

@app.route('/callback_graph_4', methods=['POST', 'GET'])
def cb_graph_4():
    return icicle_main_symbols_graph()

def pie_main_symbols_graph():
    """Generates a pie chart showing the proportion of mentions for the top 5 symbols.
    
    Creates a Pie chart using Plotly, with the labels and values specified. 
    Colors are set to a predefined palette.
    
    The figure is then converted to JSON string to return.
    """
    labels = ['TSLA','AAPL','MSFT','PENN', 'Other']
    values = [4500, 2500, 1053, 500, 300]    
    
    colors = ['#363432', '#196774', '#90A19D', '#F0941F', '#EF6024']

    # Create a Pie chart with specified colors
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.3, marker=dict(colors=colors))])
    fig.update_traces(textposition='inside', textfont_size=18)    
    fig.update_layout(title_text='Pie Chart', font_family="Roboto")   

    graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return graph

def bar_graph(sentiment_values):    
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
        title='Gráfico de Barras',
        xaxis=dict(title='Assets'),
        yaxis=dict(title='Valor')
    )

    # Change the bar mode
    fig.update_layout(barmode='group')
    fig.update_traces(textposition='inside', textfont_size=18)    
    fig.update_layout(title_text='Sentiment per asset', font_family="Roboto")       

    graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return graph

def pie_assets_proportion_graph(proportion_values):    
    assets = ['Equity', 'Index', 'Forex', 'ETF', 'Crypto', 'Mutual Fund', 'Ecn Quote', 'Undefined']    

    colors = ['rgba(50, 171, 96, 0.6)', 'rgb(128, 0, 128)']

    # Crear figura de pastel
    fig = go.Figure(data=[go.Pie(labels=assets, values=proportion_values, marker=dict(colors=colors))])

    # Diseño de la gráfica    
    fig.update_traces(textposition='inside', textfont_size=18)    
    fig.update_layout(title_text='Assets', font_family="Roboto")   

    graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return graph

def icicle_main_symbols_graph():
    fig = px.treemap(
        names=["Assets", "Equity", "AAPL", "TSLA", "PENN", "Index", "Forex", "ETF", "Crypto", "Mutual Fund", "Ecn Quote", "Undefined"],
        parents=["", "Assets", "Equity", "Equity", "Equity", "Assets", "Assets", "Assets", "Assets", "Assets", "Assets", "Assets"]
    )

    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    fig.update_layout(font_family="Roboto")

    graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return graph

@app.route('/get_graphs', methods=['GET'])
def get_graphs():
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
        
    proportion_values = [doc_dict['total_equity'],
                         doc_dict['total_index'],
                         doc_dict['total_forex'],
                         doc_dict['total_etf'],
                         doc_dict['total_crypto'],
                         doc_dict['total_mutualfund'],
                         doc_dict['total_ecnquote'],
                         doc_dict['total_undefined']]

    graph1 = pie_main_symbols_graph()
    graph2 = bar_graph(sentiment_values)
    graph3 = pie_assets_proportion_graph(proportion_values)
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
