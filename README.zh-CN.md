<div align="center">

# 🥯 BAGEL Genesis

**把一个模糊的想法，变成高质量的成品——你睡觉时完成。**

面向 Claude Code 和 Codex 的自主多智能体项目交付 skill 级操作协议。

[English](README.md) | **简体中文**

</div>

---

[![Skills Standard](https://img.shields.io/badge/Agent%20Skills-Standard-blue)](https://skills.sh)
[![Version](https://img.shields.io/badge/version-v5.0-green)](#changelog)
[![Evals](https://img.shields.io/badge/evals-120-orange)](bagel-genesis/evals/evals.json)
[![Darwin](https://img.shields.io/badge/Darwin-9%20agent%20audit-blueviolet)](#changelog)
[![License: MIT](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

## 这是什么？

BAGEL Genesis 是一个 **skill**——一个 AI 编程智能体加载并遵循的 markdown 协议。它治理长时间运行的自主多智能体工作：就是你通宵委托一个构建，明早期望看到连贯、可验证的进展。

核心循环很简单：

```text
对齐（深度）→ 构建（带证据）→ 迭代（提高标准）→ 打磨（追求卓越）
```

运行只在用户设定的迭代/预算边界、用户停止、容量耗尽带检查点、或真正的硬停时结束。

## 为什么需要它

普通 agent 使用方式恰好在无人值守工作的关键环节失败：

- 只问几个浅层规划问题 → 目标不明确
- 遇到日常摩擦就停下，而不是解决它
- 上下文被调试细节污染
- 同一个 agent 实现、审查、然后宣布胜利
- 把"所有功能做完了"当作最终完成
- 第二天早上难以验证进展

**BAGEL 把这些变成一个可计量的专家自主运行时**，用机械检查器验证进展是真实的。

## 核心特性

| 问题 | BAGEL 的解决 |
|---|---|
| 浅层前置规划 | 深度对齐（snap/standard/deep），决策持久化 |
| "稍后再来"式停顿 | 强制绑定 loop/timer，间隔 ≤25 分钟 |
| 上下文污染 | Supervisor/Orchestrator/worker 分离；替换而非压缩 |
| Agent 自我审批 | 审查独立性来自 agent/session 注册表 |
| 弱品味/局部优化 | Brainstormers + Judgment Council 做方向级决策 |
| 没有明确质量标准 | Evaluation Architect 生成指标、评分标准、反投机注释 |
| 虚假进展 | 19 个机械验证器复放证据、检查哈希、强制回归底线 |
| 静默范围蔓延 | scope delta 追踪允许/触及路径，从 git diff 派生覆盖 |
| 不可验证的声明 | 统计严谨性门控（n_seeds、p_value < 阈值、效应量、校正） |
| 伪造证据 | `--replay` 默认重跑引用的命令 |
| 输出中硬编码密钥 | `no_hardcoded_secrets` 门控无条件失败 |
| 紧急停止被无视 | 断路器 `stop_gate` HALT 整个套件（不是可修复的失败） |

## 架构

```text
用户意图
    ↓
Supervisor（根模型）——仲裁硬停、心跳、重生
    ↓
Orchestrator（内部）——分发有界工作、管理状态
    ↓
Workers——Implementer、Runtime Doctor、Reviewers、Evaluation Architect、
          Security Engineer、Product Visionary、Red-Team Oracle、...
```

**控制面**（`.bagel/`）与**交付面**（实际产物）严格分离。控制面的存在让 agent 能运行数小时而不丢失对齐或污染上下文。

## 快速开始

安装 skill 文件夹让 Claude Code/Codex 加载：

```text
bagel-genesis/
├── SKILL.md          # 核心协议
├── agents/           # 27 个角色提示
├── references/       # 65 个触发加载协议 + 6 个专家包
├── scripts/          # 26 个机械验证器
└── evals/            # 120 个行为评估 + dry-run 结果
```

然后告诉你的 agent：

```text
Use BAGEL Genesis. I want to align deeply first, then run autonomous iteration.
Bind a loop/timer no longer than 25 minutes, initialize git if needed,
and keep going until the agreed iteration budget is reached or a true hard-stop occurs.
```

## 机械验证器（反投机层）

BAGEL 附带 26 个 Python 验证器，agent 每个周期运行一次。关键的：

- **`bagel_v3_check.py`** — 统一套件运行器（26 个检查 + 紧急停止断路器）
- **`expert_strategy_check.py`** — 需求一致性、前提可证伪性、统计严谨性、claim-evidence 矩阵、Council 输出验证、命名依赖协议、数据集完整性
- **`flywheel_check.py`** — 回归底线（带溯源）、证据内容（≥50 字节）、迭代/周期/预算上限
- **`scope_check.py`** — 从 git diff 派生的 scope 覆盖（遗漏=失败）、Constitutional Court 裁决验证
- **`production_surface_check.py`** — 内联密钥扫描（无条件失败）、生产连接检测
- **`evaluation_quality_check.py`** — 可投机指标配对（metric_role 强制 + role↔name 交叉检查）
- **`bagel_telemetry_check.py`** — 模式感知治理预算（quick ≤25%，full ≤40%），从 token_log 派生份额

```bash
python bagel-genesis/scripts/bagel_v3_check.py /path/to/project
python bagel-genesis/scripts/skill_lint.py bagel-genesis
```

## 执行诚实

BAGEL 对其验证器能保证和不能保证什么异常坦诚。每个验证器都是 agent 运行的 Python 检查器，读取 agent 自己写的 `.bagel/` YAML。检查器验证的是**形状**（字段存在、枚举有效、哈希匹配）——它们提高了懒惰/粗心作弊的门槛，但一个有决心的对抗性 agent 如果用伪造数据填充完整 schema 仍能通过。完全闭合需要**平台级 provenance**（外部触发的门控、append-only 签名状态、真实 token 计量）——这在 skill 的 Enforcement Honesty 节中明确说明。

## 更新日志

### v5.0 — 模式二完成、执行落差闭合、底座外部可验证

V5 完成"既能创造又能创新的独立研究者"的两半，闭合"设计的协议"与"agent 的真实行为"之间的落差，并把 validator 底座本身放到外部 CI 之下：

- **模式二按 `research_autonomy.objective` 拆成两种完整风格。** **探索者**（`discovery`）在**零爆炸半径**沙箱契约下返回经自我验证的*新颖想法*（`research-explorer.md` + `discovery_sandbox_check.py`）；**优化者**（`optimization`）在反作弊契约下追求最高的*诚实*基准分——可调参、换组件、甚至替换方法（`research-optimizer.md` + `optimization_integrity_check.py`：先锁定目标+基线、每个保留变体在验证集而非测试集上选择、记录完整变体分母、headline 绑定模式一确证栈并由消融归因）。
- **模式一数据完整性 + 复现性底线** —— `data_leakage_check.py`（全量数据预处理 / 在测试集上选择 / 结果相关的剔除）与 `reproducibility_checklist_check.py`（NeurIPS/ICML 清单，每个机械 `yes` 都对照真实产物交叉核验，并对 YAML 布尔强制转换稳健）。
- **执行落差闭合** —— `execution_fidelity_check.py` 反转 skip-if-absent（claim 暗示某产物时，产物缺失即失败而非静默跳过）；可选 `BAGEL_REQUIRE_CONTROL_PLANE=1` 在工具边界阻止产品写入，直到 constitution 存在，与 agent 是否读过协议无关。
- **生产者侧模板**（`templates/`）让 agent 填模板而非重建 schema——每个都标注其 gate 检查什么，并端到端验证可通过。
- **底座外部可验证** —— `run_all_self_tests.py` 一条命令跑完所有 validator 自测；CI 工作流新增 `validators` job，在每次 push 上运行合并自测 + 22 条断言的机械 grader，使任何 gate 都无法在 agent 可控的进程里悄悄退化。

结构性边界保持诚实：gate 证明的是*协议*诚实（锁定目标、验证集选择、记录分母、留出确认），而非测试集从未泄漏进训练——那项审计与 `data_leakage` 组合完成；完全的 ground-truth 闭合仍需用户配置外部 CI/branch-protection。

### v4.3 — 科研实验室收尾 + 模式二覆盖度硬化

V4.3 闭合了一次 5-agent 独立审查中影响最大的发现，并把科研自主性升级为可信、CI 可验证的自主科研底座：

- **模式二 amendment 死代码修复** —— `{None, "", []}` 集合字面量在任何格式正确的 amendment 上崩溃；现已稳定运行，并强制结构化 `expected_information_gain` / `confound_risk` / `protected_field_impact` + 由 `true_subagents.observed` 证明支撑的 R3/R4 reviewer 独立性（不再是自填字符串）。
- **Lab 自动化硬化** —— pre-Build 执行不再因 `run_command` 改名 `eval_script`/`setup` 而绕过；validator 现递归扫描所有 lane 字符串字段，抓可执行命令模式和非 canonical LLM 调用。
- **平台证明 + CI auditor** —— Claude Code 的 `PostToolUse`/`PreToolUse`/`Stop` hook 用 agent 触达不到的密钥为每次 Bash/文件/turn 事件签名；CI 侧 auditor 通过 command_ref pin、非对称 verdict 签名、plan-before-runs DAG 锚定、per-seed run_ref 唯一性、统计重算（抓伪造 p 值）把 headline claim 绑定到 committed git bytes。
- **环境锁** —— `environment_lock_check.py` 要求 Build 后科研实验记录 pip-freeze/cuda/确定性标志，闭合复现性缺口。
- **覆盖度治理** —— `evals/coverage_map.py`（已升级为 per-case guard）验证每个机械 grader fixture 都能 build 且指向存在的 validator，防止"validator 存在但没有 fixture 覆盖"这类失败（正是它藏住了 v4.2 的崩溃）。

结构性边界在文档中保持诚实：pinned-but-malicious 协议脚本仍需 human code review；完全的 ground-truth 闭合需要用户配置外部 CI/branch-protection（skill 检测到后降级为 UNATTESTED，不假装已验证）。

### v4.1 — 科研完整性强化

V4.1 修复最高风险科研漏洞：dataset-integrity 会在 V4 research claim 路径触发，严格模式 authority_ref 必须绑定真实 human decision，实验计划有预注册哈希绑定，headline 指标可要求 metric recompute extractor，长程运行 heartbeat 过期会失败。

### v4.0 — 科研治理层

V4 新增严格科研协议执行模式 `protocol_execution` 和自主科研员模式 `autonomous_researcher`，要求预注册实验计划、实验事件日志、claim-evidence 矩阵，并用机械检查拦截严格模式下的协议漂移和 post-hoc 伪装成 headline confirmatory claim。

### v3.9 — 外部 9-agent 审查（关键安全 + 完整性缺陷修复）

一份 9-agent、3 轮独立外部审查发现了所有先前内部 judge 都漏掉的关键缺陷。每条声称在修复前都经过独立验证——10/10 确认。关键修复：

- **紧急停止断路器**——曾是一个 gate *失败*，agent 被施压去"修复"掉（恢复运行）；现在无条件 HALT
- **`--replay` 默认接入**——证据曾完全可伪造（零命令执行）；现在引用的命令被重新执行
- **`.bagel/` 隐私保护**——曾被静默提交到用户的 git 历史；现在在任何提交前 gitignore
- **出站/数据外泄硬停**——kill list 曾对发邮件/发布/外部 API/部署视而不见；现在已包含
- **green-floor 溯源**——伪造的 floor 曾反转回归门控；现在要求追溯到 delta 的溯源
- **原子写入 + YAMLError 守卫**——半写状态曾导致验证器崩溃；现在 temp+replace + 异常捕获

### v3.7–v3.8 — 五 judge 全 skill 审查（73.2→83.8）

5 个独立 agent 从不同视角发现 8 个共识弱点。全部解决：omission-as-pass 关闭、统计严谨性 + claim-evidence 验证器、输出侧密钥门控、NFR 质量门控（无障碍/性能）、专家包扩充、Security Engineer 角色、loading-matrix 分层、build-unlock 检查清单。

### v3.4–v3.6 — 语义完整性运行时 + 深度缺口闭合

机械反投机验证器：结构化声明需求轴（防改写）、token_log 派生治理份额、凭据扫描器、Court 裁决验证、陈旧 skill 状态检测。

### v3.1–v3.3 — 专家自主运行时 + 故障路径加固

可执行专家运行时、可计量自主循环、Supervisor 韧性、上下文树替换策略。

## 诚实边界

BAGEL 提高了高质量自主工作的概率；它不能让模型限制消失。

- 它在大型、合作、范围明确的构建上擅长**真正的无人值守通宵连续性**
- 控制面开销是真实的（约 25-40% 治理开销）；它只在真正长时间的工作上摊薄
- 执行底层是**自愿的**（agent 运行自己的审计器）——完全闭合需要平台 hook
- 它尚未在真实混乱的代码库上与直接 prompt 进行端到端 A/B 测试（这是下一步）

## 许可证

MIT
