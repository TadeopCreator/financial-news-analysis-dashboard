from flask import Flask, render_template, request
from google.cloud import firestore
from modules.graph_module import pie_main_symbols_graph, bar_graph, pie_assets_distribution_graph, icicle_main_symbols_graph, balance_1_graph

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

    if (news_list and len(news_list) >= index):
        selected_new_info = news_list[selected_new_index]
    
        return render_template('new.html', new=selected_new_info)
    else:
        return render_template('new.html', new={})

@app.route('/order_new', methods=['POST'])
def order_new():
    global news_list

    id = str(request.get_json())

    db = firestore.Client(project='financial-news-analysis-410223')
    
    new = db.collection("news").document(id).get().to_dict()

    news_list = ['']
    news_list[0] = new


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

@app.route('/callback_graph_balance_1', methods=['POST', 'GET'])
def cb_graph_balance_1():
    return balance_1_graph()

@app.route('/get_balances', methods=['GET'])
def get_balances():

    balance1 = balance_1_graph()

    list_data = [balance1]

    return list_data


@app.route('/news_insights')
def news_insights():
    return render_template('news_insights.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/portfolio')
def portfolio():    
    return render_template('portfolio.html', message="development")


@app.errorhandler(404)
def page_not_found(e):
    # Handles 404 page not found errors by rendering the 404.html template and returning a 404 status code
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
