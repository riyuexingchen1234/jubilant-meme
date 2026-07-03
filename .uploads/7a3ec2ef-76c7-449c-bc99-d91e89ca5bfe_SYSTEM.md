# 长篇小说创作系统 v5.1

## 架构概述
人在回路的多会话协作系统，由1个主控会话+3个长期工作会话+1个临时蒸馏会话组成，所有会话共享同一个Git仓库的`/workspace`目录。

### 会话分工
| 会话 | 类型 | 职责 | System Prompt |
|------|------|------|---------------|
| 主控会话 | 长期 | 和总编交互、流程调度、质量检查、文件管理 | `prompts/master.md` |
| 写稿会话 | 长期 | 选题、开书策划、写提纲、写正文、更新状态 | `prompts/writer.md` |
| 审稿会话 | 长期 | 独立第三方审稿、挑错、核对facts一致性 | `prompts/reviewer.md` |
| 调研会话 | 长期 | 热点调研、事实补全、来源验证 | `prompts/researcher.md` |
| 蒸馏会话 | 临时 | 开书前从作者样本蒸馏风格规则，做完即关 | `prompts/distiller.md` |

### 核心设计原则
1. **物理隔离防放水**：创作、审稿、调研完全独立会话，审稿永远看不到创作过程，只看文件
2. **写前必查facts**：写稿会话动笔前必须做场景事实检查，缺事实停下要调研，不许编
3. **审稿核对要有过程**：审稿必须逐维度核对并展示核对过程，泛泛说"没问题"视为不通过
4. **落盘才算数**：所有决策、事实、设定必须写入文件，对话里说的不算
5. **主控只调度不创作**：主控不写小说、不审稿，只派活、检查、传递
6. **所有硬事实有来源**：facts.md里的每条事实必须附来源，主控抽样验证

---

## 现实主义题材核心原则（所有会话必须遵守）
1. **真实性是生命线**：硬数字、硬流程、硬逻辑必须符合真实世界，不许为了戏剧冲突牺牲真实性
2. **证据链防造假**：所有新增硬事实必须有来源，附事实来源表，主控抽样验证
3. **人物行为符合身份**：老江湖有老江湖的反应，菜鸟有菜鸟的反应，不能为了剧情让人物做不符合身份的事
4. **facts.md是唯一真相来源**：所有硬事实以bible/facts.md为准，其他文件和facts矛盾必须打回

---

## 目录结构
```
/workspace/
├── SYSTEM.md                   # 本文件，系统总览
├── README.md                   # 用户使用手册（启动说明、工作流示例）
├── prompts/                    # 各会话System Prompt
│   ├── master.md
│   ├── writer.md
│   ├── reviewer.md
│   ├── researcher.md
│   ├── distiller.md
│   └── reference/              # 参考资料（题材市场地图等）
├── tools/                      # 检查脚本（纯标准库，无依赖）
│   ├── check_output.py         # 输出契约检查
│   ├── check_facts_consistency.py # facts一致性扫描
│   ├── check_ai_cliches.py     # AI套话检测
│   ├── text_stats.py           # 文本统计
│   └── epub_to_text.py         # epub转文本（蒸馏用）
├── authors/                    # 已蒸馏作者风格库
│   └── <author_slug>/
│       ├── layer0_redlines.md
│       ├── layer1_meta.md
│       ├── layer2_prose_dna.md
│       ├── layer3_characters.md
│       ├── layer4_structure.md
│       ├── layer5_antipatterns.md
│       ├── corrections.json
│       └── distillation_report.md
└── work/                       # 小说工作区
    ├── _research/              # 公共调研素材
    └── <novel_slug>/           # 每本小说一个目录
        ├── progress.md         # 项目进度（主控每次操作前后读写）
        ├── bible/              # 小说圣经（核心设定）
        │   ├── facts.md        # 事实数据表（最重要的文件）
        │   ├── world.md
        │   ├── characters/
        │   ├── style/          # 从authors复制过来的风格规则
        │   ├── character_state.md
        │   ├── foreshadow_map.md
        │   ├── timeline.md
        │   ├── plot_arcs.md
        │   └── corrections.json
        ├── batch_plans/        # 分批提纲
        ├── chapters/           # 正文
        └── reviews/            # 审稿意见
```

---

## 项目进度文件（progress.md）

每本小说目录下放一个`progress.md`，主控每次操作前读、操作后更新。格式：

```markdown
# 进度
- 当前阶段：选题/开书策划/提纲/正文/修改
- 已完成：（流水账，带日期）
- 待做：（下一步要做什么）
- 最近git标签：（如有）
```

作用：防止会话重启后丢失进度、防止阶段跳跃。

---

## 事实数据表（bible/facts.md）规范

facts.md只记录两类事实：
1. **内行一看就假的**：行业流程、专业术语、政策法规、价格区间——写错了内行读者立刻出戏
2. **前后容易矛盾的**：人物收入、关键距离、角色背景设定——写多了容易前后不一致

不记录：查一下就知道的常识、对剧情没有影响的环境细节、不确定的推断（等确认了再加）。

每条事实必须附来源。主控按"容易写错且对剧情有影响"的标准判断facts是否充分，不够就派调研会话补。表格格式按小说需要自由组织，不设固定模板。

---

## 工具脚本说明
所有脚本纯Python标准库，不需要安装依赖：

| 脚本 | 用法 | 什么时候跑 |
|------|------|-----------|
| check_output.py | `python tools/check_output.py <文件> --type <topic/opening/outline/general>` | 主控拿到任何产出后第一时间跑，FAIL直接打回 |
| check_facts_consistency.py | `python tools/check_facts_consistency.py <小说目录>` | 开书后、每批提纲后、每章后跑，扫跨文件数字矛盾 |
| check_ai_cliches.py | `python tools/check_ai_cliches.py <文件> --layer5 bible/style/layer5_antipatterns.md` | 正文审稿前跑，查AI套话（结合layer5禁用词库） |
| text_stats.py | `python tools/text_stats.py <文件> [--json]` | 每5章跑一次，查字数句长是否符合layer1 |
| epub_to_text.py | `python tools/epub_to_text.py <epub> <输出txt>` | 蒸馏作者风格时转格式用 |

---

## Git约定
- **只在总编明确指示时执行**，主控不主动commit或打标签
- 总编指示时的标签命名：
  - `topic_approved_vN` 选题通过
  - `opening_approved_vN` 开书通过
  - `batchNNN_outline_approved` 每批提纲通过
  - `chapterNNN_final` 每章定稿
  - `batchNNN_final` 每批全部通过
- 回滚优先用标签：`git reset --hard <标签名>`
- 回滚前必须告知总编

---

## 版本记录
- **v5.1 (2026-07-02)**：精简Prompt（writer/master/reviewer各砍50%），新增progress.md进度追踪，facts.md定位调整为只记关键事实，check_ai_cliches接入layer5禁用词库，审稿从"凑问题数"改为"核对过程质量"
- v5.0 (2026-07-02)：全新架构，4+1多会话物理隔离，写前场景事实检查，结构化审稿核对
- v4.7：执行层硬化，审稿隔离，输出契约，Git标签
- v4.6：证据链机制，facts.md，事实来源表，抽样验证
- v4.5-v1.0：历史版本，已废弃，见docs/design.md（参考用）
