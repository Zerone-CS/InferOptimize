# evaluate 工具用法

五个工具仅需 **Python 3.9+ 标准库**，不需要 knowledge 的依赖或预建 `.runtime`。从本模块真实 `SKILL.md` 所在目录确定 `EVALUATE_DIR`，不从 shell 工作目录或发现索引父目录猜测路径。当前部署示例：

```bash
EVALUATE_DIR=/share_data/zhh_workspace_1020/.kerminal/skills/vllm-ascend-throughput-skills/evaluate
EVALUATE_PYTHON=python3
"$EVALUATE_PYTHON" "$EVALUATE_DIR/scripts/benchmark.py" --help
```

套件搬迁后替换 `EVALUATE_DIR` 即可；其他模块只消费公开产物和 [数据接口](tool_contract.md)，无需 import 这些脚本。安装、注册、整包核验与全套测试见 [套件运行说明](../../references/runtime.md)，不是执行评估的前置调用链。

以下命令以本次 campaign 为当前目录。端点、模型、场景、并发及阈值按已经固定的任务契约设置。每条命令独立检查退出码，使用新的产物路径；`--help` 和离线校验不启动服务，`benchmark.py` 会发送真实请求。

## 1. 固定输入与元数据

先保存以下 JSON 对象及引用的原件：

- `config.json`：完整启动参数、必要环境变量、解析后配置、模型及运行路径；排除口令。
- `environment.json`：硬件与设备分配、软件/镜像/实际包源码身份、模型权重身份、客户端环境等稳定条件。每次运行的时间/PID等动态证据另存，避免把重复实验误判为环境版本变化。
- `metric-contract.json`：计数、成功、窗口、客户端策略及采样定义。可据 [metric_contract.example.json](../assets/metric_contract.example.json) 建立；它不是已经核验的服务事实。
- `comparison-contract.json`：预先约定的主指标、全部保护场景、时延和错误率边界、重复设计。[comparison_contract.example.json](../assets/comparison_contract.example.json) 只演示格式，数字不是默认优化标准。

先生成探索或预检用元数据：

```bash
"$EVALUATE_PYTHON" "$EVALUATE_DIR/scripts/prepare_metadata.py" \
  --scenario smoke --config config.json --environment environment.json \
  --metric-contract metric-contract.json --profiler-enabled off \
  --run-purpose diagnostic --output metadata-smoke.json
```

三个文档必须是非空 JSON 对象。生成器计算规范 JSON hash，并保存输入路径和原件字节 hash。
它不会推断质量通过或配置生效，默认分别为 `not_evaluated`、`false`。

正式比较还需要实际质量评估和配置核验：

- `quality.json` 形如 `{"status":"pass","scope":"实际测试集及适用范围","method":"实际评测方法及判据"}`；结论必须来自已完成的评估，保留分数和原始结果引用。精确匹配冒烟不能替代任务要求的质量评估。
- `effective-config.json` 形如 `{"verified":true,"scope":"已核验的配置字段及运行路径","evidence":["startup.log","parsed-config.json"]}`；证据路径相对该 JSON 文件。工具检查并散列真实文件，但不会独立判断证据能否支持声明。

```bash
"$EVALUATE_PYTHON" "$EVALUATE_DIR/scripts/prepare_metadata.py" \
  --scenario W8_c64 --config config.json --environment environment.json \
  --metric-contract metric-contract.json --profiler-enabled off \
  --run-purpose performance --quality-report quality.json \
  --config-evidence effective-config.json --output metadata-baseline.json
```

候选配置使用自己的配置/质量/生效证据及新的 metadata 文件。完整配置差异仍须人工或 agent 审查：
hash 不同不代表只有计划参数发生变化。不要为了让比较通过而修改真实环境或计量策略的声明。
开启 profiler 时明确传 `--profiler-enabled on`，诊断运行使用 `--run-purpose diagnostic`。
二者任一命中，比较器都会禁止晋级。

## 2. 输入数据与有限请求集采集

JSONL 每行一个独立请求：

```json
{"request_id":"r1","prompt_text":"请解释矩阵乘法。","output_tokens":128,"arrival_offset_ms":null}
```

