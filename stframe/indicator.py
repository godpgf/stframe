import numpy as np
# 从每天的数据中计算各种需要用到的统计指标并保存下来


# 处理各种指标
def process_indicator(data, market_data):
    date = data['date']
    market_date = market_data['date']
    open = data['open']
    high = data['high']
    low = data['low']
    close = data['close']
    market_close = market_data['close']
    volume = data['volume']
    turn = data['turn']
    atr = cal_atr(cal_tr(high, low, close, volume), volume)
    expect_return = cal_expect_returns(atr, close, volume, 5)
    thigh, tlow, is_inclusion = cal_inclusion(high, low)
    dif_long, dea_long, macd_long = cal_macd(close, volume, 12, 26, 9)
    dif_short, dea_short, macd_short = cal_macd(close, volume, 6, 13, 5)
    ma5 = cal_ma(close, volume, 5)
    ma10 = cal_ma(close, volume, 10)
    ma20 = cal_ma(close, volume, 20)

    vol5 = cal_ma(volume, volume, 5)
    vol10 = cal_ma(volume, volume, 10)
    vol20 = cal_ma(volume, volume, 20)

    alpha5, beta5 = cal_alpha_beta(date, close, volume, market_date, market_close, 5)
    alpha10, beta10 = cal_alpha_beta(date, close, volume, market_date, market_close, 10)
    alpha20, beta20 = cal_alpha_beta(date, close, volume, market_date, market_close, 20)

    data = np.array([date, open, high, low, close,
                     volume, turn, atr, expect_return,
                     thigh, tlow, is_inclusion,
                     dif_long, dea_long, macd_long,
                     dif_short, dea_short, macd_short,
                     ma5, ma10, ma20, vol5, vol10, vol20, alpha5, alpha10, alpha20, beta5, beta10, beta20]).T
    data = [tuple(d.tolist()) for d in data]

    stocktype = np.dtype([
        ('date', 'uint64'), ('open', 'float64'),
        ('high', 'float64'), ('low', 'float64'),
        ('close', 'float64'), ('volume', 'float64'),
        ('turn', 'float64'), ('atr', 'float64'), ('expect_return', 'float64'),
        ('thigh', 'float64'), ('tlow', 'float64'), ('is_inclusion', 'bool'),
        ('dif_long', 'float64'), ('dea_long', 'float64'), ('macd_long', 'float64'),
        ('dif_short', 'float64'), ('dea_short', 'float64'), ('macd_short', 'float64'),
        ('ma5', 'float64'), ('ma10', 'float64'), ('ma20', 'float64'),
        ('vol5', 'float64'), ('vol10', 'float64'), ('vol20', 'float64'),
        ('alpha5','float64'), ('alpha10','float64'), ('alpha20','float64'),
        ('beta5', 'float64'), ('beta10', 'float64'), ('beta20', 'float64'),
    ])
    bars = np.array(data, dtype=stocktype)
    return bars


def cal_tr(high, low, close, volume):
    tr = np.zeros(len(volume))
    last_close = None
    for i in range(len(volume)):
        if volume[i] <= 0:
            tr[i] = 0
        else:
            if last_close is None:
                tr[i] = high[i] - low[i]
            else:
                tr[i] = max((high[i] - low[i]), max(abs(low[i] - last_close), abs(high[i] - last_close)))
            last_close = close[i]
    return tr


def cal_atr(tr, volume, n=14):
    atr = np.zeros(len(volume))
    last_atr = None
    last_tr = np.zeros(n)
    last_tr_size = 0
    last_tr_index = 0
    for i in range(len(volume)):
        if volume[i] <= 0:
            atr[i] = 0 if last_atr is None else last_atr
        else:
            last_tr[last_tr_index] = tr[i]
            last_tr_index += 1
            if last_tr_index == len(last_tr):
                last_tr_index = 0
            if last_tr_size < len(last_tr):
                last_tr_size += 1.0

            atr[i] = np.sum(last_tr) / last_tr_size
            last_atr = atr[i]
    return atr


