# Profiling 映射与因子采集

优先复用基线总账、trace、引擎日志、采集命令、版本及 rank/stream 清单；缺 trace 不自动触发重型采集。

## 执行

按 [因子诊断](factor_diagnosis.md) 建立 [factor ledger](../assets/factor-ledger.example.json)；计数与窗口以 [测量契约](../../evaluate/references/measurement_contract.md) 为准。

1. 盘点因子树各分支的已知、缺失和不适用项，再按下一决策的信息价值选择精测范围，不要求先收齐全部因子。
2. 检查实际源格式、采集版本/开关、窗口、rank/stream、丢失与截断。为每项保存“字段/事件 → 源码语义 → 筛选/去重 → 聚合 → 单位”的映射、解析器身份及可手算样本，不照搬历史表名或列名。
3. 客户端提供用量、终态和完整窗口；引擎语义日志提供 K、B_k、接受、停止及输出位置。常规 msprof 的 kernel/shape 不能自动恢复业务计数，缺失时提出具体标记。
4. 核对逻辑轮、多副本/DP 边界与输出唯一键；同轮同序列重复调用不增加 B_k，TP 副本不增加逻辑输出。资源分析仍保留 rank 维度。
5. 校准客户端与 host/device、跨 host 时钟及单位，记录误差和跨界归属。短窗输出须关联最终请求状态；不能与整批输出或其他 run 拼接成精确分解。
6. 仅在同 run/同窗口、输出唯一归轮、包含关系和非零分母成立时算五因子。`tau=T/K` 是有效完成间隔，流水下不等于轮生命周期。各量标 measured/derived/estimated/unavailable/not_applicable，未知或零分母保持 null。
7. 时间事件按 scope 裁剪、取并集后分为 compute_only、communication_only、overlap、neither，保留首尾与无事件区间；跨 rank 墙钟覆盖与累计资源时长分开。PMU 仅用当前产品/版本支持的字段并记录扰动。通信可含等待，空白可为漏采，占比不等于可回收成本。
8. 独立核对输出唯一归属、逐轮参与、停止/终态与客户端总账，再记录五因子及时间残差；同组总数约消得到零残差不证明计数正确。保留差异，不调数凑齐。

当前工具不自动解析 msprof、维护 ledger 或添加语义标记。需要适配时在 campaign 保存解析器，以受控样本验证单位、边界、重复和重叠；总账工具查 [evaluate 工具手册](../../evaluate/references/tool_usage.md)，诊断产物见 [记录契约](records.md)。采集/埋点由协调者安排，诊断运行与关闭重型 profiler 的计分运行分别留存身份。

## 完成与产物

交付 ledger、字段映射/解析器、原始引用、覆盖/时钟说明、独立对账、相关观察及最小补采计划。
约定提取或审计完成即可 `completed`，不要求所有因子有值；影响结论的语义、关联或覆盖缺口返回 `needs_evidence` 及补采成本。解析/采集失败保留原件与部分覆盖。输出供诊断使用，不凭最大占比或最小因子直接判定瓶颈。
