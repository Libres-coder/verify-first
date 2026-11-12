# verify-first(中文说明)

证据闭环的全栈开发流水线(Claude Code 技能)。五阶段 —— **规格 → 架构 → 增量实现 →
真机验证 → 交付**,每阶段退出条件 = 证据;没有证据的"完成"一律视为未完成。

## 它解决什么

AI 编码最常见的失败模式:**没跑过就宣称修好了**。指令约束会被模型自我说服绕过,
所以本流水线配套一个**证据门禁**:

```bash
python scripts/verify_gate.py --repo .
# exit 0 = 证据存在且比源码新;exit 1 = 无证据/证据过期;exit 2 = 非流水线项目
```

门禁可挂成 PreToolUse hook 拦截 `git commit`(见 references/gate-setup.md),或进 CI。
证据随代码入库(`.claude/skills/verify-<app>/evidence/`)。

## 它不重造轮子

规格用 mattpocock 的 to-spec;架构用 feature-dev 代理;实现纪律用 ds-* 技能;真机验证用
pstack 的 create-verification-skill;交付用 commit-commands —— 本技能只做**编排 + 证据
要求 + 门禁**,并内置弱模型(DeepSeek 等)补偿规则。

## 实测记录

两次狗粮(docs/):Web UI+API(浏览器真机驱动)与 CLI(子进程驱动、跨进程持久化),
每条验收标准都有 measured 档证据;门禁演示过"拦下过期证据提交 → 刷新后放行"。

## 安装

```bash
cp -r verify-first ~/.claude/skills/
```

## License

MIT
