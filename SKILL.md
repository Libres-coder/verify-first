---
name: verify-first
description: "Evidence-gated full-stack development pipeline: spec, architecture, incremental build, real-app verification, and shipping - every stage produces proof, no stage claims done without it. Use when the user asks to build a new app, feature, or service end-to-end (frontend + backend), when they ask for production-quality delivery, when an end-to-end build's project has no verification harness yet, or when they say verify-first / evidence-first / 证据闭环 / 全栈流水线 / 按验收标准交付. Not for single-file fixes, small scope changes, or throwaway prototypes - use ds-plan-loop or mattpocock prototype directly."
---

# Verify-First(验证优先全栈开发)

五阶段流水线,铁律一条:**任何阶段不得在缺少证据时宣称完成。** 每阶段有明确的退出条件(证据),证据标准见 `references/evidence.md`。

## 阶段总览

| 阶段 | 工具(已装) | 产出(退出条件) |
|---|---|---|
| 1. Spec | mattpocock to-spec 或轻量 spec.md | 验收标准清单,每条可判定通过/失败 |
| 2. Architect | feature-dev code-architect 代理 | 组件蓝图 + 文件清单 + 数据流 |
| 3. Build | ds-plan-loop + ds-verify-loop | 每条验收标准对应的实现 + 检查证据 |
| 4. Verify | create-verification-skill(生成 verify-<app>) | 真机驱动验证:特性地图全跑 + 证据落盘 |
| 5. Ship | ds-review-loop + commit-commands | PR 描述含证据清单 |

## 执行规则

1. **Spec 先行,验收标准写死**:规格里每条需求必须有可判定的验收标准(命令、URL、UI 路径、可观测结果)。没有验收标准的"功能描述"退回重写。参考 `references/stages.md` 阶段 1。若 superpowers 的 brainstorming 已在本会话激活,先完成其需求澄清,再进入本阶段 —— 两者优先级:brainstorming 澄清需求,本流水线负责交付。
2. **架构先于代码,蓝图先于文件**:阶段 2 产出具体到文件与类型的蓝图;无蓝图不开工。
3. **Build 按验收标准逐条推进**:一条标准 = 一个 ds-plan-loop 步骤;每次改动过 ds-verify-loop(有测试跑测试,无测试先补最小检查)。**不要**一次实现全部再回头验证。
4. **验证闸门(执行纪律)**:阶段 3 结束后,若无项目级验证技能,先运行 `create-verification-skill` 生成 verify-<app>;然后用它跑特性地图(覆盖 = 阶段 3 已取证项之外的全部验收标准,详见 stages.md),证据按 `references/evidence.md` 落盘。**没有验证证据的"完成"= 未完成。**
5. **Ship 带证据**:提交前跑 `scripts/verify_gate.py`(证据缺失/过期即拦截;部署成 hook 与 CI 见 references/gate-setup.md);用 commit-commands 的 `/commit-push-pr`(PR 描述必须列:验收标准 → 对应验证证据路径;未验证项单独列出并标注风险);小改动无 PR 时用 `/commit`。提交前过 ds-review-loop,审查中含一次证据档位抽查(measured/inferred/guessed 标注与内容是否相符)。
6. **弱模型补偿**(全程生效):见 `references/weak-model.md` —— 短循环、硬上限、单一变量、防漂移。DeepSeek 等弱模型上违反这些规则的步骤要主动重做。

## 中断与恢复

- 任何阶段中断:读本仓库的 spec.md / PROGRESS.md / 验证证据目录,从对应阶段续接;找不到就用 ds-context-reset 重建上下文。
- 阶段 4 的验证技能和特性地图是**仓库资产**,生成后留在 `<repo>/.claude/skills/verify-<app>/`,后续任务复用与维护(maintain-verification-skill)。

## 硬规则

- 不跳过阶段 4:即使"没时间",也要跑最小验证(一条验收标准的真机证据)并如实标注其余未验证。
- 不伪造证据:验证必须是"真实用户路径 + 可观测状态变化",不是内部 setter 或测试专用端点(见 evidence.md)。
- 不替用户做产品判断:阶段 1 的验收标准与阶段 2 的取舍,涉及产品决策时问用户。
