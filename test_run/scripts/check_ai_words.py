#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from collections import defaultdict

def load_text(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def count_word(text, word):
    pattern = re.compile(re.escape(word))
    return len(pattern.findall(text))

def count_pattern(text, pattern_str):
    pattern = re.compile(pattern_str)
    return len(pattern.findall(text))

def count_idioms(text):
    common_idioms = [
        '不可思议', '恍然大悟', '豁然开朗', '千钧一发', '危在旦夕',
        '惊心动魄', '胆战心惊', '心惊肉跳', '毛骨悚然', '不寒而栗',
        '面面相觑', '目瞪口呆', '瞠目结舌', '呆若木鸡', '怅然若失',
        '若有所思', '意味深长', '不置可否', '一针见血', '一语中的',
        '一鸣惊人', '一飞冲天', '龙争虎斗', '虎视眈眈', '狼吞虎咽',
        '狼狈为奸', '蛛丝马迹', '鸡飞狗跳', '鸡犬不宁', '狼狈不堪',
        '小心翼翼', '一丝不苟', '专心致志', '全神贯注', '聚精会神',
        '废寝忘食', '孜孜不倦', '夜以继日', '通宵达旦', '兢兢业业',
        '神采奕奕', '容光焕发', '炯炯有神', '意气风发', '斗志昂扬',
        '威风凛凛', '气宇轩昂', '风度翩翩', '落落大方', '温文尔雅',
        '五彩缤纷', '五颜六色', '五光十色', '万紫千红', '花红柳绿',
        '翠色欲流', '古色古香', '金碧辉煌', '富丽堂皇', '美轮美奂',
        '巧夺天工', '鬼斧神工', '栩栩如生', '活灵活现', '惟妙惟肖',
        '行云流水', '妙笔生花', '笔走龙蛇', '龙飞凤舞', '入木三分',
        '力透纸背', '一针见血', '鞭辟入里', '深入浅出', '通俗易懂',
        '博大精深', '源远流长', '历久弥新', '长盛不衰', '经久不衰',
        '叹为观止', '蔚为大观', '琳琅满目', '美不胜收', '目不暇接',
        '五花八门', '形形色色', '各种各样', '种类繁多', '应有尽有',
        '无所不包', '包罗万象', '一应俱全', '面面俱到', '无微不至',
        '举世闻名', '闻名遐迩', '名扬四海', '家喻户晓', '妇孺皆知',
        '赫赫有名', '鼎鼎大名', '如雷贯耳', '大名鼎鼎', '声名鹊起',
        '一帆风顺', '一路顺风', '万事如意', '心想事成', '梦想成真',
        '功成名就', '马到成功', '旗开得胜', '首战告捷', '百战百胜',
        '战无不胜', '攻无不克', '所向披靡', '势如破竹', '锐不可当',
        '雷厉风行', '大张旗鼓', '大刀阔斧', '焕然一新', '翻天覆地',
        '日新月异', '今非昔比', '物是人非', '时过境迁', '沧海桑田',
        '斗转星移', '春去秋来', '寒来暑往', '光阴似箭', '日月如梭',
        '白驹过隙', '稍纵即逝', '弹指之间', '昙花一现', '电光火石',
        '风驰电掣', '一日千里', '健步如飞', '大步流星', '步履维艰',
        '寸步难行', '举步维艰', '艰难险阻', '荆棘丛生', '坎坷不平',
        '崎岖不平', '一帆风顺', '一马平川', '畅通无阻', '四通八达',
        '人山人海', '摩肩接踵', '熙熙攘攘', '人头攒动', '水泄不通',
        '万人空巷', '座无虚席', '济济一堂', '人才济济', '人才辈出',
        '高手如林', '藏龙卧虎', '群英荟萃', '八仙过海', '各显神通',
        '一鸣惊人', '脱颖而出', '出类拔萃', '卓尔不群', '鹤立鸡群',
        '非同凡响', '与众不同', '别具一格', '独树一帜', '别开生面',
        '独具匠心', '匠心独运', '别出心裁', '标新立异', '推陈出新',
        '吐故纳新', '革故鼎新', '继往开来', '承前启后', '承上启下',
        '空前绝后', '史无前例', '前所未有', '开天辟地', '惊天动地',
        '震天动地', '惊心动魄', '触目惊心', '骇人听闻', '危言耸听',
        '耸人听闻', '惊世骇俗', '惊天地泣鬼神', '前无古人', '后无来者',
        '无与伦比', '无可比拟', '独一无二', '绝无仅有', '举世无双',
        '盖世无双', '天下第一', '首屈一指', '名列前茅', '鹤立鸡群',
        '独占鳌头', '金榜题名', '蟾宫折桂', '连中三元', '独占鳌头',
    ]
    count = 0
    for idiom in common_idioms:
        count += count_word(text, idiom)
    return count, len(common_idioms)

def main():
    text = load_text('/workspace/test_run/source/yunfeng/raw_text/full_text.txt')
    total_chars = len(text)
    print(f"全文总字符数: {total_chars}")
    print("="*80)
    
    categories = {
        "第一类：AI高频副词/动作词": [
            "喃喃道", "喃喃自语", "不禁", "竟然", "居然", "缓缓", "微微", "淡淡", "默默",
            "忽然", "突然"
        ],
        "第二类：网文烂俗表情/动作词": [
            "眼中闪过", "瞳孔骤缩", "倒吸一口凉气", "嘴角勾起", "一抹", "涌上心头",
            "暗道", "不置可否", "意味深长", "若有所思"
        ],
        "第三类：比喻/似乎类词": [
            "宛如", "犹如", "仿佛", "似乎", "般的"
        ],
        "第四类：心理/下意识类词": [
            "竟然", "不由得", "忍不住", "下意识"
        ],
        "第五类：心中暗道类": [
            "心中暗道", "暗自思忖", "心中一动"
        ],
        "第六类：时间瞬词": [
            "旋即", "刹那", "霎时", "顷刻间"
        ],
        "第七类：华丽辞藻类": [
            "璀璨", "绚烂", "瑰丽", "绮丽", "旖旎"
        ],
        "第八类：心理描写词": [
            "心里一紧", "心头一震", "心下了然", "恍然大悟", "豁然开朗"
        ],
    }
    
    results = {}
    for cat_name, words in categories.items():
        print(f"\n【{cat_name}】")
        for word in words:
            cnt = count_word(text, word)
            results[word] = cnt
            per_million = cnt / total_chars * 1000000
            print(f"  {word}: {cnt} 次 (每百万字 {per_million:.1f} 次)")
    
    print("\n" + "="*80)
    print("【第九类：'地'字结构副词+动词】")
    di_patterns = [
        "轻轻地", "慢慢地", "缓缓地", "默默地", "淡淡地",
        "冷冷地", "狠狠地", "重重地", "悄悄地", "偷偷地",
        "静静地", "紧紧地", "缓缓地", "淡淡地", "默默地"
    ]
    for pat in di_patterns:
        cnt = count_word(text, pat)
        results[pat] = cnt
        per_million = cnt / total_chars * 1000000
        print(f"  {pat}: {cnt} 次 (每百万字 {per_million:.1f} 次)")
    
    print("\n" + "="*80)
    print("【对话标签统计】")
    dialogue_tags = [
        "说", "道", "问", "答", "喊", "叫", "骂", "吼", "笑", "哭",
        "冷笑道", "怒道", "喝道", "低声道", "轻声道", "大声道",
        "冷冷地说", "淡淡地说", "缓缓地说", "默默地说"
    ]
    dialogue_results = {}
    for tag in dialogue_tags:
        cnt = count_word(text, tag)
        dialogue_results[tag] = cnt
        per_million = cnt / total_chars * 1000000
        print(f"  {tag}: {cnt} 次 (每百万字 {per_million:.1f} 次)")
    
    print("\n" + "="*80)
    idiom_count, idiom_total = count_idioms(text)
    print(f"【成语统计（抽样{idiom_total}个常见成语）】")
    print(f"  抽样成语总出现次数: {idiom_count} 次 (每百万字 {idiom_count/total_chars*1000000:.1f} 次)")
    
    print("\n" + "="*80)
    print("【作者常用词对比】")
    common_words = ["他妈的", "他妈", "我靠", "卧槽", "妈的", "草", "哎", "嗯", "啊", "哦"]
    for word in common_words:
        cnt = count_word(text, word)
        print(f"  {word}: {cnt} 次 (每百万字 {cnt/total_chars*1000000:.1f} 次)")
    
    print("\n" + "="*80)
    with open('/workspace/test_run/source/yunfeng/word_stats.txt', 'w', encoding='utf-8') as f:
        f.write(f"全文总字符数: {total_chars}\n\n")
        f.write("=== AI高频词统计结果 ===\n")
        for cat_name, words in categories.items():
            f.write(f"\n【{cat_name}】\n")
            for word in words:
                cnt = results[word]
                per_million = cnt / total_chars * 1000000
                f.write(f"  {word}: {cnt} 次 (每百万字 {per_million:.1f} 次)\n")
        f.write("\n=== '地'字结构统计 ===\n")
        for pat in di_patterns:
            cnt = results[pat]
            per_million = cnt / total_chars * 1000000
            f.write(f"  {pat}: {cnt} 次 (每百万字 {per_million:.1f} 次)\n")
        f.write("\n=== 对话标签统计 ===\n")
        for tag, cnt in dialogue_results.items():
            per_million = cnt / total_chars * 1000000
            f.write(f"  {tag}: {cnt} 次 (每百万字 {per_million:.1f} 次)\n")
        f.write(f"\n=== 成语统计 ===\n")
        f.write(f"抽样{idiom_total}个常见成语，总出现次数: {idiom_count} 次\n")
        f.write(f"每百万字出现: {idiom_count/total_chars*1000000:.1f} 次\n")

if __name__ == '__main__':
    main()
