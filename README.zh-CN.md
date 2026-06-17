<div align="center">

# 🥯 BAGEL Genesis

**把一个模糊的想法，变成高质量的成品——你睡觉时完成。**

面向 Claude Code 和 Codex 的自主多智能体项目交付 skill 级操作协议。

[English](README.md) | **简体中文**

</div>

---

[![Skills Standard](https://img.shields.io/badge/Agent%20Skills-Standard-blue)](https://skills.sh)
[![Version](https://img.shields.io/badge/version-v3.9-green)](#changelog)
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

- **`bagel_v3_check.py`** — 统一套件运行器（19 个检查 + 紧急停止断路器）
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
