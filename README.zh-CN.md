# BAGEL Genesis

> 面向 Claude Code、Codex 及类似智能体编码系统的：深度前置对齐 + 长时自主迭代。

[English](README.md) | **简体中文**

---

BAGEL Genesis 是一个**技能级运行协议**（skill-level operating protocol），用于把模糊的愿景或半成品项目变成一件完成度高、质量优秀的交付物。它针对的是一个常见工作流：你在睡前与智能体完成对齐，把一项困难任务交给它，然后期望系统持续工作下去，而不是遇到第一个含糊点就停下。

它不是一段超长 prompt，而是一个结构化技能，包含：

- 入口文件：[`bagel-genesis/SKILL.md`](bagel-genesis/SKILL.md)
- 角色提示词：[`bagel-genesis/agents/`](bagel-genesis/agents/)
- 按需加载的协议：[`bagel-genesis/references/`](bagel-genesis/references/)
- 校验与运行时辅助脚本：[`bagel-genesis/scripts/`](bagel-genesis/scripts/)
- 行为评测：[`bagel-genesis/evals/evals.json`](bagel-genesis/evals/evals.json)

## BAGEL 适合做什么

当你希望一个智能体做到以下任一点时，就用 BAGEL：

- 在动手前，先把一个模糊的产品/研究/写作/优化目标澄清清楚
- 接管一个已有项目，且不偏离它真实的架构与约定
- 连续运行数小时，贯穿实现、验证、审查、恢复、打磨
- 持续产出可度量的进展，而不是为常规确认反复等待
- 在缺失本地工具、测试、截图、基准、校验器时，自己造出来
- 返回一份可读的"晨报"，说明发生了什么、改了什么、还有什么需要你拍板

不要用 BAGEL 处理琐碎脚本、几行小改、范围很窄的工单，或你只想要一次性快速答复的任务。

## 核心理念

BAGEL 跑的是一个**持续正向优化循环**：

```text
对齐  ->  构建  ->  提高标准  ->  再构建   （直到预算/迭代次数耗尽）
```

- **对齐（Align）**：把用户的意图、硬性边界、运行策略、质量标准变成可执行的内容。
- **构建（Build）**：每次只实现一个有界切片，验证它，记录客观进展，然后继续。
- **提高标准（Raise the bar）**：当当前指标集全部变绿时，生成一个更高的标准（更紧的目标、新维度、对抗性视角、惊人的完整性、更强的证据），然后继续推进。

用户明确授权长时自主后，BAGEL 处理摩擦的默认答案是**继续**：

> 如果一条规则、一次审查、一次失败尝试、一个缺失工具或一个平台限制让智能体想停下来问你，那就继续下去，除非撞上了真正的硬性停止边界。

硬性停止边界被故意收得很窄：不可逆/不可恢复的破坏性操作、严重的安全/隐私/法律/财务/生产数据风险、凭据或付费外部资源、核心产品/研究身份变更，或用户明确禁止的边界。

**停止规则是机械的，不是自评的。** 一次运行只在以下情况结束：用户设定的 `max_iterations` 耗尽、撞上 Token/预算墙、用户主动停止，或遇到真正的硬性停止边界。"我觉得它已经够好了" 永远不是停止理由。

## 关键特性

### 自主前的深度对齐

BAGEL 避免浅层的 "计划模式" 对齐。它会问出导向决策的问题，并把答案持久化到 `.bagel/` 状态里。

对齐支持三种深度：

| 深度 | 何时使用 | 行为 |
|---|---|---|
| `snap_alignment` | 紧急或低风险 | 捕获要点，可逆细节走默认值，快速开始 |
| `standard_alignment` | 默认 | 问关键选择卡 + 最相关的开放问题 |
| `deep_alignment` | 重要、模糊、高预算 | 持续追问决策点，直到用户的心智模型足够清晰 |

选择卡覆盖：自主级别、执行策略、运行预算、接管激进度、品味来源、研究验证、硬性停止边界、HTML 晨报偏好。

### 持续正向优化（飞轮）

