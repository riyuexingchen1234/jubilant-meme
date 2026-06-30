#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import argparse


SKIP_KEYWORDS = ['目录', '版权', '出版社', '内容简介', '作者简介', '前言', '序', '楔子']
MIN_CHAPTER_LENGTH = 100

epub = None
ebooklib = None
BeautifulSoup = None


def _check_dependencies():
    global epub, ebooklib, BeautifulSoup
    try:
        import ebooklib as _ebooklib
        from ebooklib import epub as _epub
        from bs4 import BeautifulSoup as _BeautifulSoup
        epub = _epub
        ebooklib = _ebooklib
        BeautifulSoup = _BeautifulSoup
        return True
    except ImportError:
        print("错误：需要安装 ebooklib 和 beautifulsoup4")
        print("请运行：pip install ebooklib beautifulsoup4")
        return False


def _html_to_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def should_skip_chapter(title, text):
    if len(text) < MIN_CHAPTER_LENGTH:
        return True
    title_lower = title if title else ''
    for kw in SKIP_KEYWORDS:
        if kw in title_lower:
            return True
    first_line = text.split('\n')[0].strip() if text else ''
    for kw in SKIP_KEYWORDS:
        if kw in first_line and len(first_line) < 30:
            return True
    return False


def extract_epub_text(epub_path):
    book = epub.read_epub(epub_path)
    chapters_text = []
    
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            html = item.get_content().decode("utf-8", errors="replace")
            text = _html_to_text(html)
            
            if not text or len(text) < 20:
                continue
            
            title = ''
            try:
                soup = BeautifulSoup(html, "html.parser")
                h = soup.find(["h1", "h2", "h3"])
                if h:
                    title = h.get_text().strip()
            except Exception:
                pass
            
            if not title:
                lines = text.split('\n')
                for line in lines[:3]:
                    ls = line.strip()
                    if ls:
                        title = ls
                        break
            
            if should_skip_chapter(title, text):
                continue
            
            chapter_pattern = re.compile(r'^第[一二三四五六七八九十百千零\d]+[章节回卷集部篇]')
            if title and chapter_pattern.match(title):
                chapters_text.append(f"{title}\n\n{text}")
            else:
                chapters_text.append(text)
    
    full_text = "\n\n".join(chapters_text)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    return full_text.strip()


def main():
    parser = argparse.ArgumentParser(description='EPUB转文本工具 - 从EPUB文件提取正文文本')
    parser.add_argument('input', help='输入EPUB文件路径')
    parser.add_argument('output', help='输出TXT文件路径')
    args = parser.parse_args()
    
    if not _check_dependencies():
        exit(1)
    
    print(f"正在读取EPUB文件: {args.input}")
    text = extract_epub_text(args.input)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(text)
    
    char_count = len(text)
    print(f"转换完成！")
    print(f"输出文件: {args.output}")
    print(f"总字符数: {char_count:,}")


if __name__ == '__main__':
    main()
