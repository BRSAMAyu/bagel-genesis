# BAGEL Genesis

> 面向 Claude Code、Codex 及类似智能体编码系统的：深度前置对齐 + 长时自主迭代。

[English](README.md) | **简体中文**

---

## 一段话说清楚

裸跑的智能体会遇到第一个含糊点就停下、上下文一长就漂移、自己审自己走过场、把"能跑"当成"完成"。BAGEL Genesis 是一个技能级运行协议，让智能体**在你睡觉之后持续工作数小时** —— 先做深度对齐，然后驱动一个持续正向优化的循环：每一个质量标准一旦达标，就会被*提高*，而不是被宣布为"完成"。它和一段长 prompt 的区别在于：承重墙的保证是**由脚本校验、而非自报的** —— 进展增量必须指向真实证据文件，独立审查是*从注册表状态推导出来的*，跌破绿色底板的退化会直接判该周期失败，平坦空转检测器专抓"看起来很努力、其实在原地打转"的循环。

## v1.1 新增什么

四条强制规则收紧了"隔夜契约"，全部有机械 lint 检查：

- **强制 loop，最长 25 分钟。** 第一个自主周期之前，智能体*必须*绑定一个平台原生 loop（`/loop`、计划任务、Codex automation、`codex exec`+cron），间隔 <= 25 分钟，并保持绑定直到运行结束。`degraded_resume` 只有在穷尽所有原生机制仍不可用时才作为标记降级使用。
- **强制 git。** 工作文件夹在任何文件修改之前必须是 git 仓库 —— 必要时 `git init` + 基线提交，由 `project_under_version_control` 硬门强制。没有它，回滚和分支隔离都不可能。
- **强制派遣。** skill 加载后，主模型*采用 Orchestrator 角色*，把所有产品代码/测试/审查派遣给 subagent。它只写 `.bagel/` 治理文件。自己动手实现是 #1 失败信号。
- **深度对齐有数字下限。** `standard` 必须遍历全部 8 张选择卡 + >= 3 个开放问题；`deep` 必须 >= 2 轮、>= 8 个问题。4 题快速通道*仅*在 `snap` 模式有效。

加上一项基于一条公理构建的**信息架构升级** —— *上下文才是要保护的资源*：

- **Context-Isolation 公理：** 一次独立的 subagent 调用*就是*一个独立的上下文。worker 之间共享*发现*（结构化、基于 artifact 的），绝不共享*推理*（chain-of-thought、设计辩论）。
- **Brainstormer 角色：** 每次提标前派遣 >= 2 个固定 lens、独立上下文的 agent，把洞见多样性*制造*出来而非靠运气。
- **STATUS.md 所有权拆分：** orchestrator 写机械数据（遥测、增量、门）；Curator 写叙事（晨报、风险）并独家拥有 HTML 看板。
- **Orchestrator 防火墙：** 加宽到挡住实现推理进入协调者的上下文 —— 不只是"长 transcript"。

## v1.2 新增什么

针对*运行地基*的三项修复，来自观察一次真实运行：

- **验证，而非信任（探索）。** Cartographer 不再接受文档声明。它必须跑真实命令（构建/测试/lint）、grep 真实代码，文档说谎时记 `documented_but_broken`。已有 `.bagel/` context 只是*待重新验证的提示*，不是真相。orchestrator 派遣 >= 2 个探索 subagent（结构/行为/约定/表面各一个 lens），交叉核验后才写 context。`bagel_run_check.py` 现在会在 run 进了 Build 但没有真实 `.bagel/evidence/baseline/manifest.yaml` 命令台账和探索 lens 记录时直接判失败 —— 专抓"信了过期文档"和"伪 baseline 文件"这两种失败模式。
- **即时绑定 loop。** loop 在*能力检测完成后立即绑定*，在 Align 阶段之前 —— 不是拖到"Build 开始时"。对齐和探索在运行中的 loop 内进行，这样 session 在对齐中途中断也不会丢失整个 run。
- **指针式唤醒提示词。** loop 唤醒提示词从 5 行机制指令缩减成 1 句指针：*读 STATUS.md + state.yaml，然后按 SKILL.md 执行。* 把机制塞进唤醒提示词会导致每个 cycle 重复污染、和 SKILL.md 漂移、浪费 token。agent 醒来后渐进式披露自己需要的 —— 它不会重新加载整个 skill。

