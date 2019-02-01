import stframe as stf
from stdb import *
import numpy as np
import pandas as pd

if __name__ == '__main__':
    code_df = pd.read_csv("data/codes.csv", dtype=str)
    dataProxy = LocalDataProxy(min_date='2009-01-01')
    for index, row in code_df.iterrows():
        code = row['code']
        data = stf.process_indicator(dataProxy.get_all_data(code), dataProxy.get_all_data('sz399005'))
        np.save('data/%s' % code, data)

        frame_table = stf.process_frame(data)
        stf.Frame.save(frame_table, 'data/%s_frame.csv' % code)

        segment_dict = stf.process_segment(frame_table, data['open'], data['thigh'], data['tlow'], data['close'])
        stf.Segment.save(segment_dict, 'data/%s_segment.csv' % code)

        center_dict = stf.process_center(frame_table, segment_dict, data['thigh'], data['tlow'])
        stf.Center.save(center_dict, 'data/%s_center.csv' % code)
        print("finish " + code)
