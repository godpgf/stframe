from enum import Enum


# 关键帧的类型
class FrameType(Enum):
    # 顶分型
    top = 1
    # 底分型
    bottom = 2
    # 顶分型停顿
    top_delay = 3
    # 底分型停顿
    bottom_delay = 4
    # 底分型停顿后继续上涨
    go_up = 5
    # 顶分型停顿后继续下跌
    go_down = 6


# 关键帧
class Frame(object):
    def __init__(self, frame_type, data_index):
        self.frame_type = frame_type
        # 关键帧对应的数据下标
        self.data_index = data_index
        # 之前的关键帧
        self.pre_frame = None
        # 之后的关键帧
        self.next_frame = None
        # 之后遇到的分型停顿
        self.next_stop_frame = None
        # 在哪一帧自己会被替换
        self.next_replace_frame = None
        # 在这一帧发现线段
        # 规定：在每个股票第一个关键帧上加上一个假线段，pre_segment=0，这样就可以把所有票合并在一起，并有标记区分开
        # self.pre_segment = None

    @classmethod
    def save(cls, frame_table, path):
        with open(path, 'w') as f:
            f.write("frame_type,data_index,pre_frame,next_frame,next_stop_frame,next_replace_frame\n")
            for frame in frame_table:
                s = "%d,%d,%s,%s,%s,%s\n" % (frame.frame_type.value,
                                     frame.data_index,
                                     str(frame.pre_frame) if frame.pre_frame is not None else '',
                                     str(frame.next_frame) if frame.next_frame is not None else '',
                                     str(frame.next_stop_frame) if frame.next_stop_frame is not None else '',
                                     str(frame.next_replace_frame) if frame.next_replace_frame is not None else '')
                f.write(s)




