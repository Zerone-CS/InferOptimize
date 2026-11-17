---
name: evaluate
description: 独立测量和验证 vLLM-Ascend 吞吐：定义计量与公开数据格式，采集并核验运行，比较质量/SLO、全场景效果及机制证据；返回事实、未决项与建议。
---

# 测基线与验效果

提供 **测量** 和 **验证** 两种独立能力。它们对应典型主线的①和④，不要求连续调用，也不自行推进下一模块。
按 [任务交接契约](../references/suite_contract.md) 接收明确上下文并返回产物；独立请求可建立最小输入。

| 能力 / handoff.role | 输入 | 公开产物与执行说明 |
|---|---|---|
| 测量 / `measurement` | 目标、质量/SLO、服务与源码身份、负载及客户端策略；已有 run 或允许采集的范围和预算 | [测量阶段](references/measurement.md)：计量契约、原始 run、校验报告、重复结果与补证动作 |
| 验证 / `validation` | 固定的实验契约、baseline/candidate 身份、计划与实际变更、原始 run 或执行方案；机制判断另需事前预测及观测证据 | [验证阶段](references/validation.md)：逐场景比较、质量/SLO、效果与机制判定、adopt/revert/defer 建议 |

## 边界与公开接口

- 本模块维护 [计量定义](references/measurement_contract.md)、[工具数据接口](references/tool_contract.md) 和 [评估记录](references/records.md)。其他模块消费这些公开契约及产物，不依赖脚本内部函数或临时目录。
- 一次任务固定契约版本或内容 hash，原始运行与派生报告保留身份和来源。未知、无效、真实失败和否定结论分别报告；旧数据不因文件搬迁被重写。
- 分别报告数据有效性、质量/SLO、性能效果、机制和决策建议。收益不自动证明机制；总账可独立核验时，不必等待内部因子齐全。
- 只写本任务的评估产物与交接结果；不修改全局 state、当前基线、服务配置或其他模块产物。主入口决定晋级、采纳、回退和下一任务。授权范围内可发送压测请求；服务排他与预算沿用交接上下文。
- 需要额外 profiling 或知识时返回所需证据及理由，由主入口安排；复用已有公开证据不触发隐式采集、知识建设或服务操作。

[五个工具](references/tool_usage.md) 位于本模块 `scripts/`，仅需 Python 3.9+ 标准库，可从任意工作目录调用，无需安装 knowledge 依赖或预建 `.runtime`。工具只在显式调用时执行；`benchmark.py` 会发送真实请求。