## v1.3 新增什么

一次完整的对抗性审计（2 个独立审查 agent + 自审）发现并修复了 **29 个问题**，其中 8 个 P0 逻辑漏洞会导致真实 agent 死锁、静默失败、或绕过自己的门：

- **循环依赖已解决。** 规范同时说"对齐前绑 loop"和"没 Stop Contract 不能绑 loop"和"Stop Contract 是对齐产物"。agent 照做会死锁。解决：能力检测 → 绑 loop → 开始对齐 → 第一个对齐产物就是 Stop Contract → 深度下限 → Build。
- **max_iterations 现在有交叉校验。** `flywheel_check.py` 从 constitution.yaml 的 Stop Contract 读 max_iterations，如果 state 里的副本不一致或迭代已超限就判失败。之前迭代执行器从不读 Stop Contract —— agent 可以跑超约定上限。
- **Brainstormer 派遣与提标机械链接。** bar-raises.yaml 的每条提标现在必须带 >= 2 个 brainstormer_dispatch_ids。agent 不能再跳过 brainstormer 直接提标 —— 飞轮门会失败。
- **非 runnable 项目不再误判。** LaTeX 论文、数据 notebook、无构建步骤的静态网站不再触发假门失败 —— 只要 Cartographer 确认 no_runnable_commands_confirmed 或自建了本地验证器。
- **基线证据防伪造启发式。** 证据文件必须 > 50 字节 —— 1 字节占位符不再通过。
- **唤醒损坏回退。** 唤醒时如果 state.yaml 解析失败（崩溃中断写入），唤醒提示词现在指向 .bagel/snapshots/manifest.json 做恢复。
- **degraded_resume 被诚实标记为死路。** 规范现在明确：degraded_resume 没有唤醒机制；session 结束 run 就死。它不是 loop 绑定，是 session-only 模式。
- **12 个 agent 自证的 gate 谓词被诚实标记。** gate-predicates.md 新增 Enforcement Model 表，区分机械强制门（脚本校验、无法绕过）和 agent 自证门（agent 检查它们，但无脚本独立复核 —— 独立飞轮审计是兜底）。
- **Stop Contract 传播**到 constitution-template.md、excellence-loop.md、loop-runtime.md、runtime-protocol.md。
- **新增创新层。** 高野心或空白产品运行现在会捕获 `innovation_contract`，派遣 Product Visionary 做范式/跨域/反向假设/新机制探针，并在 `.bagel/innovation/ledger.yaml` 记录候选，避免过早收敛到局部打磨。
- **新增教训记忆层。** 恢复不再止于"修好了"。可复用的坑、环境知识、规避方案会沉淀到 `.bagel/lessons/` 或 `ledger.yaml#lessons`；`bagel_memory_check.py` 会让恢复很多却没有沉淀知识的运行失败。

## v1.4 新增什么

v1.4 补上品味和群体判断层。BAGEL 现在不只是产生大胆方向，还会判断哪些方向真的值得做，并在花掉整晚之前否决"执行得很好但方向不对"的选择：

- **Judgment Council。** 方向性决策派遣 >=3 个独立 Judgment Councilor，从用户影响、优雅性、一致性、耐久性、惊喜感等维度判断。任何 `strong_no` 否决；>=2 个 `strong_yes` 且没有 `no` 才通过；其他情况记录为有价值的分歧。
- **品味调整 EV。** 通过 Judgment Council 的方向，EV 执行阈值降低 1 分，补偿高方差好想法在有指标前被低估的问题，但不豁免成本和风险。
- **只在真正有用时使用群体智能。** 创新选择、提标、策略切换、最终交付、constitution 变更使用多视角判断；普通实现、测试、命名明确不使用。
- **完整编排地图。** `orchestration-flow.md` 定义从 run start 到 run end 的派遣、合并、记录和验证路径。

---

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

## 它凭什么做到

上面的循环图本身不是价值所在 —— 任何智能体都能画出这张图。真正的价值在于：在一段无人值守的多小时运行中，智能体的上下文会被压缩、工具会缺失、它的自述不能被信任 —— 而 BAGEL 在每一处能替换的地方，把"智能体来判断"换成"脚本来校验状态"。

