from .frame import FrameType


def get_segment_order_list(frame_table, segment_dict, cur_frame_index):
    order_list = []
    # 尝试找到上个线段，并记录到线段的所有笔

    # 先找到线段的最后一笔
    segmemt_start = None
    for frame_index in range(cur_frame_index, -1, -1):
        if segmemt_start is not None and frame_index < segmemt_start:
            break
        if (frame_table[frame_index].frame_type == FrameType.top or frame_table[frame_index].frame_type == FrameType.bottom) and (frame_table[frame_index].next_replace_frame is None or frame_table[frame_index].next_replace_frame > cur_frame_index):
            order_list.append(frame_index)
            if frame_index in segment_dict:
                segmemt_start = segment_dict[frame_index]
            break

    if len(order_list) == 0:
        return order_list, segmemt_start

    # 通过最后一笔，往前找出整条线段
    frame_index = frame_table[order_list[-1]].pre_frame
    while frame_index is not None and frame_index >= 0:
        if segmemt_start is not None and frame_index < segmemt_start:
            break
        assert (frame_table[frame_index].frame_type == FrameType.top or frame_table[frame_index].frame_type == FrameType.bottom) and (frame_table[frame_index].next_replace_frame is None or frame_table[frame_index].next_replace_frame > cur_frame_index)
        order_list.append(frame_index)
        if len(order_list) > 1:
            assert frame_table[order_list[-1]].frame_type != frame_table[order_list[-2]].frame_type
        if frame_index in segment_dict and segmemt_start is None:
            segmemt_start = segment_dict[frame_index]
        frame_index = frame_table[frame_index].pre_frame
    order_list.reverse()
    return order_list, segmemt_start