#!/usr/bin/python
"""Script to gather market data from OKCoin Spot Price API."""
import sys, getopt
import requests
from pytz import utc
from datetime import datetime
from pymongo import MongoClient
from apscheduler.schedulers.blocking import BlockingScheduler

#client = MongoClient()
#database = client['okcoindb']
#collection = database['historical_data']

def tick(collection, pair):
    """Gather market data from OKCoin Spot Price API and insert them into a
       MongoDB collection."""
    url = 'https://www.okcoin.com/api/v1/ticker.do?symbol=' + pair
    ticker = requests.get(url).json()
    url = 'https://www.okcoin.com/api/v1/depth.do?symbol=' + pair + '&size=60'
    depth = requests.get('https://www.okcoin.com/api/v1/depth.do?symbol=btc_usd&size=60').json()
    date = datetime.fromtimestamp(int(ticker['date']))
    price = float(ticker['ticker']['last'])
    v_bid = sum([bid[1] for bid in depth['bids']])
    v_ask = sum([ask[1] for ask in depth['asks']])
    collection.insert({'date': date, 'price': price, 'v_bid': v_bid, 'v_ask': v_ask})
    print(date, price, v_bid, v_ask)


def main(argv):
    pair = 'btc_usd'  
    try:
        opts, args = getopt.getopt(argv,"hp:",["pair="])
    except getopt.GetoptError:
        print 'okcoin.py -p <coin_pair>'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'okcoin.py -p <coin_pair>'
            sys.exit()
        elif opt in ("-p", "--pair"):
            pair = arg

    print('Pair: ' + pair)

    """Run tick() at the interval of every ten seconds."""
    client = MongoClient()
    database = client['okcoindb']
    collection = database['historical_data_'+pair]
    collection.drop()
 
    scheduler = BlockingScheduler(timezone=utc)
    scheduler.add_job(tick, 'interval', [collection, pair], seconds=10)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

if __name__ == "__main__":
   main(sys.argv[1:])

