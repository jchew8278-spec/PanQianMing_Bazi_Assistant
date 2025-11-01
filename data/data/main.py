# -*- coding: utf-8 -*-
"""
main.py - 潘芊名命理解说助手（命令行版）
功能概览：
- 模块化菜单（可单选/多选）：八字分析 / 单年流年 / 区间流年 / 数字命理 / 推荐4位有利号码
- 自动公历 -> 农历（若环境可用 convertdate）
- 五行统计、水晶+精油建议、流年对策、特制随身香配方（示例）
- 友善的大白话输出（温柔口语风）
- 末尾署名： 潘芊名解忧馆解说｜仅供命主本人参考
"""

import json
import sys
import itertools
from datetime import datetime

# 尝试导入 convertdate（若不可用会降级为手动输入农历）
try:
    from convertdate import chinese
    HAS_CONVERTDATE = True
except Exception:
    HAS_CONVERTDATE = False

# ---- 基础常量 ----
TIANGAN = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
DIZHI   = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

# 干-五行、支-五行
GAN_WUXING = {
  '甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'
}
ZHI_WUXING = {
  '子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'
}

# 加载数据（请确保 data/crystals.json 和 data/oils.json 存在于仓库）
try:
    with open('data/crystals.json', 'r', encoding='utf-8') as f:
        CRYSTALS = json.load(f)
except Exception:
    # 默认备份数据（防止文件没放好）
    CRYSTALS = {
      "木": ["绿草莓晶", "葡萄石", "东陵玉"],
      "火": ["紫水晶", "南红玛瑙", "红发晶"],
      "土": ["黄水晶", "茶晶", "虎眼石"],
      "金": ["白水晶", "金发晶", "银曜石"],
      "水": ["海蓝宝", "月光石", "蓝纹玛瑙"],
      "护身": ["黑曜石", "金曜石", "黑玛瑙"]
    }

try:
    with open('data/oils.json', 'r', encoding='utf-8') as f:
        OILS = json.load(f)
except Exception:
    OILS = {
      "木": ["佛手柑", "依蘭依蘭"],
      "火": ["檀香", "乳香"],
      "土": ["廣藿香", "檀香"],
      "金": ["佛手柑", "乳香"],
      "水": ["洋甘菊", "乳香"]
    }

# -------------------------
# 数字命理配置（可调整）
# -------------------------
LETTER_TO_NUMBER = {
    'A':1,'B':2,'C':3,'D':4,'E':5,'F':6,'G':7,'H':8,'I':9,
    'J':1,'K':2,'L':3,'M':4,'N':5,'O':6,'P':7,'Q':8,'R':9,
    'S':1,'T':2,'U':3,'V':4,'W':5,'X':6,'Y':7,'Z':8
}
NUMBER_TO_WUXING = {
    1: '水',
    2: '土',
    3: '木',
    4: '木',
    5: '土',
    6: '金',
    7: '金',
    8: '土',
    9: '火'
}
DIGIT_ZERO_EQ = 8  # 0 视作 8 (土)，可调整

# 五行生克关系
GENERATION = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
HELPER_FOR = {'木':'水','火':'木','土':'火','金':'土','水':'金'}  # 想补 X，需要哪年元素
CONTROLS = {'木':'土','土':'水','水':'火','火':'金','金':'木'}

# ---------- 工具函数 ----------
def sexagenary_from_year_index(year_index):
    idx = (year_index - 1) % 60
    tg = TIANGAN[idx % 10]
    dz = DIZHI[idx % 12]
    return tg + dz

def chinese_from_gregorian(y,m,d):
    if not HAS_CONVERTDATE:
        return None
    try:
        cyc, year_index, month, leap, day = chinese.from_gregorian(y,m,d)
        return (cyc, year_index, month, leap, day)
    except Exception:
        return None

