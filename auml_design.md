AUML：面向智能体时代的统一架构语言（工作流编排脑洞版）

> 本篇为「脑爆」笔记。核心命题：经典 UML 是"人写代码、人读架构"的语言；AI 时代需要一套"人 + AI 共读共写、甚至可被智能体直接执行"的统一架构语言。AUML（Agentic UML）以智能体（Agent）为一等公民，以工作流编排为主轴，原生表达不确定性、记忆、人类回环与自治边界。

## 0. 一句话定位

把 UML 的"确定性组件 + 控制流"升级为"智能体 + 上下文流 + 不确定性"的可执行架构语言：图既能给人看，也能被编排引擎直接跑。

## 1. 设计动机：为什么 UML 不够了

- **执行者变了**：UML 假设执行单元是确定性代码；AI 时代的执行单元是非确定性智能体（同一输入可能不同输出）。
- **缺一等公民**：UML 没有原生图元表示 模型 / 提示词 / 上下文窗口 / 记忆 / 置信度 / 护栏。
- **闭环表达缺失**：经典活动图难以表达"规划 → 反思 → 重试 → 降级"这种自我修正闭环。
- **可执行性为零**：UML 是给人画的，LLM 读不懂也不会执行；新语言应当"图即代码，可被编译为工作流"。

## 2. 范式转变（UML → AUML）

| 维度 | 经典 UML | AUML |
|------|----------|------|
| 主角 | 类 / 组件 / 对象 | Agent（智能体） |
| 数据流 | 参数 / 消息 | Context（上下文包，含记忆） |
| 控制流 | 确定分支 | 概率路由 + 反思回环 |
| 不确定性 | 不表达 | 一等标注（置信度/成本/风险） |
| 人 | 仅作为 Actor | Human 是回路节点（审批/兜底） |
| 状态 | 有限状态机 | 记忆演化 + 上下文窗口 |
| 可执行 | 否 | 是（编译为编排 DAG） |
| 治理 | 无 | Guardrail / 熔断 / 审计 原生 |

## 3. 元模型（核心概念）

- **Agent**：带 角色 / 底座模型 / 温度 / 系统提示 / 自治等级 的执行单元。
- **Tool / Capability**：外部能力，定义 输入契约 / 输出契约 / 副作用 / 幂等性。
- **Memory**：短期（上下文窗口）、长期（持久化）、共享（多 Agent 公共）、向量（语义检索）。
- **Human**：审批者、信息提供方、监督兜底。
- **Context**：在节点间流动的"上下文包"，承载数据 + 记忆指针 + 元数据。
- **Event**：触发器（定时 / 消息 / 条件满足）。
- **Guardrail**：护栏、条件、熔断、合规校验。
- **三角形色**：Orchestrator（编排者）、Worker（执行者）、Critic（评审者）。

## 4. AUML 的七张图

### 4.1 ACD — 智能体协作图（对标 UML 类图/组件图）
定义系统里有哪些 Agent、各自的角色与能力边界，以及谁可以委托给谁。
图元：🤖 Agent、🧩 Capability、🔗 Delegate 边。

### 4.2 WOD — 工作流编排图（对标 UML 活动图）
把一个目标拆成步骤，标明每步由哪个 Agent / Tool 执行、上下文如何流动。这是最常用的图。
图元：🔀 Router（规划/路由）、⚙ Step、📦 Context 流、🛑 Guardrail。

### 4.3 RCD — 推理链图（对标 UML 时序图）
展示一次具体任务中，多个 Agent / Tool 如何按时间顺序交互、思考、调用、反思。
图元：时间轴 + 💬 invoke + 🔁 reflect。

### 4.4 MSD — 记忆与状态图（对标 UML 状态图）
定义 Agent 的短期/长期记忆如何演化、上下文窗口如何替换、状态如何转移。
图元：🧠 Memory、⟳ State、🪟 Context Window。

### 4.5 CCD — 能力契约图（对标 UML 接口图）
定义工具/外部服务的输入输出契约、副作用、幂等性、SLA。
图元：🔧 Tool 接口、📝 Contract、✅ Idempotent 标注。

### 4.6 GLD — 治理与回环图（全新）
表达审批、人工干预、护栏、失败重试、降级、熔断，是 AI 系统稳定运行的保障图。
图元：👤 Human Approve、🛡 Guardrail、⤓ Fallback、⚡ CircuitBreaker。

### 4.7 TRD — 信任拓扑图（全新）
表达 Agent 之间的信任关系、凭证、跨域授权、身份联邦（面向多组织多智能体协作）。
图元：🔐 Trust、🪪 Credential、🌐 Domain。

## 5. 图元库（符号速查）

