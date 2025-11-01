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
