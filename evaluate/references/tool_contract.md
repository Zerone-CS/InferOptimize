# 可执行工具的数据接口（schema_version = 1）

本接口由 evaluate 维护并公开。其他模块通过版本化产物消费它，不依赖 evaluate 脚本内部实现。
`schema_version=1` 及既有字段语义保持不变；不兼容变更需新版本及显式适配，不能覆盖旧原件。脚本仅在显式调用时工作；安装 skill 不启动服务或压测。
采集器使用 Python 3.9+ 标准库，面向 OpenAI-compatible `/v1/chat/completions` 的有限 JSONL 请求集。
原始输出目录必须不存在；所有派生输出同样禁止覆盖。相对时间使用同一客户端单调时钟。

## 原始运行

`run_dir/manifest.json`、`run_dir/requests.jsonl`、`run_dir/workload.json`、`run_dir/metadata.json`
是 `validate_run.py` 的必需输入；缺少原件时不能把来源声明当作已经对账。
manifest 必需字段：

```json
{
  "schema_version": 1,
  "run_id": "unique-id",
  "scenario": "W8_c64",
  "measurement_mode": "finite_batch",
  "start_ts": 100.0,
  "end_ts": 110.0,
  "clock": "client_perf_counter",
  "profiler_enabled": false,
  "run_purpose": "performance",
  "workload_sha256": "64-hex-digits",
  "config_sha256": "64-hex-digits",
  "environment_sha256": "64-hex-digits",
  "metric_contract_sha256": "64-hex-digits",
  "benchmark_sha256": "64-hex-digits",
  "metadata_sha256": "64-hex-digits",
  "client_measurement_policy": {"version": 1, "mode": "closed_loop", "concurrency": 64, "workers": 64},
  "client_measurement_policy_sha256": "64-hex-digits",
  "quality_status": "not_evaluated",
  "effective_config_verified": false
}
```

采集器从 `--metadata` JSON 取得 scenario、config_sha256、environment_sha256、
metric_contract_sha256、quality_status、effective_config_verified、profiler_enabled、run_purpose；缺少身份信息时拒绝开始。
这些是调用者提供的声明，不能自动证明服务配置或质量已核验；同时保存 metadata 原件与 hash。
quality_status 限 pass/fail/not_evaluated；effective_config_verified、profiler_enabled 必须是 JSON 布尔值。
run_purpose 必须明确为 performance 或 diagnostic；诊断数据不能晋级为正式收益证据。
workload_sha256 是实际使用的请求数组的规范 JSON SHA-256（UTF-8、键排序、紧凑分隔符、非 ASCII 不转义）；
使用子集时仅计算子集。benchmark_sha256 来自采集脚本内容。
metadata_sha256 是 metadata.json 原件的字节 hash。client_measurement_policy 记录实际客户端参数
和计数规则，其 hash 使用规范 JSON 算法；比较器还核对该 hash，避免仅沿用声明而改变采集策略。
上例仅展示策略对象的部分字段；实际对象由采集器生成，必须保留其完整内容，不能拿示例补写运行记录。
采集器另记录请求数、实际 CLI（不含密钥）、服务地址、采样/输出参数、并发/发送模式和配置。
完整计量策略（含客户端参数）变化时须更新 metric_contract_sha256，不得仅换名字。

每个 requests.jsonl 记录为一个请求（本版仅支持 n=1）：

```json
{
  "run_id": "unique-id",
  "request_id": "r1",
  "planned_send_ts": 100.0,
  "send_start_ts": 100.1,
  "response_open_ts": 100.2,
  "first_output_ts": 101.0,
  "last_output_ts": 109.0,
  "end_ts": 110.0,
  "final_status": "success",
  "finish_reason": "length",
  "requested_max_tokens": 16,
  "actual_output_tokens": 16,
  "actual_prompt_tokens": 32,
  "token_count_source": "server_usage",
  "stream_done_received": true,
  "final_usage_received": true,
  "output_event_ts": [101.0, 109.0],
  "error": null
}
```

final_status 限 success/error/timeout/cancelled；失败请求也必须记录开始/结束。
success 必须有可识别的完成状态、最终 usage、正常流结束；缺失时记 error，不能补配额。
stream_done_received、final_usage_received 是必需布尔值；success 要求两者均为 true。
本采集器认可 stop/length 为成功终止原因；不支持 tool_calls 等其他终止策略。
actual_output_tokens、actual_prompt_tokens 缺失时为 null，实测为零时为 0；不能互换。
首/末输出指非空 content 或 reasoning_content 载荷事件，空块、role-only 和 usage 帧不算输出。
output_event_ts 是非空输出事件时间，不是逐 token 时间；chunk ITL 不得命名为 token ITL。
若没有非空输出，first/last 为 null 且事件数组为空；实际计数为正而没有可解释的输出载荷时，
本版采集器标为 error，避免误把不支持的输出通道当有效完成。

## 校验结果

`validate_run.py --run-dir PATH --output NEW.json` 输出：

