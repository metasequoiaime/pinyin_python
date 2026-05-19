import os.path

intact_pinyin_path = os.path.join(os.path.dirname(__file__), 'data/intact_pinyin.txt')


# 加载完整拼音对应的拼音表 data/intact_pinyin.txt, 共 416 个
intact_pinyin_set = set()
with open(intact_pinyin_path, 'r', encoding='utf-8') as f:
    intact_pinyin_set = set(s for s in f.read().split('\n'))

# 生成带残缺部分的拼音, 例如 'ruan' 对应的 'r', 'ru' 和 'rua', 共 504 个, 对应的拼音表为 data/all_pinyin.txt
all_pinyin_set = set(s[:i] for s in intact_pinyin_set for i in range(1, len(s) + 1))

# 用于保存动态规划答案的字典
intact_cut_pinyin_ans = {}
all_cut_pinyin_ans = {}
# 动态规划判断进行拼音划分
def cut_pinyin(pinyin: str, is_intact=False, is_break=True):
    '''
    进行拼音划分, 返回拼音划分结果列表
    pinyin: 待划分的拼音, 并且是无空格字符串, 例如 `kongjian`
    is_intact: 拼音是否需要完整匹配, 默认为 False, 可以使用残缺部分的拼音进行分词
    is_break: 是否开启分隔符, 开启后可以使用 ' 进行分割, 例如 `kong'jian`
    
    return: 拼音划分结果列表, 例如 `cut_pinyin('kongjian', True)` 会返回 `[('kong', 'jian'), ('kong', 'ji', 'an')]`
    '''
    if is_intact:
        pinyin_set = intact_pinyin_set
        ans_dict = intact_cut_pinyin_ans    
    else:
        pinyin_set = all_pinyin_set
        ans_dict = all_cut_pinyin_ans
    # 如果保存有, 直接返回保存结果
    if pinyin in ans_dict:
        return ans_dict[pinyin]
    # 如果 is_break, 就进行分割
    if is_break and '\'' in pinyin:
        pinyins = pinyin.split('\'')
        components = [cut_pinyin(p, is_intact, False) for p in pinyins]
        ans = components[0]
        for i in range(1, len(components)):
            ans = [p1 + p2 for p1 in ans for p2 in components[i]]
        return ans
    # 如果没有, 递归地动态规划生成
    ans = [] if pinyin not in pinyin_set else [(pinyin,)]
    for i in range(1, len(pinyin)):
        # 进行划分 pinyin[:i], 如果是正确拼音, 就继续动态规划
        if pinyin[:i] in pinyin_set:
            appendices = cut_pinyin(pinyin[i:], is_intact, is_break=False)
            for appendix in appendices:
                ans.append((pinyin[:i],) + appendix)
    ans_dict[pinyin] = ans
    return ans

def cut_pinyin_greedy(pinyin: str, is_intact=False, is_break=True):
    '''
    使用最长前缀优先的贪心策略进行拼音划分.
    每一步都选择当前位置能匹配到的最长拼音前缀.

    pinyin: 待划分的拼音
    is_intact: 是否要求每个切分片段都为完整拼音
    is_break: 是否支持使用 ' 作为显式分隔符

    return: 成功时返回仅包含一个划分结果的列表, 失败时返回空列表.
    '''
    pinyin_set = intact_pinyin_set if is_intact else all_pinyin_set

    if is_break and '\'' in pinyin:
        parts = pinyin.split('\'')
        ans = []
        for part in parts:
            cut = cut_pinyin_greedy(part, is_intact, False)
            if not cut:
                return []
            ans.extend(cut[0])
        return [tuple(ans)]

    ans = []
    index = 0
    while index < len(pinyin):
        matched = None
        for end in range(len(pinyin), index, -1):
            piece = pinyin[index:end]
            if piece in pinyin_set:
                matched = piece
                break
        if matched is None:
            return []
        ans.append(matched)
        index += len(matched)
    return [tuple(ans)]