def ganzhi_and_element_for_year(year):
    """
    用天干来代表当年五行（常用简化方法）。
    公式：stem = TIANGAN[(year - 4) % 10], branch = DIZHI[(year - 4) % 12]
    （因为 1984 为甲子年 -> year-4 对齐）
    """
    stem = TIANGAN[(year - 4) % 10]
    branch = DIZHI[(year - 4) % 12]
    ganzhi = stem + branch
    element = GAN_WUXING.get(stem, None)
    return ganzhi, element

def reduce_number_keep_master(n):
    if n in (11,22):
        return n
    while n > 9:
        s = sum(int(d) for d in str(n))
        if s in (11,22):
            return s
        n = s
    return n

def number_from_digits_string(s):
    digits = [int(ch) for ch in s if ch.isdigit()]
    if not digits:
        return None
    total = sum(digits)
    return reduce_number_keep_master(total)

def name_to_number(name):
    total = 0
    for ch in name.upper():
        if ch in LETTER_TO_NUMBER:
            total += LETTER_TO_NUMBER[ch]
    if total == 0:
        return None
    return reduce_number_keep_master(total)

def number_to_wuxing(num):
    if num in (11,22):
        return "特殊主数"
    return NUMBER_TO_WUXING.get(num, "未知")

# 五行统计从柱
def elem_count_from_pillars(pillars):
    count = {'木':0,'火':0,'土':0,'金':0,'水':0}
    for p in pillars:
        if len(p) >= 1:
            tg = p[0]
            if tg in GAN_WUXING:
                count[GAN_WUXING[tg]] += 1
        if len(p) >= 2:
            dz = p[1]
            if dz in ZHI_WUXING:
                count[ZHI_WUXING[dz]] += 1
    return count

def summarize_wuxing(count):
    s = "、".join([f"{k}({count[k]})" for k in ['金','木','水','火','土']])
    summary = f"五行计数：{s}。"
    conclusion = []
    for k in ['金','木','水','火','土']:
        v = count[k]
        if v >= 3:
            conclusion.append(f"{k}偏旺")
        elif v <= 1:
            conclusion.append(f"{k}偏弱")
    if not conclusion:
        conclusion_text = "五行较为均衡。"
    else:
        conclusion_text = "，".join(conclusion) + "。"
    return summary + conclusion_text

# 选择水晶与精油
def choose_crystals_for_wuxing(count):
    weakest = sorted(count.items(), key=lambda x: x[1])[:2]
    left = []
    for k,v in weakest:
        if k in CRYSTALS:
            left.extend(CRYSTALS[k][:2])
    right = []
    # 右手优先稳土/稳金/护身
    right.extend(CRYSTALS.get('土', [])[:1])
    right.extend(CRYSTALS.get('金', [])[:1])
    right.extend(CRYSTALS.get('护身', [])[:1])
    return left, right

def choose_oils_for_wuxing(count):
    oils = []
    if count.get('木',0) <= 1:
        oils.append("佛手柑（提振人缘）")
    if count.get('水',0) <= 1:
        oils.append("乳香或洋甘菊（舒缓情绪）")
    oils.append("檀香（接地稳心）")
    return oils
    # -------------------------
# 数字模块函数（评分 + 替代 + 推荐号码）
# -------------------------
def score_number_against_profile(num, profile_count):
    if num in (11,22):
        return ("B", "主数为特殊主数（11/22），视为中性/需个别分析")
    wux = number_to_wuxing(num)
    if wux not in profile_count:
        return ("B", f"对应五行为 {wux}（系统默认未记录为强弱）")
    val = profile_count[wux]
    if val <= 1:
        return ("A", f"{wux}偏弱，数字可用来补益")
    elif val >= 3:
        return ("C", f"{wux}偏旺，使用该数字可能加剧偏旺")
    else:
        return ("B", f"{wux}处于中等水平，使用中性")

