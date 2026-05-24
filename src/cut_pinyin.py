import os.path

intact_pinyin_path = os.path.join(os.path.dirname(__file__), "data/intact_pinyin.txt")


# 加载完整拼音对应的拼音表 data/intact_pinyin.txt, 共 416 个
intact_pinyin_set = set()
with open(intact_pinyin_path, "r", encoding="utf-8") as f:
    intact_pinyin_set = set(s for s in f.read().split("\n"))

# 生成带残缺部分的拼音, 例如 'ruan' 对应的 'r', 'ru' 和 'rua', 共 504 个, 对应的拼音表为 data/all_pinyin.txt
all_pinyin_set = set(s[:i] for s in intact_pinyin_set for i in range(1, len(s) + 1))

DEFAULT_FUZZY_RULES = {
    ("z", "zh"): False,
    ("c", "ch"): False,
    ("s", "sh"): False,
    ("g", "k"): False,
    ("h", "f"): False,
    ("n", "l"): False,
    ("r", "l"): False,
    ("an", "ang"): False,
    ("en", "eng"): False,
    ("in", "ing"): False,
    ("an", "ai"): False,
    ("eng", "ong"): False,
    ("ian", "iang"): False,
    ("on", "ong"): False,
    ("uan", "uang"): False,
    ("un", "ong"): False,
    ("un", "iong"): False,
    ("hui", "fei"): False,
    ("huang", "wang"): False,
}

# 用于保存动态规划答案的字典
intact_cut_pinyin_ans = {}
all_cut_pinyin_ans = {}


# 动态规划判断进行拼音划分
def cut_pinyin(pinyin: str, is_intact=False, is_break=True):
    """
    进行拼音划分, 返回拼音划分结果列表
    pinyin: 待划分的拼音, 并且是无空格字符串, 例如 `kongjian`
    is_intact: 拼音是否需要完整匹配, 默认为 False, 可以使用残缺部分的拼音进行分词
    is_break: 是否开启分隔符, 开启后可以使用 ' 进行分割, 例如 `kong'jian`

    return: 拼音划分结果列表, 例如 `cut_pinyin('kongjian', True)` 会返回 `[('kong', 'jian'), ('kong', 'ji', 'an')]`
    """
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
    if is_break and "'" in pinyin:
        pinyins = pinyin.split("'")
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
    """
    使用最长前缀优先的贪心策略进行拼音划分.
    每一步都选择当前位置能匹配到的最长拼音前缀.

    pinyin: 待划分的拼音
    is_intact: 是否要求每个切分片段都为完整拼音
    is_break: 是否支持使用 ' 作为显式分隔符

    return: 成功时返回仅包含一个划分结果的列表, 失败时返回空列表.
    """
    pinyin_set = intact_pinyin_set if is_intact else all_pinyin_set

    if is_break and "'" in pinyin:
        parts = pinyin.split("'")
        ans = []
        for part in parts:
            cut = cut_pinyin_greedy(part, is_intact, False)
            if cut:
                ans.extend(cut[0])
                continue
            # 显式分隔出的片段允许原样保留, 其余片段继续贪心切分.
            ans.append(part)
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


def _find_longest_prefix(pinyin: str, pinyin_set):
    for end in range(len(pinyin), 0, -1):
        if pinyin[:end] in pinyin_set:
            return pinyin[:end]
    return None


def _swap_adjacent(s: str, index: int):
    return s[:index] + s[index + 1] + s[index] + s[index + 2 :]


def _correct_first_syllable_by_swap(pinyin: str):
    partial = _find_longest_prefix(pinyin, all_pinyin_set)
    if partial is None or len(partial) >= len(pinyin):
        return None
    for end in range(len(pinyin), len(partial), -1):
        candidate = pinyin[:end]
        for index in range(0, len(candidate) - 1):
            corrected = _swap_adjacent(candidate, index)
            if corrected in intact_pinyin_set:
                return corrected, end
    return None


def _iter_fuzzy_variants(text: str, fuzzy_rules):
    for (source, target), enabled in fuzzy_rules.items():
        if not enabled:
            continue
        directions = ((source, target), (target, source))
        for old, new in directions:
            start = 0
            while True:
                pos = text.find(old, start)
                if pos == -1:
                    break
                yield text[:pos] + new + text[pos + len(old) :]
                start = pos + 1


def _apply_fuzzy_rules_globally(pinyin: str, fuzzy_rules):
    changed = pinyin
    for (source, target), enabled in fuzzy_rules.items():
        if not enabled:
            continue
        if source in changed:
            changed = changed.replace(source, target)
        elif target in changed:
            changed = changed.replace(target, source)
    return changed


