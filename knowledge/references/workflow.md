# 知识库检索、建设与实验反馈

本模块提供 query、build、review、publish 四种可独立委托的能力，输入输出见 [知识记录契约](records.md)。
查询消费固定快照，现场源码身份有则提供；身份未知时可返回未核验线索，不宣称现场约束或推荐已核验。
建设消费明确缺口、范围和预算；查询与建设没有自动跳转。
review 与 publish 分开返回结果，build 完成不触发发布。全局状态、预算分配和活动快照选择归主入口。
代码、756 张历史卡片、提取参数和构建日志内置于套件的 `knowledge/kb/`；默认使用该不可变历史快照。
查询、提取和解析经 `knowledge/scripts/kb.py query|extract|parse` 进入，不依赖旧知识库目录或额外 launcher。
卡片是参数与源码的索引；参数名或具体问题即可独立查询，不要求先调用 diagnose。
已有相关 [因子观测表与瓶颈候选](../../diagnose/references/factor_diagnosis.md) 时，按问题需要绑定 target_factor、限制机制、假设和观测引用；不读取 diagnose 的临时分析目录或调用其内部实现。
查询参数约束、关联项与实现路径；推荐值本身不构成瓶颈证据。
不把全部卡片装入上下文，也不要求每轮调优重建全库。

## 1. 触发与产物

| 主流程位置 | 执行动作 | 保存的最小证据 |
|---|---|---|
| 独立参数查询 | 按参数名或具体问题检索 | snapshot、命令与结果、选用卡片及 hash；未知源码身份标 unknown |
| S0/S1 | 核对委托的知识快照与现场源码 | snapshot 身份、manifest hash、两仓库匹配状态，交协调者固定 |
| S3 | 按目标因子和限制机制检索，也可查询事件语义帮助诊断 | 因子/假设引用、查询命令、完整结果、选中卡片及 hash、未命中项 |
| S4 | 核对参数定义、guard、覆盖与依赖 | 当前源码依据、适用性、计划变更集 |
| 知识缺口 | 定向提取和解析；必要时全量建设 | 构建范围、预算、输入、进度及检查报告 |
| S6/S7 | 消费已封存实验报告，产生知识增量 | run 引用、效果/机制状态、适用范围、审查状态 |

缺卡、版本变化、关键主张无依据或卡片冲突时，返回 knowledge_gap、影响范围和建议动作；
仅当下一任务明确委托建设时进入 build，原 query 任务不扩大为建设任务。
能直接查源码解决的小缺口，优先定向补证；全量建设须有明确复用价值和预算。
检索失败记 `knowledge_gap`，同时登记替代证据和下一动作；不自动阻塞所有实验。

## 2. 固定快照与来源匹配

协调者维护 campaign state 的 `knowledge.record`，指向 `knowledge/snapshot.json`，并保留当前 snapshot_id、
source_match、open_gaps 和 active_build。该记录保存 `kb_root`、`snapshot_id`、`params_dir`、
`manifest_sha256`、`query_script_sha256`、两套源码的 `source_match`，以及查询、缺口、构建和增量引用。
knowledge 交付快照记录和证据引用；只有协调者将它们接入 [campaign 状态](../../references/campaign_state.md)。
这些项目事实保存在 campaign，不写入通用 skill 或覆盖原始卡片。
快照身份包含文件内容清单；目录名、生成日期和 Git HEAD 单独都不足以标识数据。
运行中固定具体快照；默认发布引用变化后，也不能静默替换本次 campaign 的证据。

分别记录服务进程实际使用的 vLLM、vLLM-Ascend 源码根、commit、dirty diff 或安装文件 hash。
对照 KB manifest 的 `source_commits`，将匹配状态标为：

- `exact`：两仓库内容身份均可对应；commit 相同但存在未登记修改不能算 exact。
- `compatible_verified`：相关定义、guard、覆盖和调用路径已逐项证明兼容；附证据。
- `mismatch`：已知不同；`unknown`：无法充分比对。