def cut_pinyin_with_error_correction(pinyin: str):
    '''
    纠错匹配, 从第二个字母开始, 依次交换两个连续字母并进行*完整划分*.
    如果完整划分返回非空列表, 即匹配成功, 并加入到返回字典中.
    pinyin: 待纠错划分的拼音

    return: 返回字典, 字典的 key 为纠错后的拼音序列, value 为匹配成功的划分结果.
            并且会包含一个 key = 'all' 的项, 包括了所有 value.
    '''
    ans = {}
    for i in range(1, len(pinyin) - 1):
        # 避免交换分词符
        if pinyin[i-1] == '\'' or pinyin[i] == '\'' or pinyin[i + 1] == '\'':
            continue
        key = pinyin[:i] + pinyin[i + 1] + pinyin[i] + pinyin[i + 2:]
        value = cut_pinyin(key, is_intact=True)
        if value:
            ans[key] = value
    ans['all'] = [p for t in ans.values() for p in t]
    return ans

def cut_pinyin_with_strategy(pinyin: str):
    '''
    使用各种策略对拼音进行划分, 其中包括:
    1. 完整划分
    2. 去尾字母完整划分
    3. 纠错划分
    4. 去尾字母纠错划分
    5. 贪心划分
    6. 模糊划分
    7. 结果综合

    pinyin: 待划分的拼音

    return: {
        'intact': [...],
        'intact_tail': [...],
        'error_correction': [...],
        'error_correction_tail': [...],
        'greedy': [...],
        'fuzzy': [...]
        'combine': [...],
    }
    '''
    ans = {
        'intact': cut_pinyin(pinyin, is_intact=True),
        'intact_tail': [] if pinyin[-1] not in all_pinyin_set else [t + (pinyin[-1],) for t in cut_pinyin(pinyin[:-1], is_intact=True)],
        'error_correction': cut_pinyin_with_error_correction(pinyin)['all'],
        'error_correction_tail': [] if pinyin[-1] not in all_pinyin_set else [t + (pinyin[-1],) for t in cut_pinyin_with_error_correction(pinyin[:-1])['all']],
        'greedy': cut_pinyin_greedy(pinyin, is_intact=False),
        'fuzzy': cut_pinyin(pinyin, is_intact=False),
        'combine': [],
    }
    ans['combine'] = set(ans['intact'] + ans['intact_tail'] + ans['error_correction'] + ans['error_correction_tail'] + ans['greedy'] + ans['fuzzy'])
    return ans


def normlize_pinyin(pinyin: str):
    """
    规范化拼音
    将所有 ue 转化为 ve
    """
    return pinyin.replace('ue', 've', -1)


if __name__ == '__main__':
    # print(cut_pinyin('kongjian', True))
    assert cut_pinyin('kongjian', True) == [('kong', 'jian'), ('kong', 'ji', 'an')]
    # print(cut_pinyin('zhang\'an\'gai', True))
    assert cut_pinyin('zhang\'an\'gai', True) == [('zhang', 'an', 'gai')]
    
    # print(cut_pinyin_with_error_correction('tain'))
    assert cut_pinyin_with_error_correction('tain') == {'tian': [('tian',), ('ti', 'an')], 'tani': [('ta', 'ni')], 'all': [('tian',), ('ti', 'an'), ('ta', 'ni')]}
    # print(cut_pinyin_with_strategy('kauil')['error_correction_tail'])
    assert cut_pinyin_with_strategy('kauil')['error_correction_tail'] == [('kuai', 'l'), ('ku', 'ai', 'l')]
    assert cut_pinyin_greedy('xianren', True) == [('xian', 'ren')]
    assert cut_pinyin_with_strategy('kuail')['greedy'] == [('kuai', 'l')]
    res = cut_pinyin("kongjian", True)
    print(res)
    res = cut_pinyin("xian", True)
    print(res)
    res = cut_pinyin("kong'jian", True, True)
    print(res)
    res = cut_pinyin("kong'ji'an", True, True)
    print(res)
    res = cut_pinyin("xi'an", True, True)
    print(res)
    res = cut_pinyin_with_error_correction("tain")
    print(res)
    res = cut_pinyin_with_error_correction("jainmian")
    print(res)
    res = cut_pinyin("jainmian", True)
    print(res)
    res = cut_pinyin("kuail", True)
    print(res)
    res = cut_pinyin_greedy("kuail", False)
    print(res)
