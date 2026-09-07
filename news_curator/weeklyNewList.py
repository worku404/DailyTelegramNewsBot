import feedparser, requests
from news_curator.sources import STREAMS
from news_curator.rss_fetcher import FEED_HEADERS
def weekly_lists():
    for sid, sm in STREAMS.items():
        print('STREAM', sid, sm['name'])
        for s in sm['sources']:
            try:
                r = requests.get(s.feed_url, headers=FEED_HEADERS, timeout=10)
                f = feedparser.parse(r.content)
                print('->', s.name, 'entries count:', len(f.entries))
                for e in f.entries[:4]:
                    d = getattr(e, 'published', None) or getattr(e, 'updated', None)
                    print('   ', d, '|', e.title[:65])
            except Exception as ex:
                print('->', s.name, 'ERR', ex)
