"""
db path: C:\\Users\\SonnyCalcr\\EDisk\\CppCodes\\IMECodes\\MetasequoiaImeDict\\makecikudb\\quanpindb\\makedb\\multi_table_has_jp\\out\\quanpin_multi_tbl_has_jp.db

# sql statement to create a table
create_table_sql = '''
create table if not exists {} (
   "key" text, -- 全拼拼音
   "jp" text, -- 全拼简拼
   "value" text, -- 对应的汉字或者词组
   "weight" integer default 0 -- 权重
);
'''

# 表的名称：e.g. tbl_3_a means 三个汉字的词条，并且全拼拼音以 a 开头
# 一些查询的示例：
'''
select * from tbl_1_a;

select * from tbl_2_y;

select * from tbl_2_y where key = "yi'ge";

select * from tbl_2_y where key = "yi'ge" order by weight desc limit 8;
'''
"""

import sqlite3
from cut_pinyin import (
    cut_pinyin_greedy,
    cut_pinyin_by_mode,
    cut_pinyin,
)

# 数据库路径
DB_PATH = (
    r"C:\\Users\\SonnyCalcr\\EDisk\\CppCodes\\IMECodes\\MetasequoiaImeDict"
    r"\\makecikudb\\quanpindb\\makedb\\multi_table_has_jp"
    r"\\out\\quanpin_multi_tbl_has_jp.db"
)


def _build_table_name(segments: tuple[str, ...]) -> str:
    """
    根据分词结果构造表名，例如 ('ni', 'hao') -> tbl_2_n
    """
    n = len(segments)
    first_letter = segments[0][0]  # 第一个拼音段的首字母
    return f"tbl_{n}_{first_letter}"


def _segments_to_key(segments: tuple[str, ...]) -> str:
    """将分词结果拼接为数据库中的 key 格式，例如 ('ni', 'hao') -> "ni'hao" """
    return "'".join(segments)


def _segments_to_jp(segments: tuple[str, ...]) -> str:
    """将分词结果转换为简拼，例如 ('ni', 'hao') -> "nh"。"""
    return "".join(segment[0] for segment in segments if segment)


def _build_key_like_pattern(segments: tuple[str, ...]) -> str:
    """
    构造按分词段补全的 key 查询模式。

    规则：
    - 非最后一段：如果只有 1 个字母，则视为该段残缺，写成 `k%`
    - 最后一段：始终允许继续补全，写成 `segment%`

    例如：
    - ('ni', 'm') -> "ni'm%"
    - ('ni', 'me') -> "ni'me%"
    - ('k', 'wu', 'ya') -> "k%'wu'ya%"
    """
    parts = []
    last_index = len(segments) - 1
    for index, segment in enumerate(segments):
        if index == last_index:
            parts.append(f"{segment}%")
        elif len(segment) == 1:
            parts.append(f"{segment}%")
        else:
            parts.append(segment)
    return "'".join(parts)


def _is_pure_jp_input(segments: tuple[str, ...]) -> bool:
    """是否为纯简拼输入，例如 ('j', 'j', 'j')。"""
    return all(len(segment) == 1 for segment in segments)


def query_single_cut(
    conn: sqlite3.Connection,
    segments: tuple[str, ...],
    limit: int = 8,
) -> list[tuple[str, int]]:
    """
    对单个切分结果执行数据库查询。

    conn:     数据库连接
    segments: 一个切分结果，例如 ('ni', 'hao')
    limit:    返回的最大条数

    return: [(value, weight), ...] 按 weight 降序排列
    """
    table = _build_table_name(segments)
    key = _segments_to_key(segments)
    jp = _segments_to_jp(segments)
    key_like_pattern = _build_key_like_pattern(segments)

    try:
        exact_sql = (
            f'SELECT "value", "weight" FROM "{table}" '
            f'WHERE "key" = ? ORDER BY "weight" DESC LIMIT ?'
        )
        cursor = conn.execute(exact_sql, (key, limit))
        rows = cursor.fetchall()
        if rows:
            return [(row[0], row[1]) for row in rows]

        # 精确匹配为空时，退化为按分词段补全的 key 匹配。
        # 例如 ni'm 可以匹配 ni'ma、ni'men；
        # kwuya -> ('k', 'wu', 'ya') 时，会尝试 k%'wu'ya%。
        prefix_sql = (
            f'SELECT "value", "weight" FROM "{table}" '
            f'WHERE "key" LIKE ? ORDER BY "weight" DESC LIMIT ?'
        )
        cursor = conn.execute(prefix_sql, (key_like_pattern, limit))
        rows = cursor.fetchall()
        if rows:
            return [(row[0], row[1]) for row in rows]

        # 只有纯简拼输入才尝试 jp 查询。
        # 例如 jjj 可以匹配 jp = jjj 的三字词；
        # kewuya 这类已经是完整全拼的输入，不应回退到 jp。
        if not _is_pure_jp_input(segments):
            return []

        jp_exact_sql = (
            f'SELECT "value", "weight" FROM "{table}" '
            f'WHERE "jp" = ? ORDER BY "weight" DESC LIMIT ?'
        )
        cursor = conn.execute(jp_exact_sql, (jp, limit))
        rows = cursor.fetchall()
        if rows:
            return [(row[0], row[1]) for row in rows]

        return []

    except sqlite3.OperationalError:
        # 表不存在等情况
        return []


