import re
from pathlib import Path
from typing import List, Dict, Any
import chardet

AD_PATTERNS = [
    r"www\.[a-zA-Z0-9\-]+\.[a-zA-Z]+",
    r"https?://[^\s]+",
    r"更多精[品彩]小说.*",
]
AUTHOR_NOTE_PATTERNS = [
    r"作者有话说[：:].*",
    r"PS[：: ].*",
    r"求收藏.*求推荐.*",
    r"本章完.*",
]
CHAPTER_PATTERN = re.compile(
    r"^(?:第[一二三四五六七八九十百千零\d]+[章节回卷集部篇]|楔子|序章|引子|终章|尾声)\s*.{0,30}$",
    re.MULTILINE,
)

def detect_encoding(file_path) -> str:
    with open(file_path, "rb") as f:
        raw = f.read(1024 * 1024)
    result = chardet.detect(raw)
    enc = result.get("encoding", "utf-8") or "utf-8"
    if enc.lower() in ("gb2312", "gbk", "gb18030"):
        enc = "gb18030"
    return enc

def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for p in AD_PATTERNS:
        text = re.sub(p, "", text)
    for p in AUTHOR_NOTE_PATTERNS:
        text = re.sub(p, "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()

def split_chapters(text: str) -> List[Dict[str, Any]]:
    matches = list(CHAPTER_PATTERN.finditer(text))
    chapters = []
    if not matches:
        chapters.append({"title": "正文", "content": text.strip(), "index": 0})
        return chapters
    if matches[0].start() > 0:
        pre = text[:matches[0].start()].strip()
        if pre and len(pre) > 100:
            chapters.append({"title": "楔子", "content": pre, "index": 0})
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            chapters.append({"title": m.group(0).strip(), "content": content, "index": len(chapters)})
    return chapters

def load_and_clean_txt(file_path) -> Dict[str, Any]:
    encoding = detect_encoding(file_path)
    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        raw = f.read()
    cleaned = clean_text(raw)
    chapters = split_chapters(cleaned)
    return {
        "raw_text": raw, "cleaned_text": cleaned, "chapters": chapters,
        "total_chars": len(cleaned), "total_chapters": len(chapters), "encoding": encoding,
    }
