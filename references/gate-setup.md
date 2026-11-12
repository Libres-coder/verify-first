# 证据门禁部署(verify_gate)

## 本地 hook(拦截 git commit)

项目 `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python \"<verify-first 安装路径>/scripts/gate_hook.py\"",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

gate_hook.py 只拦截 `git commit`(含 `git -C <path> commit`),其余命令零开销放行;门禁失败时以 exit 2 阻止提交并把原因显示给用户。门禁自身崩溃时放行并告警(不因 hook 故障锁死仓库)。

## CI 门禁(PR 级)

仓库 `.github/workflows/verify.yml`:

```yaml
name: verify-gate
on:
  pull_request:
jobs:
  evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Evidence gate
        run: |
          curl -fsSL -o /tmp/verify_gate.py <verify-first 发布地址>/scripts/verify_gate.py
          python /tmp/verify_gate.py --repo . --strict
```

注意:CI 拉取的仓库不含本地证据(证据应随仓库提交 —— 阶段 4 的落盘目录在仓库内,提交时一并入库,这正是"证据随代码走"的设计);`--strict` 保证声称走 verify-first 的仓库缺验证技能时 CI 直接失败。

## 门禁语义

| 状态 | exit | 行为 |
|---|---|---|
| 证据存在且比最新源码新 | 0 | 放行 |
| 无证据 / 证据过期 | 1 | 拦截并列出过期文件 |
| 无 verify-<app> 技能(非 verify-first 项目) | 2 | 放行(--strict 下改判失败) |

豁免:`--ignore GLOB` 排除无需验证的文件(如纯文档);`.claude/` 整树与 .git、node_modules 等不计入源码。
