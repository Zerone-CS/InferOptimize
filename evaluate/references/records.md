# evaluate 的公开记录

本模块维护测量和评估产物，供主入口及其他模块按契约消费。这里是研究记录的语义要求；工具已经实现的机器字段以 [工具数据接口](tool_contract.md) 的 `schema_version=1` 为准。扩展记录不能假装是工具已采得的字段；缺证据保留 null/unknown。

## 1. 固定任务上下文与计量契约

全局 `contract.json` 由主入口维护。本模块接收其固定引用与 hash，不改目标、预算或成功标准；如需调整，返回原因和拟议变更。使用独立能力时也明确保存最小上下文：

| 输入 | 使用方式与责任 |
|---|---|
| campaign/task ID、objective | 主入口给定固定负载吞吐、完成时间或受约束容量目标 |
| service_scope | 固定端点、实例/副本、模型、设备及计分边界；核验实际运行归属 |
| workload | 绑定请求文件 hash、生成器、tokenizer/模板版本、seed、到达表/模式、并发与采样 |
| metric_contract | evaluate 维护计数、成功、窗口、warmup、跨界处理定义；本任务固定具体版本/hash |
| constraints、comparison_contract | 按已约定的质量基准、容忍度、时延/SLO、错误率、资源、全部主/保护场景与最小收益检验；工具不支持跨场景加权抵消 |
| budget、stop_policy | 消费委托中的可用预算与停止条件；返回实际用量与未完成项，由主入口更新全局状态 |

固定本模块 [计量定义](measurement_contract.md) 和数据接口的版本或内容 hash，另存本任务参数化的计量/比较契约。参数模板只演示格式，不提供默认达标阈值。

## 2. 来源与运行身份

`source_manifest.json` 是主入口维护的全局来源索引；本模块消费它的固定版本，在运行 metadata/manifest 和评估结果中绑定实际输入身份。不能从声明的版本推断真实服务已核验。

- skill：发现索引、实际套件与 evaluate 入口、release/manifest 和相关文件 hash；发现位置与真实资源位置分别记录。
- 执行环境：实际解释器路径/版本、宿主及必要依赖身份。五个评估工具只用标准库；若选择 `.runtime/bin/python`，记录该解释器，不把其存在列为评估前置条件。
- 软件与源码：镜像 digest、驱动/CANN/框架/模型身份、实际 import 路径/包元数据，真实部署 commit 与 dirty patch hash 或安装文件集合 hash；不能只记邻近 checkout。
- 负载与工具：输入文件与实际请求子集、客户端策略、采集器/分析器/比较器真实路径与内容 hash。`benchmark_sha256` 是脚本字节身份，搬位置不应改写历史 run。
- 服务归属：主机、容器、PID 与启动时刻、设备映射、端口、模型、完整 argv、必要环境变量、解析后配置与实际生效证据；计划与实际 diff 分开。
- 外部证据：质量报告、diagnose 观测/预测及需要引用的知识快照、卡片和来源报告，均绑定版本/hash；由对应模块维护原件，evaluate 不修改其产物。
- 运行状态：开始/结束、实际退出码、warmup、profiling 开关、环境变化、有效性和原因。口令、令牌及无关环境不得进入记录；敏感配置只留受控引用。

入口加载和版本核对见 [任务交接契约](../../references/suite_contract.md)。运行目录由新 run_id 创建；每次请求运行、解析修复或比较均使用新产物路径。原始数据结束封存后不覆盖；派生报告记录输入 hash、工具版本及被替代报告引用。

## 3. 逐请求记录

| 字段 | 定义/检查 |
|---|---|
| run_id, request_id, sequence_id | 唯一标识；多序列输出时注明父请求 |
| planned_send_ts | 计划到达时刻，可选，但开环发送滞后分析必需 |
| client_queue_enter_ts, send_start_ts | 客户端等待与真正发起调用的时刻；不可在等待响应头后才记 send_start |
| response_open_ts, first_output_ts, last_output_ts, end_ts | 流建立、首个/最后一个符合口径输出、终止；缺失标 null |
| transport_status, final_status, finish_reason | HTTP/流成功与业务最终成功分开；服务停止原因、错误码和客户端终止原因保留 |
| actual_prompt_tokens, tokenizer_revision, template_hash | 实测输入量及其来源、分词器/模板身份；不可只用输入长度设定值 |
| requested_max_tokens, actual_output_tokens | 上限与实测值分别保存；实测缺失不可回填上限 |
| token_count_source, count_policy | usage/生成 ID/客户端重分词及版本；不同来源不可静默混合 |
| chunk_events | 若需要流间隔，保存事件时间与有效载荷类型；不把 role-only/空 content 当首输出 |
| quality_status, slo_status | 按契约评估，未评估为 null/unknown |

