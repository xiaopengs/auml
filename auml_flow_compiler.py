#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUML @flow compiler prototype (v0.2)
====================================
Parses a subset of the AUML `@flow` DSL and emits:
  - an executable workflow DAG (JSON)
  - a Mermaid diagram
  - static semantic warnings (per WOD/GLD spec)

New in v0.2:
  - @subflow reuse:   define `@subflow X { ... }`, reference via `use X`
  - loop bounds:      `A ↺|c<0.8,max=3| B`  (reflect edge with max_iter)
  - parallel fork:    `parallel[p=a,b,c]` node (branches listed in `p=`)

Usage:
  python3 auml_flow_compiler.py                      # run built-in v0.2 example
  python3 auml_flow_compiler.py --input file.flow    # compile a file
  python3 auml_flow_compiler.py --mermaid-only       # only print mermaid
"""
import re
import json
import sys
import argparse

# ---------- pattern helpers ----------
DECL_RE = re.compile(r'^@(\w+)\s+(\w+)\s*(.*)$')
FLOW_OPEN_RE = re.compile(r'^@(flow|subflow)\s+(\S+)\s*\{$')
ANNOT_RE = re.compile(r'\[([^\]]+)\]')
GUARD_RE = re.compile(r'(\w+)\s*\{([^}]+)\}')
ARROW_RE = re.compile(r'(->|⇢|⇉|↺|☑|⤓)')


def parse_annotations(text):
    out = {}
    for m in ANNOT_RE.finditer(text):
        body = m.group(1)
        for part in body.split(','):
            if '=' in part:
                k, v = part.split('=', 1)
                out[k.strip()] = v.strip()
    return out


def parse_token(tok):
    """Return (name, annot_dict, guard_expr_or_None)."""
    tok = tok.strip()
    pm = re.match(r'parallel\[p=([^\]]+)\]', tok)
    if pm:
        return 'parallel', {'p': pm.group(1)}, None
    gm = GUARD_RE.search(tok)
    if gm:
        name = gm.group(1)
        guard = gm.group(2).strip()
        annot = parse_annotations(tok)
        return name, annot, guard
    annot = parse_annotations(tok)
    name = re.sub(r'\[[^\]]*\]', '', tok).strip()
    return name, annot, None


def parse_edge(line):
    cond = None
    max_iter = None
    m = re.search(r'\|([^|]+)\|', line)
    if m:
        raw = m.group(1).strip()
        line = line[:m.start()] + line[m.end():]
        conds = []
        for p in raw.split(','):
            p = p.strip()
            if p.startswith('max='):
                try:
                    max_iter = int(p[4:])
                except ValueError:
                    pass
            elif p:
                conds.append(p)
        cond = ','.join(conds) if conds else None
    am = ARROW_RE.search(line)
    if not am:
        return None
    arrow = am.group(1)
    src = line[:am.start()].strip()
    dst = line[am.end():].strip()
    return src, dst, arrow, cond, max_iter


def normalize(tok):
    """Map `use X` tokens to subflow references."""
    tok = tok.strip()
    if tok.startswith('use '):
        return tok[4:].strip(), 'subflow'
    return tok, None


# node type heuristics (entity declarations override these)
def infer_type(name, declared):
    if name in declared.get('agent', {}):
        return 'agent'
    if name in declared.get('tool', {}):
        return 'tool'
    if name in declared.get('human', {}):
        return 'human'
    low = name.lower()
    if name.startswith('event') or low == 'start':
        return 'event'
    if name.startswith('guardrail') or name.startswith('guard'):
        return 'guardrail'
    if name.startswith('fallback'):
        return 'fallback'
    if name.startswith('reply') or name.startswith('emit') or low == 'end':
        return 'end'
    if name.startswith('router'):
        return 'router'
    if name.startswith('parallel'):
        return 'parallel'
    return 'step'


EDGE_KIND = {
    '->': 'sequence',
    '⇢': 'dataflow',
    '⇉': 'delegate',
    '↺': 'reflect',
    '☑': 'approve',
    '⤓': 'fallback',
}


def compile_text(text):
    declared = {'agent': {}, 'tool': {}, 'human': {}, 'subflow': {}}
    flows = []
    cur = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or line.startswith('//'):
            continue
        dm = DECL_RE.match(line)
        if dm and not (line.startswith('@flow') or line.startswith('@subflow')):
            kind, name, rest = dm.group(1), dm.group(2), dm.group(3)
            if kind in declared:
                declared[kind][name] = parse_annotations(rest)
            continue
        fm = FLOW_OPEN_RE.match(line)
        if fm:
            kind = 'subflow' if line.startswith('@subflow') else 'flow'
            cur = {'name': fm.group(2), 'kind': kind, 'nodes': {}, 'edges': []}
            if kind == 'subflow':
                declared['subflow'][fm.group(2)] = cur
            else:
                flows.append(cur)
            continue
        if line == '}':
            cur = None
            continue
        if cur is None:
            continue
        e = parse_edge(line)
        if not e:
            continue
        src_tok, dst_tok, arrow, cond, max_iter = e
        s_raw, s_annot, s_guard = parse_token(src_tok)
        d_raw, d_annot, d_guard = parse_token(dst_tok)
        s_name, s_force = normalize(s_raw)
        d_name, d_force = normalize(d_raw)
        for (n_name, n_annot, n_guard, n_force) in (
                (s_name, s_annot, s_guard, s_force),
                (d_name, d_annot, d_guard, d_force)):
            if n_name not in cur['nodes']:
                ntype = n_force or infer_type(n_name, declared)
                cur['nodes'][n_name] = {
                    'id': n_name,
                    'type': ntype,
                    'annotations': n_annot,
                    'guard': n_guard,
                }
        edge = {
            'from': s_name,
            'to': d_name,
            'kind': EDGE_KIND.get(arrow, 'sequence'),
            'condition': cond,
        }
        if max_iter is not None:
            edge['max_iter'] = max_iter
        if s_annot:
            edge['from_annot'] = s_annot
        if d_annot:
            edge['to_annot'] = d_annot
        cur['edges'].append(edge)
    return declared, flows


def validate(flow):
    warnings = []
    nodes = flow['nodes']
    edges = flow['edges']
    subflows = flow.get('subflows', {})
    indeg = {n: 0 for n in nodes}
    outdeg = {n: 0 for n in nodes}
    for e in edges:
        outdeg[e['from']] += 1
        indeg[e['to']] += 1
    # 1. entry
    if not [n for n in nodes if indeg[n] == 0]:
        warnings.append('W1: 无入度为0的入口节点')
    # 2. exit
    if not [n for n in nodes if outdeg[n] == 0]:
        warnings.append('W2: 无出口节点(end/emit)')
    # 3. router coverage
    for n, info in nodes.items():
        if info['type'] == 'router':
            outs = [e for e in edges if e['from'] == n]
            if any(e['condition'] is None for e in outs):
                warnings.append(f'W3: router「{n}」存在无条件的出边')
    # 4. guardrail binary
    for n, info in nodes.items():
        if info['type'] == 'guardrail':
            outs = [e for e in edges if e['from'] == n]
            conds = [e['condition'] for e in outs if e['condition']]
            if len(conds) < 2:
                warnings.append(f'W4: guardrail「{n}」未区分 yes/no 二值条件')
    # 5. high-risk fallback
    for n, info in nodes.items():
        if info['annotations'].get('risk') == 'H':
            succ = [e['to'] for e in edges if e['from'] == n]
            succ_types = {nodes[s]['type'] for s in succ}
            if not (succ_types & {'human', 'fallback'}):
                warnings.append(f'W5: 高风险节点「{n}」缺少 Human/Fallback 兜底')
    # 6. reflect/retry must have max_iter
    for e in edges:
        if e['kind'] == 'reflect':
            mi = e.get('max_iter')
            if not mi or mi < 1:
                warnings.append(f'W6: 反思/重试边 {e["from"]}->{e["to"]} 缺少有效 max 上限')
    # 7. isolated
    for n in nodes:
        if indeg[n] == 0 and outdeg[n] == 0:
            warnings.append(f'W7: 孤立节点「{n}」')
    # 8. subflow reference exists
    for n, info in nodes.items():
        if info['type'] == 'subflow' and n not in subflows:
            warnings.append(f'W8: 引用未定义的子图「{n}」')
    # 9. parallel needs >=2 branches
    for n, info in nodes.items():
        if info['type'] == 'parallel':
            br = [b for b in info['annotations'].get('p', '').split(',') if b.strip()]
            if len(br) < 2:
                warnings.append(f'W9: parallel「{n}」分支不足2个')
    flow['warnings'] = warnings
    return warnings


def to_mermaid(flow):
    lines = ['flowchart TD']
    shape = {
        'agent': lambda n: f'{n}(({n}\\n🤖))',
        'tool': lambda n: f'{n}[{n}\\n🔧]',
        'human': lambda n: f'{n}([{n}\\n👤])',
        'router': lambda n: f'{n}{{ {n} }}',
        'guardrail': lambda n: f'{n}{{ {n}\\n🛡 }}',
        'fallback': lambda n: f'{n}[{n}\\n⤓]',
        'end': lambda n: f'{n}(({n}\\n🏁))',
        'event': lambda n: f'{n}[{n}\\n⚡]',
        'subflow': lambda n: f'{n}[/{n}\\n▣/]',
        'parallel': lambda n: f'{n}{{ {n}\\n⇉ }}',
    }
    for nid, info in flow['nodes'].items():
        lines.append('  ' + shape.get(info['type'], lambda x: f'{x}[{x}]')(nid))
    for e in flow['edges']:
        cond = f'|{e["condition"]}|' if e['condition'] else ''
        loop = f'|max={e["max_iter"]}|' if e.get('max_iter') else ''
        lines.append(f'  {e["from"]} -->{cond}{loop} {e["to"]}')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input')
    ap.add_argument('--mermaid-only', action='store_true')
    args = ap.parse_args()

    if args.input:
        with open(args.input, encoding='utf-8') as f:
            text = f.read()
    else:
        text = BUILTIN_EXAMPLE

    declared, flows = compile_text(text)
    result = {'declared': declared, 'flows': []}
    for flow in flows:
        flow['subflows'] = declared['subflow']
        validate(flow)
        result['flows'].append({
            'name': flow['name'],
            'nodes': list(flow['nodes'].values()),
            'edges': flow['edges'],
            'warnings': flow['warnings'],
        })
        if args.mermaid_only:
            print(to_mermaid(flow))
        else:
            print(f"=== @flow: {flow['name']} ===")
            print(json.dumps({
                'nodes': list(flow['nodes'].values()),
                'edges': flow['edges'],
            }, ensure_ascii=False, indent=2))
            if flow['warnings']:
                print('校验告警:')
                for w in flow['warnings']:
                    print('  -', w)
            else:
                print('校验: 通过 ✓')
            print(f"(子图定义: {list(declared['subflow'].keys())})")
            print('\n--- Mermaid ---\n' + to_mermaid(flow) + '\n')

    if args.input and not args.mermaid_only:
        with open(args.input + '.dag.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f'(已写出 {args.input}.dag.json)')


BUILTIN_EXAMPLE = r"""
@agent planner role=规划 al=2
@agent worker  role=执行 al=1
@agent critic  role=评审 al=2
@tool  search  in=q out=r idempotent=true
@human reviewer role=复审

@subflow 质检 {
  critic ->|c>=0.8| pass
  critic ->|c<0.8| fail
}

@flow 研究 {
  start -> planner
  planner -> parallel[p=worker,search]
  parallel[p=worker,search] -> reviewer
  reviewer -> use 质检
  use 质检 ->|pass| critic
  use 质检 ->|fail| worker
  worker -> critic
  critic ->|c>=0.8| end
  critic ↺|c<0.8,max=3| worker
}
"""

if __name__ == '__main__':
    main()
