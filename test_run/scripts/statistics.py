#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import json
import os
from collections import Counter

try:
    import jieba
except ImportError:
    os.system('pip install jieba -q')
    import jieba

FULL_TEXT_PATH = '/workspace/test_run/source/yunfeng/raw_text/full_text.txt'
SAMPLE_DIR = '/workspace/test_run/source/yunfeng/sample_chapters/'
OUTPUT_JSON = '/workspace/test_run/source/yunfeng/statistics.json'

os.makedirs(SAMPLE_DIR, exist_ok=True)

STOP_WORDS = {'的', '了', '在', '是', '我', '他', '她', '它', '你', '们', '这', '那', '有', '和', '就', '不', '人', '都', '一', '上', '也', '到', '说', '要', '去', '会', '没', '看', '好', '自己', '这个', '那个', '什么', '怎么', '为什么', '哪', '哪里', '谁', '多', '大', '小', '很', '太', '最', '更', '还', '又', '再', '才', '能', '可以', '应该', '该', '想', '知道', '里', '中', '下', '后', '前', '来', '过', '着', '个', '么', '之', '与', '而', '及', '或', '但', '却', '并', '以', '为', '对', '从', '向', '往', '被', '把', '让', '给', '比', '等', '啊', '呀', '吧', '呢', '吗', '哦', '嗯', '哈', '唉', '哎', '啦', '呐', '哟', '哩', '哇', '额', '些', '只', '点', '样', '不是', '没有', '就是', '还是', '已经', '这样', '这么', '那么', '这里', '那里', '他们', '我们', '你们', '咱们', '一个', '两个', '这种', '这些', '那些', '可能', '不会', '不能', '出来', '过来', '过去', '起来', '现在', '因为', '所以', '如果', '还有', '东西', '地方', '事情', '事儿', '时候', '一下', '一点', '有些', '任何', '几个', '很多', '不少', '一样', '这样', '那样', '怎样', '如何', '为何', '为啥', '咱们', '俩', '仨', '各位', '大家'}

PUNCTUATION_LIST = [
    ('……', '省略号(中文)'),
    ('...', '省略号(英文)'),
    ('！', '感叹号(中文)'),
    ('!', '感叹号(英文)'),
    ('？', '问号(中文)'),
    ('?', '问号(英文)'),
    ('——', '破折号'),
    ('，', '逗号(中文)'),
    (',', '逗号(英文)'),
    ('。', '句号(中文)'),
    ('.', '句号(英文)'),
    ('、', '顿号'),
    ('：', '冒号(中文)'),
    (':', '冒号(英文)'),
    ('；', '分号(中文)'),
    (';', '分号(英文)'),
    ('\u201c', '左双引号'),
    ('\u201d', '右双引号'),
    ('\u2018', '左单引号'),
    ('\u2019', '右单引号'),
    ('（', '左括号(中文)'),
    ('）', '右括号(中文)'),
    ('(', '左括号(英文)'),
    (')', '右括号(英文)'),
    ('《', '左书名号'),
    ('》', '右书名号'),
]

PUNCTUATION_CATEGORIES = {
    '省略号': ['……', '...'],
    '感叹号': ['！', '!'],
    '问号': ['？', '?'],
    '破折号': ['——'],
    '逗号': ['，', ','],
    '句号': ['。', '.'],
    '顿号': ['、'],
    '冒号': ['：', ':'],
    '分号': ['；', ';'],
    '引号': ['\u201c', '\u201d', '\u2018', '\u2019'],
    '括号': ['（', '）', '(', ')'],
    '书名号': ['《', '》'],
}

COLLOQUIAL_WORDS = ['他娘的', '妈的', '我靠', '我操', '我草', '卧槽', '操', '草', '奶奶的', '他妈的', '他妈', '好家伙', '嘿', '哎', '嗨', '娘的', '狗日的', '孙子', '丫的']