def cut_pinyin_by_mode(pinyin: str, mode="greedy", fuzzy_rules=None, is_break=True):
    """
    按照指定模式进行拼音切分.

    mode:
    - 'greedy': 直接使用贪心策略切分, 允许残缺尾部
    - 'correction': 优先完整拼音; 若首段不完整则尝试相邻字母交换纠错; 失败时回退到残缺贪心切分
    - 'fuzzy': 返回原始贪心结果, 并额外返回整串应用模糊规则后的贪心结果

    fuzzy_rules:
    - 字典格式为 {(source, target): bool}
    - 仅在 mode='fuzzy' 时使用

    return:
    - 成功时返回 tuple 列表
    - 失败时返回空列表
    """
    if mode not in {"greedy", "correction", "fuzzy"}:
        raise ValueError("mode must be one of: 'greedy', 'correction', 'fuzzy'")
    if fuzzy_rules is None:
        fuzzy_rules = DEFAULT_FUZZY_RULES

    if is_break and "'" in pinyin:
        parts = pinyin.split("'")
        ans = []
        for part in parts:
            cut = cut_pinyin_by_mode(
                part, mode=mode, fuzzy_rules=fuzzy_rules, is_break=False
            )
            if cut:
                ans.extend(cut[0])
                continue
            if mode in {"greedy", "correction"}:
                # 显式分隔出的片段允许原样保留, 其余片段继续做纠错.
                ans.append(part)
                continue
            return []
        return [tuple(ans)]

    def _cut_recursive(rest: str):
        if not rest:
            return [[]]

        first = _find_longest_prefix(rest, all_pinyin_set)
        if first is None:
            return []

        if mode == "greedy":
            tails = _cut_recursive(rest[len(first) :])
            return [[first] + tail for tail in tails]

        if first in intact_pinyin_set:
            tails = _cut_recursive(rest[len(first) :])
            if tails:
                return [[first] + tail for tail in tails]

        correction = _correct_first_syllable_by_swap(rest)
        if correction is not None:
            corrected, consumed = correction
            tails = _cut_recursive(rest[consumed:])
            if tails:
                return [[corrected] + tail for tail in tails]

        tails = _cut_recursive(rest[len(first) :])
        if tails:
            return [[first] + tail for tail in tails]

        return []

    if mode == "fuzzy":
        ans = []
        base = cut_pinyin_greedy(pinyin, is_intact=False, is_break=is_break)
        if base:
            ans.extend(base)
        fuzzy_pinyin = _apply_fuzzy_rules_globally(pinyin, fuzzy_rules)
        if fuzzy_pinyin != pinyin:
            fuzzy_cut = cut_pinyin_greedy(
                fuzzy_pinyin, is_intact=False, is_break=is_break
            )
            if fuzzy_cut and fuzzy_cut[0] not in ans:
                ans.extend(fuzzy_cut)
        return ans

    ans = _cut_recursive(pinyin)
    return [tuple(item) for item in ans]


def cut_pinyin_with_error_correction(pinyin: str):
    """
    纠错匹配, 从第二个字母开始, 依次交换两个连续字母并进行*完整划分*.
    如果完整划分返回非空列表, 即匹配成功, 并加入到返回字典中.
    pinyin: 待纠错划分的拼音

    return: 返回字典, 字典的 key 为纠错后的拼音序列, value 为匹配成功的划分结果.
            并且会包含一个 key = 'all' 的项, 包括了所有 value.
    """
    ans = {}
    for i in range(1, len(pinyin) - 1):
        # 避免交换分词符
        if pinyin[i - 1] == "'" or pinyin[i] == "'" or pinyin[i + 1] == "'":
            continue
        key = pinyin[:i] + pinyin[i + 1] + pinyin[i] + pinyin[i + 2 :]
        value = cut_pinyin(key, is_intact=True)
        if value:
            ans[key] = value
    ans["all"] = [p for t in ans.values() for p in t]
    return ans


def cut_pinyin_with_strategy(pinyin: str):
    """
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
    """
    ans = {
        "intact": cut_pinyin(pinyin, is_intact=True),
        "intact_tail": (
            []
            if pinyin[-1] not in all_pinyin_set
            else [t + (pinyin[-1],) for t in cut_pinyin(pinyin[:-1], is_intact=True)]
        ),
        "error_correction": cut_pinyin_with_error_correction(pinyin)["all"],
        "error_correction_tail": (
            []
            if pinyin[-1] not in all_pinyin_set
            else [
                t + (pinyin[-1],)
                for t in cut_pinyin_with_error_correction(pinyin[:-1])["all"]
            ]
        ),
        "greedy": cut_pinyin_greedy(pinyin, is_intact=False),
        "fuzzy": cut_pinyin(pinyin, is_intact=False),
        "combine": [],
    }
    ans["combine"] = set(
        ans["intact"]
        + ans["intact_tail"]
        + ans["error_correction"]
        + ans["error_correction_tail"]
        + ans["greedy"]
        + ans["fuzzy"]
    )
    return ans


def normlize_pinyin(pinyin: str):
    """
    规范化拼音
    将所有 ue 转化为 ve
    """
    return pinyin.replace("ue", "ve", -1)


