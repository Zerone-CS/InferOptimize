# 诊断公开产物：观测账本与假设

本模块维护观测、证据覆盖、假设和鉴别建议。evaluate、optimize 与协调者按下列公开语义消费产物，不依赖解析器或临时目录的内部实现。记录以任务输入的 run、窗口、契约版本和来源 hash 为准；这是建议的记录契约，现有工具不会自动生成完整账本。

## 1. 输入与结果边界

输入包括待回答问题、[计量契约](../../evaluate/references/measurement_contract.md)、evaluate 的[公开测量记录](../../evaluate/references/records.md)、原始 trace/日志及其身份，按需附历史假设和固定知识快照。缺失项明确记录，不以旧运行填补当前运行的未知量。

输出为账本、映射/解析器、覆盖说明、假设和 next_actions。每个结果注明输入引用、适用范围、证据状态、未决项与实际采集副作用；completed 表示委托完成，不证明根因唯一。数据无效、无法解析、证据不足和机制被反驳分别报告。

本模块不写全局 baseline、decision 或 campaign state。需新的运行/采集/变更时返回具体任务建议，由协调者安排；局部分析可以独立完成。

## 2. 因子观测表与 profiling 提取计划

[因子观测模板](../assets/factor-ledger.example.json) 是本轮诊断的中间产物，使用方法见
[因子驱动诊断](factor_diagnosis.md)。一张表绑定一个 run、窗口和计数范围；不同采集范围分别建表。
`measured/derived/estimated/unavailable/not_applicable` 表示取值方式与可得性，不能代替语义核验或机制置信度。
模板数值为 null，不会自动读取 trace、推导因子或判定瓶颈。

- `counts/factors`：原子计数及公式、定义、单位、数值、状态、来源、聚合和适用条件；零分母或缺失计数保留不可得。
- `sources`：source_id、原始路径/hash、采集工具版本/开关、字段或事件实义、rank/stream、时间单位和时钟、覆盖范围、关联键。
- `extraction_plan`：目标因子/解释量、实际原始字段、过滤与聚合规则、去重/关联、验证样例和缺字段动作；可内嵌，也可另存独立文件并引用。
- `observations`：时间线区间、PMU、图命中、KV、调度原因等机制解释量；每项保存值/单位、scope、来源、聚合规则及状态。
  这些量不是新增的吞吐乘法因子，关联到它们支持或反驳的机制。
- `coverage`：已遍历分支、已发现的原件、不可得项和优先补采；未采到的分支不能写为正常。
- `bottleneck_candidates`：hypothesis_id、target_factors、观察与限制解释、竞争解释、作用条件、预计各因子方向、鉴别实验和证伪条件。
- `reconciliation`：同运行/窗口、逻辑去重、输出唯一归轮、包含关系、分母有效性、输出/时间对账、乘积与总吞吐及误差解释。
  同组总数派生的因子乘积只是算术自洽；另保存 `independent_evidence_checks`，逐项引用输出/轮次原件与客户端总账的交叉核验，不能以零残差替代。

基线与候选先各自对账，再比较因子变化。若诊断使用开启 profiler 的运行，而正式收益使用关闭 profiler 的运行，
两组各保留原始身份；诊断因子用于解释机制，不移植为正式计分运行的精确分解。
结论明确是已测限制、待证瓶颈候选还是不可判断，并附适用条件；脚本生成的统计值不自动填为瓶颈结论。

## 3. hypotheses 及修订

每条假设保存 hypothesis_id、scope、目标因子、ledger/观察引用、限制机制、竞争解释、缺失证据、机制预测、证伪条件、状态和修订原因。时间与来源必须能定位到实际 run/窗口/配置；历史假设不自动升级为当前事实。

假设应回答一个可区分的问题。机制声明、支持/反驳证据和下一鉴别动作分别保存；允许 unresolved/contradicted，不因候选有收益而强行补齐机制。修订以新事件记录 event_id、时间和 supersedes，保留已排除解释。

详细假设卡见 [归因方法](attribution.md)。干预意图与预期可在假设中表达，完整变更集、实验矩阵和实际执行由 [optimize 实验契约](../../optimize/references/experiment_contract.md) 维护；诊断建议不是服务操作委托。

## 4. 候选与交接

next_actions 记录要区分的问题、建议能力/role、必要输入、预期信息、预算与服务访问条件。排序可依据辨别力、收益空间、成本、风险与可逆性；返回排序建议，由协调者更新全局 backlog。

知识证据通过 [knowledge 查询接口](../../knowledge/references/records.md) 引用固定快照、命中卡片及适用性。查询缺口返回补证建议，不自动建设知识库。效果结论引用 evaluate 的报告；机制结论由本模块维护，最终去留决策归协调者。
