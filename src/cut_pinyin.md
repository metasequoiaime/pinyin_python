## 全拼拼音分词

一共有三种模式。

- 默认不开启拼音纠正、模糊拼音 => 直接用贪心策略
- 简单的纠错模式 => 先用贪心策略分一下词，如果分词后的第一个部分都凑不出一个完整的拼音，就对其就行纠错，纠错完第一个完整部分后，对剩余部分作同样的递归处理。
    - 这里的纠错方案要这样：就是两两交换看交换之后能不能组成一个合格的拼音，如果可以了，就直接返回这个拼音，就不继续操作了。比如，jain 的纠错可以有三种选择，ajin, jian, jani，其中，到了 jian 这一步的时候，就可以停止并且返回 jian 了。
- 模糊拼音有这么多，要看用户是否开启。可以传一个字典进去。
    - z = zh, off
    - c = ch, off
    - s = sh, off
    - g = k, off
    - h = f, off
    - n = l, off
    - r = l, off
    - an = ang, off
    - en = eng, off
    - in = ing, off
    - an = ai, off
    - eng = ong, off
    - ian = iang, off
    - on = ong, off
    - uan = uang, off
    - un = ong, off
    - un = iong, off
    - hui = fei, off
    - huang = wang, off