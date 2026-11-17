---
name: diagnose
description: 将 vLLM-Ascend profiling 与引擎语义映射成可核验的因子账本，识别限制、建立竞争假设并提出鉴别动作。用于独立 profiling 解析、覆盖审计或瓶颈分析。
---

# 找原因

本模块提供观测解析与机制推理两种能力，可直接接收独立任务。按 [任务契约](../references/suite_contract.md) 接手与返回；五步主线中的“找原因”仅是典型用途，不要求先运行其他模块。

## 公开输入与输出

| 能力 / role | 输入 | 公开产物 |
|---|---|---|
| 采集与映射 / profiling | 待回答问题、计量契约、基线总账、trace/日志、格式与采集身份、覆盖范围及访问条件 | [profiling 方法](references/profiling.md)：ledger、字段映射/解析器、覆盖/时钟说明、独立对账与最小补采计划 |
| 解释与鉴别 / diagnosis | 可信总账、负载/配置身份、观测账本与原件；按需附历史假设、实验和知识快照 | [推理方法](references/reasoning.md)：限制形态、竞争假设、预测/反证、排序及下一动作 |

产物结构由 [诊断记录契约](references/records.md) 维护。只读任务消费已有产物，不依赖协调者 state 的内部布局或其他模块临时目录；已具备可信账本可直接推理，缺内部因子不阻止利用可信总账推进。

## 边界与完成条件

计数和窗口引用 evaluate 的 [测量契约](../evaluate/references/measurement_contract.md)；本模块维护 [因子映射与独立对账](references/factor_diagnosis.md)。五因子零残差不能替代原件交叉核验，占比或最小因子不能单独定位根因。

可按 [knowledge 公开接口](../knowledge/references/records.md) 在委托范围内查询固定快照，保存来源和适用性。缺卡或版本不匹配返回缺口；知识建设是单独任务，不隐式触发。

缺 trace 不自动启动采集；采集、语义埋点或服务操作由协调者明确安排。本模块没有通用 msprof 解析器，现场适配需保存解析器并验证样例。计量修复、候选实施和新知识建设写成 next_actions，不链式启动 evaluate/optimize/knowledge。

约定解析或推理完成即可 completed，不要求所有因子有值或根因唯一。影响判断的缺口返回 needs_evidence；失败保留原件、部分覆盖与实际副作用。效果与机制分别判断，模块不更新全局 state、基线或最终决策。独立任务由当前 agent 协调其请求范围。
