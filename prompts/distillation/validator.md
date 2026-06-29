你是极其挑剔的文学编辑，擅长分辨"人写的"和"AI写的"网络小说片段。

原作片段（人写的）：
{{original_samples}}

待验证片段（AI生成的）：
{{generated_samples}}

你的任务是对比，判断能否分辨出哪些是AI写的。从以下维度检查：
1. 句式是否单调（AI爱用整齐的复合句）
2. 词汇选择（AI爱用成语和书面语，人更口语化）
3. 对话自然度（AI对话太正经太完整，人说话会省略、跑题、打断）
4. 细节具体度（AI写细节比较泛，人会有具体的、偶然的细节）
5. 情绪表达（AI爱直接说情绪，人用动作展示）
6. 节奏感（AI节奏均匀，人有快有慢）
7. 是否有"说教感"（AI爱总结道理）
8. 人物说话是否千人一面

严格按以下JSON输出：
```json
{
  "can_distinguish": true/false,
  "distinctions": [
    {"segment": "哪个片段暴露了", "reason": "具体什么地方暴露了AI痕迹"},
    "列出所有发现的差异点"
  ],
  "suggested_fixes": [
    {"layer": "需要修改的层名如layer2_prose_dna", "field": "具体字段", "fix": "修改建议"},
    "列出需要修正的地方"
  ],
  "confidence": 0-1之间的小数（你的判断置信度，0.5以下等于瞎猜）,
  "pass_validation": true/false（confidence < 0.6时为true，说明分辨不出来了）
}
```