# 尝试添加顶分型。第一个分型就是顶分型
# 分型会被未来分型调整的情况只有两种：
# 1、未来遇到相同顶（底）分型比自己高（低）
# 2、未来遇到一个因为太靠近而失败的不同底（顶）分型，比前一个底（顶）还低（高），需要用它来代替前一个底（顶），于是先后会调整前一个顶（底）和前一个底（顶）
#    特别的，当前一个底（顶）换成自己的时候，他们之间的那个顶（底）居然比更之前的顶高（底低），需要保留上一个顶（底），删除上一个顶（底）前的一个底（顶）和一个顶（底），并认为当前失败。
def process_order(frame_table, thigh, tlow, close, is_inclusion, index):
    # 当前遇到的是否是顶分型
    is_top = (thigh[index - 1] > thigh[index - 2] and thigh[index - 1] > thigh[index])
    # 当前遇到的是否是底分型
    is_bottom = (tlow[index - 1] < tlow[index - 2] and tlow[index - 1] < tlow[index])
    assert (is_top and not is_bottom) or (is_bottom or not is_top)
    if is_top or is_bottom:
        # 如果遇到顶(底)分型

        # 看之前是顶分型还是底分型，以及停顿的位置
        frame_index_1 = None
        frame_stop_index_1 = None
        for i in range(len(frame_table) - 1, -1, -1):
            if (frame_table[i].frame_type == FrameType.top or frame_table[i].frame_type == FrameType.bottom) and \
                    frame_table[i].next_replace_frame is None:
                frame_index_1 = i
                if frame_stop_index_1 is not None:
                    if frame_table[i].frame_type == FrameType.top:
                        assert frame_table[frame_stop_index_1].frame_type == FrameType.top_delay
                    else:
                        assert frame_table[frame_stop_index_1].frame_type == FrameType.bottom_delay
                break
            elif (frame_table[i].frame_type == FrameType.top_delay
                  or frame_table[i].frame_type == FrameType.bottom_delay):
                assert frame_stop_index_1 is None
                frame_stop_index_1 = i

        if frame_index_1 is None:
            frame_table.append(Frame(FrameType.top, index) if is_top else Frame(FrameType.bottom, index))
        else:
            frame_1 = frame_table[frame_index_1]
            if frame_1.frame_type == (FrameType.top if is_top else FrameType.bottom):
                # 如果之前遇到的是顶(底)分型，现在遇到的也是顶(底)分型
                if (is_top and thigh[index - 1] >= thigh[frame_1.data_index - 1]) or (
                        is_bottom and tlow[index - 1] <= tlow[frame_1.data_index - 1]):
                    # 如果之前遇到过顶(底)分型，自己比它高(低)就把之前的去掉，换成自己后继续找底(顶)或者换顶(底)
                    frame_1.next_replace_frame = len(frame_table)
                    frame = Frame(FrameType.top, index) if is_top else Frame(FrameType.bottom, index)
                    frame.pre_frame = frame_1.pre_frame
                    if frame.pre_frame is not None:
                        frame_table[frame.pre_frame].next_frame = len(frame_table)
                    frame_table.append(frame)
                    # 在换顶（底）的过程中不会遇到失败的底（顶）分型，比前底（顶）还低（高），因为如果出这样的事情之前遇到失败分型时早就换底（顶）了
            else:
                # 如果之前是底(顶)分型，现在却是顶(底)分型

                # 用k_cnt判断这个分型距离前分型的距离
                k_cnt = 0
                for k in range(frame_1.data_index, index - 1):
                    if not is_inclusion[k]:
                        k_cnt += 1

                if k_cnt < 3:
                    # 如果当前的顶(底)分型距离之前的底(顶)分型太近(两个分型之间没有包含关系的k线少于5根)，驻顶(底)失败
                    # 找到前一个顶（底分型）
                    frame_index_2 = frame_1.pre_frame
                    assert frame_index_2 is None or frame_table[frame_index_2].frame_type == (
                        FrameType.top if is_top else FrameType.bottom)

                    if frame_index_2 is not None and (
                            (is_top and thigh[index - 1] >= thigh[frame_table[frame_index_2].data_index - 1]) or
                            (is_bottom and tlow[index - 1] <= tlow[frame_table[frame_index_2].data_index - 1])):
                        # 如果失败的顶(底)比前一个顶高(底低)，修正前一个顶(底)

                        frame_index_3 = frame_table[frame_index_2].pre_frame
                        assert frame_index_3 is None or frame_table[frame_index_3].frame_type == (
                            FrameType.bottom if is_top else FrameType.top)

                        if (is_top and frame_index_3 is not None and tlow[frame_1.data_index - 1] < tlow[
                            frame_table[frame_index_3].data_index - 1]) or \
                                (is_bottom and frame_index_3 is not None and thigh[frame_1.data_index - 1] > thigh[
                                    frame_table[frame_index_3].data_index - 1]):
                            # 把前顶(底)换成自己的时候，发现前底低(顶高)于前前底(顶)，这是不允许的
                            # 把前顶（底）和前前底（顶）都删掉，保留前底（顶），认为当前失败
                            frame_table[frame_index_2].next_replace_frame = len(frame_table) + 1
                            frame_table[frame_index_2].next_frame = len(frame_table)
                            frame_table[frame_index_3].next_replace_frame = len(frame_table) + 1
                            frame_table[frame_index_3].next_frame = len(frame_table)
                            # 把前底（顶）也删掉，因为它身上有失败的结构。然后再从新加一次前底（顶）
                            frame_table[frame_index_1].next_replace_frame = len(frame_table) + 1
                            frame_table[frame_index_1].next_frame = len(frame_table)
                            # 重新添加一次前底（顶）作为新底（顶）。因为这个线段向前看到的线段和中枢有改变，只有从新添加一次后面的程序才会更新这些信息。
                            frame = Frame(frame_1.frame_type, frame_1.data_index)
                            frame.pre_frame = frame_table[frame_index_3].pre_frame
                            if frame.pre_frame is not None:
                                frame_table[frame.pre_frame].next_frame = len(frame_table)
                            frame_table.append(frame)
                            # 标记一下失败的顶（底），以便后面做次低（高）点成笔
                            loss_frame = Frame(FrameType.top if is_top else FrameType.bottom, index)
                            loss_frame.next_replace_frame = len(frame_table)
                            loss_frame.pre_frame = len(frame_table) - 1
                            frame_table.append(loss_frame)
                            # _process_order(close, thigh, tlow, is_inclusion, index + 1, order_list, pre_graph_id)
                        else:
                            # 删掉前底(顶)
                            frame_1.next_replace_frame = len(frame_table)
                            frame_1.next_frame = len(frame_table)
                            # 删掉前顶(底)
                            frame_table[frame_index_2].next_replace_frame = len(frame_table)
                            frame_table[frame_index_2].next_frame = len(frame_table)
                            frame = Frame(FrameType.top if is_top else FrameType.bottom, index)
                            frame.pre_frame = frame_table[frame_index_2].pre_frame
                            if frame.pre_frame is not None:
                                frame_table[frame.pre_frame].next_frame = len(frame_table)
                            frame_table.append(frame)
                            # _process_order(close, thigh, tlow, is_inclusion, index + 1, order_list)
                    else:
                        # 否则继续
                        # 标记一下失败的顶（底），以便后面做次低（高）点成笔
                        loss_frame = Frame(FrameType.top if is_top else FrameType.bottom, index)
                        loss_frame.next_replace_frame = len(frame_table)
                        loss_frame.pre_frame = frame_index_1
                        frame_table.append(loss_frame)
                else:
                    pre_loss_index = None
                    pre_loss_frame = None
                    for i in range(len(frame_table) - 1, frame_index_1, -1):
                        if frame_table[i].next_replace_frame is not None and frame_table[i].frame_type == (
                        FrameType.top if is_top else FrameType.bottom):
                            pre_loss_index = frame_table[i].data_index
                            pre_loss_frame = i
                            break
                    if pre_loss_index:
                        # 如果之前有失败的驻顶(底)
                        # 之前失败的分型是因为多短所以失败
                        pre_k_cnt = 0
                        for k in range(frame_1.data_index, pre_loss_index - 1):
                            if not is_inclusion[k]:
                                pre_k_cnt += 1
                        if (is_top and thigh[index - 1] > thigh[pre_loss_index - 1]) or \
                                (is_bottom and tlow[index - 1] < tlow[pre_loss_index - 1]):
                            # 如果不是次高顶(次低底)或者与上个分型之间没有出现停顿
                            if (is_top and close[index - 1] <= thigh[pre_loss_index - 1]) or \
                                    (is_bottom and close[index - 1] >= tlow[
                                        pre_loss_index - 1]) or frame_stop_index_1 is None:
                                # 如果收盘没有击穿之前失败的分型，就是打横，打横不画笔
                                loss_frame = Frame(FrameType.top if is_top else FrameType.bottom, index)
                                loss_frame.next_replace_frame = len(frame_table)
                                loss_frame.pre_frame = frame_table[pre_loss_frame].pre_frame
                                frame_table.append(loss_frame)
                            # elif pre_k_cnt >= 2:
                            else:
                                # 如果不是打横，驻顶(底)成功，继续找底(顶)或换顶(底)
                                frame = Frame(FrameType.top if is_top else FrameType.bottom, index)
                                frame.pre_frame = frame_table[pre_loss_frame].pre_frame
                                if frame.pre_frame is not None:
                                    frame_table[frame.pre_frame].next_frame = len(frame_table)
                                frame_table.append(frame)
                        elif (pre_k_cnt == 2 and frame_stop_index_1 is not None) and \
                                ((is_top and (tlow[index - 2] - thigh[pre_loss_index - 1]) / (
                                        tlow[frame_1.data_index - 1] - thigh[pre_loss_index - 1]) < 0.5) or
                                 (is_bottom and (thigh[index - 2] - tlow[pre_loss_index - 1]) / (
                                         thigh[frame_1.data_index - 1] - tlow[pre_loss_index - 1]) < 0.5)):
                            # 如果之前驻顶(底)失败但是没有和前分型公用k线，现在重新驻顶(底)前一天下(上)影线的回探没有之前最高点和最低点的50%，于是次高点成顶
                            frame = Frame(FrameType.top if is_top else FrameType.bottom, index)
                            frame.pre_frame = frame_table[pre_loss_frame].pre_frame
                            if frame.pre_frame is not None:
                                frame_table[frame.pre_frame].next_frame = len(frame_table)
                            frame_table.append(frame)
                    else:
                        if frame_stop_index_1 is not None:
                            # 驻顶(底)成功，继续找底(顶)或换顶(底)
                            frame = Frame(FrameType.top if is_top else FrameType.bottom, index)
                            frame.pre_frame = frame_index_1
                            if frame.pre_frame is not None:
                                frame_table[frame.pre_frame].next_frame = len(frame_table)
                            frame_table.append(frame)
                        else:
                            # 两个分型之间没有停顿是不允许的，于是记录失败的驻顶（底）
                            loss_frame = Frame(FrameType.top if is_top else FrameType.bottom, index)
                            loss_frame.next_replace_frame = len(frame_table)
                            loss_frame.pre_frame = frame_index_1
                            frame_table.append(loss_frame)