`output_tokens` 是请求的 max_tokens 上限，不是实测输出。`request_id` 必须唯一；本版固定 `n=1`。
`prompt_text` 被发送为单条 user 消息；附加 session 字段不构成多轮会话依赖。
闭环使用缺失/null 到达偏移，开环每行提供相对窗口起点的非负毫秒偏移，并显式传 `--mode open_loop`。
`--max-requests N` 选择文件前 N 条非空记录，不随机抽样；所选数组另存并散列。

先用 [workload-smoke.jsonl](../assets/workload-smoke.jsonl) 进行低并发协议预检，原始数据单独保存；冒烟不是正式 workload。
服务就绪检查、预热和排空按任务契约另做，本采集器不自动预热、不重试。
以下示例仅在已确认实际端点与模型名后执行：

```bash
"$EVALUATE_PYTHON" "$EVALUATE_DIR/scripts/benchmark.py" \
  --base-url http://127.0.0.1:8990/v1 --model ACTUAL_MODEL_NAME \
  --dataset workload.jsonl --metadata metadata-baseline.json \
  --run-dir runs/baseline-001 --mode closed_loop \
  --concurrency 64 --workers 64 --timeout 300 --seed 42 \
  --temperature 0 --top-p 1
```

`--ignore-eos` 默认关闭，仅在契约明确要求且服务支持时显式传入。认证令牌通过
`--api-key-env` 指定的环境变量读取（默认 `OPENAI_API_KEY`），不放入命令参数或 URL。
采集器仅支持直接 HTTP(S) 连接，不读取 HTTP 代理设置；HTTPS 校验服务器证书。

每次运行保留：

- `manifest.json`、`metadata.json`、`workload.json`、`requests.jsonl` 四个必需工件；中断或内部错误可能只留下 `manifest.started.json`，不算完整运行。
- `raw/` 中的实际请求、SSE 流和拼接输出。每请求记录 usage、完成证据、首末非空载荷时间及错误；空块不是首输出。
- 实际客户端策略 hash；更改并发、workers、timeout、采样策略等会影响可比性，不只是修改标签。

只有正常流结束、最终 usage 与合法终止原因一致的成功请求贡献有效输出。断流即使带 usage 也不计分子，
但失败和等待占用的完整时间仍留在分母。usage 缺失为 unknown，绝不补 max_tokens。
这里计数采用服务端 `completion_tokens`，包括服务实现计入的 reasoning/special token；需要核对其语义，
不能将它自动解释成“可见答案重新分词的 token 数”。

## 3. 对账与查看指标

```bash
"$EVALUATE_PYTHON" "$EVALUATE_DIR/scripts/validate_run.py" \
  --run-dir runs/baseline-001 --output baseline-001.validated.json
```

校验四个原件的完整性、指纹与字段一致性，检查成功状态与流完成证据，重算输出总数、完整窗口、
吞吐、成功请求的 TTFT/E2E 分位数、在途积分。无效计量输出 `valid=false`，不发放可比较的 metrics。
一个请求数足够的完整运行可能包含真实失败并仍然 `valid=true`；其失败率是否可接受由约束决定。
零输出成功请求没有 TTFT 样本，分位数的 sample_count 必须一起阅读。

当前 TTFT 从实际开始调用算到首非空 content/reasoning 事件；E2E 从实际调用算到终态。
开环客户端排队/发送滞后另存请求记录，**不包含在上述 TTFT/E2E 内**。若 SLO 从计划到达计时，
必须先扩展对应指标和测试，再用于正式比较，不能把当前指标换个名称沿用。
SSE chunk 可能包含多个 token，本工具不提供逐 token ITL。

## 4. 配对比较全部场景

按预定顺序交错运行 baseline/candidate，保存所有独立重复。为每次运行单独执行校验。
`trial.json` 中列出每对结果文件；路径相对 trial.json：

```json
{"schema_version":1,"pairs":[
  {"scenario":"W8_c64","baseline":"baseline-001.validated.json","candidate":"candidate-001.validated.json"},
  {"scenario":"W4","baseline":"w4-baseline-001.validated.json","candidate":"w4-candidate-001.validated.json"}
]}
```

