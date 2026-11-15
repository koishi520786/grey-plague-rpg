#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""灰疫之年知识库 → 静态站点生成器（单源生成，不存第二份正文）。

特性：首页 / 分类浏览 / 关键词搜索（search-index.json）/ Markdown 原文链接 / 上下篇 / 移动端。

用法：
  python tools/build_site.py --src . --out site --repo koishi520786/grey-plague-rpg
兼容旧用法：--exclude 目录（可多次） --home 入口（生成跳转首页）
"""
import argparse
import html
import json
import os
import re
import shutil

import markdown

DEFAULT_ACCENT = "#c2410c"

CSS = r"""
:root{
  --bg:#faf8f5; --fg:#1d1a16; --muted:#6f675c; --line:#e4ded4; --card:#fff;
  --accent:%ACCENT%; --nav:#f3efe8; --code:#f4f1ea; --mark:#ffe08a;
}
html[data-theme="dark"]{
  --bg:#141210; --fg:#eae4d9; --muted:#a69d8f; --line:#332d26; --card:#1c1915;
  --nav:#191613; --code:#241f19; --mark:#7a5a12;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font:16px/1.78 -apple-system,"Segoe UI","Noto Sans SC","PingFang SC","Microsoft YaHei",sans-serif;
  -webkit-text-size-adjust:100%}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
img{max-width:100%}
.topbar{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 90%,transparent);
  backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
.topbar .in{max-width:1180px;margin:0 auto;padding:11px 20px;display:flex;align-items:center;gap:12px}
.brand{font-weight:700;font-size:15px;white-space:nowrap;color:var(--fg)}
.brand em{font-style:normal;color:var(--accent);margin:0 2px}
.tsearch{flex:1;max-width:420px;margin-left:auto}
.tsearch input{width:100%;padding:8px 12px;border:1px solid var(--line);border-radius:9px;
  background:var(--card);color:var(--fg);font-size:13.5px}
.iconbtn{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:9px;
  padding:7px 10px;font-size:12.5px;cursor:pointer;white-space:nowrap}
.menubtn{display:none}
.layout{max-width:1180px;margin:0 auto;display:flex;align-items:flex-start}
aside{width:280px;flex:0 0 280px;position:sticky;top:52px;height:calc(100vh - 52px);overflow-y:auto;
  padding:16px 12px 80px;border-right:1px solid var(--line)}
aside .grp>span{display:block;font-size:11.5px;letter-spacing:.08em;color:var(--muted);
  text-transform:uppercase;padding:9px 8px 4px}