def suggest_alternatives_for_number_string(s):
    digits = ''.join(ch for ch in s if ch.isdigit())
    if not digits:
        return []
    base_list = []
    for d in range(10):
        candidate = digits[:-1] + str(d) if len(digits) > 1 else str(d)
        root = number_from_digits_string(candidate)
        base_list.append((candidate, root))
    uniq = {}
    for cand,root in base_list:
        if cand not in uniq:
            uniq[cand] = root
    items = list(uniq.items())[:30]
    out = []
    for cand, root in items[:6]:
        out.append((cand, root))
    return out

# 推荐4位号码模块
def digit_to_reduced_number(d):
    if not d.isdigit():
        return None
    val = int(d)
    if val == 0:
        val = DIGIT_ZERO_EQ
    return reduce_number_keep_master(val)

def digit_to_wuxing(d):
    r = digit_to_reduced_number(d)
    if r is None:
        return None
    if r in (11,22):
        return "特殊主数"
    return number_to_wuxing(r)

def candidate_matches_profile(candidate_str, profile_count, prefer_wuxings, avoid_wuxings):
    root = number_from_digits_string(candidate_str)
    if root is None:
        return False, "无数字"
    root_wux = number_to_wuxing(root)
    if prefer_wuxings:
        if root_wux not in prefer_wuxings:
            return False, f"主数五行 {root_wux} 非首选（偏好 {prefer_wuxings}）"
    avoid_count = 0
    for ch in candidate_str:
        w = digit_to_wuxing(ch)
        if w in avoid_wuxings:
            avoid_count += 1
    if avoid_count >= 2:
        return False, f"包含過多不利元素（{avoid_count} 位屬 {avoid_wuxings}）"
    return True, f"主數{root}（{root_wux}）符合偏好"

def generate_recommended_numbers(profile_count, length=4, n=15):
    weak = [k for k,v in profile_count.items() if v <= 1]
    strong = [k for k,v in profile_count.items() if v >= 3]
    prefer_wuxings = weak[:] if weak else ['木','火','土','金','水']
    avoid_wuxings = strong[:]
    results = []
    min_val = 0
    max_val = 10 ** length - 1
    val = min_val
    i = 0
    # 遍历直到找到 n 个推荐
    while val <= max_val and len(results) < n:
        s = str(val).zfill(length)
        ok, reason = candidate_matches_profile(s, profile_count, prefer_wuxings, avoid_wuxings)
        if ok:
            root = number_from_digits_string(s)
            results.append({'num': s, 'root': root, 'wuxing': number_to_wuxing(root), 'reason': reason})
        val += 1
        i += 1
        if i > 400000:  # 保护阈值
            break
    # 若不够，则放宽条件：只要主数不为避开五行
    if len(results) < n:
        val = 0
        while val <= max_val and len(results) < n:
            s = str(val).zfill(length)
            root = number_from_digits_string(s)
            if root is None:
                val += 1; continue
            root_wux = number_to_wuxing(root)
            if root_wux not in avoid_wuxings:
                results.append({'num': s, 'root': root, 'wuxing': root_wux, 'reason': '次优候選（避免忌用五行）'})
            val += 1
            if val > max_val:
                break
    return results[:n]

# -------------------------
# 流年评估（单年 / 区间）
# -------------------------
def assess_year_against_profile(year, profile_count):
    ganzhi, elem = ganzhi_and_element_for_year(year)
    weak = [k for k,v in profile_count.items() if v <= 1]
    strong = [k for k,v in profile_count.items() if v >= 3]
    notes = []
    advice = []
    helped = [w for w in weak if HELPER_FOR.get(w) == elem]
    if helped:
        notes.append(f"当年属{elem}（{ganzhi}），可补{'、'.join(helped)}（对偏弱项有帮助）")
        advice.append("建议：主动抓住机会、拓展人脉与学习，利用流年力量补短板。")
        purpose = 'boost'
    else:
        harmed = [s for s in strong if CONTROLS.get(elem) == s]
        if harmed:
            notes.append(f"当年属{elem}（{ganzhi}），可能会克{'、'.join(harmed)}，需注意情绪与健康")
            advice.append("建议：重要决策缓一缓，稳健为主，注重休息与情绪管理。")
            purpose = 'protect'
        else:
            notes.append(f"当年属{elem}（{ganzhi}），与命主关系中性，宜稳健行事")
            advice.append("建议：保持常态、稳步推进计划即可。")
            purpose = 'general'
    return {
        'year': year,
        'ganzhi': ganzhi,
        'element': elem,
        'note_lines': notes,
        'advice_lines': advice,
        'purpose': purpose
    }

