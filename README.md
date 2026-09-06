# pinyin_python

拼音切分与候选查询的 Python 早期原型。

**这个仓库已被取代，不再用于水杉输入法的开发。** 它保留下来是作为历史记录：拼音切分的思路最早是在这里推的，之后才成为产品代码。

现在的实现在 [MSIME-Engine](https://github.com/metasequoiaime/MSIME-Engine)——跨平台组词引擎、共享协议、词库生产与辅助码都在那里，Windows、Apple、Linux 三个前端都以 submodule 的形式固定引用它。要改切分规则、查询逻辑或词库，去 MSIME-Engine，不要改这里。

本仓库内容：

- `src/cut_pinyin.py` 与 `src/cut_pinyin.md` — 拼音切分的原型实现与当时的推导笔记
- `src/query_words.py` — 候选查询原型
- `src/calc_single_letter_word.py` — 单字母词的统计脚本
- `main.py` — 未使用的脚手架入口

这些代码不参与任何产品构建，也不接受功能性改动。