aside a{display:block;font-size:13.4px;padding:5px 9px;border-radius:7px;color:var(--fg);opacity:.86;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
aside a:hover{background:var(--nav);opacity:1;text-decoration:none}
aside a.cur{background:var(--card);color:var(--accent);font-weight:600;opacity:1;
  box-shadow:inset 2px 0 0 var(--accent)}
main{flex:1;min-width:0;padding:32px 44px 130px}
.crumb{font-size:12.5px;color:var(--muted);margin-bottom:8px}
.crumb a{color:var(--muted)}
article{max-width:820px}
article h1{font-size:28px;line-height:1.35;margin:4px 0 6px}
article h2{font-size:20px;margin:34px 0 12px;padding-top:16px;border-top:1px solid var(--line)}
article h3{font-size:16.5px;margin:24px 0 8px}
article h4{font-size:14.6px;margin:18px 0 6px;color:var(--muted)}
article p{margin:10px 0}
article ul,article ol{padding-left:22px;margin:10px 0}
article li{margin:4px 0}
blockquote{margin:14px 0;padding:9px 15px;border-left:3px solid var(--accent);
  background:var(--card);color:var(--muted);font-size:14.6px;border-radius:0 8px 8px 0}
code{background:var(--code);padding:1px 5px;border-radius:4px;font-size:13px;
  font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
pre{background:var(--code);padding:13px 15px;border-radius:9px;overflow-x:auto;font-size:13px}
pre code{background:none;padding:0}
table{border-collapse:collapse;width:100%;margin:14px 0;font-size:13.6px;display:block;overflow-x:auto}
th,td{border:1px solid var(--line);padding:6px 10px;text-align:left;vertical-align:top}
th{background:var(--nav);font-weight:600;white-space:nowrap}
hr{border:none;border-top:1px solid var(--line);margin:26px 0}
mark{background:var(--mark);color:inherit;border-radius:3px;padding:0 2px}
.docbar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;max-width:820px;
  margin:0 0 14px;padding:9px 12px;border:1px solid var(--line);border-radius:10px;background:var(--card);
  font-size:12.5px;color:var(--muted)}
.docbar .sp{flex:1}
.pager{display:flex;justify-content:space-between;gap:12px;max-width:820px;margin-top:46px;
  padding-top:18px;border-top:1px solid var(--line);font-size:13.5px}
.pager a{max-width:47%}
.pager .lbl{display:block;font-size:11px;color:var(--muted)}
.hero{padding:50px 0 8px;max-width:860px}
.hero .kick{font-size:11.5px;letter-spacing:.24em;color:var(--muted);text-transform:uppercase}
.hero h1{font-size:36px;line-height:1.28;margin:12px 0 10px}
.hero p{color:var(--muted);font-size:15.4px;max-width:680px}
.hero .cta{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0 6px}
.btn{display:inline-block;padding:10px 18px;border-radius:10px;font-size:14px;font-weight:600;
  border:1px solid var(--accent);color:var(--accent)}
.btn.solid{background:var(--accent);color:#fff}
.btn:hover{text-decoration:none;opacity:.9}
.stats{display:flex;gap:26px;flex-wrap:wrap;margin:26px 0 8px;padding:18px 0;
  border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.stats div{font-size:12.5px;color:var(--muted)}
.stats b{display:block;font-size:22px;color:var(--fg);font-weight:700;line-height:1.3}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;margin:22px 0 40px;
  max-width:980px}
.card{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:17px 18px;
  transition:.15s ease}
.card:hover{border-color:var(--accent);transform:translateY(-2px)}
.card h3{margin:0 0 6px;font-size:15.5px}
.card h3 a{color:var(--fg)}
.card p{margin:0 0 10px;font-size:13px;color:var(--muted);line-height:1.6}
.card .n{font-size:11.5px;color:var(--accent);font-weight:600;letter-spacing:.06em;margin-bottom:8px}
.card ul{margin:0;padding-left:16px}
.card li{font-size:12.8px;color:var(--muted);margin:2px 0}
.card li a{color:var(--muted)}
.searchwrap{max-width:820px;padding-top:36px}
.searchbox{display:flex;gap:10px;margin:18px 0 8px}
.searchbox input{flex:1;padding:12px 15px;font-size:15px;border:1px solid var(--line);
  border-radius:11px;background:var(--card);color:var(--fg)}
.hits{margin:16px 0}
.hit{padding:13px 0;border-bottom:1px solid var(--line)}
.hit h3{margin:0 0 4px;font-size:15px}
.hit .path{font-size:11.5px;color:var(--muted);margin-bottom:6px}
.hit p{margin:0;font-size:13.4px;color:var(--muted)}
.hint{color:var(--muted);font-size:13.4px}
@media (max-width:900px){
  .menubtn{display:inline-block}
  aside{position:fixed;left:0;top:52px;z-index:19;background:var(--bg);
    transform:translateX(-100%);transition:.18s;width:84vw;max-width:320px;flex-basis:auto;height:calc(100vh - 52px)}
  aside.open{transform:none;box-shadow:0 12px 40px rgba(0,0,0,.22)}
  main{padding:20px 18px 90px}
  article{max-width:none}
  .hero{padding:28px 0 6px}
  .hero h1{font-size:26px}
  .tsearch{display:none}
  .pager{flex-direction:column}
  .pager a{max-width:none}
}
"""

JS = r"""
(function(){
  var root=document.documentElement;
  var KEY='gp-theme', saved=localStorage.getItem(KEY);
  if(saved){root.setAttribute('data-theme',saved);}
  else if(matchMedia('(prefers-color-scheme: dark)').matches){root.setAttribute('data-theme','dark');}
  var tb=document.getElementById('themeBtn');
  if(tb)tb.addEventListener('click',function(){
    var cur=root.getAttribute('data-theme')==='dark'?'light':'dark';
    root.setAttribute('data-theme',cur);localStorage.setItem(KEY,cur);
  });
  var mb=document.getElementById('menuBtn'), sb=document.getElementById('sidebar');
  if(mb&&sb)mb.addEventListener('click',function(){sb.classList.toggle('open');});
  var ts=document.getElementById('topSearch');
  if(ts)ts.addEventListener('keydown',function(e){
    if(e.key==='Enter'){
      var q=ts.value.trim(), r=root.getAttribute('data-root')||'';
      location.href=r+'search.html'+(q?('?q='+encodeURIComponent(q)):'');
    }
  });
})();
(function(){
  var box=document.getElementById('q'), out=document.getElementById('hits'), meta=document.getElementById('hitmeta');
  if(!box||!out)return;
  var data=null, root=document.documentElement.getAttribute('data-root')||'';
  function esc(s){return String(s).replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c];});}
  function hl(s,q){
    var i=s.toLowerCase().indexOf(q.toLowerCase());
    if(i<0)return esc(s);
    return esc(s.slice(0,i))+'<mark>'+esc(s.slice(i,i+q.length))+'</mark>'+esc(s.slice(i+q.length));
  }
  function render(q){
    if(!data)return;
    q=(q||'').trim();
    if(!q){out.innerHTML='';if(meta)meta.textContent='输入关键词开始检索，例如「苏晞」「Z-5」「反刷」「价格」「判定」。';return;}
    var terms=q.toLowerCase().split(/\s+/).filter(Boolean), hits=[];
    data.forEach(function(d){
      var hay=(d.t+' '+d.h+' '+d.b).toLowerCase(), score=0;
      for(var i=0;i<terms.length;i++){
        var t=terms[i], idx=hay.indexOf(t);
        if(idx<0){score=-1;break;}
        score += (d.t.toLowerCase().indexOf(t)>=0?8:0) + (d.h.toLowerCase().indexOf(t)>=0?3:0) + 1;
      }
      if(score<0)return;
      var body=d.b, pos=-1;
      for(var j=0;j<terms.length;j++){var k=body.toLowerCase().indexOf(terms[j]);if(k>=0&&(pos<0||k<pos))pos=k;}
      if(pos<0)pos=0;
      hits.push({d:d,s:score,snip:body.slice(Math.max(0,pos-70), Math.max(0,pos-70)+190)});
    });
    hits.sort(function(a,b){return b.s-a.s;});
    if(meta)meta.textContent='找到 '+hits.length+' 条结果';
    out.innerHTML=hits.slice(0,60).map(function(h){
      return '<div class="hit"><h3><a href="'+root+h.d.u+'">'+hl(h.d.t,q.split(/\s+/)[0])+'</a></h3>'+
        '<div class="path">'+esc(h.d.p)+'</div><p>'+esc(h.snip)+'…</p></div>';
    }).join('')||'<p class="hint">没有匹配的条目。</p>';
  }
  fetch(root+'search-index.json').then(function(r){return r.json();}).then(function(j){
    data=j; var q=new URLSearchParams(location.search).get('q')||''; box.value=q; render(q);
  }).catch(function(e){out.innerHTML='<p class="hint">搜索索引加载失败：'+esc(e)+'</p>';});
  box.addEventListener('input',function(){render(box.value);});
})();
"""


def collect(src, extra_skip=()):
    skip = {'site', '__pycache__', '.git', 'node_modules'} | set(extra_skip or ())
    out = []
    for dp, dns, fns in os.walk(src):
        dns[:] = sorted(d for d in dns if not d.startswith('.') and d not in skip)
        for fn in sorted(fns):
            if fn.lower().endswith('.md'):
                out.append(os.path.join(dp, fn))
    return out


def rel(p, base):
    return os.path.relpath(p, base).replace('\\', '/')


def strip_md(text):
    t = re.sub(r'```[\s\S]*?```', ' ', text)
    t = re.sub(r'`[^`]*`', ' ', t)
    t = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', t)
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)
    t = re.sub(r'^\s*[#>|\-*+\d\.]+\s*', ' ', t, flags=re.M)
    t = re.sub(r'[*_~|]', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()


def title_of(text, fallback):
    m = re.search(r'^#\s+(.+)$', text, flags=re.M)
    if m:
        return re.sub(r'[*`]', '', m.group(1)).strip()
    return fallback


def rewrite_links(body, src_root, cur_rel):
    cur_dir = os.path.dirname(cur_rel)
    depth = cur_rel.count('/')

    def rep(m):
        href = m.group(1)
        if href.startswith(('http', '#', 'mailto:', 'javascript:')):
            return m.group(0)
        anchor = ''
        if '#' in href:
            href, anchor = href.split('#', 1)
            anchor = '#' + anchor
        if not href.lower().endswith('.md'):
            return 'href="%s%s"' % (href, anchor)
        c1 = os.path.normpath(os.path.join(cur_dir, href))
        c2 = os.path.normpath(href)
        for cand in (c1, c2):
            if os.path.exists(os.path.join(src_root, cand.replace('/', os.sep))):
                target = cand.replace(os.sep, '/').replace('\\', '/')
                relpath = os.path.relpath(target, cur_dir or '.').replace(os.sep, '/')
                return 'href="%s%s"' % (relpath[:-3] + '.html', anchor)
        return 'href="%s%s"' % (('../' * depth if depth else '') + href[:-3] + '.html', anchor)

    return re.sub(r'href="([^"]+)"', rep, body)


def build(src, out, title, subtitle, accent, repo, exclude=(), home=None):
    files = collect(src, exclude)
    if not files:
        raise SystemExit('源目录没有 Markdown 文件：' + src)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(out, exist_ok=True)

    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'sane_lists', 'toc'],
                           extension_configs={'toc': {'permalink': False}})

    docs = []
    for p in files:
        r = rel(p, src)
        text = open(p, encoding='utf-8').read()
        heads = [h.strip('# ').strip() for h in re.findall(r'^#{2,3}\s+.+$', text, flags=re.M)]
        docs.append({'rel': r, 'title': title_of(text, os.path.basename(r)[:-3]), 'text': text,
                     'heads': heads, 'plain': strip_md(text),
                     'group': r.split('/')[0] if '/' in r else '根目录'})

    order = [d['rel'] for d in docs]
    by_group = {}
    for d in docs:
        by_group.setdefault(d['group'], []).append(d)
    for g in by_group:
        by_group[g].sort(key=lambda d: (0 if ('/00_' in d['rel'] or d['rel'].startswith('00_')) else 1, d['rel']))

    index = [{'t': d['title'], 'p': d['rel'], 'u': d['rel'][:-3] + '.html', 'g': d['group'],
              'h': ' · '.join(d['heads'][:14]), 'b': d['plain'][:2400]} for d in docs]
    json.dump(index, open(os.path.join(out, 'search-index.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)

    def sidebar(cur, ups=''):
        parts = ['<div class="grp"><span>导航</span><a href="%sindex.html">首页</a>'
                 '<a href="%ssearch.html">搜索</a></div>' % (ups, ups)]
        for g in sorted(by_group, key=lambda x: (x != '根目录', x)):
            parts.append('<div class="grp"><span>%s</span>' % html.escape(g))
            for d in by_group[g]:
                cls = ' class="cur"' if d['rel'] == cur else ''
                name = d['rel'].split('/')[-1][:-3]
                parts.append('<a href="%s%s.html"%s title="%s">%s</a>'
                             % (ups, d['rel'][:-3], cls, html.escape(d['rel']), html.escape(name)))
            parts.append('</div>')
        return '\n'.join(parts)

    alltext = '\n'.join(d['text'] for d in docs)
    stats = [('文档', len(docs)), ('字数', '%d 千' % (len(alltext) // 1000))]
    for label, pat in [('势力', r'F-0\d'), ('地点', r'LOC-\d{2}'), ('人物', r'NPC-\d{2}')]:
        stats.append((label, len(set(re.findall(pat, alltext)))))

    # 丧尸类型：只数图鉴里的二级标题，避免把"保留空号 Z-4b"算进去
    zfile = os.path.join(src, '02_丧尸', '02_丧尸类型图鉴.md')
    if os.path.exists(zfile):
        stats.append(('丧尸类型', len(re.findall(r'^#{2,3}\s+Z-', open(zfile, encoding='utf-8').read(),
                                            flags=re.M))))

    # 商品条目：只数索引表格中的编号行，避免把脚注里的空号算进去
    ifile = os.path.join(src, '交易系统', '商品索引.md')
    if os.path.exists(ifile):
        codes = set()
        for line in open(ifile, encoding='utf-8'):
            if line.lstrip().startswith('|'):
                c = line.strip().strip('|').split('|')[0].strip().strip('*')
                if re.fullmatch(r'(?:SUP|MED|AMM|ARM|MAT|TOOL|VEH|GROW|RARE)-\d{2,3}|WPN-[MF]\d{2}', c):
                    codes.add(c)
        stats.append(('商品条目', len(codes)))

    for i, d in enumerate(docs):
        md.reset()
        body = rewrite_links(md.convert(d['text']), src, d['rel'])
        prev_rel = order[i - 1] if i > 0 else None
        next_rel = order[i + 1] if i + 1 < len(order) else None
        depth = d['rel'].count('/')
        up = '../' * depth

        def lab(r):
            return os.path.basename(r)[:-3]

        pager = '<div class="pager">'
        pager += ('<a href="%s%s.html"><span class="lbl">← 上一篇</span>%s</a>'
                  % (up, prev_rel[:-3], html.escape(lab(prev_rel)))) if prev_rel else '<span></span>'
        pager += ('<a href="%s%s.html" style="text-align:right"><span class="lbl">下一篇 →</span>%s</a>'
                  % (up, next_rel[:-3], html.escape(lab(next_rel)))) if next_rel else '<span></span>'
        pager += '</div>'

        raw = 'https://github.com/%s/blob/main/%s' % (repo, d['rel'])
        docbar = ('<div class="docbar"><span>%s</span><span class="sp"></span>'
                  '<a href="%s" target="_blank" rel="noopener">Markdown 原文 ↗</a>'
                  '<a href="%ssearch.html?q=%s">全库搜索</a></div>'
                  % (html.escape(d['rel']), raw, up, html.escape(d['title'][:24])))

        main_html = ('<div class="crumb"><a href="%sindex.html">%s</a> / %s</div>%s'
                     '<article>\n%s\n</article>%s'
                     % (up, html.escape(title), html.escape(d['group']), docbar, body, pager))
        page = page_tpl(title=title, subtitle=subtitle,
                        head_title='%s · %s' % (d['title'], title),
                        root=up, nav=sidebar(d['rel'], up), main=main_html)
        out_path = os.path.join(out, d['rel'][:-3] + '.html')
        os.makedirs(os.path.dirname(out_path) or out, exist_ok=True)
        open(out_path, 'w', encoding='utf-8').write(page)

    cards = []
    for g in sorted(by_group, key=lambda x: (x != '根目录', x)):
        items = by_group[g]
        links = ''.join('<li><a href="%s.html">%s</a></li>' % (d['rel'][:-3], html.escape(d['title'][:26]))
                        for d in items[:5])
        cards.append('<div class="card"><div class="n">%d 篇</div><h3><a href="%s.html">%s</a></h3>'
                     '<p>%s</p><ul>%s</ul></div>'
                     % (len(items), items[0]['rel'][:-3], html.escape(g),
                        html.escape(desc_of(g, items)), links))
    stat_html = ''.join('<div><b>%s</b>%s</div>' % (html.escape(str(v)), html.escape(k)) for k, v in stats)
    landing = page_tpl(
        title=title, subtitle=subtitle, head_title=title, root='', nav=sidebar('__none__'),
        main='''<div class="hero">
  <div class="kick">Tabletop RPG Knowledge Base</div>
  <h1>灰疫之年 · 末日丧尸文字跑团库</h1>
  <p>2026 年 11 月 13 日，临江市陷落第七天。18 岁的沈砚和 16 岁的苏晞从断电的出租屋里睁眼——他身上多了一个只有他能看见的结算系统。</p>
  <div class="cta">
    <a class="btn solid" href="AI_START_HERE.html">从 AI_START_HERE 开始</a>
    <a class="btn" href="00_GM启动提示词.html">GM 启动提示词</a>
    <a class="btn" href="search.html">搜索全库</a>
  </div>
  <div class="stats">%s</div>
</div>
<h2 style="font-size:19px;margin:30px 0 4px">按目录浏览</h2>
<p class="hint" style="margin-top:0">每个目录的 <code>00_</code> 文件是索引，先读它再读正文；根目录的 <code>AI_START_HERE.md</code> 是接手说明。</p>
<div class="cards">%s</div>
<p class="hint">本页与全站页面均由仓库内 Markdown 自动生成，正文与 GitHub 同源，不另存第二份。</p>'''
        % (stat_html, ''.join(cards)))
    open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(landing)

    if home:
        open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(
            '<!DOCTYPE html><html><head><meta charset="utf-8">'
            '<meta http-equiv="refresh" content="0;url=%s"></head><body>'
            '<a href="%s">进入</a></body></html>' % (html.escape(home), html.escape(home)))
    else:
        open(os.path.join(out, 'search.html'), 'w', encoding='utf-8').write(page_tpl(
            title=title, subtitle=subtitle, head_title='搜索 · ' + title, root='',
            nav=sidebar('__none__'),
            main='''<div class="searchwrap">
  <div class="crumb"><a href="index.html">首页</a> / 搜索</div>
  <h1 style="font-size:26px;margin:6px 0 0">搜索全库</h1>
  <div class="searchbox"><input id="q" placeholder="苏晞 / Z-5 / 反刷 / 判定 / 价格 …" autocomplete="off"></div>
  <div class="hint" id="hitmeta">正在载入索引…</div>
  <div class="hits" id="hits"></div>
</div>'''))

    assets = os.path.join(out, 'assets')
    os.makedirs(assets, exist_ok=True)
    open(os.path.join(assets, 'style.css'), 'w', encoding='utf-8').write(CSS.replace('%ACCENT%', accent))
    open(os.path.join(assets, 'app.js'), 'w', encoding='utf-8').write(JS)
    open(os.path.join(out, '.nojekyll'), 'w').close()
    print('构建完成：%d 篇文档 → %s' % (len(docs), out))
    return len(docs)


DESC = {
    '01_世界观': '病毒编年、临江市地理与 24 个地点、8 个势力、气候季节、现实经济。',
    '02_丧尸': '感染机制、六类主型与四种演变态、分布迁移、对抗与清楼流程。',
    '03_角色': '主角沈砚、苏晞完整档案、26 名 NPC、关系网与十四天登场表。',
    '04_系统': 'SP 结算流程、反刷三系数、库存与负重规则。',
    '交易系统': '定价权威：手册（规则与平衡测试）与 168 条商品索引。',
    '系统设定': '经验与等级曲线、五项属性、15 项技能、升级条件与特殊能力。',
    '06_跑团规则': 'GM 总则、玩家控制权、叙事与苏晞演出、判定与战斗、生存与台账。',
    '07_剧本': '开场与三幕结构、第一章场景链、前十四天事件池。',
    '08_索引': '总索引、计数、关键词索引、自动自检报告。',
    '研究资料': '参照作品的系统机制对比与证据分级（只作参照，不作设定）。',
    '根目录': '接手入口、GM 启动提示词、项目说明、本地存档模板。',
}


def desc_of(g, items):
    return DESC.get(g, '共 %d 篇文档。' % len(items))


def page_tpl(title, subtitle, head_title, root, nav, main):
    side = ('<aside id="sidebar">%s</aside>' % nav) if nav is not None else ''
    return '''<!DOCTYPE html>
<html lang="zh-CN" data-root="{root}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{head_title}</title>
<meta name="description" content="{subtitle}">
<link rel="stylesheet" href="{root}assets/style.css">
</head>
<body>
<header class="topbar"><div class="in">
  <button class="iconbtn menubtn" id="menuBtn">目录</button>
  <a class="brand" href="{root}index.html">灰疫之年<em>·</em>跑团库</a>
  <div class="tsearch"><input id="topSearch" placeholder="搜索全库，回车确认"></div>
  <a class="iconbtn" href="{root}search.html">搜索</a>
  <button class="iconbtn" id="themeBtn">明/暗</button>
</div></header>
<div class="layout">
{side}
<main>
{main}
</main>
</div>
<script src="{root}assets/app.js"></script>
</body>
</html>
'''.format(root=root, head_title=html.escape(head_title), subtitle=html.escape(subtitle),
           side=side, main=main)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', default='.')
    ap.add_argument('--out', default='site')
    ap.add_argument('--title', default='灰疫之年 · 末日丧尸跑团库')
    ap.add_argument('--subtitle', default='现代丧尸末日文字跑团知识库')
    ap.add_argument('--accent', default=DEFAULT_ACCENT)
    ap.add_argument('--repo', default='koishi520786/grey-plague-rpg')
    ap.add_argument('--exclude', action='append', default=[])
    ap.add_argument('--home', default=None)
    a = ap.parse_args()
    build(os.path.abspath(a.src), os.path.abspath(a.out), a.title, a.subtitle,
          a.accent, a.repo, a.exclude, a.home)
