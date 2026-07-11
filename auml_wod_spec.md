AUML·WOD 工作流编排图：完整符号规范（v0.1 脑爆稿）

> 本篇为「脑爆」笔记，是 AUML 七张图中的 **WOD（Workflow Orchestration Diagram，工作流编排图）** 的完整符号规范。WOD 是 AUML 的主轴图，表达"一个目标如何被拆解为有序步骤、每步由谁执行、Context 如何流动、失败/降级/审批如何介入"。

## 1. 用途与适用场景
- 把业务目标拆解为可执行的步骤序列。
- 标明每一步的执行主体（Agent / Tool / Human）。
- 表达 Context（数据 + 记忆）在步骤间的流动。
- 刻画 路由 / 护栏 / 降级 / 审批 等 AI 工作流特有的稳定性结构。
- 可作为 `@flow` 编译器（见配套原型）的输入，直接生成可执行 DAG。

## 2. 节点符号表（Node Symbols）

| 符号 | 名称 | 类型 | 语义 | 必填属性 | 可选标注 |
|------|------|------|------|----------|----------|
| 🚀 | Start | start | 工作流入口（可省略，首节点即入口） | id | — |
| 🏁 | End | end | 正常出口 | id | — |
| 🤖 | Agent | agent | 模型驱动的执行单元 | role, model, al | c, cost, lat, risk |
| 🔧 | Tool | tool | 外部/确定性能力 | in, out | idempotent, risk |
| 👤 | Human | human | 审批/提供/兜底 | role | risk |
| 🔀 | Router | router | 规划/路由分发 | strategy | — |
| 🛡 | Guardrail | guardrail | 条件校验/熔断 | rule | — |
| ⤓ | Fallback | fallback | 异常/低置信兜底 | to | — |
| 📤 | Emit | emit | 对外输出结果 | channel | — |
| ⚡ | Event | event | 外部事件触发起点 | source | — |

## 3. 边符号表（Edge Symbols）

| 符号 | 文本语法 | 语义 |
|------|----------|------|
| → | `A -> B` | 顺序流转（默认） |
| ⇢ | `A ⇢ B` | Context 数据流（强调数据载体） |
| ⇉ | `A ⇉ B` | 委托 / 交接（handoff） |
| \|cond\| | `A ->\|cond\| B` | 条件分支（必须带标签） |
| ↺ | `A ↺ B` | 反思 / 重试回环（必须带退出条件） |
| ☑ | `A ☑ B` | 需人工审批 |
| ⤓ | `A ⤓ B` | 降级路径 |

## 4. 标注体系（Annotation）

**节点标注**（写在节点名后 `[...]`）
- `c=0.9` 置信度
- `cost=$0.01` 单次成本
- `lat=2s` 时延预算
- `risk=H|M|L` 错误后果等级
- `role=...` / `model=...` / `al=2` 角色与自治等级
- `idempotent=true` 工具幂等性
- `strategy=rule|llm` 路由策略

**边标注**
- `|cond|` 条件分支标签（如 `|简单|`、`|c>=0.8|`、`|yes|`）
- 边可附加 `c=`、`risk=` 同节点。

## 5. 语法（文本 DSL 片段）

```
@flow 工单处理 {
  ⚡ event[新工单] -> 🔀 router[strategy=rule]
  🔀 router ->|简单| 🤖 solver[al=2,c=0.9]
  🔀 router ->|复杂| 👤 manager[role=审批]
  🤖 solver -> 🔧 kb[idempotent=true]
  🤖 solver -> 🛡 guardrail{risk>=H?}
  🛡 guardrail ->|yes| 👤 manager
  🛡 guardrail ->|no| 📤 reply
  🤖 solver ->|c<0.7| ⤓ fallback
  ⤓ fallback -> 👤 manager
  📤 reply -> 🏁 end
}
```

## 6. 语义规则（Semantics / 静态校验）

1. **入口**：每个 `@flow` 至少存在一个入度为 0 的节点作为起点。
2. **出口**：至少存在一个 `end` / `emit` 类出口节点。
3. **路由覆盖**：`router` 的所有出边必须带 `|cond|` 标签；建议条件互斥且全集覆盖。
4. **护栏二分**：`guardrail` 出边必须区分 `|yes|` / `|no|`（或等价二值条件）。
5. **高风险兜底**：任意 `risk=H` 的节点或边，其后必须存在 Human 回环（👤）或 Fallback（⤓）。
6. **回环可退出**：所有 `↺` 回环必须带退出条件，禁止无条件死循环。
7. **连通性**：从入口可达所有节点；无孤立节点。
8. **幂等约束**：被多次触发的 Tool（如写库）应标注 `idempotent=true`，否则编译器告警。

## 7. 布局约定
- 默认自上而下（TD）或自左向右（LR）。
- Router 置于分叉点，Guardrail 紧贴其保护的高风险节点之后。
- Human / Fallback 节点置于回环或分支末端，视觉上"兜底"。

## 8. 与 UML 活动图差异小结
- UML 活动图：确定性动作 + 决策节点；无智能体/记忆/置信度概念。
- WOD：执行主体是 Agent（带自治等级与不确定性），原生含 Guardrail / Fallback / Human 回环，且"图即代码"可被编译执行。

---
*配套交付：`auml_flow_compiler.py`（@flow 编译器原型），可将该 DSL 编译为可执行 DAG（JSON）+ Mermaid，并执行第 6 节的静态校验。*