下面的每一个机制，我们都标注了它的强制强度，让你清楚哪些是承重墙：

- **代码强制** —— `flywheel_check.py` 违反即判该 cycle 失败，无法被说服绕过。
- **门禁强制** —— 一道硬门挡住进展（合并、下一个切片、完成判定），直到条件通过。
- **协议强制** —— 写在角色提示词和 references 里，承重于智能体遵守指令。

### 它专门要打败的失败模式

| 不用 skill 时，智能体容易… | BAGEL 的对抗机制 | 强制 |
|---|---|---|
| 上下文变长就漂移 | `constitution.yaml` 锚点，每次状态转移都重新对齐；每个 worker 只看自己的分派信封，不看历史 | 协议 |
| 一遇困难就停下问你 | 不可覆盖的 tie-breaker：摩擦的默认答案是*继续*；硬停清单故意收得很窄 | 协议 |
| 把"能跑"当成"完成" | baseline 完成只是 excellence loop 的*起点*，不是终点 | 协议 + 代码 |
| 自己审自己（橡皮图章） | review registry 记录 `reviewer_id`/`session_id`；独立性是*推导*出来的，不是自报的 | **代码** |
| 报告根本不存在的进展 | 每条 forward/lateral/backward 增量都必须指向磁盘上真实存在的、非空的 evidence 文件 | **代码** |
| 悄悄退化一个已经变绿的指标 | 绿色底板退化门；被删/改名的指标也逃不掉保护 | **代码** |
| 宣布"够好了"然后停下 | 没有自评停止；全绿时必须*提高标准*（5 种规范动作）；平坦爬升检测器专抓几乎无收益的空转 | **代码** |
| 反复重试同一个死胡同烧预算 | 连续三次 lateral 强制切换策略；改参数/改措辞算*同一个*策略 | **代码** |

`flywheel_check.py` 的头文件写明了它的设计意图：*"这里的每一个检查，都是因为之前某次审计发现对应的保证只是散文或自报。"*

### 怎么做到连续数小时不用你盯着（长程耐久性）

四层叠加，让长跑耐久，而不是依赖模型"记得继续"：

1. **循环是外置的，不是模型内部的。** 一个 cycle = 一个有界单元（一道门 / 一次分派 / 一次审查 / 一次小修）。每个 cycle 结束必须选且只选一个动作：继续 / 进恢复 / 隔离车道去做别的 / 仅硬停才停 / 安排下一个 cycle。
2. **transcript 是一次性的，`.bagel/` 是持久的。** 这是核心不变量。每个 cycle 写 checkpoint（状态/进度/任务队列/决策/风险/下一步动作），然后丢弃 worker 的原始推理和长日志。下一个 cycle 从 `.bagel/` 重建，绝不依赖"我下次会记得"。
3. **snapshot 抗崩溃、抗压缩。** 每次压缩前先写一份带 checksum 的紧凑控制态快照。resume 时：加载最新快照 → 校验 checksum → 对比 live state → 只执行保存的 `next-action.md`。如果快照和 live 在 scope/契约/已完成 slice 上打架，它会*停下来写冲突报告，而不是猜*。
4. **平台定时器绑定。** Claude Code 上绑定 scheduled task / `/loop` / cloud Routine / 外部 cron 调 `claude -p`；Codex 上绑定 automation / cloud task / `codex exec` / `PreCompact`·`SessionStart` 钩子。

**诚实的边界：** 如果平台上没有调度器，BAGEL *必须先绑定一个原生 loop*（`/loop`、计划任务、Codex automation、`codex exec`+cron），间隔 <= 25 分钟，才能开始第一个周期。只有穷尽所有原生机制后，才允许记录 `degraded_resume`（STATUS 标记 `[DEGRADED]`）—— 即便如此也**被禁止**声称能无人值守续跑。隔夜承诺的前提，是真的有一个唤醒机制被配置好并带证据记录下来。

### 遇到问题怎么恢复而不是停下（九级恢复阶梯）

当有东西坏了 —— 门失败、工具缺失、测试退化、假设停滞、审查者反对 —— BAGEL 在考虑叫醒你之前，会爬一条九级的阶梯：

