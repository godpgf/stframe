import numpy as np


# 从每天的数据中计算各种需要用到的统计指标并保存下来


# 处理各种指标
def process_indicator(data):
    # "date","open","high","low","close","price","volume","turnover"
    date = data['date']
    open = data['open']
    high = data['high']
    low = data['low']
    close = data['close']
    price = data['price']
    volume = data['volume']
    turnover = data['turnover']
    atr = cal_atr(cal_tr(high, low, close, volume), volume)
    thigh, tlow, is_inclusion = cal_inclusion(high, low)

    data = np.array([date, open, high, low, close, price, volume, turnover, atr, thigh, tlow, is_inclusion]).T
    data = [tuple(d.tolist()) for d in data]

    stocktype = np.dtype([
        ('date', 'uint64'), ('open', 'float32'),
        ('high', 'float32'), ('low', 'float32'),
        ('close', 'float32'), ('price', 'float32'),
        ('volume', 'uint64'), ('turnover', 'float32'),
        ('atr', 'float32'), ('thigh', 'float32'),
        ('tlow', 'float32'), ('is_inclusion', 'bool'),
    ])
    bars = np.array(data, dtype=stocktype)
    return bars


# 处理包含关系
def cal_inclusion(high, low):
    assert len(high) == len(low)
    thigh = np.zeros(len(high))
    tlow = np.zeros(len(low))
    is_inclusion = [False] * len(low)
    thigh[0], thigh[1] = high[0], high[1]
    tlow[0], tlow[1] = low[0], low[1]
    is_inclusion[0], is_inclusion[1] = False, False
    for i in range(2, len(high)):
        is_in = (high[i] >= thigh[i - 1] and low[i] <= tlow[i - 1]) or (
                    high[i] <= thigh[i - 1] and low[i] >= tlow[i - 1])
        thigh[i], tlow[i] = high[i], low[i]
        if is_in:
            is_inclusion[i] = True
            if thigh[i - 1] > thigh[i - 2] and tlow[i - 1] > tlow[i - 2]:
                # 高高
                thigh[i] = max(thigh[i - 1], thigh[i])
                tlow[i] = max(tlow[i - 1], tlow[i])
                thigh[i - 1] = (thigh[i] + thigh[i - 2]) / 2
                tlow[i - 1] = (tlow[i] + tlow[i - 2]) / 2
            elif thigh[i - 1] < thigh[i - 2] and tlow[i - 1] < tlow[i - 2]:
                # 低低
                thigh[i] = min(thigh[i - 1], thigh[i])
                tlow[i] = min(tlow[i - 1], tlow[i])
                thigh[i - 1] = (thigh[i] + thigh[i - 2]) / 2
                tlow[i - 1] = (tlow[i] + tlow[i - 2]) / 2
        else:
            is_inclusion[i] = False
    return thigh, tlow, is_inclusion


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