**节点 Node**
- 🤖 Agent（角色 + 模型 + 自治等级）
- 🔧 Tool（能力契约）
- 🧠 Memory（短/长/共享/向量）
- 👤 Human（审批/提供/监督）
- 📦 Context（数据 + 记忆指针）
- ⚡ Event / Trigger
- 🛡 Guardrail（条件/熔断/合规）
- 🔀 Router / Planner（规划/路由）

**边 Edge**
- → invoke（调用）
- ⇢ dataflow（上下文流）
- ⇉ delegate / handoff（委托/交接）
- ⟶ message（消息）
- ↺ reflect / feedback（反思/反馈）
- ☑ approve（审批）
- ● trigger（触发）
- ⤓ fallback（降级）
- ⚡ break（熔断）

**不确定性标注（边/节点上可附）**
- 置信度 `c=0.82`
- 成本 `cost=$0.003`
- 延迟 `lat=1.2s`
- 风险 `risk=H/M/L`

## 6. 自治等级模型（Autonomy Levels, AL0–AL4）

- **AL0 纯工具**：确定性函数，无自主决策（等同传统 API）。
- **AL1 受限执行**：在固定工作流里调用 LLM 做单步生成。
- **AL2 步骤规划**：能自选工具顺序，但范围受限。
- **AL3 目标自治**：给定目标可自主拆解并迭代，关键节点需 Human 审批。
- **AL4 完全自主**：端到端自主，仅在护栏触发时上报。

> 设计原则：AL 越高，越需要 Guardrail 与 Human 回环兜底。

## 7. 不确定性标注体系

每条边 / 每个节点可挂四维标签，让架构图"可量化评估"：
- **c（Confidence）** 输出置信度，低于阈值触发反思或人工。
- **cost（Cost）** 单次调用成本（token / 费用）。
- **lat（Latency）** 时延预算。
- **risk（Risk）** 错误后果等级 H/M/L，驱动治理强度。

## 8. 文本 DSL：@flow

为可落地，定义一套类 PlantUML 的文本 DSL `@flow`，可编译为 LangGraph / AutoGen 等编排引擎。

语法骨架：
```
@agent 名字 role="..." model="..." al=2
@tool  名字 in=(...) out=(...) idempotent=true
@human 名字 role="approver"
@flow 工单处理 {
  start -> router[规划]
  router -> workerA[c=0.9]
  router -> workerB
  workerA -> guardrail{risk>=H?}
  guardrail ->|yes| human[审批]
  guardrail ->|no|  tool[写库]
  workerB -> critic[反思] ->|c<0.7| fallback[降级话术]
}
```

**完整示例：客服工单自动处理**
```
@agent triage   role="分类"      model="gpt-class"  al=1
@agent solver   role="解决"      model="gpt-solve"  al=3
@agent critic   role="质检"      model="gpt-crit"   al=2
@tool  kb       in=(query) out=(answer) idempotent=true
@human manager  role="审批复杂赔付"

@flow 工单 {
  event[新工单] -> triage[c=0.85]
  triage -> solver
  solver -> kb[查知识库]
  solver -> critic[质检 c=0.8]
  critic ->|c>=0.8| reply[自动回复]
  critic ->|c<0.8| manager[人工审批]
  solver ->|异常| fallback[降级:转人工]
}
```
这段 `@flow` 既能被人读懂，也能由编译器直接生成可执行工作流。

## 9. 与经典 UML 的映射

| UML 图 | AUML 对应 | 关键差异 |
|--------|-----------|----------|
| 类图 | ACD | 类→Agent+Capability，增加自治等级 |
| 活动图 | WOD | 增加反思回环、不确定性路由 |
| 时序图 | RCD | 增加反思/降级时序 |
| 状态图 | MSD | 增加记忆演化与上下文窗口 |
| 接口图 | CCD | 增加副作用/幂等/风险 |
| （无） | GLD / TRD | 全新：治理与信任 |

## 10. 工具链与开放问题

**理想工具链**
- 编译器：`@flow` → 可执行 DAG（LangGraph / AutoGen / Dify）。
- 可视化：双向编辑（图 ⇄ 文本）。
- 仿真：在沙箱跑一遍并标注 c/cost/lat/risk。
- 治理校验：静态检查 Guardrail 是否覆盖所有高风险边。
- 版本与差分：架构演进可 diff。

**开放问题（留给后续脑爆）**
1. 不确定性标注由谁给出（模型自评 / 历史统计）？
2. 多组织 TRD 信任拓扑如何用现有 OAuth/VC 落地？
3. AUML 是否需要标准化组织（类比 OMG 之于 UML）？
4. "可执行架构"会不会让架构图过度绑定某引擎？

---
*本篇为脑爆稿，欢迎继续发散。下一步可挑一张图做完整符号规范，或把 @flow 编译器原型化。*
