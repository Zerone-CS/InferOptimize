# Campaign 组织、状态与决策

主入口维护本次任务的事实和决策；skill 保存通用规则。本文是建议的记录契约，可映射到已有系统，不是已实现的状态服务。模块输出的机器格式以各模块公开接口为准。

## 1. 状态所有权

协调者唯一更新目标/约束、总预算、当前基线、活动候选、活动任务和最终决策。模块写局部产物并返回引用；协调者验收后登记，不让模块直接修改活动 state。独立模块任务由当前 agent 协调其请求范围，不必建立完整 campaign。

同一 agent 同时承担模块和协调角色时，也保留报告与决策的区别：evaluate 返回证据判定，diagnose 返回机制判断，optimize 返回实际执行/回退记录，knowledge 返回查询/建设证据；协调者记录采用哪些证据作了什么决定。

## 2. 产物组织与引用

```text
campaign/
  contract.json, source_manifest.json
  state/0001.json, 0002.json, ...
  handoffs/<task_id>/input.json, result.json
  runs/<run_id>/                         # evaluate：运行原件
  analysis/<analysis_id>/                # 各模块：独立分析产物
  hypotheses.jsonl                       # diagnose：假设与修订
  trials.jsonl                           # optimize：计划及执行引用
  backlog.jsonl                          # 主入口：候选调度和阻塞
  knowledge/                             # knowledge：查询/建设/反馈
```

这是默认组织示例，模块只消费明确传入的产物，不按目录位置推断当前基线或读取其他模块临时文件。每个引用保留路径、字节数、hash、用途和生产任务；固定契约与来源版本，不静默混用新旧定义。公开字段变化应注明兼容性，已有 state 无需因目录重组改写。

run_id 在命令启动前生成；目标目录须新建成功，已存在则换新 ID。日志可在运行时追加，结束封存，原始数据不覆盖。解析修复生成新 analysis_id，记录输入 hash、解析器版本及旧结果引用，保留原 summary。JSONL 修订追加事件及 event_id、时间、supersedes，不抹去旧判断。

各项细节由所有者维护：

- [evaluate 记录](../evaluate/references/records.md)：目标/测量契约、run 数据与评估报告；其中目标、预算和约束的实际值由协调者确定，evaluate 不自行放宽。
- [diagnose 记录](../diagnose/references/records.md)：因子观测、来源/覆盖、假设及反证。
- [optimize 实验契约](../optimize/references/experiment_contract.md)：设计、执行、回退及试验关联。
- [knowledge 记录](../knowledge/references/records.md)：固定快照、查询、建设和反馈。

`backlog` 由协调者维护 candidate_id、假设/依赖、适用条件、预期收益及依据、成本、优先级理由、状态、阻塞解锁条件与下一动作。候选用完不等于系统全局最优。

## 3. 来源与部署身份

- skill：发现薄索引、其指向的套件入口、入口真实路径、套件 release/manifest 与逐文件 hash；发现路径和实际资源路径分别记录。
- 套件运行时：系统 Python 身份、本任务实际解释器（系统 Python 或 `.runtime/bin/python`）、依赖锁定文件/轮子与资源核验报告；安装/重建记录和当前解释器版本。
- 软件：镜像 digest、驱动/CANN/框架/模型版本；实际 import 路径和包元数据。
- 源码：仓库 commit、dirty patch hash，或安装文件集合及 hash；不能只记旁边 checkout 的 commit。
- 知识：固定 KB 的数据目录、manifest/查询器/`knowledge/scripts/kb.py` 入口 hash、与两套部署源码的匹配判断；实际使用的卡片另记 name、路径和 hash。内置历史快照、源码标签及计数差异保留；声明的版本不替代实际源码身份证据。
- 分析器/benchmark/比较器：真实路径、版本/hash、参数说明来源；修改后生成新工具版本。
- 运行归属：主机、容器 ID、服务 PID 与启动时刻、设备映射、端口；只记录本实验所需信息。
- 配置：完整 argv 数组、必要环境变量、解析后配置、运行路径证据、预期与实际 config diff。
- 保密：不把口令、密钥或完整无关环境转储到报告；敏感配置用受控存储引用。
- 状态：开始/结束、退出码、warmup、profiling 开关、环境快照、有效性与原因。