`mismatch/unknown` 的卡片仍可用于发现候选，但默认值、约束、依赖和建议必须重新查现场源码。
`compatible_verified` 只适用于已核对的主张，不是对全库的兼容保证。
manifest 中的短 commit 应在相应仓库解析为完整身份；源码分支名或软件版本字符串不能替代内容核对。
新构建由显式源码输入记录 Git 身份、dirty 状态及相关内容指纹；非 Git 输入记 unknown 并保存文件 hash。
这些是构建输入身份，仍须与服务实际使用的源码比对；不能因路径指向某个 checkout 就宣称部署匹配。
内置旧快照的来源标签保持为 vLLM `ced6857`、vLLM-Ascend `8fde6d4e3`，不改写为本次部署版本。
旧快照缺少充分构建来源指纹时，即使标签与部署相同，也不能仅据此升级为 exact。
该快照实际有 756 张卡；历史 manifest 记 analyzed=888、confirmed_perf_related=758、performance_high=122，
落盘 high 卡为 120。保留这些统计差异并对照输入、跳过、错误和别名记录核验，不能把迁入成功或结构检查通过写成覆盖/语义全量通过。

## 3. 实际查询接口

先按 [运行环境](../../references/runtime.md) 校验套件、准备知识依赖所需的套件根 `.runtime`；不改模型服务环境。
`SKILL_DIR` 是主入口的真实目录，即套件根目录，先按发现薄索引读取目标入口；`CAMPAIGN_DIR` 是本次 campaign。
查询和检查输出文件名必须未使用。

```bash
SUITE_ROOT=$(realpath "$SKILL_DIR")
KB_ROOT="$SUITE_ROOT/knowledge/kb"
SUITE_PYTHON="$SUITE_ROOT/.runtime/bin/python"
PARAMS_DIR="$KB_ROOT/parse_params/output/params"
KB_MANIFEST="$KB_ROOT/parse_params/output/manifest.yaml"
"$SUITE_PYTHON" "$SUITE_ROOT/knowledge/scripts/check_kb_snapshot.py" \
  --params-dir "$PARAMS_DIR" --manifest "$KB_MANIFEST" \
  --output "$CAMPAIGN_DIR/knowledge/snapshot-check-001.json"
"$SUITE_PYTHON" "$SUITE_ROOT/knowledge/scripts/kb.py" query -d "$PARAMS_DIR" --count
"$SUITE_PYTHON" "$SUITE_ROOT/knowledge/scripts/kb.py" query -d "$PARAMS_DIR" --list-fields
"$SUITE_PYTHON" "$SUITE_ROOT/knowledge/scripts/kb.py" query -d "$PARAMS_DIR" --list-tags
"$SUITE_PYTHON" "$SUITE_ROOT/knowledge/scripts/kb.py" query -d "$PARAMS_DIR" \
  -w category=memory,compilation -w performance_impact=high \
  --show name,scope,constraints,source_file,tuning_advice.quick_guide
"$SUITE_PYTHON" "$SUITE_ROOT/knowledge/scripts/kb.py" query -d "$PARAMS_DIR" -s HCCL \
  --show name,performance_impact,impact_detail --format yaml
"$SUITE_PYTHON" "$SUITE_ROOT/knowledge/scripts/kb.py" query -d "$PARAMS_DIR" \
  -w name=--max-num-batched-tokens -a --format yaml
```

多个 `-w` 是 AND；单个条件中逗号分隔的值是 OR；`--where/-w` 的值是子串匹配。
选择卡片前核对 YAML 内完整 `name`、`type` 和 `scope`，不能把筛选命中当作精确身份。
`-s` 对所有字段全文搜索；命中某词不证明参数与该机制有直接关系。
输出字段可用点号路径；完整语法以当前 `kb.py query --help` 为准。
标签仅在选中数据含 tags 时适用；默认未打标数据查不到标签，不表示没有相关参数。
本套件仅迁入查询、提取和解析流程，不包含标签生成，也不隐式读取外部 tag 目录。当前查询 CLI 没有 `--limit`。

每次查询保存 `query_id`、snapshot、argv、退出码、stdout/stderr 文件及 hash。
另存选中卡片的路径/hash、精确身份、选择理由；相关假设按需附上，现场源码核验尚不可得时明确 unknown。
保存命令真实退出码，不能用 `tail` 等末端命令的成功掩盖查询失败；输出拒绝覆盖。
缺卡时查本快照的 `parameters.json`、解析输出 `logs/stage1_skipped.json`、`logs/stage2_skipped.json`，再查源码。
缺卡不等于参数不存在，也不等于参数对当前模型没有性能影响。

