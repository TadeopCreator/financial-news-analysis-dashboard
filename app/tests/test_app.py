import pytest

from app.app import app, new, get_news, selected_new_index, selected_new_info

app.CFG = {'news_list': [
  {
    'overall_sentiment_label': 'Neutral',
    'summary': 'Nate Alex ( Chainfaces ) dove into CryptoKitties in 2017 alongside j1mmy and Pranksy & snapped up 70 CryptoPunks when no one cared: NFT Creator ...',
    'url': 'https://cointelegraph.com/magazine/painful-nft-creator-nate-alex-70-cryptopunks/',
    'category_within_source': 'n/a',
    'ticker_sentiment': [
      {
        'exchange': 'Binance',
        'type': 'CRYPTO',
        'risk': 10,
        'price': 42572.85,
        'ticker_sentiment_score': '0.113934',
        'relevance_score': '0.040179',
        'ticker': 'BTC',
        'ticker_sentiment_label': 'Neutral',
        'name': 'BTC'
      },
      {
        'exchange': 'Binance',
        'type': 'CRYPTO',
        'risk': 10,
        'price': 2526.35,
        'ticker_sentiment_score': '0.103106',
        'relevance_score': '0.100224',
        'ticker': 'ETH',
        'ticker_sentiment_label': 'Neutral',
        'name': 'ETH'
      }
    ],
    'banner_image': None,
    'source': 'Cointelegraph',
    'authors': [
      'Greg Oakford'
    ],
    'topics': [
      {
        'topic': 'Blockchain',
        'relevance_score': '0.990678'
      },
      {
        'topic': 'Financial Markets',
        'relevance_score': '0.108179'
      }
    ],
    'title': "'Painful to think about': NFT Creator Nate Alex on selling 70 CryptoPunks too early",
    'time_published': '12:00 PM EST, January 18, 2024',
    'risk_avg': 10.0,
    'source_domain': 'cointelegraph.com',
    'overall_sentiment_score': 0.140032
  },
  {
    'overall_sentiment_label': 'Somewhat-Bullish',
    'summary': 'CHICAGO, Jan. 18, 2024 ( GLOBE NEWSWIRE ) -- Members of the American Health Information Management Association ( AHIMA ) elected Mona Calhoun, PhD, MS, Med, RHIA, FAHIMA, as president/chair of the 2024 AHIMA Board of Directors. Her one-year term began on January 1.',
    'url': 'https://www.benzinga.com/pressreleases/24/01/g36678641/ahima-announces-2024-board-presidentchair-new-board-members',
    'category_within_source': 'News',
    'ticker_sentiment': [
      {
        'exchange': 'PNK',
        'type': 'EQUITY',
        'risk': 5,
        'price': 8.49,
        'ticker_sentiment_score': '0.115533',
        'relevance_score': '0.039614',
        'ticker': 'OUSZF',
        'ticker_sentiment_label': 'Neutral',
        'name': 'OUTSOURCING INC'
      }
    ],
    'banner_image': 'https://www.benzinga.com/next-assets/images/schema-image-default.png',
    'source': 'Benzinga',
    'authors': [
      'Globe Newswire'
    ],
    'topics': [
      
    ],
    'title': 'AHIMA Announces 2024 Board President/Chair, New Board Members',
    'time_published': '12:00 PM EST, January 18, 2024',
    'risk_avg': 5.0,
    'source_domain': 'www.benzinga.com',
    'overall_sentiment_score': 0.235385
  },
  {
    'overall_sentiment_label': 'Somewhat-Bullish',
    'summary': 'Meta Platforms, Inc. META apps reportedly witnessed a notable 32% boost in return on spending, facilitated by artificial intelligence. Ads using AI also reduced the cost of acquisition by about 17%, Bloomberg reported, citing statements from an interview with Nicola Mendelsohn, the head of the ...',
    'url': 'https://www.benzinga.com/markets/equities/24/01/36678631/metas-ai-magic-ad-returns-reportedly-soar-32-with-breakthrough-technology-boost',
    'category_within_source': 'News',
    'ticker_sentiment': [
      {
        'exchange': 'NMS',
        'type': 'EQUITY',
        'risk': 10,
        'price': 372.1648,
        'ticker_sentiment_score': '0.29229',
        'relevance_score': '0.669956',
        'ticker': 'META',
        'ticker_sentiment_label': 'Somewhat-Bullish',
        'name': 'Meta Platforms, Inc.'
      },
      {
        'exchange': 'NMS',
        'type': 'EQUITY',
        'risk': 1,
        'price': 187.105,
        'ticker_sentiment_score': '0.05904',
        'relevance_score': '0.303175',
        'ticker': 'AAPL',
        'ticker_sentiment_label': 'Neutral',
        'name': 'Apple Inc.'
      }
    ],
    'banner_image': 'https://cdn.benzinga.com/files/images/story/2024/META-1.png?width=1200&height=800&fit=crop',
    'source': 'Benzinga',
    'authors': [
      'Nabaparna Bhattacharya'
    ],
    'topics': [
      {
        'topic': 'Technology',
        'relevance_score': '1.0'
      },
      {
        'topic': 'Financial Markets',
        'relevance_score': '0.108179'
      }
    ],
    'title': "Meta's AI Magic! Ad Returns Reportedly Soar 32% With Breakthrough Technology Boost - Meta Platforms  ( NASDAQ:META ) ",
    'time_published': '12:00 PM EST, January 18, 2024',
    'risk_avg': 5.5,
    'source_domain': 'www.benzinga.com',
    'overall_sentiment_score': 0.167294
  },
  {
    'overall_sentiment_label': 'Neutral',
    'summary': 'Wells Fargo & Co. and Morgan Stanley have picked up separate downgrades as analysts sift through fourth-quarter earning updates in the face of headwinds tied to the cost of deposits and retooling by the two big banks.',
    'url': 'https://www.marketwatch.com/story/earnings-reports-spark-downgrades-of-wells-fargo-and-morgan-stanley-as-analysts-see-headwinds-98467627',
    'category_within_source': 'Top Stories',
    'ticker_sentiment': [
      {
        'exchange': 'NYQ',
        'type': 'EQUITY',
        'risk': 5,
        'price': 46.46,
        'ticker_sentiment_score': '-0.020293',
        'relevance_score': '0.422661',
        'ticker': 'WFC',
        'ticker_sentiment_label': 'Neutral',
        'name': 'Wells Fargo & Company'
      },
      {
        'exchange': 'NYQ',
        'type': 'EQUITY',
        'risk': 8,
        'price': 84.51,
        'ticker_sentiment_score': '0.028238',
        'relevance_score': '0.484408',
        'ticker': 'MS',
        'ticker_sentiment_label': 'Neutral',
        'name': 'Morgan Stanley'
      }
    ],
    'banner_image': 'https://images.mktw.net/im-34943024/social',
    'source': 'MarketWatch',
    'authors': [
      'Steve Gelsi'
    ],
    'topics': [
      {
        'topic': 'Earnings',
        'relevance_score': '0.538269'
      },
      {
        'topic': 'Finance',
        'relevance_score': '1.0'
      },
      {
        'topic': 'Financial Markets',
        'relevance_score': '0.5855'
      }
    ],
    'title': 'Earnings reports spark downgrades of Wells Fargo and Morgan Stanley as analysts see headwinds',
    'time_published': '12:00 PM EST, January 18, 2024',
    'risk_avg': 6.5,
    'source_domain': 'www.marketwatch.com',
    'overall_sentiment_score': 0.114972
  },
  {
    'overall_sentiment_label': 'Neutral',
    'summary': 'Canopy Growth Corporation WEED CGC announced on Thursday that it has entered into subscription agreements with certain institutional investors in a private placement offering of 8,158,510 units at $4.29 per unit for aggregate gross proceeds of roughly $35 million.',
    'url': 'https://www.benzinga.com/markets/cannabis/24/01/36678540/weed-giant-canopy-announces-upsized-35m-private-placement',
    'category_within_source': 'News',
    'ticker_sentiment': [
      {
        'exchange': 'NMS',
        'type': 'EQUITY',
        'risk': 4,
        'price': 4.69,
        'ticker_sentiment_score': '-0.060485',
        'relevance_score': '0.190417',
        'ticker': 'CGC',
        'ticker_sentiment_label': 'Neutral',
        'name': 'Canopy Growth Corporation'
      }
    ],
    'banner_image': 'https://cdn.benzinga.com/files/images/story/2024/elsa-olofsson-FkfIPqqv2Oc-unsplash5.jpeg?width=1200&height=800&fit=crop',
    'source': 'Benzinga',
    'authors': [
      'Jelena Martinovic'
    ],
    'topics': [
      {
        'topic': 'Earnings',
        'relevance_score': '0.310843'
      },
      {
        'topic': 'Life Sciences',
        'relevance_score': '1.0'
      },
      {
        'topic': 'Financial Markets',
        'relevance_score': '0.161647'
      }
    ],
    'title': 'Weed Giant Canopy Announces Upsized $35M Private Placement - Canopy Gwth  ( NASDAQ:CGC ) ',
    'time_published': '12:00 PM EST, January 18, 2024',
    'risk_avg': 4.0,
    'source_domain': 'www.benzinga.com',
    'overall_sentiment_score': 0.131151
  }
]
}

@pytest.fixture
def client():
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client

def test_get_news(client):
    received_data = get_news()    
    # Assert that returns a news list
    assert isinstance(received_data, list), received_data
    assert all(isinstance(item, dict) for item in received_data)