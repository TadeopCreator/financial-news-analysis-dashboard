import json
import plotly
import plotly_express as px
from flask import Flask, render_template, request
from google.cloud import firestore

news_list = []
selected_new_index = -1
selected_new_info = {}

app = Flask(__name__)

@app.route('/')
def index():
    global news_list
    news_list = []    

    df = px.data.gapminder().query("country=='Canada'")
    fig = px.line(df, x="year", y="lifeExp", title='Life expectancy in Canada')

    # Configuración del tema oscuro
    fig.update_layout(
        plot_bgcolor='#212529',  # Color de fondo del gráfico
        paper_bgcolor='#212529', # Color de fondo del área del papel
        font=dict(color='white') # Cambio del color de la fuente para mejorar la visibilidad
    )

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html', graphJSON=graphJSON)

@app.route('/get_news', methods=['GET'])
def obtener_noticias():

    db = firestore.Client(project='financial-news-analysis-410223')    
    docs = db.collection("news").order_by('time_published', direction=firestore.Query.DESCENDING).limit(20).stream()

    for doc in docs:
        news_list.append(doc.to_dict())

    # Aquí devuelves las noticias como JSON o datos procesados
    return news_list


@app.route('/new_analysis/<int:index>')
def new_analysis(index):
    global news_list, selected_new_index, selected_new_info
    selected_new_index = index-1

    if (news_list):
        selected_new_info = news_list[selected_new_index]

    return render_template('new_analysis.html', new=selected_new_info)

# @app.route('/save_new', methods=['POST'])
# def save_new():
#     data = request.form['data']

#     return render_template('new_analysis.html', new=selected_new_info, index=selected_new_index, message=data)

@app.route('/market_overview')
def market_overview():
    return render_template('market_overview.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