现有 `query.py` 会跳过损坏 YAML；查询成功不能证明所有卡片均成功加载。
`check_kb_snapshot.py` 只读检查卡片结构、唯一身份/文件名碰撞及 manifest 差异，并产生新报告。
其结果不证明源码语义正确、卡片覆盖完整或 LLM 推断可信；差异须解释后决定如何使用。

## 4. 区分事实、建议与待证机制

既有字段也须核验：`constraints` 不天然是硬约束，`source_file` 也可能只指向文档或测试。
先检查限制的证据，再评估推荐值；不要将“recommended”因字段位置改写为“必须”。

| 主张类型 | 核验方式 | 允许结论 |
|---|---|---|
| `source_fact` | 当前版本的定义、assert/raise、校验、覆盖和实际使用路径 | 限定分支及前置条件下的事实 |
| `documented_advice` | 指定版本文档、模型/硬件/负载条件 | 场景建议，可成为搜索起点 |
| `inferred_mechanism` | 明示推理链和预期中间信号 | 待实验检验的解释 |
| `empirical_observation` | 原始运行、契约、质量和统计比较 | 已测条件下的观察与效果 |

关键主张的 review sidecar 至少保存：参数身份、卡片 hash、主张文本/类型、
`source_ref`（仓库身份、文件、定位、必要片段 hash）、适用条件、核验状态和备注。
核验状态用 `verified / unverified / contradicted`，不以 LLM 自评置信度替代证据。
卡片 `performance_impact` 是候选排序线索，不是本场景收益预测或已测收益。
默认值可能动态计算或被插件覆盖；`unset` 表示保持未设置，不是启动参数的字面值。
KB 中没有现成参数建议时，沿 usage_locations/source_file 核验算子、图、调度或通信实现，
也可以形成代码/执行路径候选。候选必须说明影响哪些因子和可能代价；修改实际请求语义时另建契约与基线。

## 5. 有界建设与环境准备

先确定 scope（参数/源码文件/全量）、目标源码身份、截止时间、LLM 调用与费用预算、审查范围。
按 [构建记录模板](../assets/knowledge-build.example.json) 保存身份、阶段、覆盖、验证和发布状态；它不自动执行构建。
预算属于本次 campaign；知识建设不得无限挤占真实调优和独立确认时间。
构建状态区分 `planned / running / partial / complete / failed`，另记验证和发布状态。
到达预算保留进度与缺口，回到可做的调优动作；`partial` 不得描述为全量构建完成。

使用内置构建器和独立新 build 目录，保留当前可用快照。构建器版本以套件 manifest 及实际代码 hash 固定。
套件 `scripts/setup_runtime.py` 从 manifest 读取本模块 `knowledge/resources/requirements.lock` 和 `knowledge/resources/wheels/`，离线安装到套件根 `.runtime`；
依赖由 knowledge 维护，套件工具负责安装，evaluate 的标准库工具不依赖此环境。
当前离线轮子锁定 Linux aarch64 / CPython 3.9，需要对应的系统 Python 可创建 venv；不在模型环境或系统 Python 中安装解析依赖。
轮子必须与宿主平台、架构和 Python 兼容；安装成功后执行资源核验与所需入口的 `--help`。
不要仅凭主机有 Python 就假定依赖已满足；依赖版本和运行时身份随构建记录。

源码、模型服务、profiling 原件、负载和 API 环境变量属于本次任务输入，不属于内置历史知识。
提取和解析都显式传入真实 `--vllm-src`、`--vllm-ascend-src` 与新 `--output`；解析另传 `--input`。
不得将旧源码复制进套件后当成当前服务使用的源码。输入若不是 Git 仓库，保存文件内容指纹并明确来源限制。
`kb.py` 定位并转交内置模块，底层入口根据显式参数配置源码；调用者不再手写 launcher、修改模块全局路径或设置外部 builder。

LLM 模型、凭据与可选端点只来自本次环境，不读取 `~/.claude/settings.json`。
调用前必须提供 `ANTHROPIC_MODEL` 和 `ANTHROPIC_API_KEY`（或 `ANTHROPIC_AUTH_TOKEN`）；
自定义端点用 `ANTHROPIC_BASE_URL`，未指定时使用 SDK 默认端点。采样与重试等规则记录实际内置配置。
执行前核对有效模型、端点、采样配置及配置来源；日志记录身份，不记录凭据值。
不要转储整个环境，也不要为本任务修改用户全局配置。无凭据时仍可查询、静态提取和规则预演；LLM 解析保持待执行。
`kb.py` 及其子命令的 `--help` 用于查看接口；工作流不直接调用旧底层模块入口。

