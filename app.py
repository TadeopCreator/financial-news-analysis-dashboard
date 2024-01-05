from flask import Flask, render_template
import pandas as pd
import json
import plotly
import plotly_express as px
from finvizfinance.news import News
from goose3 import Goose
from datetime import datetime
from textblob import TextBlob

from google.cloud import firestore

app = Flask(__name__)

news_url_list = []
NUM_NEWS = 20

@app.route('/')
def index():
    global news_url_list

    df = px.data.gapminder().query("country=='Canada'")
    fig = px.line(df, x="year", y="lifeExp", title='Life expectancy in Canada')

    # Configuración del tema oscuro
    fig.update_layout(
        plot_bgcolor='#212529',  # Color de fondo del gráfico
        paper_bgcolor='#212529', # Color de fondo del área del papel
        font=dict(color='white') # Cambio del color de la fuente para mejorar la visibilidad
    )

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    try:
        news_class = News()
        news = news_class.get_news()

        df_news = pd.DataFrame(news['news']).head(NUM_NEWS)
        data = df_news.to_dict(orient='records')

        for i in range(NUM_NEWS):
            news_url_list.append(news['news']['Link'].iloc[i])

        return render_template('index.html', graphJSON=graphJSON, news=data)
    except:
        return render_template('index.html', graphJSON=graphJSON, news=None)

@app.route('/new_analysis/<int:index>')
def new_analysis(index):
    global news_url_list
    new = {}

    g = Goose()

    if (news_url_list):
        url = news_url_list[index]
        article = g.extract(url=url)

        if article:
            if article.infos['meta']['keywords']:
                keywords_raw =  article.infos['meta']['keywords']
            else:
                keywords_raw = ""
            
            # favicon = article.infos['meta']['favicon'] if article.infos['meta']['favicon'] else ""
            
            if article.infos['title']:
                title =  article.infos['title']
            else:
                title = ""

            site_name = article.infos.get('opengraph', {}).get('site_name', '')

            real_url = article.infos.get('opengraph', {}).get('url', '')

            publish_date = article.infos.get('publish_date', '') if 'publish_date' in article.infos else ''

            new['title'] = title
            keywords_list = keywords_raw.split(',')[2:10]

            new['keywords'] = keywords_list
            # new['favicon'] = favicon
            new['site_name'] = site_name
            new['real_url'] = real_url

            new_text = article.cleaned_text
            new['text'] = new_text

            # Create a TextBlob object
            blob = TextBlob(new_text)

            # Extract noun phrases as keywords
            #keywords = blob.noun_phrases

            # Obtener el sentimiento
            sentiment = blob.sentiment.polarity

            # Interpretar el sentimiento
            if sentiment > 0:
                new['sentiment'] = 'positive'
            elif sentiment < 0:
                new['sentiment'] = 'negative'
            else:
                new['sentiment'] = 'neutral'

            # Score with 2 decimals
            new['score'] = abs(round(sentiment*100, 2))

            if publish_date:
                # Convertir la cadena a un objeto datetime
                date_datetime = datetime.fromisoformat(publish_date.replace('Z', '+00:00'))

                # Formatear la fecha en un formato legible
                readeble_date = date_datetime.strftime('%Y-%m-%d %H:%M:%S')
            
            new['publish_date'] = readeble_date
        else:
            return render_template('index.html', graphJSON=graphJSON, news=None)
            
        g.close()

    return render_template('new_analysis.html', new=new)

@app.route('/market_overview')
def market_overview():
    return render_template('market_overview.html')

@app.route('/about')
def about():
    db = firestore.Client(project='financial-news-analysis-410223')
    new = db.collection('news').document("3tJJR9794HRnh0FuBX8Q").get().to_dict()

    # Send data to html template
    return render_template('about.html', new=new)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
