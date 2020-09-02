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
def get_best_finish_segment_index(thigh, tlow, frame_table, order_list, new_segment_is_rise, has_start=True):
    segmemt_finish_index = len(order_list) - 2
    start_index = 2 if has_start else -1
    if new_segment_is_rise:
        # 定位之前的最低点，线段最少有3笔，所以遍历最低点时最小索引是3
        for i in range(len(order_list)-4, start_index, -2):
            if tlow[frame_table[order_list[i]].data_index - 1] < tlow[frame_table[order_list[segmemt_finish_index]].data_index - 1]:
                segmemt_finish_index = i
    else:
        # 定位之前的最高点
        for i in range(len(order_list)-4, start_index, -2):
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

            # 形成线段至少需要3笔，终结它形成又得至少往后看三笔，所以至少一共六笔
            if len(order_list) < 7:
                continue

            # if frame_index == 367:
            #     print("ffff")

            is_top = (frame_table[order_list[-1]].frame_type == FrameType.top)

            def delta_price(oid, is_high, is_offset=False):
                # is_offset：是否隔山打牛
                if is_high:
                    return thigh[frame_table[order_list[oid]].data_index-1], (min(thigh[frame_table[order_list[oid - 2]].data_index-1], thigh[frame_table[order_list[oid - 4]].data_index-1]) if is_offset else thigh[frame_table[order_list[oid - 2]].data_index-1])
                else:
                    return tlow[frame_table[order_list[oid]].data_index-1], (max(tlow[frame_table[order_list[oid - 2]].data_index-1], tlow[frame_table[order_list[oid - 4]].data_index-1]) if is_offset else tlow[frame_table[order_list[oid - 2]].data_index-1])

            # 1+1终结
            cur_price, pre_price = delta_price(len(order_list)-2, not is_top)
            if cur_price == pre_price:
                continue
            if (cur_price - pre_price < 0) == is_top:
                continue
            cur_price, pre_price = delta_price(len(order_list)-1, is_top, True)
            if cur_price == pre_price:
                continue
            if (cur_price - pre_price < 0) == is_top:
                continue

             # 查看在顶分型出现之前有没有有效击穿之前的高点
            start_index = frame_table[order_list[-2]].data_index - 1
            end_index = frame_table[order_list[-1]].data_index
            if valid_breakdown(close[start_index:end_index + 1], open[start_index:end_index + 1], pre_price, is_top):
                segmemt_finish_index = get_best_finish_segment_index(thigh, tlow, frame_table, order_list, is_top, segmemt_start is not None)
                segment_dict[frame_index] = order_list[segmemt_finish_index]
    return segment_dict


class SegmentTool(object):
    @classmethod
    def get_segment_order_list(cls, frame_table, segment_dict, cur_frame_index):
        order_list = []
        # 尝试找到上个线段，并记录到线段的所有笔

        # 先找到线段的最后一笔
        segment_start = None
        for frame_index in range(cur_frame_index, -1, -1):
            if segment_start is not None and frame_index < segment_start:
                break
            frame_type = frame_table[frame_index].frame_type
            next_replace_frame = frame_table[frame_index].next_replace_frame
            if (frame_type == FrameType.top or frame_type == FrameType.bottom) and (next_replace_frame is None or next_replace_frame > cur_frame_index):
                order_list.append(frame_index)
                if frame_index in segment_dict and (frame_table[frame_index].next_replace_frame is None or frame_table[frame_index].next_replace_frame > cur_frame_index):
                    segment_start = segment_dict[frame_index]
                break

        if len(order_list) == 0:
            return order_list, segment_start

        # 通过最后一笔，往前找出整条线段
        frame_index = frame_table[order_list[-1]].pre_frame
        while frame_index is not None and frame_index >= 0:
            if segment_start is not None and frame_index < segment_start:
                break
            frame_type = frame_table[frame_index].frame_type
            next_replace_frame = frame_table[frame_index].next_replace_frame
            assert (frame_type == FrameType.top or frame_type == FrameType.bottom) and (next_replace_frame is None or next_replace_frame > cur_frame_index)
            order_list.append(frame_index)
            if len(order_list) > 1:
                assert frame_table[order_list[-1]].frame_type != frame_table[order_list[-2]].frame_type
            if frame_index in segment_dict and segment_start is None and (frame_table[frame_index].next_replace_frame is None or frame_table[frame_index].next_replace_frame > cur_frame_index):
                segment_start = segment_dict[frame_index]
            frame_index = frame_table[frame_index].pre_frame
        order_list.reverse()
        return order_list, segment_start

    @classmethod
    def get_center_list(cls, order_list, segment_start, frame_table, center_dict):
        is_rise_segment = (frame_table[segment_start].frame_type == FrameType.bottom)
        center_list = []
        for frame_index in order_list:
            if frame_index in center_dict:
                for center in center_dict[frame_index]:
                    if center.start_frame_index > segment_start and center.is_rise == is_rise_segment:
                        if len(center_list) > 0:
                            assert center.start_frame_index > center_list[-1].start_frame_index
                        center_list.append(center)
        return center_list

    @classmethod
    def is_extreme_price(cls, order_list, frame_table, high, low):
        frame_type = frame_table[order_list[-1]].frame_type
        data_index = frame_table[order_list[-1]].data_index - 1
        price = high[data_index] if frame_type == FrameType.top else low[data_index]
        for i in range(len(order_list)-3, 0, -2):
            assert frame_type == frame_table[order_list[i]].frame_type
            data_index = frame_table[order_list[i]].data_index - 1
            cur_price = high[data_index] if frame_type == FrameType.top else low[data_index]
            if frame_type == FrameType.top and cur_price > price:
                return False
            if frame_type == FrameType.bottom and cur_price < price:
                return False
        return True