BAGEL 绝不在 "够好" 处停下。每一轮迭代把一组目标驱动到全绿；全绿后就提高标准，开启下一轮。飞轮由一个机械校验器守护，专门防懒惰与防幻觉：

```bash
python bagel-genesis/scripts/flywheel_check.py /path/to/project
```

`flywheel_check.py` 机械地校验每次运行的六个属性：客观增量、无虚假独立性、无跌破绿色底板的退化、无纯烧预算、无冗余的标准提升、无低产打转。所有证据都必须指向真实的文件/命令/报告。

### 三种执行策略

| 策略 | 何时使用 | 行为 |
|---|---|---|
| `stable_long_run` | 隔夜/无人值守 | 较低的写入并发，更强的验证，持续循环 |
| `balanced_parallel` | 速度和可靠性都要 | 适度的并发和审查深度 |
| `fast_parallel` | 用户在场且回滚成本低 | 更快的探索，更激进的并发 |

### 风险分级的审查节奏

为了让治理开销可接受，独立审查按风险分级：

- **R3 审查**用于行为变更、退化、P0/P1 变更。
- **低风险打磨**使用编排器 diff 检查 + 每 4 轮一次 R3 审查。

这样自主循环不会被每一轮都卡在审查上。

### 运行时循环与定时器绑定

用户说 "开始自主迭代" 时，BAGEL 必须绑定到可用的最强运行时：

- `scheduled_resume`：平台自动化、计划任务或定时器
- `external_harness`：cron、launchd、云任务、CLI 循环或其他外部驱动
- `active_session_loop`：当前平台循环正在活跃运行
- `manual_resume_required`：没有任何真正的唤醒机制，无法保证无人值守续跑

循环状态记录：触发间隔、下次唤醒时间、调度证明、续跑命令、遥测。

### 客观进展信号

每一轮都向 `.bagel/evidence/progress-deltas.yaml` 追加一条增量，分类为：

- `forward`：可度量的改进或关闭的风险
- `lateral`：有动作但无可度量进展
- `backward`：退化、新阻塞、指标恶化或交付物状态变差

连续三次 `lateral` 强制切换策略。`backward` 必须先修复、回滚或隔离，再做不相关的打磨。

### 已有项目接管

对已有项目，BAGEL 不会让用户解释仓库自己就能揭示的事实。它先跑一遍 Project Cartographer，起草：当前技术栈、入口、运行/验证命令、行为基线、受保护面（公开 API、数据契约、用户可见流程）、可替换面、可复用资产。用户可以否决或更正这份草稿，而不必凭记忆重建整个项目。

### 可读的晨报

BAGEL 维护 `.bagel/STATUS.md`（含强制的 `Morning Briefing` 块）和 `.bagel/user_briefing/`。可选的 HTML 看板定义在 [`bagel-genesis/references/alignment-dashboard-html.md`](bagel-genesis/references/alignment-dashboard-html.md)。

## 仓库结构

```text
.
└── bagel-genesis/
    ├── SKILL.md              # 入口文件
    ├── README.md             # 技能目录内的 readme
    ├── agents/               # 角色提示词（编排器、实现者、审查者、制图师等）
    ├── references/           # 31 个按需加载的协议
    ├── scripts/
    │   ├── detect_runtime_capabilities.py
    │   ├── flywheel_check.py     # 飞轮完整性机械校验器
    │   └── skill_lint.py         # 技能自洽性 lint
    └── evals/
        └── evals.json        # 38 条行为评测
```

## 安装

### 从 GitHub

```bash
git clone https://github.com/BRSAMAyu/bagel-genesis.git
```

然后把 `bagel-genesis` 目录复制或软链到你所用智能体平台的技能目录。

### Codex

```bash
mkdir -p ~/.codex/skills
cp -R bagel-genesis ~/.codex/skills/
```

在 Codex 会话中：

```text
Use the bagel-genesis skill. I want to align on this product idea, then run stable long-run autonomous iteration overnight.
```

### Claude Code

把仓库克隆到 Claude Code 能读到的地方，然后让 Claude Code 直接使用 `bagel-genesis` 技能目录：