# 尝试加入顶底分型停顿
def process_order_stop(frame_table, open, high, low, close, index):
    # 看之前是顶分型还是底分型
    frame_index_1 = None
    for i in range(len(frame_table) - 1, -1, -1):
        if (frame_table[i].frame_type == FrameType.top or frame_table[i].frame_type == FrameType.bottom) and \
                frame_table[i].next_replace_frame is None:
            frame_index_1 = i
            break
        elif frame_table[i].frame_type == FrameType.top_delay or frame_table[i].frame_type == FrameType.bottom_delay:
            return

    if frame_index_1 is not None:
        frame_1 = frame_table[frame_index_1]
        index_1 = frame_1.data_index
        if frame_1.frame_type == FrameType.top and open[index] > close[index] and close[index] < low[index_1]:
            frame = Frame(FrameType.top_delay, index)
            frame.pre_frame = frame_index_1
            frame_table[frame_index_1].next_stop_frame = len(frame_table)
            frame_table.append(frame)
        elif frame_1.frame_type == FrameType.bottom and open[index] < close[index] and close[index] > high[index_1]:
            frame = Frame(FrameType.bottom_delay, index)
            frame.pre_frame = frame_index_1
            frame_table[frame_index_1].next_stop_frame = len(frame_table)
            frame_table.append(frame)


