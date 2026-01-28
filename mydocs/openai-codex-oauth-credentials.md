# openai-codex OAuth 凭证存储与切换指南

## 📋 概述

本文档记录了 moltbot 中 openai-codex provider 通过 OAuth2 授权后凭证的存储机制、文件路径，以及配套的模型切换脚本使用方法。

## 🎯 凭证存储路径

### 核心存储位置

openai-codex 的 OAuth 凭证（access token、refresh token）**实际存储在 agent 级别的凭证文件中**：

```
~/.moltbot/agents/main/agent/auth-profiles.json
```

该文件包含所有 provider 的凭证，结构如下：

```json
{
  "version": 1,
  "profiles": {
    "openai-codex:default": {
      "type": "oauth",
      "provider": "openai-codex",
      "access": "<JWT access token>",
      "refresh": "<refresh token>",
      "expires": <timestamp>,
      "accountId": "<ChatGPT account UUID>"
    },
    "minimax:default": {
      "type": "api_key",
      "provider": "minimax",
      "key": "<API key>"
    }
  },
  "lastGood": {
    "openai-codex": "openai-codex:default",
    "minimax": "minimax:default"
  },
  "usageStats": {
    "openai-codex:default": {
      "lastUsed": <timestamp>,
      "errorCount": 0
    }
  }
}
```

### 文件层级说明

| 文件 | 存储内容 | 是否含 token |
|------|----------|:---:|
| `~/.moltbot/agents/main/agent/auth-profiles.json` | **实际凭证**（access/refresh token） | ✅ |
| `~/.moltbot/moltbot.json` → `auth.profiles` | 元数据（provider + mode） | ❌ |
| `~/.moltbot/auth-profiles.json` | 全局凭证（如 google-gemini-cli） | 因 provider 而异 |

### 代码路径

凭证写入逻辑：
- `src/agents/auth-profiles/paths.ts` — `resolveAuthStorePath()` 解析存储路径
- `src/agents/auth-profiles/constants.ts` — 定义文件名常量 `AUTH_PROFILE_FILENAME = "auth-profiles.json"`
- `src/agents/auth-profiles/store.ts` — `updateAuthProfileStoreWithLock()` 带文件锁写入

路径解析公式：
```
agentDir (默认 ~/.moltbot/agents/main/agent/) + "auth-profiles.json"
```

## 🔧 首次 OAuth 授权（一次性）

远程服务器上无法直接打开浏览器，需要手动完成 OAuth 流程：

### 步骤

1. **在服务器终端启动授权：**
   ```bash
   cd /path/to/moltbot && pnpm moltbot models auth login --provider openai-codex
   ```

2. **终端显示 OAuth URL，复制到本地浏览器：**
   ```
   Visit this URL to authorize:
   https://auth.openai.com/authorize?...
   ```

3. **本地浏览器中：** 登录 ChatGPT 账号 → 授予权限 → 点击允许

4. **浏览器跳转到回调 URL，复制整个 URL：**
   ```
   http://localhost:PORT/?code=...&state=...
   ```
   > ⚠️ 浏览器可能显示"无法访问此网站"，这是正常的。直接从地址栏复制完整 URL。

5. **回到服务器终端，粘贴回调 URL 并按 Enter**

### 验证授权成功

```bash
pnpm moltbot config get agents.defaults.model.primary
# 应该看到当前模型名称输出
```

查看凭证文件确认写入：
```bash
cat ~/.moltbot/agents/main/agent/auth-profiles.json | python3 -m json.tool | grep -A2 openai-codex
```

## 🔄 模型切换脚本

### 安装位置

```
/home/cjie/script/switch-model.sh
```

### 用法

```bash
cd /home/cjie/script

./switch-model.sh status        # 查看当前默认模型
./switch-model.sh openai-codex  # 切换到 openai-codex/gpt-5.2
./switch-model.sh minimax       # 切换回之前的 MINIMAX 模型
```

别名支持：`openai` = `openai-codex`，`minmax` = `minimax`

### 切换机制

1. **切换到 openai-codex 前**：
   - 检查凭证是否存在（查 `auth-profiles.json` 和 `moltbot.json` 的 `auth.profiles`）
   - 将当前模型名保存到 `/home/cjie/script/.model-state`（仅非 openai-codex 时保存，避免覆盖）
   - 执行 `pnpm --silent moltbot config set agents.defaults.model.primary "openai-codex/gpt-5.2"`

2. **切换回 MINIMAX 时**：
   - 从 `.model-state` 读取之前保存的模型名
   - 执行 `pnpm --silent moltbot config set agents.defaults.model.primary "<saved>"`

### 底层 CLI 机制

`moltbot config set` 修改 `~/.moltbot/moltbot.json` 中的 `agents.defaults.model.primary`，对应代码：
```
src/cli/config-cli.ts → setAtPath() → writeConfigFile()（原子写入 + 备份轮转）
```

> **注意：** moltbot 不是全局安装的 CLI，必须通过 `pnpm --silent moltbot` 从项目目录调用。脚本内部用 `run_moltbot()` 包装函数处理此问题，同时用 `--silent` 抑制 pnpm 横幅输出。

## 🐛 故障排查

### 问题1：`moltbot: command not found`

**原因：** moltbot 未全局安装，需从项目目录通过 pnpm 调用。

**解决：**
```bash
cd /path/to/moltbot && pnpm moltbot <command>
```

### 问题2：切换脚本保存的模型名带有 pnpm 横幅信息

**原因：** `pnpm moltbot config get` 的 stdout 会夹杂 `> moltbot@version ...` 的横幅行。

**解决：** 使用 `--silent` 抑制横幅，同时用 `tail -1` 只取最后一行实际值：
```bash
pnpm --silent moltbot config get agents.defaults.model.primary | tail -1
```

### 问题3：凭证检查通过但模型切换后实际调用失败

**可能原因：**
- OAuth access token 已过期，需要 refresh token 自动续期
- refresh token 也过期（通常几周到几个月）

**解决：** 重新运行 OAuth 授权流程：
```bash
cd /path/to/moltbot && pnpm moltbot models auth login --provider openai-codex
```

### 问题4：状态文件不存在，无法切换回 MINIMAX

**原因：** 状态文件 `.model-state` 未生成（可能是首次切换或文件被删除）。

**解决：** 手动设置：
```bash
cd /path/to/moltbot && pnpm moltbot config set agents.defaults.model.primary "minimax/MiniMax-M2.1"
```

## 📁 相关文件汇总

| 路径 | 用途 |
|------|------|
| `~/.moltbot/agents/main/agent/auth-profiles.json` | 所有 provider 的实际凭证存储 |
| `~/.moltbot/moltbot.json` | 主配置（含 `auth.profiles` 元数据 + 默认模型设置） |
| `/home/cjie/script/switch-model.sh` | 模型切换脚本 |
| `/home/cjie/script/.model-state` | 切换前的模型名备份 |
| `src/agents/auth-profiles/paths.ts` | 凭证路径解析逻辑 |
| `src/agents/auth-profiles/store.ts` | 凭证读写逻辑（带文件锁） |

## 📝 更新记录

- **2026-01-28**: 初始版本，记录 openai-codex OAuth 凭证存储机制和切换脚本设计

---

**文档维护者**: Claude Code
**最后更新**: 2026-01-28