解析入口在写入构建目录或初始化 API 前，拒绝重复 name，并对完整 Stage 1 通过集预检 sanitize 后的文件名碰撞。
预检包括 `--max-params` 截取范围之外的条目；例如 `--foo-bar` 和 `--foo_bar` 都生成 `foo_bar.yaml`，会明确失败。
该检查不修改命名规则、不自动合并别名，也不证明参数身份已核验。同名跨 scope/type 的参数仍须人工解释和保存映射。
概念身份至少由 `type/name/scope` 区分；当前生成器按 name 生成单一文件名，不能把文件名当作完整参数主键。
遇到冲突先解决输入/别名或修改并核验生成器，再用新 build 解析；不能删除冲突条目后冒称输入已全量处理。

Stage 2 返回的 `name/type/scope` 必须与当前输入精确一致，包括被判断为 `performance_impact=none` 的条目。
缺失或不一致的身份记为解析错误，不修正为看似成功的卡片。卡片以禁止覆盖的方式写入，目标已存在时保留原件并记录错误；不要为继续构建而删除冲突原件。

## 6. 提取与规则预演

`NEW_BUILD` 是 campaign 下本次新建目录，所有输入/输出路径均使用绝对路径。
`VLLM_REPO` 与 `ASCEND_REPO` 必须是已核对来源的实际源码目录；`SUITE_PYTHON` 沿用第 3 节。

```bash
"$SUITE_PYTHON" "$SUITE_ROOT/knowledge/scripts/kb.py" extract \
  --vllm-src "$VLLM_REPO" --vllm-ascend-src "$ASCEND_REPO" \
  --output "$NEW_BUILD/parameters.json" --pretty
```

默认提取是静态阶段，不调用 LLM；它不等于完整文档补全。
显式 `--with-claude` 才进入文档 LLM 补全及其 regex fallback；先核对该阶段有效模型、端点和预算。
保存提取输入/输出 hash、源码身份、原始日志及真实退出码；先校验参数身份、计数和碰撞，再解析。
输出不指向套件内置历史快照，也不覆盖已封存 build。

解析保留 `--input/-i`、`--output/-o`、`--resume/-r`、`--dry-run-stage1`、
`--max-params/-n`、`--concurrency/-c`、`--verbose/-v`，同时要求两套显式源码路径。
不需要提供 `SOURCE_COMMIT_*` 标签，入口根据实际输入记录来源；来源记录不代替部署一致性核验。

```bash
"$SUITE_PYTHON" "$SUITE_ROOT/knowledge/scripts/kb.py" parse \
  --vllm-src "$VLLM_REPO" --vllm-ascend-src "$ASCEND_REPO" \
  --input "$NEW_BUILD/parameters.json" --output "$NEW_BUILD/stage1-preview" \
  --dry-run-stage1
```

dry-run 不发解析 API，但会创建日志、schema 副本、progress 和筛除记录；它不是只读预览。
该构建的 mode 固定为 `stage1-only`，不能用 `--resume` 将它转成 `llm` 模式；正式解析使用新输出目录。
核对 Stage 1 筛除理由，避免仅凭筛选规则丢弃当前假设需要的参数。

## 7. LLM 解析、恢复与验证

确认有效配置、依赖、源码和预算后，在新目录执行小范围解析：

```bash
"$SUITE_PYTHON" "$SUITE_ROOT/knowledge/scripts/kb.py" parse \
  --vllm-src "$VLLM_REPO" --vllm-ascend-src "$ASCEND_REPO" \
  --input "$NEW_BUILD/parameters.json" --output "$NEW_BUILD/analysis" \
  --max-params 8 --concurrency 1
```

`--max-params 8` 仅截取 Stage 1 通过项的前八项，既不是按名称选择，也不是八次 API 调用预算。
重试、上下文和并发都会影响调用成本；解析器没有可据此假定的硬调用预算参数。
现有封装自身会重试，且未显式设置 SDK 的 max_retries；按实际 SDK 版本核对其重试配置，将底层请求也计入预算。
需要硬预算时，先实现并核验调用计数、有界重试与截止监督；仅降低 max-params 不能声称已实现。
若只分析某些参数，生成可追溯的定向输入并保留它与全量提取结果的映射，不能冒称全量。

