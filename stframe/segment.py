from .base import get_segment_order_list
from .frame import FrameType


class Segment(object):
    @classmethod
    def save(cls, segment_dict, path):
        with open(path, 'w') as f:
            f.write("frame_index,segment_frame_index\n")
            for key, value in segment_dict.items():
                f.write("%d,%d\n" % (key, value))


# 如果终结下跌（上涨）线段，定位之前的最低（高）点
def get_best_finish_segment_index(thigh, tlow, frame_table, order_list, new_segment_is_rise):
    segmemt_finish_index = len(order_list) - 2
    if new_segment_is_rise:
        # 定位之前的最低点
        for i in range(len(order_list)-4, -1, -2):
            if tlow[frame_table[order_list[i]].data_index - 1] < tlow[frame_table[order_list[segmemt_finish_index]].data_index - 1]:
                segmemt_finish_index = i
    else:
        # 定位之前的最高点
        for i in range(len(order_list)-4, -1, -2):
            if thigh[frame_table[order_list[i]].data_index - 1] > thigh[frame_table[order_list[segmemt_finish_index]].data_index - 1]:
                segmemt_finish_index = i
    return segmemt_finish_index


# 找到最高(最低)点
def get_best_index(thigh, tlow, frame_table, order_list, start_order_index, finish_order_index, is_top):
    best_index = start_order_index
    if is_top:
        for i in range(start_order_index + 2, finish_order_index + 1, 2):
            if thigh[frame_table[order_list[i]].data_index - 1] > thigh[frame_table[order_list[best_index]].data_index - 1]:
                best_index = i
    else:
        for i in range(start_order_index + 2, finish_order_index + 1, 2):
            if tlow[frame_table[order_list[i]].data_index - 1] < tlow[frame_table[order_list[best_index]].data_index - 1]:
                best_index = i
    return best_index


# 是否有效击穿某个价格
def valid_breakdown(close, open, mid_pos, is_rise, min_cross_cnt = 3):
    cross_cnt = 0
    for i in range(len(close)):
        if (is_rise is True and close[i] > mid_pos) or (is_rise is False and close[i] < mid_pos):
            cross_cnt += 1
        else:
            cross_cnt = 0
        if cross_cnt >= min_cross_cnt and ((is_rise == True and open[i] < close[i]) or (is_rise == False and open[i] > close[i])):
            return True
    return False


# 处理线段
def process_segment(frame_table, open, thigh, tlow, close):
    segment_dict = {}
    for frame_index, frame in enumerate(frame_table):
        if (frame.frame_type == FrameType.top or frame.frame_type == FrameType.bottom) and (frame.next_replace_frame is None or frame.next_replace_frame > frame_index):
            # 尝试找到上个线段，并记录到线段的所有笔
            order_list, segmemt_start = get_segment_order_list(frame_table, segment_dict, frame_index)

            if segmemt_start is not None and len(order_list) % 2 == 0:
                # 如果之前有确定的线段，形成新线段后俩线段之间的笔一定是基数。
                continue

            if len(order_list) < 4:
                continue

            is_top = (frame_table[order_list[-1]].frame_type == FrameType.top)
            index_1 = frame_table[order_list[-1]].data_index
            next_pos_2 = thigh[index_1 - 1] if frame_table[order_list[-1]].frame_type == FrameType.top else tlow[index_1 - 1]

            segmemt_finish_index = get_best_finish_segment_index(thigh, tlow, frame_table, order_list, is_top)
            # 如果当前这一个上涨笔的最底点创了新低，肯定不成线段
            if segmemt_finish_index == len(order_list) - 2:
                continue
                # 如果之前笔已经发现了线段，就不用再做线段
            if segmemt_start == order_list[segmemt_finish_index]:
                continue

            mid_index = get_best_index(thigh, tlow, frame_table, order_list, segmemt_finish_index + 1,
                                       len(order_list) - 3, is_top)
            mid_pos = thigh[frame_table[order_list[mid_index]].data_index] if is_top else tlow[
                frame_table[order_list[mid_index]].data_index]
            if (is_top and mid_pos >= next_pos_2) or (is_top is False and mid_pos <= next_pos_2):
                # 没有站稳之前的最值点
                continue
                # 查看在顶分型出现之前有没有有效击穿之前的高点
            start_index = frame_table[order_list[-2]].data_index - 1
            end_index = frame_table[order_list[-1]].data_index
            if valid_breakdown(close[start_index:end_index + 1], open[start_index:end_index + 1], mid_pos, is_top):
                segment_dict[frame_index] = order_list[segmemt_finish_index]
    return segment_dict