```text
Use /path/to/bagel-genesis as the BAGEL Genesis skill. First run deep alignment, then start stable long-run autonomous iteration. Do not remain in planning-only mode after alignment.
```

长时无人值守工作时，请配置 Claude Code 的循环/计划任务机制，或让 BAGEL 检测并记录当前是否只能手动续跑。

## 快速开始

### 从零开始的产品

```text
Use bagel-genesis.

I want to build a polished app from this rough idea:
...

Start with standard alignment. Then use stable_long_run autonomous iteration for up to 12 cycles, checkpoint every 30 minutes, and wake me only for true hard-stops.
```

### 已有项目接管

```text
Use bagel-genesis.

This repo is an existing product. First run Project Cartographer to understand what exists, what must be preserved, and what can be redesigned. Then ask me to veto the protected/replaceable draft. After that, run stable_long_run polish and implementation.
```

### 研究或优化运行

```text
Use bagel-genesis.

I want an autonomous experiment loop. Align on the benchmark, baseline, and stop criteria. If the first approach stalls, generate alternative hypotheses and keep testing. Record progress deltas and preserve all evidence.
```

## 运行时配置

在承诺自主续跑之前，BAGEL 应运行：

```bash
python bagel-genesis/scripts/detect_runtime_capabilities.py --out .bagel/runtime_capabilities.yaml
```

它会检测平台线索、CLI 工具、调度器可用性、Git 支持、浏览器/视觉检查支持、本地工具自给能力，然后映射为 `single_session` / `manual_resume` / `scheduled_resume` / `external_harness` 之一。

显式自主迭代时，BAGEL 必须记录循环绑定：

```yaml
loop_binding:
  mode: scheduled_resume | external_harness | active_session_loop | manual_resume_required
  platform: codex | claude_code | other
  schedule_id: ""
  trigger_interval_minutes: 10
  next_wakeup_at: "ISO-8601"
  resume_command_or_action: ""
  proof:
    - "automation id, cron entry, scheduled task, active /loop config, or harness command"
```

如果结果是 `manual_resume_required`，智能体不得声称它能无人值守续跑。

## `.bagel/` 运行时状态

BAGEL 把项目级持久状态写在 `.bagel/` 下。这是运行时状态，通常应被 Git 忽略。

快速模式使用紧凑的控制面（`state.yaml`、`constitution.yaml`、`context.yaml`、`ledger.yaml`、`STATUS.md`、`evidence/`、`user_briefing/`）。完整模式会展开为更细的文件，适用于范围大、风险高、跨多天或需要并行的工作。

## 校验

校验技能本身：

```bash
python bagel-genesis/scripts/skill_lint.py bagel-genesis
python3 -m json.tool bagel-genesis/evals/evals.json >/dev/null
```

校验一次 BAGEL 运行的飞轮证据：

```bash
python bagel-genesis/scripts/flywheel_check.py /path/to/project
```

`flywheel_check.py` 校验证据路径、绿色底板退化、审查级别声明、标准提升的价值类别、卡住的指标、预算单调性等失败模式——这些都是可能让一次长跑"看起来很努力、其实没产出"的坑。

## 安全模型

BAGEL 以自主为先，但不鲁莽。它应在普通摩擦中继续前进（缺失测试、本地环境损坏、实验失败、UI 缺陷、审查失败、临时阻塞的车道、需要自建脚本/截图/基准）。它只在真正的硬性停止前停下或唤醒用户：不可逆/不可恢复的破坏性操作、生产数据或基础设施变更、凭据/Token/付费账号、严重的安全/隐私/法律/财务风险、核心产品/研究身份变更、或用户明确禁止的边界。

## 当前状态

BAGEL Genesis v1 已文档完备并通过内部校验：

- 技能元数据校验通过
- BAGEL 自洽性 lint 通过
- evals JSON 合法且编号连续
- 38 条行为评测覆盖对齐、项目接管、循环绑定、恢复、飞轮完整性、视觉证据、HTML 晨报

剩下的验证是经验性的：在真实项目上跑一夜，把结果和普通智能体用法对比。

## 许可证

MIT