# 处理包含关系
def cal_inclusion(high, low):
    assert len(high) == len(low)
    thigh = np.zeros(len(high))
    tlow = np.zeros(len(low))
    is_inclusion = [False]*len(low)
    thigh[0], thigh[1] = high[0], high[1]
    tlow[0], tlow[1] = low[0], low[1]
    is_inclusion[0], is_inclusion[1] = False, False
    for i in range(2, len(high)):
        is_in = (high[i] >= thigh[i-1] and low[i] <= tlow[i-1]) or (high[i] <= thigh[i-1] and low[i] >= tlow[i-1])
        thigh[i], tlow[i] = high[i], low[i]
        if is_in:
            is_inclusion[i] = True
            if thigh[i-1] > thigh[i-2] and tlow[i-1] > tlow[i-2]:
                #高高
                thigh[i] = max(thigh[i-1], thigh[i])
                tlow[i] = max(tlow[i-1], tlow[i])
                thigh[i-1] = (thigh[i] + thigh[i-2]) / 2
                tlow[i-1] = (tlow[i] + tlow[i-2]) / 2
            elif thigh[i-1] < thigh[i-2] and tlow[i-1] < tlow[i-2]:
                #低低
                thigh[i] = min(thigh[i-1], thigh[i])
                tlow[i] = min(tlow[i-1], tlow[i])
                thigh[i-1] = (thigh[i] + thigh[i-2]) / 2
                tlow[i-1] = (tlow[i] + tlow[i-2]) / 2
        else:
            is_inclusion[i] = False
    return thigh, tlow, is_inclusion


# 计算期望收益（赚了几个正常波动）
def cal_expect_returns(atr, close, volume, n):
    returns = np.zeros(len(close))
    returns[-1] = 0
    for i in range(len(close)-2, -1, -1):
        if volume[i] <= 0:
            returns[i] = returns[i+1]
        else:
            returns[i] = (2 * (close[i+1] - close[i])/atr[i] + (n - 1) * returns[i+1]) / (n + 1)
    return returns


# 计算macd
def cal_macd(close, volume, short=12, long=26, m=9):
    a = get_ema(close, volume, short)
    b = get_ema(close, volume, long)
    diff = a - b
    dea = np.zeros(len(diff))
    for i in range(len(diff)):
        if i == 0:
            dea[i] = diff[i]
        elif volume[i] <= 0:
            dea[i] = dea[i-1]
        else:
            dea[i] = (2 * diff[i] + (m - 1) * dea[i-1]) / (m + 1)
    return diff, dea, 2 * (diff - dea)


# 计算ema
def get_ema(data, volume, n):
    ema = np.zeros(len(data))
    for i in range(len(data)):
        if i == 0:
            ema[i] = data[i]
        else:
            if volume[i] <= 0:
                ema[i] = ema[i-1]
            else:
                ema[i] = (2 * data[i] + (n - 1) * ema[i - 1]) / (n + 1)
    return ema


def cal_ma(data, volume, n=10):
    ma = np.zeros(len(volume))
    last_ma = None
    last_data = np.zeros(n)
    last_data_size = 0
    last_data_index = 0
    for i in range(len(volume)):
        if volume[i] <= 0:
            ma[i] = data[i] if last_ma is None else last_ma
        else:
            last_data[last_data_index] = data[i]
            last_data_index += 1
            if last_data_index == len(last_data):
                last_data_index = 0
            if last_data_size < len(last_data):
                last_data_size += 1.0

            ma[i] = np.sum(last_data) / last_data_size
            last_ma = ma[i]
    return ma


def cal_alpha_beta(date, close, volume, market_date, market_close, n=5):
    alpha_list = np.zeros(len(close))
    beta_list = np.zeros(len(close))

    cur_close = np.zeros(n+1)
    cur_market_close = np.zeros(n+1)
    sub_index = 0
    market_index = 0
    for i in range(len(close)):
        if volume[i] <= 0:
            continue
        while market_date[market_index] != date[i]:
            market_index += 1
        if sub_index < len(cur_close):
            cur_close[sub_index] = close[i]
            cur_market_close[sub_index] = market_close[market_index]
            sub_index += 1
        else:
            cur_close[:-1] = cur_close[1:]
            cur_market_close[:-1] = cur_market_close[1:]
            cur_close[-1] = close[i]
            cur_market_close[-1] = market_close[market_index]

            asset_returns = cur_close[1:] / cur_close[0]
            market_returns = cur_market_close[1:] / cur_market_close[0]

            market_premium = np.atleast_2d(market_returns).T
            asset_premium = np.atleast_2d(asset_returns).T
            constant = np.ones((market_premium.shape[0], 1))
            covariates = np.concatenate((constant, market_premium), axis=1)
            theta = np.linalg.lstsq(covariates, asset_premium, rcond=-1)[0]
            alpha_list[i] = theta[0]
            beta_list[i] = theta[1]
    return alpha_list, beta_list

