#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""末日丧尸库自检：编号唯一性、价格带、跨类同价、引用有效性、计数。

用法： python tools/check.py
输出： 08_索引/CHECK_REPORT.md
"""
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CODE_RE = re.compile(r'^(SUP-\d{3}|MED-\d{3}|WPN-M\d{2}|WPN-F\d{2}|AMM-\d{2}|ARM-\d{2}|'
                     r'TOOL-\d{2}|MAT-\d{2}|VEH-\d{2}|GROW-\d{2}|RARE-\d{2})$')

INDEX_MD = os.path.join('交易系统', '商品索引.md')
MANUAL_MD = os.path.join('交易系统', '末日生存交易手册.md')


def md_files():
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d != 'site']
        for fn in filenames:
            if fn.endswith('.md'):
                out.append(os.path.join(dirpath, fn))
    return sorted(out)


def rel(p):
    return os.path.relpath(p, ROOT).replace('\\', '/')


def cells_of(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def parse_index(path):
    rows, problems = [], []
    with open(path, encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            if not line.lstrip().startswith('|'):
                continue
            cells = cells_of(line)
            if not cells:
                continue
            code = cells[0].strip().strip('*')
            if not CODE_RE.match(code):
                continue
            price = None
            for raw in cells[1:5]:
                cand = raw.replace('SP', '').replace('*', '').strip()
                if re.fullmatch(r'\d+', cand):
                    price = int(cand)
                    break
            if price is None:
                problems.append('条目无价格：%s（第 %d 行）' % (code, i))
                continue
            rows.append((code, price, i))
    return rows, problems


def parse_bands(manual):
    """从手册 B1 表解析 (前缀, 编号区间) → 价格带。"""
    ranges = []
    if not os.path.exists(manual):
        return ranges
    tok_re = re.compile(r'^([A-Z]+(?:-[A-Z])?)[-_]?(\d+)(?:～(\d+))?$')
    with open(manual, encoding='utf-8') as f:
        for line in f:
            if not line.lstrip().startswith('|'):
                continue
            cells = cells_of(line)
            if len(cells) < 4:
                continue
            seg, band = cells[2], cells[3]
            m = re.fullmatch(r'(\d+)[—~-](\d+)', band.replace(' ', ''))
            if not m:
                continue
            lo_p, hi_p = int(m.group(1)), int(m.group(2))
            last_prefix = None
            for token in re.split(r'[、,，/]', seg):
                token = token.strip()
                tm = tok_re.match(token)
                if tm:
                    last_prefix = tm.group(1)
                    lo_n = int(tm.group(2))
                    hi_n = int(tm.group(3)) if tm.group(3) else lo_n
                    ranges.append((last_prefix, lo_n, hi_n, lo_p, hi_p))
                    continue
                # 省略前缀的写法，如 "13～16" / "017"
                nm = re.fullmatch(r'(\d+)(?:～(\d+))?', token)
                if nm and last_prefix:
                    lo_n = int(nm.group(1))
                    hi_n = int(nm.group(2)) if nm.group(2) else lo_n
                    ranges.append((last_prefix, lo_n, hi_n, lo_p, hi_p))
    return ranges


def main():
    files = md_files()
    problems = []

    index_path = os.path.join(ROOT, INDEX_MD)
    if not os.path.exists(index_path):
        print('缺少商品索引：' + INDEX_MD)
        return 1
    rows, p2 = parse_index(index_path)
    problems += p2

    # 编号唯一（跨类重复允许，但必须同价）
    seen, dup_same = {}, defaultdict(int)
    for code, price, ln in rows:
        if code in seen:
            if seen[code] != price:
                problems.append('同编号不同价：%s 第 %d 行 %d ≠ 前次 %d' % (code, ln, price, seen[code]))
            else:
                dup_same[code] += 1
        else:
            seen[code] = price
    unique_codes = len(seen)

    # 价格带
    bands = parse_bands(os.path.join(ROOT, MANUAL_MD))
    if not bands:
        problems.append('未能从手册 B1 解析价格带（表格格式可能已改）')
    for code, price, ln in rows:
        cm = re.match(r'^([A-Z]+(?:-[A-Z])?)[-_]?(\d+)$', code)
        prefix, num = cm.group(1), int(cm.group(2))
        hit = None
        for bp, lo_n, hi_n, lo_p, hi_p in bands:
            if bp == prefix and lo_n <= num <= hi_n:
                hit = (lo_p, hi_p)
                break
        if not hit:
            problems.append('编号无可对照品类：%s' % code)
            continue
        lo, hi = hit
        if not (lo <= price <= hi):
            problems.append('价格越出价格带：%s 价格 %d 不在区间 %d—%d'
                            % (code, price, lo, hi))

    # 交叉引用
    ref_re = re.compile(r'`([0-9A-Za-z_\u4e00-\u9fff][^`\n]*?\.md)`')
    refs_total, broken = 0, []
    for p in files:
        text = open(p, encoding='utf-8').read()
        for m in ref_re.finditer(text):
            target = m.group(1)
            if '/' not in target:
                continue
            refs_total += 1
            if not os.path.exists(os.path.join(ROOT, target.replace('/', os.sep))):
                broken.append('%s → %s' % (rel(p), target))
    for b in sorted(set(broken)):
        problems.append('引用失效：' + b)

    # 计数
    all_text = ''
    for p in files:
        all_text += open(p, encoding='utf-8').read() + '\n'
    counts = {}
    for label, pat in [('LOC 地点', r'LOC-\d{2}'), ('F 势力', r'F-0\d'),
                       ('NPC 人物', r'NPC-\d{2}'), ('EV 事件', r'EV-\d{2}'),
                       ('MS 里程碑', r'MS-\d{2}'), ('SPC 特殊能力', r'SPC-0\d'),
                       ('Z 丧尸编号', r'Z-[1-6][a-z]?')]:
        counts[label] = len(set(re.findall(pat, all_text)))
    counts['交易条目（唯一编号）'] = unique_codes
    counts['md 文件数'] = len(files)

    out = ['# 自检报告\n', '> 由 `tools/check.py` 自动生成，请勿手改。\n',
           '## 一、计数\n', '| 项目 | 数量 |', '|---|---|']
    for k, v in counts.items():
        out.append('| %s | %s |' % (k, v))
    out += ['\n## 二、价格与引用检查\n',
            '- 索引条目行数：%d（唯一编号 %d，跨类重复登记 %d 行）'
            % (len(rows), unique_codes, sum(dup_same.values())),
            '- 已对照品类区间：%d 条（来源：手册 B1 表）' % len(bands),
            '- 交叉引用：%d 处，失效 %d 处' % (refs_total, len(set(broken))), '']
    if problems:
        out.append('### 发现 %d 个问题\n' % len(problems))
        for x in problems:
            out.append('- ' + x)
    else:
        out.append('### 全部通过：编号唯一、价格带合规、跨类同价、引用有效。\n')

    report = os.path.join(ROOT, '08_索引', 'CHECK_REPORT.md')
    with open(report, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')

    print('条目行 %d / 唯一 %d / 引用 %d' % (len(rows), unique_codes, refs_total))
    if problems:
        print('问题 %d 个：' % len(problems))
        for x in problems[:30]:
            print(' -', x)
        return 1
    print('OK 全部通过')
    return 0


if __name__ == '__main__':
    sys.exit(main())
