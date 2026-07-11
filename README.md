# AUML — Agentic Unified Modeling Language

面向 AI 智能体时代的统一架构语言（工作流编排版）。

## 项目结构

| 文件 | 说明 |
|------|------|
| `auml_design.md` | AUML 总览设计（七张图 + 范式转变 + DSL + 映射表） |
| `auml_wod_spec.md` | WOD 工作流编排图完整符号规范 |
| `auml_gld_spec.md` | GLD 治理回环图完整符号规范 |
| `auml_flow_compiler.py` | @flow DSL 编译器 v0.2（子图复用 / 循环上限 / 并行分叉） |
| `auml_runtime.py` | 执行后端（DAG→LangGraph 骨架 + mock dry-run） |
| `auml_svg_gen.py` | SVG 配图生成脚本（ASCII→SVG→base64 data URI） |
| `svgs/` | 生成的 4 张 SVG 图 + results.json |

## 快速开始

```bash
# 编译 @flow DSL（内置示例）
python3 auml_flow_compiler.py

# 编译自定义文件
python3 auml_flow_compiler.py --input my_flow.flow

# 仅输出 Mermaid 图
python3 auml_flow_compiler.py --mermaid-only

# 执行后端 dry-run
python3 auml_runtime.py

# 执行后端编译自定义文件
python3 auml_runtime.py --flow my_flow.flow

# 生成 SVG 配图
python3 auml_svg_gen.py
```

## AUML 七张图

| 图 | 名称 | 定位 |
|---|------|------|
| ACD | 智能体协作图 | 定义有哪些 Agent、角色、能力边界 |
| WOD | 工作流编排图 | 主轴：目标→步骤→执行→数据流 |
| RCD | 推理链图 | 时序视角：一次交互的完整链条 |
| MSD | 记忆与状态图 | Agent 记忆演化与上下文窗口 |
| CCD | 能力契约图 | Tool/服务的输入输出契约 |
| GLD | 治理与回环图 | 审批/护栏/降级/熔断 |
| TRD | 信任拓扑图 | 跨域信任、凭证、身份联邦 |

## @flow DSL 语法示例

```
@agent planner role=规划 al=2
@tool  search  in=q out=r idempotent=true

@subflow 质检 {
  critic ->|c>=0.8| pass
  critic ->|c<0.8| fail
}

@flow 研究 {
  start -> planner
  planner -> parallel[p=worker,search]
  parallel[p=worker,search] -> reviewer
  reviewer -> use 质检
  use 质检 ->|pass| end
  use 质检 ->|fail| worker
  worker -> critic
  critic ->|c>=0.8| end
  critic ↺|c<0.8,max=3| worker
}
```

## License

MIT
