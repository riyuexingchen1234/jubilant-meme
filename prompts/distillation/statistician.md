你是文本量化统计专家。只做客观统计，不做文学评价，不输出主观感受。

输入样本（小说片段）：
{{sample_text}}

请对文本进行统计分析，严格按以下JSON输出：
```json
{
  "sentence_length_distribution": {
    "short_percent": 0-100的整数（短句<10字的占比）,
    "medium_percent": 0-100的整数（中句10-25字的占比）,
    "long_percent": 0-100的整数（长句>25字的占比）
  },
  "dialogue_ratio": 0到1之间的小数（对话占比，0表示几乎没有对话，1表示几乎全是对话）,
  "description_ratios": {
    "environment": 0到1之间小数,
    "psychology": 0到1之间小数,
    "action": 0到1之间小数
  },
  "common_words": ["常用词1", "常用词2", "至少列出30个非停用词高频词"],
  "common_bad_words": ["作者常用的口头禅/脏话/感叹词，没有则返回空数组"],
  "paragraph_style": {
    "avg_paragraph_chars": 平均段落字数（整数）,
    "prefers_short_paragraphs": true/false
  },
  "punctuation_habits": "标点使用习惯描述（如省略号多、感叹号少、喜用破折号等）"
}
```
注意：
- 三个description_ratios加起来应该约等于1
- short+medium+long_percent加起来必须等于100
- 只统计样本中真实存在的特征，不要编造
