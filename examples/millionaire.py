import sys, getopt
sys.path.append('.')

from pymongo import MongoClient
from bitcoin_price_prediction.bayesian_regression import *

data_collection ='historical_data_btc_usd'
data_base = 'okcoindb'
_t = 0.0001
_step = 1
coin_amount = 1

try:
    opts, args = getopt.getopt(sys.argv[1:],"hd:c:t:s:a:")
except getopt.GetoptError:
    print 'okcoin.py -d <database> -c <collection> -t <threshold> -s <step> -a <coin amount>'
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print 'okcoin.py -p <coin_pair>'
        sys.exit()
    elif opt == '-d':
        data_base = arg
    elif opt == '-c':
        data_collection = arg
    elif opt == '-t':
        _t = float(arg)
    elif opt == '-s':
        _step = int(arg)
    elif opt == '-a':
        coin_amount = float(arg)


print("Informations: Data base - " + data_base + " collection - " + data_collection)
print("Informations: Coin amount - " + str(coin_amount) + " step - " + str(_step) + " threshold - " + str(_t))

client = MongoClient()
database = client[data_base]
collection = database[data_collection]

# Retrieve price, v_ask, and v_bid data points from the database.
prices = []
dates = []
v_ask = []
v_bid = []
num_points = 777600
print('Making data...')
for doc in collection.find().limit(num_points):
    prices.append(doc['price'])
    dates.append(doc['date'])
    v_ask.append(doc['v_ask'])
    v_bid.append(doc['v_bid'])

# Divide prices into three, roughly equal sized, periods:
# prices1, prices2, and prices3.
[prices1, prices2, prices3] = np.array_split(prices, 3)
[dates1, dates2, dates3] = np.array_split(dates, 3)

# Divide v_bid into three, roughly equal sized, periods:
# v_bid1, v_bid2, and v_bid3.
[v_bid1, v_bid2, v_bid3] = np.array_split(v_bid, 3)

# Divide v_ask into three, roughly equal sized, periods:
# v_ask1, v_ask2, and v_ask3.
[v_ask1, v_ask2, v_ask3] = np.array_split(v_ask, 3)

# Use the first time period (prices1) to generate all possible time series of
# appropriate length (180, 360, and 720).
print('Time series...')
timeseries180 = generate_timeseries(prices1, 180)
timeseries360 = generate_timeseries(prices1, 360)
timeseries720 = generate_timeseries(prices1, 720)

# Cluster timeseries180 in 100 clusters using k-means, return the cluster
# centers (centers180), and choose the 20 most effective centers (s1).
print('Find cluster center...')
centers180 = find_cluster_centers(timeseries180, 100)
s1 = choose_effective_centers(centers180, 20)

centers360 = find_cluster_centers(timeseries360, 100)
s2 = choose_effective_centers(centers360, 20)

centers720 = find_cluster_centers(timeseries720, 100)
s3 = choose_effective_centers(centers720, 20)

# Use the second time period to generate the independent and dependent
# variables in the linear regression model:
# tp = w0 + w1 * deltap1 + w2 * deltap2 + w3 * deltap3 + w4 * r.
print('Liner regression...')
Dpi_r, Dp = linear_regression_vars(prices2, v_bid2, v_ask2, s1, s2, s3)

# Find the parameter values w (w0, w1, w2, w3, w4).
print('Find parameters...')
w = find_parameters_w(Dpi_r, Dp)

# Predict average price changes over the third time period.
print('Predict dps...')
dps = predict_dps(prices3, v_bid3, v_ask3, s1, s2, s3, w)

# What's your 'Fuck You Money' number?
print('Evaluate Performance...')
bank_balance = evaluate_performance2(coin_amount, prices3, dates3, dps, t=_t, step=_step)
