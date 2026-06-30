#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import json
import argparse


SENTENCE_END_PATTERN = r'[。！？!?…"」』】\u201d\u2019]$'


def merge_hard_wraps(text):
    lines = text.split('\n')
    merged_lines = []
    current_line = ''
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_line:
                merged_lines.append(current_line)
                current_line = ''
            continue
        
        if current_line:
            if re.search(SENTENCE_END_PATTERN, current_line) or stripped.startswith('\u201c') or stripped.startswith('"') or stripped.startswith('「'):
                merged_lines.append(current_line)
                current_line = stripped
            else:
                current_line += stripped
        else:
            current_line = stripped
    
    if current_line:
        merged_lines.append(current_line)
    
    return merged_lines


def split_sentences(text):
    pattern = r'[。！？!?…]+|\.{3,}|[」』]+'
    sentences = re.split(pattern, text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences


def extract_quotes(text):
    quotes = []
    patterns = [
        r'\u201c([^\u201c\u201d]*)\u201d',
        r'\u2018([^\u2018\u2019]*)\u2019',
        r'"([^"]*)"',
        r'「([^」]*)」',
        r'『([^』]*)』',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            quotes.append(match.group(1))
    return quotes


def count_quote_chars(text):
    quotes = extract_quotes(text)
    return sum(len(q) for q in quotes)


def split_paragraphs(text):
    return merge_hard_wraps(text)


def analyze_text(text):
    total_chars = len(text)
    
    sentences = split_sentences(text)
    sent_lengths = [len(s) for s in sentences]
    total_sentences = len(sentences)
    
    short_sent = sum(1 for l in sent_lengths if l < 10)
    mid_sent = sum(1 for l in sent_lengths if 10 <= l <= 25)
    long_sent = sum(1 for l in sent_lengths if l > 25)
    
    total_sent_categorized = short_sent + mid_sent + long_sent
    avg_sent_length = round(sum(sent_lengths) / total_sentences, 2) if total_sentences > 0 else 0
    
    quote_chars = count_quote_chars(text)
    dialogue_ratio = round(quote_chars / total_chars, 4) if total_chars > 0 else 0
    
    paragraphs = split_paragraphs(text)
    para_lengths = [len(p) for p in paragraphs]
    total_paragraphs = len(paragraphs)
    
    short_para = sum(1 for l in para_lengths if l < 50)
    mid_para = sum(1 for l in para_lengths if 50 <= l <= 200)
    long_para = sum(1 for l in para_lengths if l > 200)
    
    total_para_categorized = short_para + mid_para + long_para
    avg_para_length = round(sum(para_lengths) / total_paragraphs, 2) if total_paragraphs > 0 else 0
    
    result = {
        'total_characters': total_chars,
        'total_sentences': total_sentences,
        'avg_sentence_length': avg_sent_length,
        'short_sentence_count': short_sent,
        'mid_sentence_count': mid_sent,
        'long_sentence_count': long_sent,
        'short_sentence_ratio': round(short_sent / total_sent_categorized * 100, 2) if total_sent_categorized > 0 else 0,
        'mid_sentence_ratio': round(mid_sent / total_sent_categorized * 100, 2) if total_sent_categorized > 0 else 0,
        'long_sentence_ratio': round(long_sent / total_sent_categorized * 100, 2) if total_sent_categorized > 0 else 0,
        'dialogue_characters': quote_chars,
        'dialogue_ratio': round(dialogue_ratio * 100, 2),
        'total_paragraphs': total_paragraphs,
        'avg_paragraph_length': avg_para_length,
        'short_paragraph_count': short_para,
        'mid_paragraph_count': mid_para,
        'long_paragraph_count': long_para,
        'short_paragraph_ratio': round(short_para / total_para_categorized * 100, 2) if total_para_categorized > 0 else 0,
        'mid_paragraph_ratio': round(mid_para / total_para_categorized * 100, 2) if total_para_categorized > 0 else 0,
        'long_paragraph_ratio': round(long_para / total_para_categorized * 100, 2) if total_para_categorized > 0 else 0,
    }
    
    return result


def print_human_readable(stats):
    print("=" * 60)
    print("文本统计分析")
    print("=" * 60)
    
    print(f"\n【基本信息】")
    print(f"  总字数: {stats['total_characters']:,}")
    print(f"  总句子数: {stats['total_sentences']:,}")
    print(f"  平均句长: {stats['avg_sentence_length']} 字")
    
    print(f"\n【句子长度分布】")
    print(f"  短句 (<10字): {stats['short_sentence_count']:,} 句 ({stats['short_sentence_ratio']}%)")
    print(f"  中句 (10-25字): {stats['mid_sentence_count']:,} 句 ({stats['mid_sentence_ratio']}%)")
    print(f"  长句 (>25字): {stats['long_sentence_count']:,} 句 ({stats['long_sentence_ratio']}%)")
    
    print(f"\n【对话比例】")
    print(f"  对话字符数: {stats['dialogue_characters']:,}")
    print(f"  对话占比: {stats['dialogue_ratio']}%")
    
    print(f"\n【段落信息】")
    print(f"  总段落数: {stats['total_paragraphs']:,}")
    print(f"  平均段落长度: {stats['avg_paragraph_length']} 字")
    
    print(f"\n【段落长度分布】")
    print(f"  短段落 (<50字): {stats['short_paragraph_count']:,} 段 ({stats['short_paragraph_ratio']}%)")
    print(f"  中段落 (50-200字): {stats['mid_paragraph_count']:,} 段 ({stats['mid_paragraph_ratio']}%)")
    print(f"  长段落 (>200字): {stats['long_paragraph_count']:,} 段 ({stats['long_paragraph_ratio']}%)")
    
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='文本统计工具 - 分析文本的字数、句长、对话比例、段落分布等')
    parser.add_argument('file', help='要分析的文本文件路径')
    parser.add_argument('--json', action='store_true', help='以JSON格式输出结果')
    args = parser.parse_args()
    
    try:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(args.file, 'r', encoding='gb18030', errors='replace') as f:
            text = f.read()
    
    stats = analyze_text(text)
    
    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print_human_readable(stats)


if __name__ == '__main__':
    main()
