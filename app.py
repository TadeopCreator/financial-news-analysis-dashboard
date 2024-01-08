import json
import plotly
import plotly_express as px
from flask import Flask, render_template, request
from google.cloud import firestore

news_list = []
selected_new_index = -1
selected_new_info = {}
selected_page = 1

app = Flask(__name__)

@app.route('/')
def index():
    global news_list, selected_page

    page = int(request.args.get('page', 1))
    if page < 1:
        page = 1
    selected_page = page

    news_list = []    

    return render_template('index.html', current_page=selected_page)

@app.route('/get_news', methods=['GET'])
def obtener_noticias():
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
    global news_list, selected_new_index, selected_new_info
    selected_new_index = index-1

    if (news_list):
        selected_new_info = news_list[selected_new_index]

    return render_template('new.html', new=selected_new_info)

# @app.route('/save_new', methods=['POST'])
# def save_new():
#     data = request.form['data']

#     return render_template('new.html', new=selected_new_info, index=selected_new_index, message=data)

@app.route('/news_insights')
def news_insights():
        
    df = px.data.gapminder().query("country=='Canada'")
    fig = px.line(df, x="year", y="lifeExp", title='Life expectancy in Canada')

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('news_insights.html', graphJSON=graphJSON)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
