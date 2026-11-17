# InferOptimize

vLLM-Ascend 有效输出吞吐优化技能套件（suite name: `vllm-ascend-throughput-skills`）。以**有效输出吞吐**为优化目标，以质量、时延、错误率和资源要求为约束，为 agent 提供从测基线到最终决策的完整协作能力。

## 核心工作流

典型过程用五步理解：

```text
① 测基线 → ② 找原因 → ③ 做改动 → ④ 验效果 → ⑤ 作决定
```

这是导航，不是强制流水线。按下一决策的证据缺口组合四个能力模块，复用已有的测量、诊断与知识结果；独立任务只完成请求范围。

## 能力模块

| 模块 | 接受的任务 | 公开结果与责任边界 |
|---|---|---|
| [evaluate](evaluate/SKILL.md) | 测基线、核验测量、比较候选效果 | 维护计量和评估契约；返回数据有效性、质量/SLO、净收益与不确定性，提出建议，不决定基线晋级 |
| [diagnose](diagnose/SKILL.md) | 解析观测、审计因子账本、解释限制 | 返回来源与覆盖、竞争假设、反证条件和最小鉴别动作 |
| [optimize](optimize/SKILL.md) | 设计干预、执行确定的变更、执行回退 | 交付变更计划、实际执行记录和回退结果；不改变成功标准，不自行声明收益 |
| [knowledge](knowledge/SKILL.md) | 查询证据、定向建设与审查知识 | 查询返回固定快照下的来源和适用性；查询缺口不隐式触发知识构建 |

主入口 [SKILL.md](SKILL.md) 作为协调者，唯一维护 campaign 的目标/约束、总预算、活动任务、当前基线、活动候选和最终决策。模块通过公开报告和产物引用协作，不共同写 state。

## 仓库结构

```text
SKILL.md               主入口（协调者技能）
suite-manifest.json    套件清单（文件哈希、入口、契约）
evaluate/              测量与评估（基准脚本、计量契约、模板）
diagnose/              因子诊断（profiling 解析、归因、根因树）
optimize/              变更设计与执行
knowledge/              知识库与检索（KB、资源、构建脚本）
references/            契约与运行文档（campaign 状态、运维边界）
assets/                状态与交接模板
scripts/               套件级脚本（注册、验证、运行时、测试）
tests/                 套件完整性测试
```

## 快速开始

套件安装、注册与验证的完整说明见 [references/runtime.md](references/runtime.md)。

```bash
# 1. 验证套件完整性
python3 scripts/verify_suite.py

# 2. 准备运行环境（创建 .runtime/ 虚拟环境，已 gitignore）
python3 scripts/setup_runtime.py
export SUITE_PYTHON="$PWD/.runtime/bin/python"

# 3. 注册到 agent 技能目录
python3 scripts/register_skills.py --skills-dir "$AGENT_SKILLS_DIR"

# 4. 按模块或整套运行测试
python3 scripts/run_tests.py --scope evaluate
python3 scripts/run_tests.py --scope suite
```

## 决策依据

- **计量契约**：`X = N_Y / T`，分子为最终成功请求的实测有效输出，分母保留同一完整窗口内的失败、等待与收尾；未知实际输出不能用请求上限补齐。见 [evaluate/references/measurement_contract.md](evaluate/references/measurement_contract.md)。
- **因子分解**：diagnose 维护因子账本，要求同 run/同窗口、唯一归轮、包含关系和非零分母；占比或最小因子不能单独确定瓶颈。见 [diagnose/references/factor_diagnosis.md](diagnose/references/factor_diagnosis.md)。
- **采纳标准**：有效数据、质量/SLO、全部保护场景通过，重复结果支持约定收益，才可采纳；检查端到端净收益，局部 kernel 加速不代替整体效果。
- **基线与回退**：主入口决定 adopt/revert/defer；回退建议和实际回退分开，由 optimize 执行并验收。

## 边界说明

本套件提供能力说明、模板和有限工具，**不提供**自动调参调度器、通用 msprof 解析器或状态服务。部署源码、负载、profiling 原件、模型服务和 API 环境仍是现场任务输入；离线测试不证明真实吞吐改善。