def generate_liunian_range(profile_count, start_year=2026, end_year=2036):
    res = []
    for y in range(start_year, end_year+1):
        res.append(assess_year_against_profile(y, profile_count))
    return res

# ---------- 单年流年推荐（含水晶/精油/随身香案列） ----------
def crystal_oils_for_action(element, profile_count, purpose='general'):
    ELEMENT_TO_CRYSTALS = {
        '木': (['绿草莓晶','葡萄石'], ['黄水晶','虎眼石']),
        '火': (['紫水晶','南红玛瑙'], ['黑曜石','黄水晶']),
        '土': (['黄水晶','茶晶'], ['白水晶','虎眼石']),
        '金': (['白水晶','金发晶'], ['黑曜石','黄水晶']),
        '水': (['海蓝宝','月光石'], ['白水晶','黑曜石'])
    }
    ELEMENT_TO_OILS = {
        '木': ['佛手柑','依蘭依蘭'],
        '火': ['檀香','乳香'],
        '土': ['廣藿香','檀香'],
        '金': ['佛手柑','乳香'],
        '水': ['洋甘菊','乳香']
    }
    left, right = ELEMENT_TO_CRYSTALS.get(element, (['白水晶'], ['黑曜石']))
    oils = ELEMENT_TO_OILS.get(element, ['檀香'])
    perfume = ("10ml 随身香建议配方（示例）：\n"
               "- 顶调（清新）：{top} 3-4 滴\n"
               "- 中调（核心）：{mid} 3-4 滴\n"
               "- 基调（稳固）：{base} 2-3 滴\n"
               "使用提示：以无水基底或稀释酒精混合后喷洒，先做皮肤敏感测试。").format(
                   top=oils[0] if len(oils)>0 else '佛手柑',
                   mid=oils[1] if len(oils)>1 else oils[0],
                   base='檀香'
               )
    return left, right, oils, perfume

def get_single_year_recommendation(year, profile_count):
    info = assess_year_against_profile(year, profile_count)
    left, right, oils, perfume = crystal_oils_for_action(info['element'], profile_count, purpose=info['purpose'])
    lines = []
    lines.append(f"【{year} 年 — {info['ganzhi']} — 五行：{info['element']}】")
    lines.append("・判斷：" + "；".join(info['note_lines']))
    lines.append("・建議：" + "；".join(info['advice_lines']))
    lines.append("・左手（吸收/补益）建议： " + "、".join(left))
    lines.append("・右手（护身/守财）建议： " + "、".join(right))
    lines.append("・精油/香精建议： " + "、".join(oils))
    lines.append("・特製随身香配方（示例）：\n" + perfume)
    return "\n".join(lines)
    # -------------------------
# 完整八字+流年分析逻辑
# -------------------------
def get_full_analysis(name, birth_date_str, hour_str):
    try:
        y, m, d = map(int, birth_date_str.split('-'))
    except Exception:
        return "⚠️ 生日格式有误，请输入形如 1963-05-08"

    pillars = []
    ganzhi, elem = ganzhi_and_element_for_year(y)
    pillars.append(ganzhi)
    lunar_data = chinese_from_gregorian(y, m, d)
    if lunar_data:
        cyc, year_index, lm, leap, ld = lunar_data
        lunar_str = f"农历 {lm}月{ld}日"
    else:
        lunar_str = "农历需手动输入（convertdate不可用）"

    count = elem_count_from_pillars(pillars)
    summary = summarize_wuxing(count)
    left, right = choose_crystals_for_wuxing(count)
    oils = choose_oils_for_wuxing(count)

    output = []
    output.append(f"🌿【{name or '命主'}的八字五行分析】")
    output.append(f"公历生日：{birth_date_str} {hour_str}")
    output.append(f"{lunar_str}  → 年柱：{ganzhi}（{elem}）")
    output.append(summary)
    output.append(f"左手推荐水晶（补益方向）：{'、'.join(left)}")
    output.append(f"右手推荐水晶（守护方向）：{'、'.join(right)}")
    output.append(f"建议精油：{'、'.join(oils)}")
    return "\n".join(output)