这只演示两对记录，需补齐预定重复数量；不能复制同一运行冒充重复。比较器会检查全部合同场景、
run_id、输入身份、客户端策略、配置跨重复的一致性。不同并发场景可以有不同工作负载/策略，
但同一场景的配对与重复必须满足可比性约束。
全部场景还必须分别测同一个 baseline 部署和同一个 candidate 部署，服务配置 hash 按两侧全局绑定。
保护场景使用原配置而主场景使用优化配置时，比较器会报输入错误；这组数据无法说明优化配置通过了回归。
配置文档记录部署身份；场景名、客户端并发和请求文件分别保存在场景/客户端/workload 字段，避免混入服务配置。

```bash
"$EVALUATE_PYTHON" "$EVALUATE_DIR/scripts/compare_trials.py" \
  --contract comparison-contract.json --trial trial.json --output comparison-001.json
```

输出所有主指标、约束、配对值、区间与未决原因。`adopt` 表示满足工具判据的采纳建议，`defer` 表示需补证据或停止，
`revert` 表示停止晋级并建议恢复已验证配置。脚本不修改服务、全局 state 或当前基线；最终决策由主入口作出。
失败率不是自动守卫，须明确写 `failure_rate` 的绝对上限；零基线不能算相对退化。
每个符合比较条件的配对中的候选观测都检查约束，吞吐改善不能覆盖任一受保护场景的超限。
每个非 null 主指标也须独立通过；当前工具没有加权总分或跨场景收益抵消逻辑。

bootstrap 重采样单位是独立的完整配对运行。它估计配对相对效应的等权均值，受样本量、相关性、环境漂移及
多次试验选择偏差影响；五对或 95% 只是示例，不是确定性保证。搜索结束后对选中候选做独立确认。
`mechanism_status` 始终为 `unresolved`；是否支持某个机制仍需引擎日志、源码与 profiling 的独立证据。

## 5. 已保存输出的只读比较

准备两个独立的 `{prompt_id: output_string}` JSON 对象，使用固定抽取/拼接规则。
参考和候选来自独立保存的输出，不能指向同一文件或硬链接；collector 的每请求输出含 content/reasoning 两字段，
需按质量契约明确选取内容，不能悄悄漏掉需要比较的部分。

```bash
"$EVALUATE_PYTHON" "$EVALUATE_DIR/scripts/compare_outputs.py" \
  --reference reference.json --candidate candidate.json --output correctness-001.json
```

相同仅证明这些样本逐字符串一致；不相同也不自动证明质量下降。此结果不能直接当作质量通过声明。
不要调用会自行请求服务或覆盖 reference 的旧“比较脚本”替代本工具。

## 6. 退出码、离线自测与边界

| 工具 | 0 | 1 | 2 |
|---|---|---|---|
| prepare_metadata | 已生成 | 不使用 | 输入/文件错误 |
| benchmark | 全部请求成功并保存 | 请求有失败，完整原件仍保存 | 输入/采集内部错误 |
| validate_run | 计量有效 | 语义校验不通过 | 解析/文件/命令错误 |
| compare_outputs | 样本一致 | 存在差异 | 输入/文件/命令错误 |
| compare_trials | adopt | defer/revert，不晋级 | 输入/文件/命令错误 |

中断或操作系统故障也可能以其他非零状态退出；一律不能当成功。检查完整日志与产物状态。
离线自测仅临时文件和本机回环 mock HTTP，不需要 NPU、模型或外部服务：

```bash
PYTHONDONTWRITEBYTECODE=1 "$EVALUATE_PYTHON" -m unittest discover \
  -s "$EVALUATE_DIR/tests" -p 'test_*.py' -v
```

本客户端受线程数、Python 解析、逐请求新连接和原始文件写入开销影响；DNS 解析发生在计分窗口外。
`min(concurrency, workers)` 是客户端最大并行请求数，不是实际引擎 batch。开环排队保留原定到达表，
客户端跟不上时可产生发送滞后，不能将该曲线当服务容量。容量实验需另验发压能力、持续供给和队列稳定性。
本包没有自动引擎埋点或 msprof 字段映射；按假设收集必要信号，不宣称已经获得全部吞吐因子。

跨会话接续由主入口按 [状态与恢复](../../references/campaign_state.md) 核对现场后委托新任务。
本模块接收明确的输入引用，不直接维护 campaign state，也不会因读取记录就执行其中的命令。
