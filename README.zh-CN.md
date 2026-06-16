# BAGEL Genesis

> 面向 Claude Code 和 Codex 的 V3.1 可执行专家运行时：先深度对齐，校准专家级标准，重构问题，识别最高杠杆路线，证明 runtime 能力，复放证据、控制范围，并持续迭代到约定边界。

[English](README.md) | **简体中文**

---

## 为什么需要它

普通 agent 已经很强，但一到隔夜长程任务，常见失败点非常稳定：

- 前期只问几个浅问题，目标没有真正对齐就开干；
- 遇到常规摩擦就停下来等用户；
- 主上下文被实现、调试、环境配置细节污染；
- 同一个 agent 实现、审查、再宣布完成；
- 把“用户最初列的功能做完”当成最终完成，而不是第一轮迭代完成；
- 第二天汇报很多，但进展是否真实很难验证。

**BAGEL Genesis V3.1 把这些变成一个可执行、可测量的专家自治运行时。** 它先把用户的目标、品味、硬停边界、预算、运行模式、专家标准、问题框架、杠杆地图、评价体系对齐清楚，然后持续推进实现、审查、恢复、提标和下一轮迭代，并用脚本验证进展是否真实。

核心循环很简单：

```text
深度对齐 -> 校准专家标准 -> 重构问题 -> 杠杆地图 -> 证明 runtime -> 构建 -> 复放证据 -> 再迭代
```

运行只在这些情况下停止：用户设定的迭代/预算边界到达，用户主动停止，token/运行容量耗尽并写好恢复点，或者遇到真正的硬停边界。

## 它和普通 prompt 有什么不同

| 问题 | BAGEL 的回答 |
|---|---|
| 前期对齐太浅 | 三档深度对齐：snap / standard / deep，所有决策持久化 |
| 中途等用户 | 强制绑定 loop/timer，间隔 <= 25 分钟 |
| 主上下文污染 | 主模型做 Supervisor；内部 Orchestrator 派发实现、运行时诊断、评价设计、审查、品味判断 |
| main/orchestrator 上下文失败 | 主模型可作为 Supervisor，从 `.bagel/supervisor/resume-capsule.md` 重新派生干净 Orchestrator |
| 长上下文逐渐塞满 | Context Tree：根 Supervisor 始终极小；非根 agent 通过替换而不是常规压缩续命 |
| 自己审自己 | 审查独立性从 agent/session registry 推导，不靠自报 |
| 品味弱、只会局部优化 | Product Visionary、Brainstormer、Judgment Council 参与方向级决策 |
| 没有清晰质量标准 | Evaluation Architect 为每轮生成指标、rubric、完成规则和防刷指标说明 |
| 初始目标完成就停 | Iteration Contract：初始目标完成只算一轮；预算未尽就继续提标 |
| 反复踩同一个坑 | Lesson memory 把恢复经验沉淀成 gotcha 和 playbook |
| 进展真假难辨 | `bagel_run_check.py`、`flywheel_check.py`、`bagel_memory_check.py` 机械校验运行状态 |
| 平台能力靠猜 | V2 proof model：adapter claim 不是 proof；R3、scheduled resume、hooks 都需要 observed proof |
| `.bagel/` 自洽假账 | Evidence replay 校验命令元数据、stdout/stderr hash 和 replay policy |
| 治理工作压过产品工作 | Telemetry 区分控制面 delta 和交付面 delta，Build 阶段连续自嗨会失败 |
| 静默扩 scope | Scope delta 记录 allowed/touched paths、依赖、敏感面和 approval |
| 高层决策浅 | Domain excellence model、problem framing、leverage map、Evaluation Critic、Principal Expert、ROI Controller |
| Supervisor 偷干 worker 活 | Supervisor boundary check 拒绝根 agent 自己做实现/调试/测试 |

## 什么时候用

当你希望 Claude Code 或 Codex 做这些事时，用 BAGEL：

- 构建或大幅改进 app、网站、工具、游戏、研究产物、写作项目、数据分析；
- 接管已有项目，同时不偏离真实架构、行为和约定；
- 无人值守运行数小时，持续产出有用进展；
- 做完显而易见的目标后，自己生成更高价值的下一轮目标；
- 缺测试、验证器、截图、benchmark、setup 脚本、实验线束时自己补齐；
- 第二天给你一份有真实 before/after 证据的晨报。

不适合用在几行脚本、小 bug、范围很窄的工单，或你只想要一次性回答的场景。

## 心智模型

BAGEL 把工作拆成两层：

- **控制面**：`.bagel/` 状态、constitution、对齐决策、任务队列、证据、审查、教训、STATUS。
- **交付面**：用户真正要的 app、实验、论文、网站或其他产物。

`.bagel/` 不是交付物。它是为了让 agent 长时间运行时不丢失对齐、不污染上下文。

