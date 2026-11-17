# 套件安装、注册与验证

本文件只描述套件管理。业务 CLI 由模块维护：[evaluate 工具手册](../evaluate/references/tool_usage.md)、[knowledge 工作流](../knowledge/references/workflow.md)。diagnose 和 optimize 目前提供方法与产物契约，不伪装成自动采集器或服务执行框架。

## 1. 真实路径与运行环境

从发现薄索引读取真实入口；主入口所在目录是套件根，不从当前 shell 目录或发现索引父目录猜测。示例路径在套件搬迁后替换为实际路径。

```bash
SUITE_ROOT=$(realpath /share_data/zhh_workspace_1020/.kerminal/skills/vllm-ascend-throughput-skills)
python3 "$SUITE_ROOT/scripts/verify_suite.py"
```

每条命令独立检查退出码。verify_suite.py 读取实际套件，输出 manifest、文件与结构核验结果，不修改资源。失败时先排查版本或缺失文件，安装依赖不能修复错误的资源身份。

工具代码支持 Python 3.9+。evaluate 的五个脚本只使用标准库，可直接运行，无需安装 knowledge 依赖：

```bash
python3 "$SUITE_ROOT/evaluate/scripts/benchmark.py" --help
python3 "$SUITE_ROOT/scripts/run_tests.py" --scope evaluate
```

knowledge 的依赖锁与轮子位于 `knowledge/resources/`，当前匹配 Linux aarch64 / CPython 3.9。需要该能力时安装或复用套件根 `.runtime`：

```bash
python3 "$SUITE_ROOT/scripts/setup_runtime.py"
SUITE_PYTHON="$SUITE_ROOT/.runtime/bin/python"
"$SUITE_PYTHON" "$SUITE_ROOT/knowledge/scripts/kb.py" --help
```

setup_runtime.py 根据 manifest 定位锁文件和轮子，离线安装到根 `.runtime`，不修改系统或模型环境、不默认联网取包。宿主 Python 须可创建 venv，轮子须匹配平台/架构/Python；资源校验通过不代表任意平台可安装。`--rebuild` 在隔离位置重建并保留旧环境，按现有任务范围执行。

根 `.runtime` 是部署安排，不是模块间的实现依赖；evaluate 不通过 knowledge 或安装器调用其业务工具。搬迁后核对实际解释器及可执行路径，必要时重建；复制 venv 后文件存在不足以证明可用。

系统 Python、驱动和模型服务是宿主环境；部署源码、负载、profiling 原件及 API 环境是任务输入。安装依赖、生成元数据和校验文件不会启动模型服务；benchmark 会发送真实请求，只在相应委托内运行。

## 2. 注册发现入口

AGENT_SKILLS_DIR 由当前 agent 环境确定，注册到该实际发现目录：

```bash
python3 "$SUITE_ROOT/scripts/register_skills.py" --skills-dir "$AGENT_SKILLS_DIR"
```

注册器仅创建或更新主入口和 evaluate、diagnose、optimize、knowledge 五个普通目录薄索引，保存名称、描述和真实入口指针。主索引指向根 SKILL.md，模块索引指向各自 SKILL.md。名称冲突或已编辑的套件索引在写入前拒绝，其他目录不修改。

迁移历史版本时，先核对 measure/profile/validate 旧入口及索引确属本套件且未被用户修改，再备份到活动套件和发现目录之外；注册器不自动删除旧目录。未知副本先核对来源。

外部索引不保存第二份工作流、工具或 KB。套件搬迁后重新注册；默认不用未经 loader 验证的符号链接。注册完成不代表 loader 已发现新版本或运行中的上下文已刷新，需分别核对。

## 3. 按模块或整套验证

统一测试入口按 manifest 中实际登记的目录发现测试，任意工作目录均可调用：

```bash
python3 "$SUITE_ROOT/scripts/run_tests.py" --scope evaluate
"$SUITE_PYTHON" "$SUITE_ROOT/scripts/run_tests.py" --scope suite
"$SUITE_PYTHON" "$SUITE_ROOT/scripts/run_tests.py" --scope knowledge
"$SUITE_PYTHON" "$SUITE_ROOT/scripts/run_tests.py" --scope all
python3 "$SUITE_ROOT/scripts/verify_suite.py"
```

knowledge、suite 与 all 使用知识依赖环境；evaluate 独立使用标准库。suite 验证结构、注册、测试入口及实际 KB 查询/构建器帮助接口，因此需要 YAML 等依赖，但不启动知识构建或 API 调用。knowledge 范围包含模块外层测试和 KB 内部测试，all 汇总所有登记范围；没有专属执行代码的模块不创建空测试目录。

测试验证离线工具和接口行为，不证明 NPU 性能改善、全量知识语义正确或所有现场采集格式可解析。保留实际命令、解释器、退出码及报告；经 tail/tee 展示时不能把显示命令的退出码当作被测程序结果。