1. 本地修复 + 重跑验证
2. 缩小任务范围
3. 派一个 reviewer/debugger，只看失败证据
4. 换一条路（不同实现/设计/研究方法）
5. 在隔离的 worktree/sandbox 里重做
6. 回滚到最后一个有效 checkpoint + 走更安全的计划
7. 重新规划（更新任务队列 + 决策图）
8. **换车道** —— 隔离被堵的任务，去做另一个独立的高价值任务
9. 叫醒用户 —— 只在真正的硬停边界

**防自欺规则：** 改一个超参数、阈值或变量名，算*同一个*策略，继续计入三振计数。真正的策略切换必须改变方法、核心假设、产物结构或证据来源。验证器缺失属于恢复工作 —— 智能体自己造一个最小的本地测试/基准/截图脚本 —— 而不是豁免一道门或停下的理由。

### 多 agent 怎么分工、怎么保持诚实

BAGEL 是 hub-and-spoke 模型：一个 **Orchestrator** 一次只分派*一个有界 worker*，包在一个严格的**分派信封**里（`ROLE / READ-ONLY / WRITE-ONLY / LOCKS / EXIT-CRITERIA`，精确到文件路径而非目录）。worker 永远不读完整 skill、不读历史、不读别的 worker 的 transcript。每个角色的引用预算有上限（Implementer：0–1；reviewer：1–2）。

并行工作是 opt-in（`parallel_advanced`），由 git worktree、path lock、merge queue 守护。"worker 永远不能自己合并自己的工作"这条规则在四个文件里重复出现。合并由 Integration Manager 在五道门通过后执行。

**独立审查是从注册表状态推导的，不是自报的。** `flywheel_check.py` 在 R3/R4 审查复用实现者的 agent/session 身份时直接判失败。在平台没有真 subagent 时，BAGEL 顺序跑角色，并明确标记为 R1（*不是*独立审查）；对任何高风险的无人值守变更，它**拒绝合并那个车道** —— 隔离在分支上、推进安全的工作 —— 而不是偷偷降级审查。

**诚实的边界：** 即便是 Claude Code/Codex 上的 R3"真 subagent"，通常还是同一个底层模型族。所谓独立是*上下文/身份隔离*（独立 context window、独立 session、看不到实现者叙述），不是不同训练。真正的模型多样性独立（R4）需要外部或人类 reviewer。

### 先搭骨架，再填价值

软件类产物：**Skeleton Builder** 先搭一艘可运行的"幽灵船" —— 路由、错误/认证边界、类型化契约、注册的桩、最小测试、mock 核心旅程 —— 然后一道硬的 **Ghost Ship Gate** 在 10 个结构条件全部带真实命令/测试/浏览器输出通过之前，挡住所有价值切片工作。不允许自我认证；文档里提到某个命令名不等于通过。

研究类产物的等价骨架是 **研究协议 + 文献地图**，在任何 claim 被填充之前。"先搭骨架再推进"这条原则对每种产物类型都成立，只是骨架形态不同。

### 工程规范 vs 研究规范

BAGEL 不会把一个研究项目当成"披着研究皮的软件开发"。`artifact-types.md` 按类型切换 baseline unit、骨架门和验证模式：

| 类型 | 基线单元 | 骨架门 | 验证 |
|---|---|---|---|
| 软件 | 价值切片 | 幽灵船（可运行壳） | 测试、类型检查、端到端/浏览器 |
| 已有软件 | 有界改进 | 行为保持门 | 回归检查、diff 审查 |
| **研究** | **claim / 实验 / 章节** | **研究协议 + 文献地图** | **引文检查、方法论批判、可复现性** |
| 写作 | 章节 / 场景 / 论点 | 大纲 + 语调/连续性圣经 | 连续性、结构、语调 |
| 数据分析 | 数据集 / 问题 / 图表 | 数据管线 + 假设地图 | 数据校验、统计批判 |

对计算研究，excellence loop 明确要求：假设台账、benchmark 线束、baseline 对比、ablation/失败记录、胜者保留标准。当结果停滞（连续三次 lateral）时，规定的切换是*换假设* —— 而不是调参数。