if __name__ == "__main__":
    fuzzy_rules = DEFAULT_FUZZY_RULES.copy()
    fuzzy_rules[("z", "zh")] = True
    fuzzy_rules[("hui", "fei")] = True

    # print(cut_pinyin('kongjian', True))
    assert cut_pinyin("kongjian", True) == [("kong", "jian"), ("kong", "ji", "an")]
    # print(cut_pinyin('zhang\'an\'gai', True))
    assert cut_pinyin("zhang'an'gai", True) == [("zhang", "an", "gai")]

    # print(cut_pinyin_with_error_correction('tain'))
    assert cut_pinyin_with_error_correction("tain") == {
        "tian": [("tian",), ("ti", "an")],
        "tani": [("ta", "ni")],
        "all": [("tian",), ("ti", "an"), ("ta", "ni")],
    }
    # print(cut_pinyin_with_strategy('kauil')['error_correction_tail'])
    assert cut_pinyin_with_strategy("kauil")["error_correction_tail"] == [
        ("kuai", "l"),
        ("ku", "ai", "l"),
    ]
    assert cut_pinyin_greedy("xianren", True) == [("xian", "ren")]
    assert cut_pinyin_with_strategy("kuail")["greedy"] == [("kuai", "l")]
    assert cut_pinyin_by_mode("kuail") == [("kuai", "l")]
    assert cut_pinyin_by_mode("jainmian", mode="correction") == [("jian", "mian")]
    assert cut_pinyin_by_mode("ja'i'mnig", mode="correction") == [
        ("j", "a", "i", "ming")
    ]
    assert cut_pinyin_by_mode("zzzq", mode="correction") == [("z", "z", "z", "q")]
    assert cut_pinyin_by_mode("hhhh", mode="correction") == [("h", "h", "h", "h")]
    assert cut_pinyin_by_mode("ja'i'mnig", mode="greedy") == [
        ("j", "a", "i", "m", "ni", "g")
    ]
    assert cut_pinyin_by_mode("zan", mode="fuzzy", fuzzy_rules=fuzzy_rules) == [
        ("zan",),
        ("zhan",),
    ]
    assert cut_pinyin_by_mode("zanzan", mode="fuzzy", fuzzy_rules=fuzzy_rules) == [
        ("zan", "zan"),
        ("zhan", "zhan"),
    ]
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
    res = cut_pinyin_greedy("jianxi", False)
    print(res)
    res = cut_pinyin_greedy("jianx", False)
    print(res)
    res = cut_pinyin_greedy("aa", False)
    print(res)
    res = cut_pinyin_greedy("jain", False)
    print(res)
    res = cut_pinyin_greedy("xiaojj", False)
    print(res)
    res = cut_pinyin_greedy("tain", False)
    print(res)
    print("#" * 40)
    print("greedy mode:")
    res = cut_pinyin_by_mode("zanzan", mode="greedy")  # zan zan
    print(res)
    res = cut_pinyin_by_mode("ja'i'mnig", mode="greedy")  # j a i m ni g
    print(res)
    res = cut_pinyin_by_mode("jaimnig", mode="greedy")  # j ai m ni g
    print(res)
    print("correction mode:")  # 这个是日常会使用的模式
    res = cut_pinyin_by_mode("jainmian", mode="correction")  # jian mian
    print(res)
    res = cut_pinyin_by_mode("jainshi", mode="correction")  # jian shi
    print(res)
    res = cut_pinyin_by_mode("jaimnig", mode="correction")  # jia ming
    print(res)
    res = cut_pinyin_by_mode("jai'mnig", mode="correction")  # jia ming
    print(res)
    res = cut_pinyin_by_mode("ja'i'mnig", mode="correction")  # j a i ming
    print(res)
    res = cut_pinyin_by_mode("xi'an", mode="correction")  # xi an
    print(res)
    res = cut_pinyin_by_mode("xian", mode="correction")  # xian
    print(res)
    res = cut_pinyin_by_mode("xianyang", mode="correction")  # xian
    print(res)
    res = cut_pinyin_by_mode("xi'anyang", mode="correction")  # xian
    print(res)
    res = cut_pinyin_by_mode("zzzq", mode="correction")  # z z z q
    print(res)
    res = cut_pinyin_by_mode("hhhh", mode="correction")  # h h h h
    print(res)
    res = cut_pinyin_by_mode("nimen", mode="correction")  # ni men
    print(res)
    res = cut_pinyin_by_mode("nime", mode="correction")  # ni me
    print(res)
    res = cut_pinyin_by_mode("nim", mode="correction")  # ni m
    print(res)
    print("fuzzy mode:")
    res = cut_pinyin_by_mode(
        "zan", mode="fuzzy", fuzzy_rules=fuzzy_rules
    )  # zan or zhan
    print(res)
    res = cut_pinyin_by_mode(
        "zandui", mode="fuzzy", fuzzy_rules=fuzzy_rules
    )  # zan dui or zhan dui
    print(res)
    res = cut_pinyin_by_mode(
        "zanzan", mode="fuzzy", fuzzy_rules=fuzzy_rules
    )  # zan zan or zhan zhan
    print(res)
    res = cut_pinyin_by_mode(
        "huiji", mode="fuzzy", fuzzy_rules=fuzzy_rules
    )  # hui ji or fei ji
    print(res)
