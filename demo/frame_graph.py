from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from stframe import FrameType


if __name__ == '__main__':
    code = '601169'
    data = np.load('output/%s.npy' % code)
    frame_table = pd.read_csv("output/%s_frame.csv" % code, dtype={'frame_type': np.int32,
                                                                 'data_index': np.int32})
    min_data_index = np.min(frame_table['data_index'].values)
    segment_table = pd.read_csv("output/%s_segment.csv" % code)
    center_table = pd.read_csv("output/%s_center.csv" % code)

    date = data['date'] // 1000000
    date = ["%s-%s-%s" % (str(int(d))[:4], str(int(d))[4:6], str(int(d))[6:]) for d in date]
    ma5 = data['ma5']
    ma10 = data['ma10']
    thigh = data['thigh']
    tlow = data['tlow']

    close = data['close']
    dif = data['dif_short']
    macd = data['macd_short']
    atr = data['atr']

    plt.figure(figsize=(24, 6))

    plt.plot_date(date[min_data_index-1:], thigh[min_data_index-1:], '.', color=(1,0,0), markersize=2)
    plt.plot_date(date[min_data_index-1:], tlow[min_data_index-1:], '.', color=(0,1,0), markersize=2)

    plt.plot(date[min_data_index-1:], ma5[min_data_index-1:], color=(0.5,0.5,0.5))
    plt.plot(date[min_data_index-1:], ma10[min_data_index-1:], color=(0,0,0))

    # 画笔
    order_list = []
    for index, row in frame_table.iterrows():
        if pd.isnull(row['next_replace_frame']):
            if row['frame_type'] == FrameType.top.value:
                order_list.append(index)
            elif row['frame_type'] == FrameType.bottom.value:
                order_list.append(index)

    for id, oid in enumerate(order_list):
        if id == 0:
            continue
        pre_index = frame_table['data_index'].loc[order_list[id-1]] - 1
        index = frame_table['data_index'].loc[oid] - 1
        pre_pos = tlow[pre_index] if frame_table['frame_type'].loc[oid] == FrameType.top.value else thigh[pre_index]
        pos = thigh[index] if frame_table['frame_type'].loc[oid] == FrameType.top.value else tlow[index]
        plt.plot([date[pre_index], date[index]], [pre_pos, pos], color=(0.5, 0.5, 0.5))


    # 画线段
    x = []
    y = []
    for index, row in segment_table.iterrows():
        id = frame_table['data_index'].loc[row['segment_frame_index']] - 1
        if frame_table['frame_type'].loc[row['segment_frame_index']] == FrameType.top.value:
            x.append(date[id])
            y.append(thigh[id])
        elif frame_table['frame_type'].loc[row['segment_frame_index']] == FrameType.bottom.value:
            x.append(date[id])
            y.append(tlow[id])
    plt.plot(np.array(x), np.array(y), color=(0, 0, 1))

    # 画中枢
    for index, row in center_table.iterrows():
        e_id = row['end_frame']
        s_id = row['start_frame']
        lowp = row['bottom']
        highp = row['top']
        start_index = frame_table['data_index'].loc[s_id] - 1
        end_index = frame_table['data_index'].loc[e_id] - 1
        is_rise = row['is_rise'] > 0
        frame_index = row['frame_index']
        if not pd.isna(frame_table['next_replace_frame'].loc[frame_index]):
            continue
        if is_rise:
            plt.plot(np.array([date[start_index], date[end_index]]),np.array([highp, highp]),color=(1,0,0))
            plt.plot(np.array([date[start_index], date[end_index]]), np.array([lowp, lowp]), color=(1, 0, 0))
        else:
            plt.plot(np.array([date[start_index], date[end_index]]),np.array([highp, highp]),color=(0,1,0))
            plt.plot(np.array([date[start_index], date[end_index]]), np.array([lowp, lowp]), color=(0, 1, 0))

    # 画停顿
    x = []
    y = []
    for i in range(len(order_list)):
        next_stop_frame = frame_table['next_stop_frame'].loc[order_list[i]]
        if i < len(order_list) - 1:
            assert not pd.isna(next_stop_frame)
        if not pd.isna(next_stop_frame):
            index = frame_table['data_index'].loc[int(next_stop_frame)]
            x.append(date[index])
            y.append(close[index])
    plt.plot_date(x, y, '.', color=(0, 0, 0), markersize=12)

    plt.show()
    print('finish')