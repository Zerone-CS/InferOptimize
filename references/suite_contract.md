# 任务接口与职责边界

根目录是协调入口；evaluate、diagnose、optimize、knowledge 是可独立接任务的四个能力模块。不设 shared 业务层：公共内容由明确的能力所有者维护，使用者引用其公开契约。读取入口不是执行任务，典型五步不限定能力调用顺序。

## 1. 入口、版本与职责

当前服务器套件根为 `/share_data/zhh_workspace_1020/.kerminal/skills/vllm-ascend-throughput-skills`。实际加载位置可以不同：读取发现薄索引指向的真实入口，不从 shell 工作目录或索引父目录猜测路径。主入口名为 `vllm-ascend-throughput-optimization`，位于根 `SKILL.md`。

| 所有者 | 维护的公开契约与产物 | 不承担的责任 |
|---|---|---|
| 主入口 | 本文任务接口、[campaign 状态](campaign_state.md)、目标/约束、预算、基线与最终决定 | 不复制模块计量、推理或知识规则 |
| evaluate | [计量定义](../evaluate/references/measurement_contract.md)、[工具数据接口](../evaluate/references/tool_contract.md)、[测量和比较记录](../evaluate/references/records.md) | 不晋级基线或自动启动后续模块 |
| diagnose | [因子账本和假设](../diagnose/references/records.md)、证据映射与鉴别建议 | 不把缺证据解释为无收益，不隐式启动服务操作 |
| optimize | [实验与变更契约](../optimize/references/experiment_contract.md)、计划、执行记录和回退结果 | 不自行放宽约束或宣布性能成立 |
| knowledge | [查询与建设](../knowledge/references/workflow.md)、[知识记录](../knowledge/references/records.md)、快照与来源证据 | 不由查询隐式建设/发布，不静默切换 campaign 快照 |

模块只接收明确上下文及产物引用，不依赖协调者内部存储或其他模块的临时分析文件。公开格式发生变化时记录版本/文件 hash 和兼容性；冻结中的 campaign 保留原引用，不能静默套用新定义。这里约定工作接口，未声称工具已实现通用 schema 验证或服务 API。

`role` 描述任务目的，模块描述能力组织。历史 role 保持稳定：

| role | 模块 | 入口参考 |
|---|---|---|
| measurement | evaluate | [测量与基线](../evaluate/references/measurement.md) |
| validation | evaluate | [候选验证](../evaluate/references/validation.md) |
| profiling | diagnose | [采集与解析](../diagnose/references/profiling.md) |
| diagnosis | diagnose | [机制推理](../diagnose/references/reasoning.md) |
| design | optimize | [设计、执行与回退](../optimize/SKILL.md) |
| knowledge | knowledge | [查询与建设](../knowledge/SKILL.md) |

optimize 的 design role 可按 goal 委托设计、执行或回退，不新增历史记录必须迁移的角色。`mode` 描述工作范围，不表示阶段。旧 measure/profile/validate 路径已退出，历史 measurement/profiling/validation role 仍按上表路由。

套件统一发布，根 `scripts/verify_suite.py` 核对 manifest；[运行支持](runtime.md) 负责安装、注册和测试。evaluate 使用 Python 标准库；knowledge 的离线依赖归其 resources，根 `.runtime` 暂保留。套件工具不参与业务模块调用链；注册成功不证明当前 loader 上下文已刷新。

## 2. 任务输入

按 [输入模板](../assets/handoff-input.example.json) 保存最小必要上下文。独立模块任务可直接从用户上下文建立委托，无需用户另调主入口；当前 agent 承担请求范围内的协调责任，沿用已有授权。

| 字段 | 语义 |
|---|---|
| task_id、parent_task_id、campaign_root | 本任务、来源和产物根；不要求模块依赖 state 的内部布局 |
| role、goal | 上表角色、要回答的具体问题或要实施的确定动作 |
| mode | observe 读取/解析；diagnose 推理/鉴别建议；prepare 准备方案；execute 执行已委托动作 |
| artifacts | 所需公开契约、基线、报告、ledger、假设或计划及原件引用；仅传必要 state 摘要 |
| scenario_scope、constraints | 场景、质量/SLO/资源保护及不可更改条件 |
| budget | 分配的时间、运行/API 次数或费用；未知为 null 并说明补充方式 |
| service_access | 目标实例、授权依据、动作范围及排他安排 |
| expected_outputs、return_conditions | 应交付的证据、记录及完成/返回条件 |

相对路径以 campaign_root 解析，外部原件可用绝对路径；引用保存 hash 和用途，缺 hash 说明原因。observe/diagnose 可写局部分析，prepare 可隔离准备变更；服务操作须符合 execute 的委托与已有授权。缺少输入时先完成独立可推进部分。

只传任务所需信息，排除凭据。真实部署源码、负载、服务和 profiling 是任务输入，历史 KB 不替代现场事实；KB API 配置取本次环境，不读取 `~/.claude/settings.json`。

## 3. 返回结果

按 [结果模板](../assets/handoff-result.example.json) 写新文件。模块拥有并封存自己的局部产物；重算/重试使用新 analysis/run/task 身份。

| 字段 | 语义 |
|---|---|
| task_id、role、input_ref | 委托及输入身份 |
| status | completed 完成委托；needs_evidence 需要可采证据；blocked 明确外部依赖；failed 执行/解析失败 |
| artifacts | 已产生文件、hash、用途与完整性；已生成的计划文档也是产物，不填尚未生成的预期文件 |
| observations、claims | 观察与解释分开，附来源、范围、状态及局限 |
| uncertainties、next_actions | 缺口和具体动作，注明所属能力、目的、输入及执行条件 |
| decision_recommendation | adopt/revert/defer 等建议；无比较依据为 null |
| budget_used、side_effects | 实际用量、文件/服务/发布变更、失败及恢复；未测成本不填零 |

completed 不等于数据有效、质量通过、机制成立或允许采纳。缺证据、执行失败、候选无收益分别报告；blocked 写依赖和解锁条件，协调者仍可推进其他方向。路径/hash 不替代语义、配置生效或来源审阅。

## 4. 状态所有权与执行协调

主入口是 campaign state、总预算、目标/约束、当前基线和最终决策的唯一写入者。模块可创建各自的报告/假设/计划/知识产物，返回引用；由主入口验收后写新 state。即使同一个 agent 执行多个能力，也按角色分开“模块报告”与“协调决策”。独立任务不必建立完整 campaign，但不得修改未委托的既有 campaign。

模块可以建议下一动作，不能因此隐式调用下一个模块。diagnose、optimize 可在委托范围内直接只读查询固定知识快照；知识缺口返回协调者，建设/发布是有独立范围与预算的任务。发布新快照和切换 campaign 引用是不同动作，后者由协调者记录。

同一实例的变更、重启、profiling 与压测排他安排；当前无自动锁，执行前核对归属与冲突。封存数据分析可并行。执行中计划条件不成立时记录现场与已发生动作，返回协调者调整；不因失败擅自扩大变更集、总预算或服务范围。

主入口根据 evaluate 的效果与守卫评估、diagnose 的机制解释和 optimize 的实际执行状态，作 adopt/revert/defer 决定。回退建议不等于已回退，基线更新只引用验收通过的实际配置。停止条件与恢复见 [campaign 状态](campaign_state.md)。
