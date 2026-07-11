#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AUML SVG diagram generator — ASCII draft → SVG → base64 data URI."""
import base64, os, json, sys

OUT_DIR = '/sandbox/workspace/svgs'
os.makedirs(OUT_DIR, exist_ok=True)

PALETTE = {
    'event':'#1ABC9C','start':'#1ABC9C','agent':'#4A90D9','tool':'#7BC67E',
    'human':'#F5A623','router':'#9B59B6','guardrail':'#E74C3C','fallback':'#FF8C00',
    'parallel':'#E91E8C','subflow':'#85C1E9','end':'#95A5A6','emit':'#95A5A6',
    'breaker':'#F39C12','audit':'#3498DB','alarm':'#E74C3C','retry':'#E67E22',
}
WN=120; HN=40; LG=80; XG=150; XM=50

# ---------- layout ----------
def layout(nodes, edges):
    indeg={n['id']:0 for n in nodes}
    for e in edges: indeg[e['to']]+=1
    layers={}; visited=set(); queue=[n['id'] for n in nodes if indeg[n['id']]==0]
    visited.update(queue); lv=0
    while queue:
        nxt=[]
        for nid in queue:
            layers[nid]=lv
            for e in edges:
                if e['from']==nid and e['to'] not in visited:
                    indeg[e['to']]-=1
                    if indeg[e['to']]==0: nxt.append(e['to']); visited.add(e['to'])
        queue=nxt; lv+=1
    for n in nodes:
        if n['id'] not in layers: layers[n['id']]=lv
    by={}
    for nid,l in layers.items(): by.setdefault(l,[]).append(nid)
    pos={}
    for l in sorted(by):
        nids=by[l]; tw=len(nids)*XG; sx=max(XM,(600-tw)//2)
        for i,nid in enumerate(nids): pos[nid]=(sx+i*XG, 40+l*LG)
    return pos, layers

# ---------- SVG render ----------
def render(nodes, edges, title=''):
    pos,layers=layout(nodes,edges)
    my=max(p[1] for p in pos.values())+HN+50
    S=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 %d" width="600" height="%d">'%(my,my)]
    S.append('<style>text{font-family:system-ui,sans-serif;font-size:12px;fill:#2c3e50;text-anchor:middle}.c{font-size:10px;fill:#7f8c8d}.e{font-size:14px}</style>')
    S.append('<defs><marker id="a" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L10 5L0 10z" fill="#7f8c8d"/></marker></defs>')
    S.append('<rect width="600" height="%d" fill="#fafafa" rx="12"/>'%my)
    if title:
        S.append(f'<text x="300" y="20" font-size="14" font-weight="700" fill="#2c3e50">{title}</text>')
    for n in nodes:
        x,y=pos[n['id']]; c=PALETTE.get(n['type'],'#4A90D9')
        rx=12 if n['type'] in ('human','end','event','start','emit') else 6
        S.append(f'<rect x="{x}" y="{y}" width="{WN}" height="{HN}" rx="{rx}" fill="{c}" fill-opacity="0.12" stroke="{c}" stroke-width="2"/>')
        em=n.get('emoji',''); lb=n['label']
        if em:
            S.append(f'<text x="{x+18}" y="{y+HN//2+5}" class="e">{em}</text>')
            S.append(f'<text x="{x+WN//2+10}" y="{y+HN//2+5}" font-weight="600" fill="{c}" font-size="11">{lb}</text>')
        else:
            S.append(f'<text x="{x+WN//2}" y="{y+HN//2+5}" font-weight="600" fill="{c}" font-size="11">{lb}</text>')
    for e in edges:
        x1,y1=pos[e['from']]; x2,y2=pos[e['to']]
        cond=e.get('cond','')
        upward=layers[e['from']]>=layers[e['to']]
        if upward:
            sx=x1+WN; sy=y1+HN//2; ex=x2+WN; ey=y2+HN//2
            cx=max(sx,ex)+30; my2=(sy+ey)//2
            S.append(f'<path d="M{sx},{sy} C{cx},{sy} {cx},{ey} {ex},{ey}" stroke="#e74c3c" stroke-width="1.5" fill="none" stroke-dasharray="4,3" marker-end="url(#a)"/>')
            if cond: S.append(f'<text x="{cx+5}" y="{my2}" class="c">{cond}</text>')
        else:
            sx=x1+WN//2; sy=y1+HN; ex=x2+WN//2; ey=y2
            S.append(f'<line x1="{sx}" y1="{sy}" x2="{ex}" y2="{ey}" stroke="#7f8c8d" stroke-width="1.5" marker-end="url(#a)"/>')
            if cond:
                mx=(sx+ex)//2; my2=(sy+ey)//2-8
                S.append(f'<text x="{mx+8}" y="{my2}" class="c">{cond}</text>')
    S.append('</svg>')
    return '\n'.join(S)

# ---------- graph definitions ----------
FIG1_NODES=[
    {'id':'acd','label':'ACD 协作图','type':'agent','emoji':'🤖'},
    {'id':'wod','label':'WOD 编排图','type':'router','emoji':'🔀'},
    {'id':'trd','label':'TRD 信任图','type':'guardrail','emoji':'🔐'},
    {'id':'rcd','label':'RCD 推理链','type':'agent','emoji':'💬'},
    {'id':'msd','label':'MSD 记忆态','type':'agent','emoji':'🧠'},
    {'id':'ccd','label':'CCD 契约图','type':'tool','emoji':'🔧'},
    {'id':'gld','label':'GLD 治理图','type':'guardrail','emoji':'🛡'},
]
FIG1_EDGES=[
    {'from':'acd','to':'wod'},{'from':'acd','to':'trd'},
    {'from':'wod','to':'rcd'},{'from':'wod','to':'msd'},
    {'from':'wod','to':'ccd'},{'from':'wod','to':'gld'},
]

FIG2_NODES=[
    {'id':'ev','label':'新工单','type':'event','emoji':'⚡'},
    {'id':'rt','label':'路由','type':'router','emoji':'🔀'},
    {'id':'sv','label':'solver','type':'agent','emoji':'🤖'},
    {'id':'mg','label':'manager','type':'human','emoji':'👤'},
    {'id':'kb','label':'知识库','type':'tool','emoji':'🔧'},
    {'id':'gd','label':'护栏','type':'guardrail','emoji':'🛡'},
    {'id':'rp','label':'reply','type':'end','emoji':'📤'},
    {'id':'fb','label':'降级','type':'fallback','emoji':'⤓'},
    {'id':'en','label':'end','type':'end','emoji':'🏁'},
]
FIG2_EDGES=[
    {'from':'ev','to':'rt'},
    {'from':'rt','to':'sv','cond':'简单'},{'from':'rt','to':'mg','cond':'复杂'},
    {'from':'sv','to':'kb'},{'from':'sv','to':'gd'},
    {'from':'gd','to':'mg','cond':'yes'},{'from':'gd','to':'rp','cond':'no'},
    {'from':'sv','to':'fb','cond':'c<0.7'},{'from':'fb','to':'mg'},
    {'from':'rp','to':'en'},
]

FIG3_NODES=[
    {'id':'s','label':'Start','type':'start','emoji':'🚀'},
    {'id':'a','label':'Agent','type':'agent','emoji':'🤖'},
    {'id':'t','label':'Tool','type':'tool','emoji':'🔧'},
    {'id':'h','label':'Human','type':'human','emoji':'👤'},
    {'id':'r','label':'Router','type':'router','emoji':'🔀'},
    {'id':'g','label':'Guardrail','type':'guardrail','emoji':'🛡'},
    {'id':'f','label':'Fallback','type':'fallback','emoji':'⤓'},
    {'id':'em','label':'Emit','type':'emit','emoji':'📤'},
    {'id':'e','label':'End','type':'end','emoji':'🏁'},
]
FIG3_EDGES=[
    {'from':'s','to':'a'},
    {'from':'a','to':'t'},{'from':'a','to':'h'},{'from':'a','to':'r'},
    {'from':'r','to':'g'},{'from':'r','to':'f'},
    {'from':'g','to':'em'},{'from':'f','to':'e'},{'from':'em','to':'e'},
]

FIG4_NODES=[
    {'id':'req','label':'请求','type':'event','emoji':'📨'},
    {'id':'gd','label':'护栏','type':'guardrail','emoji':'🛡'},
    {'id':'ap','label':'审批','type':'human','emoji':'👤'},
    {'id':'ex','label':'执行','type':'agent','emoji':'🤖'},
    {'id':'cb','label':'熔断','type':'breaker','emoji':'⚡'},
    {'id':'fb','label':'降级','type':'fallback','emoji':'⤓'},
    {'id':'ok','label':'完成','type':'end','emoji':'✓'},
    {'id':'al','label':'告警','type':'alarm','emoji':'🚨'},
]
FIG4_EDGES=[
    {'from':'req','to':'gd'},
    {'from':'gd','to':'ap','cond':'yes'},{'from':'gd','to':'ex','cond':'no'},
    {'from':'ex','to':'cb'},
    {'from':'cb','to':'fb','cond':'open'},{'from':'cb','to':'ok','cond':'close'},
    {'from':'fb','to':'al'},{'from':'ap','to':'ok'},
]

# ---------- ASCII drafts ----------
ASCII = {
    'fig1': """\
  ┌──────────┐     ┌──────────┐
  │  ACD     │─────│  TRD     │
  │  协作图  │     │  信任图  │
  └──────────┘     └──────────┘
       │
       ▼
  ┌──────────┐
  │  WOD     │
  │  编排图  │
  └──────────┘
       │
  ┌────┼────────┬────┐
  │    │        │    │
  ▼    ▼        ▼    ▼
┌────┐┌────┐ ┌────┐┌────┐
│RCD ││MSD │ │CCD ││GLD │
│推理││记忆│ │契约││治理│
└────┘└────┘ └────┘└────┘""",
    'fig2': """\
⚡新工单 → 🔀路由
            ┌────┴────┐
            │简单  复杂│
            ▼         ▼
        🤖solver    👤manager
            │         │
        ┌───┼───┐     │
        │   │   │     │
        ▼   ▼   ▼     │
     🔧kb 🛡护栏 ⤓降级  │
            ││       │   │
          yes│no     │   │
            ▼ ▼     ▼   │
          👤 📤reply──→🏁end""",
    'fig3': """\
       🚀Start
          │
          ▼
       🤖Agent
     ┌────┼────┐
     │    │    │
     ▼    ▼    ▼
  🔧Tool 👤Human 🔀Router
               ┌──┼──┐
               │  │  │
               ▼  ▼  │
            🛡Guard ⤓Fallback
               │      │
               ▼      ▼
            📤Emit → 🏁End""",
    'fig4': """\
  📨请求 → 🛡护栏{risk>=H?}
              ┌────┴────┐
           yes│      no │
              ▼         ▼
           👤审批    🤖执行
              │         │
              │     ⚡熔断?
              │     ┌──┴──┐
              │  open│ close│
              │     ▼      ▼
              │   ⤓降级   ✓完成
              │     │
              │   🚨告警
              │
              └──→ ✓完成""",
}

# ---------- main ----------
FIGS = [('fig1','AUML 七图总览',FIG1_NODES,FIG1_EDGES),
        ('fig2','工单处理 WOD',FIG2_NODES,FIG2_EDGES),
        ('fig3','WOD 图元总览',FIG3_NODES,FIG3_EDGES),
        ('fig4','GLD 治理回路',FIG4_NODES,FIG4_EDGES)]

results = {}
for fid, title, nodes, edges in FIGS:
    svg = render(nodes, edges, title)
    path = os.path.join(OUT_DIR, f'{fid}.svg')
    with open(path, 'w', encoding='utf-8') as f: f.write(svg)
    b64 = base64.b64encode(svg.encode('utf-8')).decode('ascii')
    uri = f'data:image/svg+xml;base64,{b64}'
    results[fid] = {'svg_path': path, 'data_uri': uri, 'ascii': ASCII[fid], 'title': title}
    print(f"✓ {fid}: {title} → {path}")

# output JSON for downstream use
with open('/sandbox/workspace/svgs/results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("\nresults.json written.")
