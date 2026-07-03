# 小说创作多Agent系统 v5.3

## 系统概述
这是一个用于创作现实主义题材长篇网络小说的多Agent协同系统。核心原则：**真实性是生命线**。系统通过会话物理隔离、证据链机制、事实数据表（facts.md）、独立审稿，系统性防止LLM编造事实、假装调研、角色放水。

## 架构：4+1 会话

| 会话 | 职责 | 是否长期驻留 |
|------|------|-------------|
| 主控会话（总编助理） | 流程调度、派活、质量检查、文件管理、和总编交互 | ✅ 长期 |
| 写稿会话 | 选题、开书策划、写提纲、写正文、更新状态文件 | ✅ 长期 |
| 审稿会话 | 独立五维度审稿（事实/真实/逻辑/节奏/文笔），物理隔离 | ✅ 长期 |
| 调研会话 | 热点调研、事实补全、来源WebFetch验证 | ✅ 长期 |
| 蒸馏会话 | 从作者已有作品蒸馏风格规则（layer0-5） | ❌ 开书前用一次，用完关 |

**核心设计**：所有会话共享同一个本地`/workspace`目录，通过读写文件协作，通过总编在会话间传递消息。写稿和审稿完全物理隔离——审稿会话永远看不到写稿会话的思考过程，只看到最终文件。

## 核心机制

### 1. 证据链机制（防LLM假装调研）
- **事实来源表**：选题、开书、每批提纲末尾必须附结构化事实来源表（序号|事实内容|来源类型|来源路径/URL|来源摘要）
- **主控抽样验证**：主控收到任何产出，随机抽1-2条来源WebFetch验证，发现编造直接打回
- **填空式自检**：不允许打勾式自检，必须填具体内容

### 2. bible/facts.md事实数据表
facts.md是所有硬事实的唯一真相来源，只记两类事实：
1. **内行一看就假的**（经济数据、行业流程、地理距离、通讯方式、出入境规则）
2. **前后容易矛盾的**（人物手里多少钱、别人欠他多少、人物关系状态）
不记录常识，不记录不确定的推断。格式自由组织，但必须覆盖6大类必填类目（物理行动/资金/生意/风险/关系/时间空间）。

### 3. progress.md进度追踪
每个小说项目根目录必须有`progress.md`，记录：当前阶段、已完成步骤、待完成步骤、当前批次/章节号。主控每次操作前后必须读写，防止会话重启后丢失进度。

### 4. 写前场景事实检查
写稿会话动笔前必须先列出本任务涉及的所有场景动作（怎么买票、怎么付钱、怎么打电话），逐项对照facts.md，缺的列"需要补调研清单"停下，facts齐全才开始写。这是防止"护照/电话卡/现金"类低级硬伤的核心防线。

### 5. 审稿过程质量要求
审稿不再强制要求"至少找出N个问题"（容易凑数），而是要求**必须展示核对过程**：每个维度核对了什么、怎么核对的。没有核对过程直接说"没问题"，视为审稿不通过。

### 6. 上下文按需加载
写稿会话不得全量加载所有历史章节和人物卡：前一章只读最后1500字衔接，旧内容从状态文件查。这是防止长篇写作上下文爆炸的关键。

## 目录结构
```
workspace/
├── SYSTEM.md                    # 本文件
├── README.md                    # 使用说明
├── prompts/                     # 各会话System Prompt
│   ├── master.md
│   ├── writer.md
│   ├── reviewer.md
│   ├── researcher.md
│   └── distiller.md
├── tools/                       # 检查脚本
│   ├── check_output.py          # 检查输出格式完整性
│   ├── check_facts_consistency.py # 跨文件数字一致性检查
│   ├── check_ai_cliches.py      # AI套话检测（支持--layer5读反模式库）
│   ├── text_stats.py            # 文本统计（字数/对话占比/段落数）
│   └── epub_to_text.py          # epub转文本（蒸馏用）
├── authors/                     # 作者风格库
│   └── <author_slug>/
│       ├── layer0_theme_hard_redlines.md
│       ├── layer1_rhythm_structure.md
│       ├── layer2_prose_dna.md
│       ├── layer3_character_speech.md
│       ├── layer4_foreshadow_craft.md
│       ├── layer5_antipatterns.md
│       ├── corrections.json
│       └── distillation_report.md
├── work/                        # 小说工作区
│   ├── _research/               # 公共调研素材
│   └── <novel_slug>/            # 每本小说独立目录
│       ├── progress.md
│       ├── bible/
│       │   ├── facts.md
│       │   ├── world.md
│       │   ├── characters/
│       │   ├── style/           # 从authors复制
│       │   ├── character_state.md
│       │   ├── foreshadow_map.md
│       │   ├── timeline.md
│       │   ├── plot_arcs.md
│       │   └── corrections.json
│       ├── batch_plans/
│       ├── chapters/
│       └── reviews/
└── docs/                        # 文档（design.md为历史文档）
```

## 工具脚本说明

| 脚本 | 用法 | 什么时候跑 |
|------|------|-----------|
| check_output.py | `python tools/check_output.py <文件> --type <topic/opening/outline/chapter>` | 任何创作产出后 |
| check_facts_consistency.py | `python tools/check_facts_consistency.py work/<slug>` | 开书后、每批提纲后、正文后 |
| check_ai_cliches.py | `python tools/check_ai_cliches.py <文件> --layer5 work/<slug>/bible/style/layer5_antipatterns.md` | 正文后 |
| text_stats.py | `python tools/text_stats.py <文件>` | 正文后 |
| epub_to_text.py | `python tools/epub_to_text.py <epub> <输出txt>` | 蒸馏时 |

## Git规则
主控不主动执行任何Git操作（包括commit）。只有总编明确指示时才commit/push/打标签。

## 版本记录
- v5.3: 合并优化——精简prompt、增加progress.md、上下文按需加载、写前场景检查、审稿过程质量代替凑数、facts不设固定表格、Git完全手动、check_ai_cliches支持--layer5
- v5.0-v5.2: 4+1多会话架构、证据链机制、facts.md体系、热点融入规则