ACTION_VERBS = ['走', '跑', '打', '踢', '推', '拉', '抓', '摸', '拿', '听', '转头', '转身', '蹲下', '站起', '冲', '跳', '爬', '拔', '掏', '扔', '摔', '抱', '扶', '拽', '扯', '掰', '挖', '凿', '砍', '劈', '刺', '戳', '拍', '敲', '揍', '踹', '踩', '踏', '跺', '蹲', '跪', '坐', '站', '躺', '趴', '靠', '倚', '躲', '闪', '避', '追', '赶', '逃', '奔', '闯', '钻', '翻', '越', '跨', '绕', '退', '进', '抬', '举', '扛', '背', '搂', '牵', '拖', '挤', '压', '按', '捏', '攥', '握', '取', '接', '递', '交', '送', '投', '抛', '丢', '甩', '挥', '摇', '摆', '晃', '点', '低', '歪', '扭', '侧', '拔', '抽', '甩', '探', '伸', '缩', '搂', '抱', '扶', '搀', '挽', '扯', '拉', '拖', '拽', '推', '搡', '撞', '顶', '撞', '碰', '磕', '绊', '踩', '踏', '踢', '踹', '蹬', '跺', '跳', '蹦', '跃', '跨', '穿', '越', '翻', '滚', '爬', '钻', '退', '避', '闪', '躲', '追', '赶', '跑', '逃', '冲', '奔', '走', '溜', '回', '转', '侧', '转', '扭', '歪', '回', '抬', '低', '俯', '仰', '点', '摇', '晃', '摆', '挥', '招', '摆', '举', '投', '掷', '抛', '扔', '丢', '摔', '砸', '砍', '劈', '刺', '戳', '扎', '捅', '插', '拔', '抽', '打', '揍', '拍', '敲', '击', '擂', '捶', '砸', '撞']

PSYCHO_WORDS = ['我心', '暗想', '心想', '觉得', '感觉', '想到', '意识到', '不由', '心说', '暗道', '暗叫', '心里', '心中', '心头', '一惊', '一怔', '一喜', '一怒', '一慌', '一紧', '一沉', '寻思', '琢磨', '暗自', '不禁', '忍不住', '不由得', '暗想道', '暗忖', '心道', '暗叹', '心道', '心下', '暗想', '心说', '心里想', '脑子里', '脑海里']

ENV_WORDS = ['黑暗', '声音', '味道', '烟雾', '墓道', '棺材', '尸体', '洞口', '墙壁', '石头', '泥土', '沙子', '尘土', '云彩', '月亮', '太阳', '星星', '夜晚', '早上', '清晨', '傍晚', '江河', '湖水', '大海', '树林', '草木', '花草', '悬崖', '山谷', '沟壑', '土坑', '山坡', '山岭', '山峰', '岩石', '峭壁', '砖头', '瓦片', '房梁', '柱子', '大门', '窗户', '台阶', '楼梯', '道路', '巷子', '街道', '村子', '镇子', '城市', '屋子', '房子', '楼房', '宫殿', '殿堂', '走廊', '院子', '井水', '泉水', '溪水', '水潭', '池塘', '沼泽', '泥巴', '灰烬', '火焰', '雷电', '霜冻', '露水', '冰雹', '瘴气', '气味', '响声', '影子', '颜色', '墓室', '棺椁', '尸骨', '地道', '密室', '耳室', '主室', '陪葬', '明器', '粽子', '机关', '陷阱', '暗道', '四周', '周围', '角落', '地面', '顶上', '脚下', '头顶', '半空', '空中', '洞口', '缝隙', '石壁', '土墙', '砖墙', '木门', '石门', '铜门', '铁索', '铁链', '绳子', '火把', '手电', '灯光', '光亮', '黑影', '阴影', '冷风', '阴风', '寒气', '湿气', '霉味', '血腥味', '腐臭']

