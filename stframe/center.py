from .base import get_segment_order_list
from .frame import FrameType


# 中枢
class Center(object):
    def __init__(self, start_frame_index, end_frame_index, is_rise, top, bottom):
        self.start_frame_index = start_frame_index
        self.end_frame_index = end_frame_index
        assert end_frame_index >start_frame_index
        self.is_rise = is_rise
        self.top = top
        self.bottom = bottom

    @classmethod
    def save(cls, center_dict, path):
        with open(path, 'w') as f:
            f.write("frame_index,start_frame,end_frame,is_rise,top,bottom\n")
            for key, value in center_dict.items():
                for center in value:
                    f.write("%d,%d,%d,%d,%.4f,%.4f\n" % (key, center.start_frame_index, center.end_frame_index,
                                                         1 if center.is_rise else 0, center.top, center.bottom))


def process_center(frame_table, segment_dict, thigh, tlow):
    center_dict = {}
    for frame_index, frame in enumerate(frame_table):
        if (frame.frame_type == FrameType.top or frame.frame_type == FrameType.bottom) and (frame.next_replace_frame is None or frame.next_replace_frame > frame_index):
            # 尝试找到上个线段，并记录到线段的所有笔
            order_list, segmemt_start = get_segment_order_list(frame_table, segment_dict, frame_index)

            # 笔中对中枢的描述有三种
            # 1、刚形成中枢'center'
            # 2、之前的中枢'pre_center'
            # 3、没有中枢
            if segmemt_start is None:
                # 无线段不中枢
                continue

            if frame_table[segmemt_start].frame_type == FrameType.top:
                is_rise = False
            else:
                is_rise = True

            if len(order_list) < 5:
                # 形成不了新中枢
                continue

            id = 1
            pre_center = None
            # 记录这一笔向前看到的最近一个新中枢
            if len(center_dict) > 0:
                for i in range(len(order_list) - 1, -1, -1):
                    if order_list[i] in center_dict and center_dict[order_list[i]][-1].is_rise == is_rise:
                        pre_center = center_dict[order_list[i]][-1]
                        id = i
                        while id >= 0 and order_list[id] > pre_center.end_frame_index:
                            id -= 1
                        if pre_center.end_frame_index < order_list[0]:
                            # 中枢是上个线段的
                            pre_center = None
                            id = 1
                            break
                        assert order_list[id] == pre_center.end_frame_index
                        id += 1
                        break

            last_id = len(order_list) - 3 if len(order_list) % 2 > 0 else len(order_list) - 4
            while id < last_id:
                if is_rise:
                    high = min(thigh[frame_table[order_list[id]].data_index - 1], thigh[frame_table[order_list[id + 2]].data_index - 1])
                    low = max(tlow[frame_table[order_list[id + 1]].data_index - 1], tlow[frame_table[order_list[id + 3]].data_index - 1])
                else:
                    low = max(tlow[frame_table[order_list[id]].data_index - 1], tlow[frame_table[order_list[id + 2]].data_index - 1])
                    high = min(thigh[frame_table[order_list[id + 1]].data_index - 1], thigh[frame_table[order_list[id + 3]].data_index - 1])

                if high > low:
                    # 初步满足形成中枢的条件
                    if frame_index not in center_dict:
                        # center_list.append((is_rise, order_list[id], order_list[id+3], low, high))
                        if pre_center is None or low > pre_center.top or high < pre_center.bottom:
                            center_dict[frame_index] = [Center(order_list[id], order_list[id + 3], is_rise, high, low)]
                            pre_center = center_dict[frame_index][-1]
                            id += 4
                            continue
                    elif low > center_dict[frame_index][-1].top or high < center_dict[frame_index][-1].bottom:
                        center_dict[frame_index].append(Center(order_list[id], order_list[id + 3], is_rise, high, low))
                        pre_center = center_dict[frame_index][-1]
                        id += 4
                        continue
                id += 2
    return center_dict

