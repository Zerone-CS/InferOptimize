---
name: knowledge
description: 为 vLLM-Ascend 吞吐优化提供随用随查的知识支持：按参数问题或因子机制检索知识、核对部署源码，并按需建设知识快照。用于知识缺口或参数/代码依据核验。
---

# 随用随查的知识支持

需要参数、机制或源码依据时调用，不作为五步主线中的固定步骤。按 [主入口交接契约](../references/suite_contract.md) 接手与返回；维护本模块的查询证据、构建、审查和发布记录，不写全局 state、当前基线或活动 campaign 的快照选择。

## 公开能力

| 操作 | 输入 | 返回与边界 |
|---|---|---|
| query | 参数名或具体问题、固定 snapshot；部署源码身份及因子/假设引用有则提供 | 带来源、版本、适用范围的证据或 knowledge_gap；源码身份未知时只返回未核验线索，不隐式 extract、parse 或发布 |
| build | 明确缺口、源码身份、构建范围、预算、新目录 | 构建产物与 complete/partial/failed 记录；不发布或切换快照 |
| review | 固定构建/快照、需要审查的主张及范围 | 分开的结构、源码语义和覆盖审查；不把结构通过等同于语义通过 |
| publish | 已审查快照、明确发布目标与回退计划 | 不可变快照和发布记录；仅执行已委托的发布，campaign 是否切换由协调者决定 |

接口、证据字段与写入归属见 [知识记录契约](references/records.md)。查询可独立使用；build、review、publish 是可分别委托的能力，查不到时只返回缺口与下一动作。
内置历史数据在 `kb/`；工具为本模块 `scripts/kb.py` 与 `scripts/check_kb_snapshot.py`。首次使用或 `.runtime` 缺失时，先按 [运行环境](../references/runtime.md) 执行套件 `scripts/setup_runtime.py`，再使用 `.runtime/bin/python`。知识依赖归本模块 `resources/`；其他模块无需安装它们才能离线评估。

## 查询与核验

按 [知识工作流](references/workflow.md) 的查询章节执行；仅建设时加载其构建/恢复/发布章节。

1. 固定 snapshot、manifest/查询器/卡片身份。有部署源码时对照实际使用的 vLLM 与 Ascend 源码 commit/dirty 或文件 hash，分别记录 exact、compatible_verified、mismatch、unknown；未知身份不阻塞检索，但不能宣称现场适用性已核验。历史标签不证明部署匹配。
2. 将参数名或具体问题转为支持的名称、分类或全文查询；已有 target_factor/mechanism 或假设时按需关联，不要求先经过 diagnose。`-w` 为子串匹配；核完整 name/type/scope，保存命令、结果与卡片 hash。缺卡先查原始参数、筛除/错误记录及可用源码。
3. 宣称现场适用性前，核对现场定义、guard、平台覆盖、依赖和实际使用路径，分开源码事实、文档建议、机制推断与实测观察。推荐值、影响等级、卡片字段和 LLM 自评均不能代替证据；源码足够时可直接补证。

## 按需建设与发布

缺口影响下一决策且建设有复用价值时，约定范围、源码/构建器身份、时间与调用预算。

1. 使用新 campaign build；`kb.py extract/parse` 显式提供 `--vllm-src`、`--vllm-ascend-src`、`--output`，parse 另给 `--input`。API 配置取本次环境，不读 `~/.claude/settings.json`，不改内置快照或模型环境。
2. 区分静态提取、规则预演和 LLM 解析：dry-run 会写文件；max-params 不是 API 调用预算。resume 只接受输入/源码、构建器、规则/提示/schema、运行配置和模型/端点身份一致的构建，不自动重试 error_params；详见工作流恢复规则。
3. 解析器核对返回的 name/type/scope 与输入一致，拒绝覆盖已有卡片；存在解析或恢复错误时返回非零，并保留逐项结果。记录退出码、manifest 与 progress，再运行 `scripts/check_kb_snapshot.py`，核验去向账、来源与关键主张。结构通过不证明语义或覆盖通过；保留历史快照的来源与计数差异，不把迁入成功当全量核验。
4. 分别交付构建、审查和发布产物；构建成功不自动进入发布。仅在 execute 且已委托发布时切换指定发布引用；当前 campaign 固定快照的切换由协调者留痕。实验正负结果先由其产出模块封存，再形成有范围/证据的待审增量，不原地覆盖旧卡片。

## 完成与产物

交付查询/源码证据、缺口与下一动作；建设任务另交 build 进度、snapshot、检查/审查报告及反馈增量的实际引用。
observe/diagnose 只查询核验，prepare 准备可审阅产物，execute 执行已委托动作。达到预算保留 partial 和恢复点；委托目标完成可 `completed`，尚需可采证据则 `needs_evidence`。结构报告不是自动语义审阅结论。