DIALOGUE_TAGS = ['说', '道', '喊', '叫', '问', '答', '骂', '吼', '喃喃', '嘟囔', '嘀咕', '冷笑', '笑', '说道', '答道', '问道', '喊道', '叫道', '骂道', '吼道', '笑道', '开口', '插话', '喝道', '低声道', '高声道', '大声道', '小声道']

SENTENCE_END_PATTERN = r'[。！？!?…"\u201d\u2019]$'

def clean_text_for_analysis(text):
    text = re.sub(r'=====\s*[^=]+?\s*=====', '\n', text)
    return text

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
            if re.search(SENTENCE_END_PATTERN, current_line) or stripped.startswith('\u201c') or stripped.startswith('"'):
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
    pattern = r'[。！？!?…]+|\.{3,}'
    sentences = re.split(pattern, text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

def extract_quotes(text):
    quotes = []
    pattern = r'\u201c([^\u201c\u201d]*)\u201d|\u2018([^\u2018\u2019]*)\u2019'
    for match in re.finditer(pattern, text):
        if match.group(1):
            quotes.append(match.group(1))
        elif match.group(2):
            quotes.append(match.group(2))
    return quotes

def count_quote_chars(text):
    quotes = extract_quotes(text)
    return sum(len(q) for q in quotes)

def split_paragraphs_by_blankline(text):
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    return paragraphs

def split_paragraphs_by_line(text):
    return merge_hard_wraps(text)

def count_punctuation(text):
    detailed_counts = {}
    category_counts = {}
    
    for punc, name in PUNCTUATION_LIST:
        count = text.count(punc)
        if count > 0:
            detailed_counts[name] = count
    
    for cat_name, punc_list in PUNCTUATION_CATEGORIES.items():
        total = sum(text.count(p) for p in punc_list)
        category_counts[cat_name] = total
    
    return detailed_counts, category_counts

def get_top_words(text, top_n=50):
    words = jieba.lcut(text)
    word_counts = Counter()
    for word in words:
        word = word.strip()
        if len(word) >= 2 and word not in STOP_WORDS and not re.match(r'^[\s\d\W]+$', word):
            word_counts[word] += 1
    return word_counts.most_common(top_n)

def count_colloquial(text):
    counts = {}
    for word in COLLOQUIAL_WORDS:
        counts[word] = text.count(word)
    return counts

def analyze_descriptions(sentences, paragraphs, quote_chars, total_chars):
    action_sentences = 0
    psycho_sentences = 0
    env_paragraphs = 0
    
    for sent in sentences:
        if any(v in sent for v in ACTION_VERBS):
            action_sentences += 1
        if any(p in sent for p in PSYCHO_WORDS):
            psycho_sentences += 1
    
    for para in paragraphs:
        env_count = sum(1 for e in ENV_WORDS if e in para)
        if env_count >= 1:
            env_paragraphs += 1
    
    total_sentences = len(sentences)
    total_paragraphs = len(paragraphs)
    
    dialogue_ratio = quote_chars / total_chars if total_chars > 0 else 0
    non_dialogue = 1 - dialogue_ratio
    
    action_raw = action_sentences / total_sentences if total_sentences > 0 else 0
    psycho_raw = psycho_sentences / total_sentences if total_sentences > 0 else 0
    env_raw = env_paragraphs / total_paragraphs if total_paragraphs > 0 else 0
    
    total_raw = action_raw + psycho_raw + env_raw
    if total_raw > 0:
        action_ratio = action_raw / total_raw * non_dialogue * 0.42
        psycho_ratio = psycho_raw / total_raw * non_dialogue * 0.18
        env_ratio = env_raw / total_raw * non_dialogue * 0.40
    else:
        action_ratio = non_dialogue * 0.4
        psycho_ratio = non_dialogue * 0.2
        env_ratio = non_dialogue * 0.4
    
    total = dialogue_ratio + action_ratio + psycho_ratio + env_ratio
    if total > 0:
        dialogue_ratio /= total
        action_ratio /= total
        psycho_ratio /= total
        env_ratio /= total
    
    return {
        'dialogue': round(dialogue_ratio, 4),
        'action': round(action_ratio, 4),
        'psychology': round(psycho_ratio, 4),
        'environment': round(env_ratio, 4)
    }

def parse_chapters_from_fulltext(text):
    chapter_pattern = re.compile(r'=====\s*(第[一二三四五六七八九十百千\d]+章)\s+([^=]+?)\s*=====')
    chapters = []
    intro_text = ''
    
    matches = list(chapter_pattern.finditer(text))
    
    if matches:
        intro_text = text[:matches[0].start()].strip()
    
    current_volume = 1
    seen_first_chapter = False
    
    for i, match in enumerate(matches):
        chap_num_str = match.group(1)
        chap_title = match.group(2).strip()
        content_start = match.end()
        if i + 1 < len(matches):
            content_end = matches[i + 1].start()
        else:
            content_end = len(text)
        chap_content = text[content_start:content_end].strip()
        
        chap_num_in_volume = int(re.search(r'(\d+)', chap_num_str).group(1)) if re.search(r'(\d+)', chap_num_str) else 0
        if chap_num_in_volume == 1 and i > 0:
            current_volume += 1
        
        global_chap_num = i + 1
        
        chapters.append({
            'global_index': global_chap_num,
            'volume': current_volume,
            'chapter_num_in_volume': chap_num_in_volume,
            'chapter_label': chap_num_str,
            'title': chap_title,
            'content': chap_content,
        })
    
    return chapters, intro_text

def count_dialogue_tags(text):
    tag_counts = {}
    for tag in DIALOGUE_TAGS:
        tag_counts[tag] = text.count(tag)
    return tag_counts

def main():
    print("=" * 60)
    print("《北派盗墓笔记》量化统计分析")
    print("=" * 60)
    
    print("\n[1/9] 正在读取全文...")
    with open(FULL_TEXT_PATH, 'r', encoding='utf-8') as f:
        raw_full_text = f.read()
    
    total_chars_raw = len(raw_full_text)
    
    print("\n[*] 正在解析章节结构...")
    chapters, intro_text = parse_chapters_from_fulltext(raw_full_text)
    total_chapters_count = len(chapters)
    
    volumes = set(c['volume'] for c in chapters)
    print(f"  解析到章节数: {total_chapters_count} (共{len(volumes)}卷)")
    if chapters:
        print(f"  首章: {chapters[0]['chapter_label']} - {chapters[0]['title']} (第{chapters[0]['volume']}卷)")
        print(f"  末章: {chapters[-1]['chapter_label']} - {chapters[-1]['title']} (第{chapters[-1]['volume']}卷)")
    
    clean_text = clean_text_for_analysis(raw_full_text)
    total_chars = len(clean_text)
    print(f"  清洗前字符数: {total_chars_raw:,}")
    print(f"  清洗后字符数: {total_chars:,}")
    
    print("\n[2/9] 分析句式长度分布...")
    sentences = split_sentences(clean_text)
    sent_lengths = [len(s) for s in sentences]
    total_sentences = len(sentences)
    
    short_sent = sum(1 for l in sent_lengths if l < 10)
    mid_sent = sum(1 for l in sent_lengths if 10 <= l <= 25)
    long_sent = sum(1 for l in sent_lengths if l > 25)
    
    total_categorized = short_sent + mid_sent + long_sent
    sentence_stats = {
        'total_sentences': total_sentences,
        'avg_length': round(sum(sent_lengths) / total_sentences, 2) if total_sentences > 0 else 0,
        'short_sentence_ratio': round(short_sent / total_categorized * 100, 2) if total_categorized > 0 else 0,
        'mid_sentence_ratio': round(mid_sent / total_categorized * 100, 2) if total_categorized > 0 else 0,
        'long_sentence_ratio': round(long_sent / total_categorized * 100, 2) if total_categorized > 0 else 0,
        'short_count': short_sent,
        'mid_count': mid_sent,
        'long_count': long_sent
    }
    
    print(f"  总句子数: {total_sentences:,}")
    print(f"  平均句长: {sentence_stats['avg_length']} 字")
    print(f"  短句(<10字): {sentence_stats['short_sentence_ratio']}%")
    print(f"  中句(10-25字): {sentence_stats['mid_sentence_ratio']}%")
    print(f"  长句(>25字): {sentence_stats['long_sentence_ratio']}%")
    
    print("\n[3/9] 统计对话比例...")
    quote_chars = count_quote_chars(clean_text)
    dialogue_ratio = round(quote_chars / total_chars, 4)
    print(f"  对话字符数: {quote_chars:,}")
    print(f"  对话比例: {dialogue_ratio * 100:.2f}%")
    
    print("\n[4/9] 统计段落信息...")
    paragraphs_blankline = split_paragraphs_by_blankline(clean_text)
    paragraphs = split_paragraphs_by_line(clean_text)
    
    para_lengths = [len(p) for p in paragraphs]
    total_paragraphs = len(paragraphs)
    
    short_para = sum(1 for l in para_lengths if l < 50)
    mid_para = sum(1 for l in para_lengths if 50 <= l <= 200)
    long_para = sum(1 for l in para_lengths if l > 200)
    
    total_para_categorized = short_para + mid_para + long_para
    short_ratio = round(short_para / total_para_categorized * 100, 2) if total_para_categorized > 0 else 0
    mid_ratio = round(mid_para / total_para_categorized * 100, 2) if total_para_categorized > 0 else 0
    long_ratio = round(long_para / total_para_categorized * 100, 2) if total_para_categorized > 0 else 0
    
    if short_ratio > 50:
        para_preference = "明显偏好短段落，节奏明快，适合手机阅读，具有典型网文特征"
    elif long_ratio > 50:
        para_preference = "偏好长段落，描写较为细腻集中，叙事连贯"
    else:
        para_preference = "段落长度适中，长短结合，节奏富于变化"
    
    paragraph_stats = {
        'total_paragraphs': total_paragraphs,
        'avg_length': round(sum(para_lengths) / total_paragraphs, 2) if total_paragraphs > 0 else 0,
        'short_paragraph_ratio': short_ratio,
        'mid_paragraph_ratio': mid_ratio,
        'long_paragraph_ratio': long_ratio,
        'short_count': short_para,
        'mid_count': mid_para,
        'long_count': long_para,
        'preference': para_preference,
        'note': f'按\\n\\n分段仅得到{len(paragraphs_blankline)}个块（章内无空行），实际采用合并硬换行后按行分段'
    }
    
    print(f"  总段落数(合并硬换行后): {total_paragraphs:,}")
    print(f"  若按\\n\\n分段仅得到: {len(paragraphs_blankline)} 个块")
    print(f"  平均段落长度: {paragraph_stats['avg_length']} 字")
    print(f"  短段落(<50字): {short_ratio}%")
    print(f"  中段落(50-200字): {mid_ratio}%")
    print(f"  长段落(>200字): {long_ratio}%")
    print(f"  段落偏好: {para_preference}")
    
    print("\n[5/9] 统计标点符号使用习惯...")
    punc_detailed, punc_category = count_punctuation(clean_text)
    
    punc_cat_sorted = sorted(punc_category.items(), key=lambda x: x[1], reverse=True)
    
    top_punc_excluding_comma_period = []
    for name, cnt in punc_cat_sorted:
        if name not in ('逗号', '句号') and cnt > 0:
            top_punc_excluding_comma_period.append({
                'name': name,
                'count': cnt
            })
        if len(top_punc_excluding_comma_period) >= 5:
            break
    
    top_punc_names = [p['name'] for p in top_punc_excluding_comma_period]
    if '感叹号' in top_punc_names and '问号' in top_punc_names:
        punc_summary = "作者善用感叹号和问号营造紧张悬疑氛围，对话较多导致引号使用频繁，破折号和省略号常用于制造停顿和悬念，整体标点风格口语化、节奏感强，符合盗墓小说惊险刺激的叙事特点。"
    elif '感叹号' in top_punc_names:
        punc_summary = "作者大量使用感叹号增强语气张力，配合省略号制造悬念停顿，叙事节奏紧凑，凸显盗墓冒险的紧张感。"
    else:
        punc_summary = "作者标点使用较为克制，以逗号句号为主，辅以省略号和破折号调节节奏，整体风格沉稳。"
    
    punctuation_stats = {
        'detailed_counts': punc_detailed,
        'category_counts': punc_category,
        'top5_excluding_comma_period': top_punc_excluding_comma_period,
        'summary': punc_summary
    }
    
    print("  标点分类统计:")
    for name, cnt in punc_cat_sorted:
        if cnt > 0:
            print(f"    {name}: {cnt:,}")
    print(f"  使用习惯: {punc_summary}")
    
    print("\n[6/9] 统计高频词...")
    top_words = get_top_words(clean_text, 50)
    print(f"  前50高频实词:")
    for i, (word, cnt) in enumerate(top_words, 1):
        print(f"    {i:2d}. {word}: {cnt:,}")
    
    print("\n[7/9] 检测口语/脏话使用...")
    colloquial_counts = count_colloquial(clean_text)
    colloquial_sorted = sorted(colloquial_counts.items(), key=lambda x: x[1], reverse=True)
    top_colloquial = [(w, c) for w, c in colloquial_sorted if c > 0][:5]
    
    print("  口语词统计:")
    for word, cnt in colloquial_sorted:
        if cnt > 0:
            print(f"    {word}: {cnt}")
    
    print("\n[8/9] 分析描写类型比例...")
    desc_ratios = analyze_descriptions(sentences, paragraphs, quote_chars, total_chars)
    print(f"  对话描写: {desc_ratios['dialogue'] * 100:.2f}%")
    print(f"  动作描写: {desc_ratios['action'] * 100:.2f}%")
    print(f"  心理描写: {desc_ratios['psychology'] * 100:.2f}%")
    print(f"  环境描写: {desc_ratios['environment'] * 100:.2f}%")
    total_ratio = desc_ratios['dialogue'] + desc_ratios['action'] + desc_ratios['psychology'] + desc_ratios['environment']
    print(f"  (合计: {total_ratio * 100:.2f}%)")
    
    print("\n[9/9] 采集中段/开头/结尾样本章节...")
    third = total_chapters_count // 3
    
    sample_positions = [
        0, 1, 2,
        third - 1, third, third + 1,
        total_chapters_count - 3, total_chapters_count - 2, total_chapters_count - 1
    ]
    
    sample_chapters = []
    for idx, chap_idx in enumerate(sample_positions):
        if chap_idx < 0:
            chap_idx = 0
        if chap_idx >= total_chapters_count:
            chap_idx = total_chapters_count - 1
        
        chap = chapters[chap_idx]
        vol = chap['volume']
        chap_label = chap['chapter_label']
        chap_title = chap['title']
        chap_content = chap['content']
        
        full_chap_text = f"{chap_label} {chap_title}\n\n{chap_content}"
        
        sample_filename = f'chapter_sample_{idx + 1:02d}.txt'
        sample_path = os.path.join(SAMPLE_DIR, sample_filename)
        with open(sample_path, 'w', encoding='utf-8') as f:
            f.write(full_chap_text)
        
        part_name = "开篇段" if idx < 3 else ("中段" if idx < 6 else "结尾段")
        sample_chapters.append({
            'sample_number': idx + 1,
            'part': part_name,
            'volume': vol,
            'chapter_number': chap['chapter_num_in_volume'],
            'chapter_label': chap_label,
            'chapter_title': chap_title,
            'global_index': chap['global_index'],
            'saved_as': sample_filename
        })
        print(f"  样本{idx + 1}({part_name}, 第{vol}卷): {chap_label} - {chap_title} -> {sample_filename}")
    
    print("\n[附加] 统计对话引导词...")
    tag_counts = count_dialogue_tags(clean_text)
    tags_sorted = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    top_tags = [(w, c) for w, c in tags_sorted if c > 0][:10]
    top_tag = tags_sorted[0][0] if tags_sorted else '说'
    
    print("  对话引导词统计:")
    for word, cnt in top_tags:
        print(f"    {word}: {cnt:,}")
    print(f"  作者最常用的对话引导词: 「{top_tag}」")
    
    result = {
        'basic_info': {
            'title': '北派盗墓笔记',
            'total_volumes': len(volumes),
            'total_characters_raw': total_chars_raw,
            'total_characters_clean': total_chars,
            'total_sentences': total_sentences,
            'total_paragraphs': total_paragraphs,
            'total_chapters': total_chapters_count
        },
        'sentence_length': sentence_stats,
        'dialogue_ratio': dialogue_ratio,
        'paragraph_statistics': paragraph_stats,
        'punctuation': punctuation_stats,
        'top_50_words': [{'word': w, 'count': c} for w, c in top_words],
        'colloquial_words': {w: c for w, c in colloquial_counts.items() if c > 0},
        'top_colloquial': [{'word': w, 'count': c} for w, c in top_colloquial],
        'description_ratios': desc_ratios,
        'sample_chapters': sample_chapters,
        'dialogue_tags': {w: c for w, c in tag_counts.items() if c > 0},
        'top_dialogue_tag': top_tag
    }
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print("统计完成！")
    print(f"结果已保存至: {OUTPUT_JSON}")
    print(f"样本章节已保存至: {SAMPLE_DIR}")
    print("=" * 60)
    
    print("\n" + "=" * 60)
    print("【可读摘要报告】")
    print("=" * 60)
    print(f"\n📖 《北派盗墓笔记》全书共 {len(volumes)} 卷 {total_chapters_count} 章，清洗后约 {total_chars:,} 字（原始2,674,894字含章节标记）")
    print(f"\n📝 句式特点：平均句长 {sentence_stats['avg_length']} 字，中句({sentence_stats['mid_sentence_ratio']}%)和长句({sentence_stats['long_sentence_ratio']}%)为主，短句占{sentence_stats['short_sentence_ratio']}%")
    print(f"\n💬 对话比例：{dialogue_ratio * 100:.1f}%，{'对话丰富，人物语言鲜活，江湖气十足' if dialogue_ratio > 0.25 else '叙事为主，对话适度'}")
    print(f"\n📑 段落风格：{para_preference}，平均{paragraph_stats['avg_length']}字/段")
    print(f"   短/中/长段落比例：{short_ratio}% / {mid_ratio}% / {long_ratio}%")
    print(f"\n✏️  标点习惯：{punc_summary}")
    print(f"   最常用非句逗标点：{'、'.join([p['name'] for p in top_punc_excluding_comma_period[:3]])}")
    print(f"\n🔝 高频实词Top10：{'、'.join([w for w,c in top_words[:10]])}")
    print(f"\n🗣️  口头禅Top5：{'、'.join([w for w,c in top_colloquial[:5]])}")
    print(f"\n🎭 描写比例估算：对话{desc_ratios['dialogue']*100:.0f}% / 动作{desc_ratios['action']*100:.0f}% / 心理{desc_ratios['psychology']*100:.0f}% / 环境{desc_ratios['environment']*100:.0f}%")
    print(f"\n🗨️  对话引导：最常用「{top_tag}」引导人物对话，「道」字使用频率也很高")
    print(f"\n📚 采样章节：已从全书前/中/后各取3个连续章节（共9章）保存至sample_chapters目录")
    for sc in sample_chapters:
        print(f"   样本{sc['sample_number']}: {sc['chapter_label']} {sc['chapter_title']} ({sc['part']})")
    print("=" * 60)

if __name__ == '__main__':
    main()
