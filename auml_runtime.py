#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUML runtime prototype (v0.1)
==============================
Two backends for an AUML @flow DAG produced by auml_flow_compiler:
  1. emit_langgraph(dag) -> generates LangGraph-style Python source (text, not executed)
  2. MockRuntime.run()    -> local mock execution (no external LLM needed), prints a trace

Usage:
  python3 auml_runtime.py                 # run built-in v0.2 example
  python3 auml_runtime.py --flow x.flow  # run your .flow file
"""
import re
import sys
import argparse
from auml_flow_compiler import compile_text, BUILTIN_EXAMPLE


class MockRuntime:
    def __init__(self, dag):
        self.nodes = {n['id']: n for n in dag['nodes']}
        self.edges = dag['edges']
        self.loops = {}
        self.trace = []

    def out(self, nid):
        return [e for e in self.edges if e['from'] == nid]

    def match(self, cond, ctx):
        cond = cond.strip()
        if cond in ('yes',):
            return bool(ctx.get('_guard'))
        if cond in ('no',):
            return not ctx.get('_guard')
        m = re.match(r'(\w+)\s*(>=|<=|>|<|=)\s*(.+)', cond)
        if m:
            v = ctx.get(m.group(1))
            if v is None:
                return False
            try:
                return eval(f'{float(v)}{m.group(2)}{float(m.group(3))}')
            except Exception:
                return str(v) == m.group(3)
        return True

    def pick(self, edges, ctx):
        cond = [e for e in edges if e.get('condition')]
        dflt = [e for e in edges if not e.get('condition')]
        for e in cond:
            if self.match(e['condition'], ctx):
                return e
        return dflt[0] if dflt else (cond[0] if cond else None)

    def run(self, ctx=None):
        ctx = dict(ctx or {})
        indeg = {n: 0 for n in self.nodes}
        for e in self.edges:
            indeg[e['to']] += 1
        cur = next((n for n in self.nodes if indeg[n] == 0), None)
        if cur is None:
            self.trace.append('(无入口节点)')
            return self.trace
        steps = 0
        while cur and steps < 200:
            steps += 1
            node = self.nodes[cur]
            t = node['type']
            self.trace.append(f"▶ {cur} ({t})")
            if t in ('end', 'emit'):
                self.trace.append(f"  ✓ 输出: {ctx}")
                break
            if t == 'human':
                self.trace.append("  ⏸ 人工审批(模拟通过)")
                ctx['_approved'] = True
            elif t == 'guardrail':
                ctx['_guard'] = ctx.get('risk') == 'H'
                self.trace.append(f"  🛡 护栏 risk={ctx.get('risk')} -> {'yes' if ctx['_guard'] else 'no'}")
            elif t == 'fallback':
                self.trace.append("  ⤓ 降级执行")
            elif t == 'tool':
                self.trace.append(f"  🔧 工具 {cur}")
            elif t == 'agent':
                ctx['c'] = float(node['annotations'].get('c', '0.7'))
                self.trace.append(f"  🤖 Agent {cur} (c={ctx['c']})")
            elif t == 'subflow':
                self.trace.append(f"  ▣ 子图 {cur}")
            elif t == 'parallel':
                br = [b.strip() for b in node['annotations'].get('p', '').split(',') if b.strip()]
                self.trace.append(f"  ⇉ 并行分支 {br}")
            outs = self.out(cur)
            if not outs:
                break
            nxt = self.pick(outs, ctx)
            if nxt is None:
                break
            if nxt.get('kind') == 'reflect':
                k = (nxt['from'], nxt['to'])
                self.loops[k] = self.loops.get(k, 0) + 1
                if self.loops[k] > int(nxt.get('max_iter', 1)):
                    self.trace.append(f"  ↺ 循环达上限 {nxt.get('max_iter')}，退出")
                    others = [e for e in outs if e.get('kind') != 'reflect']
                    nxt = others[0] if others else None
                    if nxt is None:
                        break
            cur = nxt['to']
        return self.trace


def emit_langgraph(dag):
    L = ["from langgraph.graph import StateGraph, END",
         "from typing import TypedDict", "",
         "class State(TypedDict):", "    data: dict", "",
         "def build():", "    g = StateGraph(State)"]
    for n in dag['nodes']:
        L.append(f"    g.add_node('{n['id']}', node_{n['type']})")
    for e in dag['edges']:
        if e.get('condition'):
            L.append(f"    g.add_conditional_edges('{e['from']}', route_{e['from']}, "
                     f"{{'{e['condition']}': '{e['to']}'}})")
        elif e.get('kind') == 'reflect':
            L.append(f"    # reflect loop max={e.get('max_iter')}: g.add_edge('{e['from']}', '{e['to']}')")
        else:
            L.append(f"    g.add_edge('{e['from']}', '{e['to']}')")
    L.append("    return g")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--flow')
    args = ap.parse_args()
    text = open(args.flow, encoding='utf-8').read() if args.flow else BUILTIN_EXAMPLE
    _, flows = compile_text(text)
    for f in flows:
        dag = {'nodes': list(f['nodes'].values()), 'edges': f['edges']}
        print(f"=== dry_run: {f['name']} ===")
        for line in MockRuntime(dag).run(ctx={'risk': 'M'}):
            print(' ', line)
        print("\n--- LangGraph skeleton ---")
        print(emit_langgraph(dag))


if __name__ == '__main__':
    main()
