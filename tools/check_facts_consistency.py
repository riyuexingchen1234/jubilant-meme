#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import argparse
import sys
from pathlib import Path


def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='gb18030', errors='replace') as f:
                return f.read()
        except Exception:
            return None


def extract_money_amounts(text):
    amounts = []
    patterns = [
        (r'(\d+(?:\.\d+)?)\s*万元?', 10000),
        (r'(\d+(?:\.\d+)?)\s*元', 1),
        (r'(\d+(?:\.\d+)?)\s*块钱?', 1),
        (r'(\d+(?:\.\d+)?)\s*w', 10000),
        (r'(\d+(?:\.\d+)?)\s*W', 10000),
    ]
    lines = text.split('\n')
    for line_num, line in enumerate(lines, start=1):
        for pattern, multiplier in patterns:
            for match in re.finditer(pattern, line):
                try:
                    num = float(match.group(1))
                    amount = num * multiplier
                    amounts.append({
                        'amount': amount,
                        'raw': match.group(0),
                        'line': line_num,
                        'num': num,
                        'unit': multiplier
                    })
                except ValueError:
                    continue
    return amounts


def extract_registered_ranges(facts_text):
    ranges = []
    in_econ_table = False
    econ_keywords = ['经济事实表', '收入', '支出', '钱', '资产', '负债', '垫资', '欠款', '存款']
    for line in facts_text.split('\n'):
        if any(kw in line for kw in econ_keywords) and '|' in line:
            in_econ_table = True
        if in_econ_table and line.strip().startswith('|') and '---' not in line:
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if len(cells) >= 3:
                person = cells[0]
                range_matches = re.findall(r'(\d+(?:\.\d+)?)\s*[-~到至]\s*(\d+(?:\.\d+)?)\s*(万元?|元|w|W)?', line)
                for m in range_matches:
                    try:
                        low = float(m[0])
                        high = float(m[1])
                        unit = m[2] if m[2] else '万'
                        mult = 10000 if '万' in unit or 'w' in unit.lower() else 1
                        ranges.append({
                            'person': person,
                            'low': low * mult,
                            'high': high * mult,
                            'raw': m[0] + '-' + m[1] + unit
                        })
                    except ValueError:
                        continue
    return ranges


def scan_directory_for_md(novel_dir):
    md_files = []
    bible_dir = novel_dir / 'bible'
    batch_dir = novel_dir / 'batch_plans'
    chapters_dir = novel_dir / 'chapters'
    for d in [bible_dir, batch_dir, chapters_dir]:
        if d.exists():
            md_files.extend(d.rglob('*.md'))
    return md_files


def main():
    parser = argparse.ArgumentParser(description='事实一致性检查工具 - 扫描跨文件硬数字矛盾')
    parser.add_argument('novel_dir', help='小说目录路径（work/<novel_slug>/）')
    args = parser.parse_args()
    novel_dir = Path(args.novel_dir)
    facts_path = novel_dir / 'bible' / 'facts.md'
    print("=" * 60)
    print("事实一致性检查")
    print("=" * 60)
    print(f"小说目录：{novel_dir}")
    issues = []
    if not facts_path.exists():
        print("⚠️  未找到 bible/facts.md，跳过事实表比对")
        print("=" * 60)
        sys.exit(0)
    facts_text = read_file(facts_path)
    if facts_text is None:
        print("❌ 无法读取 facts.md")
        sys.exit(1)
    registered_ranges = extract_registered_ranges(facts_text)
    if not registered_ranges:
        print("⚠️  facts.md中未解析到经济事实数字范围（可能表格格式不规范）")
    else:
        print(f"已从facts.md解析到 {len(registered_ranges)} 条经济事实范围：")
        for r in registered_ranges:
            low_w = r['low'] / 10000 if r['low'] >= 10000 else r['low']
            high_w = r['high'] / 10000 if r['high'] >= 10000 else r['high']
            unit = '万' if r['high'] >= 10000 else '元'
            print(f"  - {r['person']}: {low_w:.1f}-{high_w:.1f}{unit}")
    print("-" * 60)
    md_files = scan_directory_for_md(novel_dir)
    print(f"扫描 {len(md_files)} 个markdown文件...")
    print("-" * 60)
    total_mismatches = 0
    files_with_issues = 0
    files_checked = 0
    for md_file in sorted(md_files):
        if md_file.name == 'facts.md':
            continue
        text = read_file(md_file)
        if text is None:
            continue
        files_checked += 1
        amounts = extract_money_amounts(text)
        file_issues = []
        for amt in amounts:
            matched = False
            for r in registered_ranges:
                if r['low'] * 0.8 <= amt['amount'] <= r['high'] * 1.2:
                    matched = True
                    break
            if not matched and registered_ranges and amt['amount'] > 100:
                rel_path = md_file.relative_to(novel_dir)
                file_issues.append(
                    f"  第{amt['line']}行: 「{amt['raw']}」（约{amt['amount']/10000:.1f}万元）"
                    f" 未在facts.md登记的经济范围内"
                )
        if file_issues:
            files_with_issues += 1
            total_mismatches += len(file_issues)
            rel_path = md_file.relative_to(novel_dir)
            print(f"⚠️  {rel_path}:")
            for issue in file_issues[:10]:
                print(issue)
            if len(file_issues) > 10:
                print(f"  ... 还有{len(file_issues)-10}处")
    print("-" * 60)
    if total_mismatches == 0:
        print("✅ PASS：未发现明显的硬数字矛盾")
    else:
        print(f"❌ 发现 {total_mismatches} 处可疑金额，分布在 {files_with_issues} 个文件中")
        print("   注意：这只是正则扫描的初步结果，有误报可能，请人工核对上下文")
    print(f"共检查了 {files_checked} 个文件")
    print("=" * 60)
    sys.exit(1 if total_mismatches > 0 else 0)


if __name__ == '__main__':
    main()
