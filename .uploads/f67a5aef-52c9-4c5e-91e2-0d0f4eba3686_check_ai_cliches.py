#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import argparse
from collections import defaultdict


DEFAULT_BLACKLIST = [
    '喃喃道',
    '眼中闪过一丝',
    r'一股.{1,10}?的感觉涌上心头',
    '嘴角勾起一抹',
    '下意识地',
    '忍不住',
    '心中暗道',
    '不置可否',
    '意味深长',
    '若有所思',
    '瞳孔骤缩',
    '倒吸一口凉气',
    '不禁',
    '缓缓地',
    '淡淡地',
    '默默地',
    '幽幽道',
    '冷声说',
    '邪笑道',
    '讥讽道',
    '一字一句道',
    '咬牙切齿道',
]


def load_blacklist(file_path):
    words = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if word:
                words.append(word)
    return words


def extract_from_layer5(layer5_path):
    """从layer5_antipatterns.md中提取禁用表达。
    解析两种格式：
    1. 编号列表：'1. 瞳孔骤缩（0次）' -> 提取'瞳孔骤缩'
    2. 子弹列表：'- 幽幽道' -> 提取'幽幽道'
    跳过描述性的长段落（烂俗桥段、写作反模式等）。
    """
    words = []
    with open(layer5_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()

        # 编号列表格式：'1. 词（次数）' 或 '1. 词'
        m = re.match(r'^\d+\.\s+(.+?)(?:（|$)', stripped)
        if m:
            word = m.group(1).strip().rstrip('（(')
            # 跳过太长的（描述性内容而非关键词）
            if len(word) <= 20 and '**' not in word:
                words.append(word)
            continue

        # 子弹列表格式：'- 词' （对话标签黑名单部分）
        m = re.match(r'^[-*]\s+(.+?)(?:（|$)', stripped)
        if m:
            word = m.group(1).strip().rstrip('（(')
            if len(word) <= 20 and '**' not in word:
                words.append(word)

    return words


def find_matches(text, patterns):
    results = defaultdict(lambda: {'count': 0, 'lines': []})
    lines = text.split('\n')
    
    for line_num, line in enumerate(lines, start=1):
        for pattern in patterns:
            regex = re.compile(pattern)
            matches = list(regex.finditer(line))
            if matches:
                if pattern not in results:
                    results[pattern] = {'count': 0, 'lines': []}
                results[pattern]['count'] += len(matches)
                if line_num not in results[pattern]['lines']:
                    results[pattern]['lines'].append(line_num)
    
    return dict(results)


def main():
    parser = argparse.ArgumentParser(description='AI套话检测工具 - 检查文本中是否包含AI高频套话')
    parser.add_argument('file', help='要检查的文本文件路径')
    parser.add_argument('--blacklist', help='额外黑名单文件路径（每行一个词/正则表达式）')
    parser.add_argument('--layer5', help='layer5_antipatterns.md文件路径，自动提取禁用表达')
    args = parser.parse_args()
    
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(args.file, 'r', encoding='gb18030', errors='replace') as f:
            text = f.read()
    
    blacklist = list(DEFAULT_BLACKLIST)
    if args.blacklist:
        extra_words = load_blacklist(args.blacklist)
        blacklist.extend(extra_words)
    if args.layer5:
        layer5_words = extract_from_layer5(args.layer5)
        blacklist.extend(layer5_words)
        print(f"[从layer5加载了 {len(layer5_words)} 条禁用表达]")
    
    results = find_matches(text, blacklist)
    
    if not results:
        print("未检测到AI套话")
        return
    
    print("=" * 60)
    print("AI套话检测结果")
    print("=" * 60)
    print(f"{'匹配词语':<25} {'出现次数':<10} {'所在行号'}")
    print("-" * 60)
    
    sorted_results = sorted(results.items(), key=lambda x: x[1]['count'], reverse=True)
    for word, info in sorted_results:
        lines_str = ', '.join(str(l) for l in info['lines'][:20])
        if len(info['lines']) > 20:
            lines_str += f' ... (+{len(info["lines"]) - 20}行)'
        print(f"{word:<25} {info['count']:<10} {lines_str}")
    
    print("-" * 60)
    total_count = sum(info['count'] for info in results.values())
    print(f"共检测到 {len(results)} 种AI套话，累计出现 {total_count} 次")
    print("=" * 60)


if __name__ == '__main__':
    main()
