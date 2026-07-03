#!/usr/bin/env python3
import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict

DEFAULT_BLACKLIST = [
    "一股暖流", "一股寒意", "一股莫名的", "涌上心头", "心中暗道", "嘴角勾起",
    "不由得", "忍不住", "下意识", "情不自禁", "赫然发现", "猛然发现",
    "瞳孔骤缩", "瞳孔一缩", "眼中闪过一丝", "眼底掠过一丝", "嘴角微微上扬",
    "不禁", "竟然", "居然", "宛如", "犹如", "仿佛", "似乎", "好像",
    "这一刻", "那一瞬", "刹那间", "霎时间", "不知何时",
    "倒吸一口凉气", "深吸一口气", "长舒一口气", "淡淡道", "冷冷道", "沉声道",
    "心里咯噔一下", "心跳漏了一拍", "呼吸一滞", "如坠冰窟", "浑身一震",
]


def extract_from_layer5(layer5_path: Path) -> list:
    """从layer5_antipatterns.md提取关键词"""
    keywords = []
    text = layer5_path.read_text(encoding="utf-8")

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # 匹配编号列表项: 1. xxx / 2. xxx / - xxx / * xxx
        m = re.match(r'^(?:\d+\.|-|\*)\s*(.+)$', line)
        if m:
            content = m.group(1).strip()
            # 提取引号中的短语
            quoted = re.findall(r'[「""【](.+?)[」""】]', content)
            if quoted:
                keywords.extend([q.strip() for q in quoted if len(q.strip()) >= 2])
            else:
                # 没有引号，取前10个字作为关键词
                clean = re.sub(r'[（(].*?[)）]', '', content).strip()
                if len(clean) >= 2 and len(clean) <= 15:
                    keywords.append(clean)
    return keywords


def find_matches(text: str, blacklist: list) -> dict:
    matches = defaultdict(list)
    for word in blacklist:
        if len(word) < 2:
            continue
        for m in re.finditer(re.escape(word), text):
            line_num = text[:m.start()].count('\n') + 1
            context_start = max(0, m.start() - 20)
            context_end = min(len(text), m.end() + 20)
            context = text[context_start:context_end].replace('\n', ' ')
            matches[word].append((line_num, context))
    return matches


def main():
    parser = argparse.ArgumentParser(description="检测AI套话和陈词滥调")
    parser.add_argument("file", help="待检测文本文件路径")
    parser.add_argument("--blacklist", help="自定义黑名单文件（每行一个词）", default=None)
    parser.add_argument("--layer5", help="从layer5反模式文件提取关键词", default=None)
    parser.add_argument("--threshold", type=int, default=0, help="问题词数量阈值，超过则返回非0退出码")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"错误：文件不存在 {file_path}")
        sys.exit(1)

    text = file_path.read_text(encoding='utf-8')

    blacklist = list(DEFAULT_BLACKLIST)

    if args.blacklist:
        bl_path = Path(args.blacklist)
        if bl_path.exists():
            extra = [line.strip() for line in bl_path.read_text(encoding='utf-8').splitlines()
                     if line.strip() and not line.startswith('#')]
            blacklist.extend(extra)

    if args.layer5:
        l5_path = Path(args.layer5)
        if l5_path.exists():
            l5_words = extract_from_layer5(l5_path)
            blacklist.extend(l5_words)
            print(f"从layer5提取了 {len(l5_words)} 个禁用词/短语")
        else:
            print(f"警告：layer5文件不存在 {l5_path}")

    blacklist = list(dict.fromkeys(blacklist))

    matches = find_matches(text, blacklist)

    if not matches:
        print("✅ 未检测到AI套话/陈词滥调")
        sys.exit(0)

    total = sum(len(v) for v in matches.values())
    print(f"⚠️  检测到 {len(matches)} 种问题词/短语，共 {total} 处：\n")
    for word, occurrences in sorted(matches.items(), key=lambda x: -len(x[1])):
        print(f"  「{word}」出现 {len(occurrences)} 次：")
        for line_num, context in occurrences[:5]:
            print(f"    L{line_num}: ...{context}...")
        if len(occurrences) > 5:
            print(f"    ...还有 {len(occurrences) - 5} 处")
        print()

    if args.threshold > 0 and total > args.threshold:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