```json
{
  "schema_version": 1,
  "valid": true,
  "errors": [],
  "warnings": [],
  "manifest": {},
  "source_hashes": {},
  "metrics": {
    "n_requests": 1,
    "n_success": 1,
    "n_failed": 0,
    "failure_rate": 0.0,
    "wall_s": 10.0,
    "effective_output_tokens": 16,
    "output_token_throughput": 1.6,
    "request_throughput": 0.1,
    "ttft_p50_s": 0.9,
    "ttft_p99_s": 0.9,
    "e2e_p50_s": 9.9,
    "e2e_p99_s": 9.9,
    "observed_mean_in_flight": 0.99
  }
}
```

校验同时检查字段类型、有限数值、唯一 ID、时间顺序/窗口、实际计数与成功状态、
完整在途积分；输出 p99 使用线性插值并明确样本集为成功请求。
失败时间留在 wall_s 中。不存在逐 token ITL；可另输出名字准确的 chunk 间隔指标。
`valid` 只代表本文件契约通过，不代表现场无干扰、吞吐具有重复性或质量已通过。
输入不是本接口（如旧 benchmark records）时明确报错；不可静默“迁移”为可信数据。

## 实验比较

`compare_trials.py --contract contract.json --trial trial.json --output NEW.json` 只读取校验结果。
contract：

```json
{
  "schema_version": 1,
  "min_pairs": 5,
  "confidence": 0.95,
  "bootstrap_samples": 2000,
  "seed": 42,
  "scenarios": {
    "W8_c64": {
      "primary": {"metric": "output_token_throughput", "direction": "higher", "min_relative_improvement": 0.02},
      "guardrails": [{"metric": "ttft_p99_s", "direction": "lower", "max_relative_regression": 0.06}, {"metric": "failure_rate", "max_value": 0.0}]
    }
  }
}
```

trial：`{"schema_version":1,"pairs":[{"scenario":"W8_c64","baseline":"a.validated.json","candidate":"b.validated.json"}]}`。
路径相对 trial.json。每对必须来自两个独立运行，同一运行不能重复充当重复样本。
各组需相同工作负载、环境、计量契约、实际客户端策略、benchmark 版本与计分模式；基线/候选配置 hash 可不同，
但各自跨重复保持一致。正式比较拒绝 profiler_enabled=true、run_purpose=diagnostic、未核验配置、质量未通过、无效计量。
配置身份还须跨全部场景一致：一次 trial 只比较一个 baseline 部署与一个 candidate 部署。
不同场景可以有不同的 workload 和客户端策略；不能有不同的同侧服务配置。
`config_sha256` 对应部署配置，场景名称、客户端参数与请求文件不要混入服务配置文档；动态 PID/时间另存。
如果任务需要按场景切换服务配置，应显式设计并验证这种部署策略，当前比较器不支持合并为一次晋级结论。
这种拒绝是停止晋级，不是证明候选性能有害；缺失比较信息不自动变成外部阻塞。
重复单位是完整配对 run，bootstrap 在配对效应上重采样，保留方法与假设；不是对请求重采样。
在预定配对/稳定环境假设下，主指标区间下界超过最小收益、全部约束通过才可建议采纳。
样本不足、区间跨边界等记 inconclusive/defer；观察到保护条件超限则停止晋级。
min_pairs 是本轮设计参数，不是统计保证；五对是示例，不能借此保证小样本置信区间可靠。
比较器不确认性能机制；始终保留 mechanism_status=unresolved，机制证据另外登记。
primary 可为 null，仅保护该回归场景；至少一个场景指定主指标。
所有非 null 主指标及全部 guardrails 都须逐项通过，不支持加权汇总或跨场景抵消。
guardrail 可以规定 max_value/min_value 绝对界限，也可另加相对退化界限。
约束逐个检查所有符合比较条件的候选运行；任一观测超限停止晋级。主指标比较的是配对相对效应的等权均值，
不是合并所有 token 和时间后的吞吐比值。区间为各指标各场景单独区间，不是多重比较的联合置信保证。
允许的失败率必须显式写入 guardrails；比较器不会自动添加零失败约束。
基线为零时不能算相对变化；例如零失败要求使用 failure_rate 的 max_value=0。
搜索多个候选后应安排独立确认运行，避免把选择过程中的偶然最好成绩当可重复收益。

## 纯离线正确性比较

`compare_outputs.py --reference REF.json --candidate CAND.json --output NEW.json`。
两个输入都是 `{prompt_id: output_string}`，必须键集合相同、路径不同且文件存在。
只能读取，禁止同一文件/硬链接被当作对照；输出用独占创建，不覆盖输入或既有结果。
精确一致只报告样本 exact-match，通过不等于普遍质量等价；不同输出需任务质量评估。

本模块工具的 `--help` 均无副作用。上述五个测量/比较工具约定：0 完成/通过；1 检查失败、差异或未能建议采纳；
2 输入/命令/运行错误。benchmark 有请求失败时返回 1，但仍保存完整运行以供分析。
所有比较判定都是建议；工具不修改服务、主入口 state 或当前基线。外部质量声明和配置核验证据还需按 [评估记录](records.md) 审阅。
