#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

EPUB_PATH = "/workspace/test_run/source/北派盗墓笔记(1-4卷) -- 云峰 -- 番茄小说网 -- ff59e5accd489f0c9f112ad4461088bf -- Anna’s Archive.epub"
CHAPTERS_DIR = "/workspace/test_run/source/yunfeng/chapters"
RAW_TEXT_DIR = "/workspace/test_run/source/yunfeng/raw_text"
REPORT_PATH = "/workspace/test_run/source/yunfeng/parse_report.txt"
MIN_CHAPTER_LENGTH = 100

CHAPTER_PATTERN = re.compile(r'^第[一二三四五六七八九十百千零\d]+[章节卷]')


def extract_text(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    for tag in soup(['script', 'style', 'nav']):
        tag.decompose()
    text = soup.get_text(separator='\n', strip=True)
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    return '\n'.join(lines)


def find_chapter_title(text):
    lines = text.split('\n')
    for line in lines[:5]:
        ls = line.strip()
        if CHAPTER_PATTERN.match(ls):
            return ls
    return None


def count_chars(text):
    return len(text.replace('\n', '').replace(' ', '').replace('\r', ''))


def main():
    print(f"Reading EPUB from: {EPUB_PATH}")
    book = epub.read_epub(EPUB_PATH)

    item_map = {}
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            item_map[item.get_id()] = item

    preface = None
    preface_seen = False
    chapters = []

    for spine_entry in book.spine:
        item_id = spine_entry[0]
        if item_id not in item_map:
            continue
        item = item_map[item_id]
        html = item.get_content()
        text = extract_text(html)

        if len(text) < MIN_CHAPTER_LENGTH:
            continue

        title = find_chapter_title(text)

        if title:
            body_start = text.find(title)
            if body_start != -1:
                body = text[body_start + len(title):].strip()
            else:
                body = text
            chapters.append((title, body))
        else:
            if not preface_seen:
                preface = text
                preface_seen = True

    if preface:
        chapters.insert(0, ("作品简介", preface))

    os.makedirs(CHAPTERS_DIR, exist_ok=True)
    os.makedirs(RAW_TEXT_DIR, exist_ok=True)

    full_parts = []
    for idx, (title, body) in enumerate(chapters, start=1):
        chapter_text = f"{title}\n\n{body}"
        chapter_filename = f"chapter_{idx:03d}.txt"
        chapter_path = os.path.join(CHAPTERS_DIR, chapter_filename)
        with open(chapter_path, 'w', encoding='utf-8') as f:
            f.write(chapter_text)
        full_parts.append(f"===== {title} =====\n{body}")

    full_text = '\n\n'.join(full_parts)
    full_text_path = os.path.join(RAW_TEXT_DIR, "full_text.txt")
    with open(full_text_path, 'w', encoding='utf-8') as f:
        f.write(full_text)

    total_chars = count_chars(full_text)
    num_chapters = len(chapters)
    chapter_lengths = [count_chars(body) for _, body in chapters]
    avg_chars = sum(chapter_lengths) / num_chapters if num_chapters > 0 else 0

    top10_titles = [f"{i+1}. {chapters[i][0]}" for i in range(min(10, num_chapters))]

    preview_text = full_text.replace('\n', ' ')
    preview = preview_text[:500]

    def chapter_sort_key(fname):
        m = re.match(r'chapter_(\d+)\.txt', fname)
        return int(m.group(1)) if m else 0
    chapter_files = sorted([f for f in os.listdir(CHAPTERS_DIR) if f.startswith('chapter_') and f.endswith('.txt')], key=chapter_sort_key)

    report_lines = []
    report_lines.append("=" * 60)
    report_lines.append("EPUB 解析统计报告")
    report_lines.append("=" * 60)
    report_lines.append(f"总字数（去空白）: {total_chars}")
    report_lines.append(f"章节总数: {num_chapters}")
    report_lines.append(f"每章平均字数: {avg_chars:.1f}")
    report_lines.append("")
    report_lines.append("前10章标题:")
    for t in top10_titles:
        report_lines.append(f"  {t}")
    report_lines.append("")
    report_lines.append("开头500字预览:")
    report_lines.append(preview)
    report_lines.append("")
    report_lines.append("=" * 60)
    report_lines.append("文件生成状态:")
    report_lines.append(f"  full_text.txt: {'存在' if os.path.exists(full_text_path) else '缺失'} ({os.path.getsize(full_text_path)} bytes)")
    report_lines.append(f"  parse_report.txt: 存在 (本文件)")
    report_lines.append(f"  章节文件数: {len(chapter_files)}")
    report_lines.append(f"  章节文件范围: {chapter_files[0] if chapter_files else 'N/A'} ~ {chapter_files[-1] if chapter_files else 'N/A'}")
    report_lines.append("=" * 60)

    report_content = '\n'.join(report_lines)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(report_content)
    print(f"\n解析完成，报告已保存到: {REPORT_PATH}")


if __name__ == "__main__":
    main()
