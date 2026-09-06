# pinyin_python

<!-- badges:start -->
[![CI](https://img.shields.io/github/actions/workflow/status/metasequoiaime/pinyin_python/ci.yml?branch=main&label=CI)](https://github.com/metasequoiaime/pinyin_python/actions/workflows/ci.yml)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/metasequoiaime/pinyin_python/codeql.yml?branch=main&label=CodeQL)](https://github.com/metasequoiaime/pinyin_python/actions/workflows/codeql.yml)
[![License](https://img.shields.io/github/license/metasequoiaime/pinyin_python)](LICENSE)
[![Stars](https://img.shields.io/github/stars/metasequoiaime/pinyin_python?style=flat)](https://github.com/metasequoiaime/pinyin_python/stargazers)
<!-- badges:end -->

拼音切分与候选查询的 Python 早期原型。

这是水杉输入法最早的探索性实现，用来验证全拼串怎么切分成音节、以及候选怎么查。`src/cut_pinyin.py` 是切分算法，`src/query_words.py` 是候选查询，`src/cut_pinyin.md` 记录了切分的推导过程。

**这个仓库已经被取代，不再开发。** 正式实现在 [MSIME-Engine](https://github.com/metasequoiaime/MSIME-Engine) 的 `quanpin/` 与 `core/`，是 C++ 写的，三个平台的前端都用它。这里保留下来是因为切分那部分的推导过程对理解引擎仍然有参考价值。

要参与输入法开发请到 [MSIME-Engine](https://github.com/metasequoiaime/MSIME-Engine) 或各平台前端仓库。

<!-- star-history:start -->
## Star History

<a href="https://star-history.com/#metasequoiaime/pinyin_python&Date">
  <img src="https://api.star-history.com/svg?repos=metasequoiaime/pinyin_python&type=Date" alt="Star History Chart" width="600">
</a>
<!-- star-history:end -->