# 波动相对于上一帧超过2个atr，证明可能形成趋势，需要记录这些点
def process_trend(frame_table, atr, close, index):
    # 找到上个有可能就行买卖操作的帧
    pre_frame_index = len(frame_table) - 1
    while pre_frame_index >= 0 and (frame_table[pre_frame_index].frame_type == FrameType.top or frame_table[
        pre_frame_index].frame_type == FrameType.bottom):
        pre_frame_index -= 1
    if pre_frame_index < 0 or frame_table[pre_frame_index].pre_frame is None:
        return

    pre_index = frame_table[pre_frame_index].data_index
    if abs(close[index] - close[pre_index]) < (atr[index] + atr[pre_index]):
        frame_table.append(Frame(FrameType.go_down if close[index] < close[pre_index] else FrameType.go_up, index))
        frame_table[-1].pre_frame = frame_table[pre_frame_index].pre_frame


def process_frame(data):
    frame_table = []
    atr, thigh, tlow, open, high, low, close, is_inclusion = data['atr'], data['thigh'], data['tlow'], data['open'], data['high'], data['low'], data['close'], data['is_inclusion']
    for i in range(2, len(data)):
        cur_frame_cnt = len(frame_table)
        # 将顶底分型作为关键帧
        process_order(frame_table, thigh, tlow, close, is_inclusion, i)
        if cur_frame_cnt == len(frame_table):
            # 如果没有新的顶底分型加入，就尝试加入顶底分型停顿
            process_order_stop(frame_table, open, high, low, close, i)
        if cur_frame_cnt == len(frame_table):
            process_trend(frame_table, atr, close, i)

    return frame_table