空流 HTTP 成功不意味着产生了有效输出：记录实际为零、首输出为 null。
允许零输出是否算请求成功由契约决定，但永远不能据配额给它补 token。
无法从客户端事件分辨逐 token 到达时，TTFT 可按明确的首有效载荷定义计算，
ITL 应标不可得或报告 chunk 间隔；不能冒充精确逐 token ITL。

## 4. 统计可校验规则

1. 所有时间使用可比时钟和显式单位；检查事件次序与窗口边界。
2. 每个已发请求都能对应一个终态或明确删失状态；缺失不得当作成功。
3. `N_Y=sum(最终成功请求的实测有效输出)`；`T=t_end-t_start`；summary 可由逐请求数据重算。
4. 成功、失败、超时分开；聚合吞吐比值与逐请求吞吐均值不等价。
5. p99 必须记录样本集合、加权和分位算法。全体 token 间隔 p99、
   每请求平均 ITL 的 p99、每请求 TPOT 的 p99 是三个不同指标。
6. `TTFT=first_output_ts-send_start_ts` 仅在两端定义匹配时成立；客户端排队时间另报。
   若报告 TPOT，明确采用末输出还是响应结束时刻以及分母；例如实测输出数 O>1 时，
   `(last_output_ts-first_output_ts)/(O-1)` 是该定义的平均输出间隔，不等于逐 token ITL 分位数。
   O≤1 或缺少端点时该式不可用，标 null，不用零填充时延分布。
7. 在途数从发送/终止事件重建，先用上一段在途数积分，再应用当前事件：
   `area += previous_inflight × (event_ts-previous_ts)`，然后加减请求数。
   同时刻事件合并处理；完整批次检查在途数不负、末尾回到零。
8. 完整批次的在途面积应与全部请求逗留时长之和一致；稳态截断窗口另处理跨界请求。
9. 重复运行以 run 为单位保存；不把一个 run 内请求数当作重复实验次数。
10. profiler 开启的运行与关闭的计分运行分组；不同配置/负载/窗口不可静默合并。
11. 分子对不上不代表所有历史结果必错；逐 run 标明已验证、可修复、不可追溯及影响范围。
12. 回归矩阵逐项执行契约，特别保留受保护尾时延；不能用总评语覆盖不通过项。

## 5. 评估结果与工具对应

调用与退出码见 [工具用法](tool_usage.md)，机器字段见 [数据接口](tool_contract.md)。保存真实脚本路径/hash、argv、完整 stdout/stderr、原始退出码及产物引用。工具只覆盖部分契约；配置差异、实际生效、完整任务质量和机制语义仍需核验。

对每项委托返回：

- 固定契约、baseline/candidate、全部原始 run 与校验/比较报告的引用和 hash。
- 每个场景的全部独立重复、运行顺序、效应及不确定性方法，主指标与每条保护条件的结果。
- `data_validity`、`quality_slo`、`performance_effect`、`mechanism` 四项独立判定，及 `decision_recommendation`（adopt/revert/defer）与理由。工具 JSON 中既有 `decision` 字段也仅表示算法建议，不是主入口已采纳的决定。
- 正确性参考/候选输出的 ID 与 hash、比较器输入方向、质量适用范围；机制部分引用事前预测与诊断证据，不用性能收益代替机制验证。
- 工作完成状态、实际执行/用量、部分产物、未决项、最小补证动作和继续条件。已完成审计、证据不足、执行失败、证据支持无收益分别报告。

完整 trial 的设计、执行和回退由 [optimize 的实验契约](../../optimize/references/experiment_contract.md) 定义，评估结果通过引用附入；基线晋级、最终决定与状态快照属于 [主入口](../../references/campaign_state.md)。本模块不维护第二份当前基线或全局 state，不执行建议的回退。