**诚实的边界：** `flywheel_check.py` 能校验一个标记为 `stronger_evidence` 的研究标准提升确实带了一个存在的 evidence 文件 —— 但它无法校验那个文件真的是一次合格的证伪实验或真正的 baseline 对比。研究内容的语义严谨性靠独立 reviewer 和周期性独立飞轮审计，而不是脚本。

### 哪些由代码强制、哪些由协议强制 —— 以及那一处缺口

八项反幻觉属性由 `flywheel_check.py` 作为硬门强制：evidence 文件存在性、审查独立性推导、绿色底板退化（方向感知、删指标也逃不掉）、迭代预算、预算单调性、标准提升价值类别、卡住指标分类、平坦爬升重算。

有一项保证**目前仍是纯散文**：周期性的*独立飞轮审计*（一个 R3+ reviewer 把 agent 自己写的 `.bagel/` evidence 重新对照真实仓库核查，以抓出"agent 写了一份内部自洽的 fiction 骗过所有检查"）被写成每 N cycle 必做，但没有任何脚本校验它是否真的被执行了。这是当前最大的散文 vs 代码缺口。现实中的兜底是：另外八项检查已经把"造假成本"抬得足够高，让审计的负担变得有界 —— 但把审计本身也代码强制化，是显而易见的下一步硬化方向。

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

BAGEL 绝不在 "够好" 处停下。每一轮迭代把一组目标驱动到全绿；全绿后就提高标准，开启下一轮。运行由两个机械校验器守护：一个校验运行地基，一个校验进步完整性。

```bash
python bagel-genesis/scripts/bagel_run_check.py /path/to/project
python bagel-genesis/scripts/bagel_memory_check.py /path/to/project
python bagel-genesis/scripts/flywheel_check.py /path/to/project
```

`bagel_run_check.py` 校验一次运行是否真的接上了自主执行：git 回滚存在、≤25 分钟 loop/timer 已绑定、对齐深度下限已满足、agent 派遣记录存在、实现/审查角色分离、STATUS.md 完整、HTML 看板所有权明确。

`bagel_memory_check.py` 校验创新野心是否有概念候选/探针，以及恢复事件是否沉淀成可复用教训，而不是一次性修完就忘。

`flywheel_check.py` 机械地校验每次运行的六个属性：客观增量、无虚假独立性、无跌破绿色底板的退化、无纯烧预算、无冗余的标准提升、无低产打转。所有证据都必须指向真实的文件/命令/报告。

### 上下文才是要保护的资源（信息架构）

长跑失败不是因为懒惰，而是因为*上下文污染*：协调 agent 吸收了实现细节，审查者吸收了实现者的自我辩解，每次头脑风暴都收敛到同一个显而易见的想法。BAGEL 的 v1.1 架构把上下文当作稀缺资源，显式控制它的流动：

- **Orchestrator 是协调者，不是实现者。** 它分派、验证、持久化状态 —— 它永远不写产品代码。它的防火墙挡住实现推理、设计辩论、debug 叙述进入它的上下文。
- **每个角色拿到干净的上下文。** 一次 subagent 调用*就是*一个独立的 context window。worker 收到的是分派信封（ROLE / READ-ONLY 文件 / WRITE-ONLY 文件 / EXIT-CRITERIA），永远不是完整 skill、不是历史、不是别的 worker 的 chain-of-thought。
- **发现可以流动，推理不可以。** 一个 worker 可以读另一个 worker 的*发现*（审查报告、测试结果、基准数字）。它绝不能读另一个 worker 的*推理*（为什么选这个方案）。这就是协作发生但不被污染的方式。
- **洞见多样性是被制造出来的。** 提高标准之前，orchestrator 派遣 >= 2 个 **Brainstormer** subagent，每个固定一个 lens（性能 / 韧性 / 用户价值 / 简约 / 完整性 / 证据强度 / 对抗），每个互不可见输出。orchestrator 在全部返回后才合并。这是唯一能产生真正发散想法、而非收敛到显而易见答案的机制。
- **文档所有权是拆分的，不是共享的。** orchestrator 每周期写 STATUS.md 的机械区块（遥测、增量趋势、loop 绑定、门）；User Alignment Curator 在触发节奏上写叙事区块（晨报、风险框架）并独家拥有 HTML 看板。没有任何文件有两个写者。

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
- `degraded_resume`：所有原生 loop 机制都证明不可用，无法保证无人值守续跑（STATUS 标记 `[DEGRADED]`）

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
    ├── references/           # 36 个按需加载的协议
    ├── scripts/
    │   ├── detect_runtime_capabilities.py
    │   ├── bagel_run_check.py    # 运行期地基校验器
    │   ├── bagel_memory_check.py # 创新与教训记忆校验器
    │   ├── flywheel_check.py     # 飞轮完整性机械校验器
    │   └── skill_lint.py         # 技能自洽性 lint
    └── evals/
        └── evals.json        # 57 条行为评测
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