在 Claude Code/Codex 支持 true subagents 时，主模型成为 **Supervisor**。它负责理解用户、保持心跳、仲裁硬停，并在需要时重新派生干净的内部 **Orchestrator**。Orchestrator 再派遣专门角色：

- **Project Cartographer**：用真实文件和命令验证已有项目。
- **Evaluation Architect**：为每轮迭代设计评价体系。
- **Implementer / Skeleton Builder**：做有边界的实现工作。
- **Runtime Doctor**：处理环境、依赖、build/test、浏览器、截图、验证器失败。
- **Reviewers / Red-Team**：独立审查变更。
- **Product Visionary / Brainstormers**：生成更高价值、更有新意的方向。
- **Judgment Council**：做有品味的方向选择，并否决“做得精致但方向错了”的方案。
- **User Alignment Curator**：维护面向用户的晨报和可选 HTML 看板。

## 快速开始

把 skill 文件夹安装或复制到 Claude Code/Codex 能加载的位置：

```text
bagel-genesis/
├── SKILL.md
├── agents/
├── references/
├── scripts/
└── evals/
```

然后这样要求 agent：

```text
Use BAGEL Genesis. I want to align deeply first, then run autonomous iteration.
Bind a loop/timer no longer than 25 minutes, initialize git if needed, and keep going
until the agreed iteration budget is reached or a true hard-stop occurs.
```

已有项目接管：

```text
Use BAGEL Genesis to take over this project. First verify the repo reality from files
and commands, draft protected vs replaceable surfaces, ask me only for intent/taste/
hard-stop decisions, then run autonomous iterations.
```

研究或实验：

```text
Use BAGEL Genesis for an autonomous research run. Align on the hypothesis, evaluation
method, budget, and hard-stops; build or repair the benchmark harness; run experiments;
record lessons; and iterate on better hypotheses when results stall.
```

## 对齐时应该捕获的配置

BAGEL 应该在对齐阶段持久化这些决策：

- `alignment_depth`：`snap_alignment` / `standard_alignment` / `deep_alignment`
- `execution_strategy`：`stable_long_run` / `balanced_parallel` / `fast_parallel`
- `stop_contract`：最大迭代次数、目标迭代次数、时间/token 预算、硬停边界
- `autonomy_contract`：agent 可以自主决定什么
- `taste_kernel`：参考样例、风格、产品身份、质量期待
- `innovation_contract`：执行打磨 / 差异化 / 突破式
- `evaluation`：指标、rubric、完成规则、防刷指标说明
- `loop_binding`：真实 timer/scheduler 证据，间隔 <= 25 分钟
- `git`：基线提交和回滚策略
- `supervisor`：心跳、resume capsule、当前 Orchestrator session、重启策略

## 运行时校验

在包含 `.bagel/` 的项目根目录运行：

```bash
python bagel-genesis/scripts/bagel_v3_check.py /path/to/project
python bagel-genesis/scripts/skill_lint.py bagel-genesis
```

这些脚本会抓：

- R3 / scheduled resume / hooks 等能力缺少真实 observed proof；
- 缺 git 回滚点或 loop/timer 证据；
- 缺 agent 派遣记录；
- 把控制面工作误当成产品任务；
- Build/迭代已经开始但没有评价体系；
- 虚假或缺失证据文件；
- 虚假的独立审查；
- 跌破过去绿色底板的退化；
- 没有 Brainstormer 或 Judgment Council 的提标；
- `iterations_completed < max_iterations` 却标记 complete；
- 恢复了很多问题却没有沉淀可复用教训。
- evidence hash 不匹配、handoff 丢状态、idempotency 风险、scope creep、taste alignment 过期、治理自嗨。

## 当前内容

```text
bagel-genesis/
├── SKILL.md
├── agents/          # 26 个角色提示词
├── references/      # 58 个按触发加载的协议 + 6 个 expert packs
├── scripts/         # 23 个校验/辅助脚本
└── evals/           # 109 条行为评测 + long-run scaffold
```

## 当前状态

当前版本：**v3.1 — Executable Expert Runtime**。

本地已验证：

- skill 元数据校验通过；
- BAGEL 自洽性 lint 通过；
- evals JSON 合法且编号连续；
- 针对真实问题的运行时测试通过：控制面误判、缺评价体系、过早 complete、Orchestrator 上下文污染、缺 Supervisor/resume 防线。

## 诚实边界

BAGEL 提高长程自治成功率，但不会消除模型能力上限。

- 它适合计算实验、benchmark、app 构建、UI 打磨、写作、项目优化。
- 没有授权证据管线时，它不能验证物理世界或经验科学声明。
- 它应当在不可逆破坏性操作、生产数据/基础设施、凭据、付费资源、严重安全/隐私/法律/财务风险、核心身份变化时停止。

## 许可证

MIT
