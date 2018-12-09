import stframe as stf
from stdb import *
import numpy as np

if __name__ == '__main__':
    dataProxy = LocalDataProxy(cache_path='data', is_offline=True)
    code = '600887'
    data = stf.process_indicator(dataProxy.get_all_data(code)[-300:], dataProxy.get_all_data('sh000001'))
    np.save('data/%s' % code, data)

    frame_table = stf.process_frame(data)
    stf.Frame.save(frame_table, 'data/%s_frame.csv' % code)

    segment_dict = stf.process_segment(frame_table, data['open'], data['thigh'], data['tlow'], data['close'])
    stf.Segment.save(segment_dict, 'data/%s_segment.csv' % code)

    center_dict = stf.process_center(frame_table, segment_dict, data['thigh'], data['tlow'])
    stf.Center.save(center_dict, 'data/%s_center.csv' % code)