它会检测平台线索、CLI 工具、调度器可用性、Git 支持、浏览器/视觉检查支持、本地工具自给能力，然后映射为 `single_session` / `degraded_resume` / `scheduled_resume` / `external_harness` 之一。

显式自主迭代时，BAGEL 必须记录循环绑定：

```yaml
loop_binding:
  mode: scheduled_resume | external_harness | active_session_loop | degraded_resume   # 间隔 <= 25 分钟
  platform: codex | claude_code | other
  schedule_id: ""
  trigger_interval_minutes: 10
  next_wakeup_at: "ISO-8601"
  resume_command_or_action: ""
  proof:
    - "automation id, cron entry, scheduled task, active /loop config, or harness command"
```

如果结果是 `degraded_resume`，智能体不得声称它能无人值守续跑，且 STATUS.md 标记 `[DEGRADED]`。

## `.bagel/` 运行时状态

BAGEL 把项目级持久状态写在 `.bagel/` 下。这是运行时状态，通常应被 Git 忽略。

快速模式使用紧凑的控制面（`state.yaml`、`constitution.yaml`、`context.yaml`、`ledger.yaml`、`STATUS.md`、`evidence/`、`user_briefing/`）。完整模式会展开为更细的文件，适用于范围大、风险高、跨多天或需要并行的工作。

## 校验

校验技能本身：

```bash
python bagel-genesis/scripts/skill_lint.py bagel-genesis
python3 -m json.tool bagel-genesis/evals/evals.json >/dev/null
```

校验一次 BAGEL 运行的运行地基和飞轮证据：

```bash
python bagel-genesis/scripts/bagel_run_check.py /path/to/project
python bagel-genesis/scripts/bagel_memory_check.py /path/to/project
python bagel-genesis/scripts/flywheel_check.py /path/to/project
```

`bagel_run_check.py` 校验真实 `.bagel/` 运行是否具备 git 回滚、loop 绑定、≤25 分钟唤醒间隔、对齐深度下限、agent 派遣记录、实现者/审查者分离、STATUS 区块和 HTML 看板所有权。

`bagel_memory_check.py` 校验创新野心是否有概念候选/探针，以及恢复事件是否沉淀成可复用教训，而不是一次性修完就忘。

`flywheel_check.py` 校验证据路径、绿色底板退化、审查级别声明、标准提升的价值类别、卡住的指标、预算单调性等失败模式——这些都是可能让一次长跑"看起来很努力、其实没产出"的坑。

## 安全模型

BAGEL 以自主为先，但不鲁莽。它应在普通摩擦中继续前进（缺失测试、本地环境损坏、实验失败、UI 缺陷、审查失败、临时阻塞的车道、需要自建脚本/截图/基准）。它只在真正的硬性停止前停下或唤醒用户：不可逆/不可恢复的破坏性操作、生产数据或基础设施变更、凭据/Token/付费账号、严重的安全/隐私/法律/财务风险、核心产品/研究身份变更、或用户明确禁止的边界。

## 当前状态

BAGEL Genesis v1.3 已文档完备并通过内部校验：

- 技能元数据校验通过
- BAGEL 自洽性 lint 通过
- evals JSON 合法且编号连续
- 57 条行为评测覆盖对齐深度下限、项目接管、强制 loop/git/dispatch、上下文隔离、brainstormer 多样性、Judgment Council 品味否决、群体决策边界、创新探针、教训记忆、验证而非信任的探索、baseline manifest、即时 loop 绑定、指针式唤醒提示词、运行期有效性审计、循环绑定、恢复、飞轮完整性、视觉证据、HTML 晨报

剩下的验证是经验性的：在真实项目上跑一夜，把结果和普通智能体用法对比。

## 许可证

MIT
