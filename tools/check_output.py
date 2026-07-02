#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import argparse
import sys


def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='gb18030', errors='replace') as f:
            return f.read()


def check_front_matter(text):
    issues = []
    if not re.search(r'前置依据|读取了以下文件|我读了', text[:2000]):
        issues.append("❌ 缺少【前置依据】模块，文件开头应该明确列出读取了哪些文件")
    return issues


def check_self_check(text):
    issues = []
    has_self_check = False
    check_keywords = ['自检', '自我检查', '自检结果', '自我校验']
    for kw in check_keywords:
        if kw in text:
            has_self_check = True
            break
    if not has_self_check:
        issues.append("❌ 缺少【填空式自检】模块")
        return issues
    checkbox_pattern = re.compile(r'\[[ xX✓✅]\]')
    if checkbox_pattern.search(text[-3000:]):
        issues.append("❌ 自检使用了打勾checkbox（[x]），必须改为填空式，填写具体内容")
    blank_patterns = [
        r'_{3,}',
        r'（\s*）',
        r'\(\s*\)',
        r':\s*$',
    ]
    blank_count = 0
    for pattern in blank_patterns:
        blank_count += len(re.findall(pattern, text[-3000:]))
    if blank_count > 0:
        issues.append(f"⚠️  自检部分还有 {blank_count} 处空项没填写（下划线/空括号/冒号后空白）")
    return issues


def check_fact_source_table(text, doc_type):
    issues = []
    required_types = ['topic', 'opening', 'outline']
    if doc_type not in required_types:
        return issues
    table_header_pattern = re.compile(r'\|\s*序号\s*\|.*事实内容.*\|', re.IGNORECASE)
    if not table_header_pattern.search(text):
        issues.append(f"❌ 缺少【事实来源表】（{doc_type}类型文件必须附事实来源表）")
        return issues
    table_rows = re.findall(r'^\|\s*\d+\s*\|', text, re.MULTILINE)
    min_rows = {'topic': 8, 'opening': 12, 'outline': 3}
    expected = min_rows.get(doc_type, 3)
    if len(table_rows) < expected:
        issues.append(f"❌ 事实来源表只有 {len(table_rows)} 条记录，要求至少 {expected} 条")
    empty_cells = 0
    for row in re.findall(r'^\|.*\|$', text[-5000:], re.MULTILINE):
        cells = [c.strip() for c in row.split('|')[1:-1]]
        for c in cells:
            if c in ['', '-', '___', '待填', '待定', 'TBD']:
                empty_cells += 1
    if empty_cells > 0:
        issues.append(f"⚠️  事实来源表有 {empty_cells} 个空单元格")
    return issues


def check_output_contract(file_path, doc_type=None):
    text = read_file(file_path)
    issues = []
    issues.extend(check_front_matter(text))
    issues.extend(check_self_check(text))
    issues.extend(check_fact_source_table(text, doc_type))
    return issues


def main():
    parser = argparse.ArgumentParser(description='输出契约检查工具 - 检查子Agent输出是否符合三模块契约')
    parser.add_argument('file', help='要检查的输出文件路径')
    parser.add_argument('--type', choices=['topic', 'opening', 'outline', 'general'], default='general',
                        help='文件类型：topic(选题) opening(开书策划) outline(提纲) general(其他)')
    args = parser.parse_args()
    print("=" * 60)
    print("输出契约检查")
    print("=" * 60)
    print(f"文件：{args.file}")
    print(f"类型：{args.type}")
    print("-" * 60)
    issues = check_output_contract(args.file, args.type)
    if not issues:
        print("✅ PASS：输出符合三模块契约要求")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ FAIL：发现以下问题：")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print("-" * 60)
        fatal_count = sum(1 for i in issues if i.startswith('❌'))
        warn_count = sum(1 for i in issues if i.startswith('⚠️'))
        print(f"总结：{fatal_count} 个严重问题，{warn_count} 个警告")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