`--resume` 要求已有本工具生成的 `build-inputs.json` 和有效 `progress.json`，并逐项比较本次构建身份：

- 输入文件的真实路径与 hash，以及两套源码的路径、Git/dirty 和 Python/Markdown 内容指纹。
- `builder.files_sha256`：`kb_runtime.py`、解析器 Python 文件、resources 中的规则/提示/schema 等资源，以及保留的 `prompt.txt`。
- Python 版本、mode（`stage1-only` 或 `llm`）、`max_params`、`concurrency`。
- `llm.model` 和实际端点；LLM 模式未配置自定义端点时记录 `https://api.anthropic.com`。API 密钥不写入身份，允许独立轮换凭据。

任一上述身份不同就拒绝续跑，必须新建输出目录；包括规则/提示/schema、模型/端点、并发或范围变化，以及 dry-run 转正式 LLM 解析。
端点不能含 userinfo、query 或 fragment；凭据仅从专用环境变量传入，不能藏在 URL 中。
续跑还会拒绝已有输出树内的符号链接，避免沿链接改写其他文件。
自动身份检查不证明旧产物语义正确、依赖环境完全一致或实际部署源码匹配；继续核验套件运行时、产物和任务范围。
resume 复用逐项终态和有效产物，保留历史错误，不自动重试 error_params；缺失或不一致的恢复证据记为错误，不能把缺卡猜成无性能影响。
存在历史或本次错误时，解析仍返回非零，manifest 的 `errors` 保留这些失败；失败不计入 `confirmed_not_perf`，`output_skipped_count` 只包含 Stage 1 跳过项与成功判为 none 的条目。
根据退出码、manifest、progress 和逐项产物共同登记 partial/failed；只有本次约定范围处理完整且无错误才能登记构建 complete，完整覆盖与语义审查另行判断。
修复规则、提示或代码后使用新 build，保留旧构建证据。本次修订改变构建器身份，旧版本产物不会被新版本静默接续；需要接续旧任务时使用与其身份匹配的原工具。
非 resume 拒绝已存在的输出路径；resume 也不是修改已发布快照的许可。内置历史快照受保护，新建结果放入 campaign。

先运行 `check_kb_snapshot.py`，再核验当前候选涉及的高风险主张：默认值、硬限制、互斥和数值语义。
检查源码引用可定位、字段类型和合法值正确、约束与建议分开、相关参数可解析或有别名说明。
对提取输入建立去向账：成卡、规则跳过、无性能影响、错误、待处理和 alias；不得无解释地丢项。
记录实际卡片文件数与 manifest 统计差异；静态结构检查通过不等于该去向账或语义已经通过。

## 8. 发布与实验反馈

新 snapshot 清单至少保存：snapshot_id、两仓库内容身份、构建器/提示/schema/model 身份、
输入 hash、实际执行范围、逐项终态、卡片 hash 清单、alias/碰撞/错误清单及审查结果。
review 交付结构、源码语义和覆盖三个独立结论及审查范围；publish 消费这些结论和明确的发布委托。
在委托要求的审查通过后，先落完整 snapshot 和清单，再切换指定发布引用，保留旧版本与回退方法。
`partial` 可显式用于发现候选，但不得当作已核验的完整知识库；使用时说明缺失范围。
发布后不改原卡片；纠错和反馈形成新版本。knowledge 返回发布记录，不写全局 state；
当前 campaign 继续 pin 原 snapshot，是否切换及重核验哪些候选由协调者决定并留痕。

实验正负结果及无效运行先由 evaluate、diagnose、optimize 各自封存产物，knowledge 只消费这些公开证据引用；原始数据、失败和中断均保留。
知识增量引用 campaign_id/run_id、契约、配置/环境/负载身份、原始与比较报告、质量/SLO、
性能效果、目标因子及实测变化、机制状态、适用范围及证据强度；之后经审查进入新 snapshot。
单次收益不能变成通用推荐，抽样输出一致不能写成整体无损，效果成立不等于机制已证实。
无效运行可产生排障线索，但不能产生可靠性能收益；受反驳的机制也应保存适用范围和证据。
未完成独立确认或源码核验的增量保持待审，不直接覆盖现有建议或扩大结论范围。