def query_words(
    pinyin: str,
    db_path: str = DB_PATH,
    mode: str = "greedy",
    limit: int = 8,
) -> dict:
    """
    对输入的拼音串进行分词，再到数据库中查询对应的汉字/词组。

    pinyin:  输入的拼音串，例如 "nihao" 或 "xi'an"
    db_path: 数据库文件路径
    mode:    分词模式，可选 'greedy'（贪心）、'correction'（纠错）、
             'fuzzy'（模糊音），默认 'greedy'
    limit:   每种切分返回的最大条数

    return: {
        'pinyin': 原始拼音,
        'mode': 使用的分词模式,
        'results': [
            {
                'segments': ('ni', 'hao'),  # 一种切分结果
                'key': "ni'hao",            # 数据库查询 key
                'table': 'tbl_2_n',         # 查询的表名
                'items': [('你好', 100), ('尼好', 50), ...],
            },
            ...
        ],
    }
    """
    # 1. 分词
    if mode == "greedy":
        cuts = cut_pinyin_greedy(pinyin, is_intact=False, is_break=True)
    elif mode == "correction":
        cuts = cut_pinyin_by_mode(pinyin, mode="correction", is_break=True)
    elif mode == "fuzzy":
        cuts = cut_pinyin_by_mode(pinyin, mode="fuzzy", is_break=True)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    if not cuts:
        return {"pinyin": pinyin, "mode": mode, "results": []}

    # 2. 去重（不同策略可能产生相同切分）
    seen = set()
    unique_cuts = []
    for seg in cuts:
        if seg not in seen:
            seen.add(seg)
            unique_cuts.append(seg)

    # 3. 对每种切分查询数据库
    results = []
    with sqlite3.connect(db_path) as conn:
        for segments in unique_cuts:
            items = query_single_cut(conn, segments, limit=limit)
            results.append(
                {
                    "segments": segments,
                    "key": _segments_to_key(segments),
                    "table": _build_table_name(segments),
                    "items": items,
                }
            )

    return {"pinyin": pinyin, "mode": mode, "results": results}


def query_words_flat(
    pinyin: str,
    db_path: str = DB_PATH,
    mode: str = "greedy",
    limit: int = 8,
) -> list[tuple[str, int]]:
    """
    简化版：直接返回所有 (汉字/词组, 权重) 的列表，按权重降序排列并去重。

    return: [(value, weight), ...]
    """
    result = query_words(pinyin, db_path, mode, limit)
    all_items = []
    seen = set()
    for r in result["results"]:
        for value, weight in r["items"]:
            if value not in seen:
                seen.add(value)
                all_items.append((value, weight))
    all_items.sort(key=lambda x: x[1], reverse=True)
    return all_items[:limit]


# ---------- 测试示例 ----------
if __name__ == "__main__":

    def print_query_demo(pinyin: str, mode: str = "greedy", flat: bool = False) -> None:
        """打印查询示例结果，便于集中展示不同模式。"""
        print("=" * 50)
        mode_label = {
            "greedy": "贪心模式",
            "correction": "纠错模式",
            "fuzzy": "模糊模式",
        }.get(mode, mode)
        print(f'查询 "{pinyin}"（{mode_label}）:')

        if flat:
            for value, weight in query_words_flat(pinyin, mode=mode):
                print(f"{value} ({weight})")
            return

        res = query_words(pinyin, mode=mode)
        for r in res["results"]:
            print(f"切分: {r['segments']} → 表 {r['table']}, key={r['key']}")
            for value, weight in r["items"]:
                print(f"{value} (权重: {weight})")
            if not r["items"]:
                print("(无结果)")

    # 示例 1：贪心模式查询 "nihao"
    print_query_demo("nihao")

    # 示例 2：简化接口
    print("=" * 50)
    print('简化查询 "nihao":')
    for value, weight in query_words_flat("nihao"):
        print(f"{value} ({weight})")

    # 示例 3：带分隔符
    print_query_demo("xi'an")

    # 示例 4：纠错模式
    print_query_demo("jain", mode="correction")

    # 示例 5：更多纠错模式示例
    print_query_demo("jainmian", mode="correction")
    print_query_demo("jainshi", mode="correction")
    print_query_demo("jaimnig", mode="correction")
    print_query_demo("jai'mnig", mode="correction")
    print_query_demo("ja'i'mnig", mode="correction")
    print_query_demo("nimen", mode="correction")
    print_query_demo("nime", mode="correction")
    print_query_demo("nim", mode="correction")
    print_query_demo("jjj", mode="correction")
    print_query_demo("n", mode="correction")
    print_query_demo("ni", mode="correction")
    print_query_demo("nim", mode="correction")
    print_query_demo("nime", mode="correction")
    print_query_demo("nimen", mode="correction")
    print_query_demo("k", mode="correction")
    print_query_demo("ke", mode="correction")
    print_query_demo("kew", mode="correction")
    print_query_demo("kewu", mode="correction")
    print_query_demo("kewuy", mode="correction")
    print_query_demo("kewuya", mode="correction")
    print_query_demo("kewuyou", mode="correction")
    # ni hao ma
    print_query_demo("n", mode="correction")
    print_query_demo("ni", mode="correction")
    print_query_demo("nih", mode="correction")
    print_query_demo("niha", mode="correction")
    print_query_demo("nihao", mode="correction")
    print_query_demo("nihaom", mode="correction")
    print_query_demo("nihaoma", mode="correction")
    # yi jin
    print_query_demo("y", mode="correction")
    print_query_demo("yi", mode="correction")
    print_query_demo("yij", mode="correction")
    print_query_demo("yiji", mode="correction")
    print_query_demo("yijin", mode="correction")
    print_query_demo("fjaksdjfl", mode="correction")
    # fja
    print_query_demo("fja", mode="correction")