# -------------------------
# 主菜单程序
# -------------------------
def main():
    print("✨ 欢迎使用：潘芊名命理解说助手（温柔口语版）")
    print("🌸 作者：潘芊名解忧馆解说｜仅供命主本人参考\n")
    name = input("请输入命主姓名（可留空）：") or "命主"
    birth_date = input("请输入公历生日（例 1963-05-08）：")
    hour_str = input("请输入出生时辰（例 未时，可留空）：")

    pillars = []
    try:
        y,m,d = map(int,birth_date.split('-'))
    except:
        print("⚠️ 日期格式错误，应为 1980-05-08")
        sys.exit(0)
    g,e = ganzhi_and_element_for_year(y)
    pillars.append(g)
    profile_count = elem_count_from_pillars(pillars)

    while True:
        print("\n========== 功能菜单 ==========")
        print("1）完整八字 + 流年分析 + 水晶 + 精油建议")
        print("2）查询某一年流年建议（含水晶香气）")
        print("3）查看流年区间（2026–2036）")
        print("4）单独查看八字五行平衡")
        print("5）数字命理分析（门牌/手机/车牌/英文名）")
        print("6）推荐 4 位有利号码")
        print("7）退出")
        print("=============================")

        choice = input("请输入选项数字：")
        if choice == '1':
            print("\n🪷【完整分析】")
            print(get_full_analysis(name, birth_date, hour_str))
            print("\n【2026–2036 流年趋势】")
            liu = generate_liunian_range(profile_count)
            for item in liu:
                print(get_single_year_recommendation(item['year'], profile_count))
                print("-" * 40)
        elif choice == '2':
            y = int(input("请输入要查询的年份（例 2026）："))
            print(get_single_year_recommendation(y, profile_count))
        elif choice == '3':
            start = 2026
            end = 2036
            liu = generate_liunian_range(profile_count, start, end)
            for item in liu:
                print(get_single_year_recommendation(item['year'], profile_count))
                print("-" * 40)
        elif choice == '4':
            print(get_full_analysis(name, birth_date, hour_str))
        elif choice == '5':
            s = input("请输入要分析的内容（门牌号、手机号、车牌或英文名）：")
            num = None
            if any(ch.isalpha() for ch in s):
                num = name_to_number(s)
            elif any(ch.isdigit() for ch in s):
                num = number_from_digits_string(s)
            else:
                print("⚠️ 未检测到有效字母或数字。")
                continue
            if num is None:
                print("⚠️ 无法计算主数。")
                continue
            score, desc = score_number_against_profile(num, profile_count)
            print(f"结果：主数 {num} → 五行：{number_to_wuxing(num)} → {desc}")
            print(f"评等：{score}")
            alt = suggest_alternatives_for_number_string(s)
            if alt:
                print("可参考相似组合：")
                for c, root in alt:
                    print(f"  {c} → {root}（{number_to_wuxing(root)}）")
        elif choice == '6':
            print("\n🔢【推荐 4 位有利号码】")
            results = generate_recommended_numbers(profile_count, 4, 12)
            for r in results:
                print(f"候选：{r['num']} → 主数{r['root']}（{r['wuxing']}） | {r['reason']}")
        elif choice == '7':
            print("\n🌸 感谢使用潘芊名命理解说助手。")
            print("✨ 潘芊名解忧馆解说｜仅供命主本人参考\n")
            break
        else:
            print("⚠️ 输入无效，请重新输入。")

if __name__ == "__main__":
    main()
