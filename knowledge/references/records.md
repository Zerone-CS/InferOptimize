# 知识能力与记录契约

本契约由 knowledge 维护。主入口和其他模块消费这里定义的公开证据与产物，不读取构建过程中的临时文件或依赖内部 Python 实现。
通用任务身份、mode 和返回状态使用 [主入口交接契约](../../references/suite_contract.md)；本页补充知识操作的输入、输出与所有权。
这些是 agent 的交接约定；现有 CLI 不自动生成全部证据记录，也不提供发布或全局状态服务。

## 1. 操作接口

| 操作 | 必要输入 | 公开结果 |
|---|---|---|
| query | 参数名或具体问题、明确 snapshot 引用及允许查询范围；部署源码身份和因子/机制/假设引用有则提供 | 查询记录、选用主张与 source_match、适用条件、未决 knowledge_gap；源码身份未知时标 unknown，只返回未核验线索 |
| build | 缺口、两套源码、输入/范围、新输出目录、构建器/运行时身份、时间与调用预算 | build 记录、输入与产物 hash、实际覆盖、错误/待处理项、恢复点；不包含发布承诺 |
| review | 固定 build/snapshot、待核验主张及审查范围、需要匹配的部署身份 | 结构、源码事实、覆盖对账三个独立结论、证据与未审范围 |
| publish | 固定且已审查的 snapshot、明确发布目标、允许的操作、回退引用 | 新 snapshot 清单、实际发布结果与回退方法；失败保留真实结果 |

query 映射到 `knowledge/scripts/kb.py query` 及源码核验；build 使用同一入口的 `extract`、`parse`。
参数查询可以独立完成，不要求已有 diagnose 结果；因子、机制、假设及观测引用按问题需要关联。
review 可使用 `knowledge/scripts/check_kb_snapshot.py` 完成结构部分，源码语义与覆盖仍需分别审查。
publish 没有隐式命令链，由执行者在明确委托范围内实施。build 成功、检查返回零或查询未命中均不触发后续操作。
查询接口和证据格式不依赖具体存储实现；更换卡片存储或检索工具后仍应保持 snapshot、来源和适用范围可追溯。

## 2. 写入与引用所有权

knowledge 拥有 `campaign/knowledge/` 下的查询、构建、审查、发布及反馈产物。目录可适配现有系统，但产物语义和引用不能省略。
任务结果返回实际路径/hash 和缺口，由协调者维护全局 `state`、知识缺口优先级、预算分配及本次 campaign 的活动快照选择。
发布引用属于知识发布目标，campaign 固定引用属于协调状态：前者更新不能自动改变后者。

输出用新 ID/目录封存，不覆写已发布卡片或历史构建；修正生成新版本并引用被替代的结果。
普通 query 只读取快照和源码、写查询证据，不调用 extract/parse，不改变发布引用。
独立 query 无法取得部署身份时仍可返回检索线索，但不能宣称约束或推荐已在现场核验。

## 3. 记录内容

- `snapshot.json`：数据目录、快照 ID、逐文件内容清单、构建 manifest、查询器与统一入口 hash、两套实际部署源码身份。
  两套来源分别判定 `exact / compatible_verified / mismatch / unknown`；compatible_verified 限于已审查主张，后两者不表示当前约束已核验。
  knowledge 提供该记录，协调者决定是否将它固定为活动 campaign 依据。
- `queries/<query_id>/`：argv 数组、退出码、完整 stdout/stderr 文件及 hash、snapshot 记录引用、参数名或具体问题；已有且相关的因子/机制/假设引用按需附上；
  保存命中逻辑 name，最终选用卡片的完整 name/type/scope、路径/hash、选择理由及部署核验记录。子串命中不等于精确身份。
- `builds/<build_id>/`：内置构建器与 `kb.py` 身份、两套显式源码、运行时和知识依赖锁、模型/提示/过滤规则身份、输入及 hash；
  保存 Git/dirty 或非 Git 文件指纹及部署匹配状态，不能以旧快照标签代替实际输入。
  每阶段记录 argv/退出码/日志/产物、预算与实际用量；新输入/源码/规则使用新目录，产物不写回内置历史快照。
  API 配置只记录有效模型、端点和环境变量来源，排除令牌；不读取或归档 `~/.claude/settings.json`。
  将唯一输入 name 对账到跳过、有效卡、非性能项、错误、待处理等互斥终态，并审查别名与文件名碰撞。
  仅有 manifest 的 `errors=0` 或卡片数一致，不能证明全量完成或来源正确。
- `reviews/<review_id>/`：被审快照/build 的内容身份、实际审查范围、结构报告、源码主张 sidecar、覆盖去向账和未审事项；
  三种结论分别保存，结构通过不升级其他结论。每项主张记录 `verified / unverified / contradicted`，不以 LLM 自评分代替证据。
- `publications/<publication_id>/`：被发布 snapshot 与审查引用、发布目标、旧/新引用、操作与退出状态、实际生效验证、回退方法。
  如果只准备了发布材料，明确未发布；没有 campaign 快照切换的写入权。
- `feedback.jsonl`：claim_id、事实/建议/机制推断/实测观察类型、参数身份、适用条件、源码位置或 run/trial 引用、
  配置/环境/负载/契约身份、质量/SLO/效应/机制判定、矛盾证据及审阅状态。候选未采纳也可提供知识。

## 4. 证据与完成语义

每个对外主张绑定版本、来源和适用范围：包括 snapshot/card hash、源码仓库内容身份与定位、相关运行/契约身份、已核验条件和缺失条件。
事实、文档建议、机制推断和实测观察分别标记；知识提供依据，由 diagnose 判断机制、evaluate 判断效果、协调者作采纳决策。
构建记录模板见 [knowledge-build.example.json](../assets/knowledge-build.example.json)，详细处理见 [工作流](workflow.md)。

委托目标达成可返回 `completed`，例如完成查询并确认未命中；若回答该问题仍缺可采证据，返回 `needs_evidence` 并列出缺口。
build 的 `planned/running/partial/complete/failed` 是构建生命周期，不能与任务完成、审查通过或发布状态互相替代。
到达预算保留 partial 和恢复点；发布成功也不证明当前 campaign 已采用新快照。
活动 campaign 继续固定原快照；协调者决定切换时，另记原因、旧/新引用和需要重新核验的候选。