入口加载、版本一致性和副本核对见 [交接契约](suite_contract.md#1-入口版本与职责)。

## 4. 状态快照与恢复

skill 保存通用规则，项目 campaign 保存本次实验事实。按 [状态模板](../assets/campaign-state.example.json)
建立首份快照；模板是示例，不是已核验状态。未知值保留 null/unknown，不用示例补成现场事实。
state 中的相对路径统一相对 campaign 根目录解析，不相对 `state/` 快照所在目录；跨目录引用也可保存绝对路径。
快照以新编号独占保存，候选/假设/试验变化向 JSONL 追加；阶段切换、判定和长操作前后更新即可，不要求每条 shell 命令都生成快照。

最小状态包含：

| 字段 | 用途 |
|---|---|
| campaign_id、state_id、supersedes | 活动、快照与修订关系 |
| contract、source_manifest | 当前规则版本及实际使用的 skill/工具/模型来源；附内容 hash |
| suite、active_tasks、last_handoff_result | 套件来源/实际加载入口、子任务与排他执行范围、最近交接产物；按套件契约协调 |
| knowledge | 固定快照记录及 hash、source_match、知识缺口与正在构建的 build 引用 |
| factor_analysis | 当前因子观测表与提取计划引用及 hash、瓶颈候选、下一次补采动作 |
| current_stage | S0 契约、S1 基线、S2 观测、S3 诊断、S4 优化、S5 验证、S6 决策、S7 交付；用于进度标记，不代替证据或限定调用顺序 |
| baseline、active_candidate、last_decision | 已验证基线、活动候选和最近判定的产物引用 |
| service_identity | host、容器、PID与启动时刻、设备、端点、模型和有效配置引用 |
| active_runs | 正在进行或中断的 run 及其目录；保留启动时登记的归属信息 |
| remaining_budget | 实际已约定的时间/运行预算、已用量与剩余量；未约定时写未知 |
| next_action、unresolved | 下一动作、目的、所需证据和不能执行的条件，以及未决问题 |
| updated_at | 状态记录时间；不能用时间新近代替配置/输入身份核验 |

接手或上下文压缩后的恢复顺序：

1. 读取最新**完整** state，并核对其契约、来源和判定引用；失败写入留下的半份文件不算最新有效快照。
2. 读取当前基线、候选与必要的最近判定；不必把全部 rollout 重读一遍。
3. 核对现场容器、PID/start time、设备、端点、模型和有效配置。端口相同或 PID 数字相同不足以证明是原实例。
4. 对 active_runs 检查原进程身份及现存产物；只有开始记录而没有最终 manifest 的目录保留为不完整运行。
   不补写成功，不覆盖重跑；不能仅因上次会话中断就清理未知归属进程。
5. 现场一致时继续登记的下一动作；现场变化时追加差异记录，重新判定哪些证据仍可复用。
   原始 run 保持封存；解析修复使用新 analysis_id，重新发请求使用新 run_id。

若只能离线分析或没有服务操作授权，next_action 应保存可执行条件和命令草案，决策保持相应的 defer/待确认状态；
不得把“缺权限”“尚未采集”“已证明无收益”写成同一件事。状态文件是接续依据，不授予额外权限。

## 5. 交接与最终决策

输入、返回、mode 与执行范围见 [任务契约](suite_contract.md)。角色 measurement/validation/profiling/diagnosis/design/knowledge 和 S0–S7 进度标记保持稳定；它们不是强制阶段状态机。

协调者接收新产物后分别记录 data_validity、quality_slo、performance_effect、mechanism 和 decision。前四项引用负责模块的证据与局限；decision 由协调者写 adopt/revert/defer、理由、基线是否更新和实际操作状态。判断所用的 run、配置、契约及报告均固定引用，不能只引用会变化的“latest”。

adopt 需要有效数据、质量/SLO、全部保护场景和约定的重复净收益成立；搜索胜出配置另需独立确认。revert 是去留决定，不意味着已完成回退：委托 optimize 执行后记录核实的结果；defer 保留缺口与补证条件，不等于否定收益。

恢复时同时核对 active_tasks、active_runs 与服务归属；本文不提供自动锁。只有目标满足、预算达到停止条件，或合理方向耗尽且无新动作时封存本轮，保留当前配置、未决项与停止理由，不宣称全局最优。
