# Moltbot Gateway Pairing 故障排查指南

## 📋 概述

本文档记录了 Moltbot Gateway 通过 nginx 反向代理访问时遇到的 pairing 问题及其解决方案。

## 🎯 问题现象

### 症状

Web 端访问 `https://moltbot.uran.vip` 时，连接失败并报错：

```
disconnected (1008): pairing required
```

### 日志表现

Gateway 日志显示大量 `pairing required` 错误：

```
[ws] closed before connect conn=xxx remote=127.0.0.1 fwd=112.10.252.49
     origin=https://moltbot.uran.vip host=moltbot.uran.vip
     code=1008 reason=pairing required
```

### 检查状态

运行 `pnpm moltbot nodes pending` 显示：

```
No pending pairing requests.
```

看似没有待批准的 pairing 请求。

## 🔍 原因分析

### 1. 两套独立的配对系统

Moltbot Gateway 有**两套不同的配对（pairing）系统**：

| 系统 | 用途 | CLI 命令 | 典型场景 |
|------|------|----------|----------|
| **Node Pairing** | 节点配对 | `moltbot nodes` | Raspberry Pi、远程 Agent 节点 |
| **Device Pairing** | 设备配对 | `moltbot devices` | Web UI、移动应用、桌面客户端 |

### 2. Web UI 触发的是 Device Pairing

- Web Control UI 客户端（`clientId: moltbot-control-ui`）连接时触发 **Device Pairing**
- 因此需要使用 `moltbot devices` 命令查看和管理，而不是 `moltbot nodes`

### 3. 远程连接不会自动批准

#### 代码逻辑（`src/gateway/server/ws-connection/message-handler.ts:637`）

```typescript
const pairing = await requestDevicePairing({
  deviceId: device.id,
  publicKey: devicePublicKey,
  displayName: connectParams.client.displayName,
  platform: connectParams.client.platform,
  clientId: connectParams.client.id,
  clientMode: connectParams.client.mode,
  role,
  scopes,
  remoteIp: reportedClientIp,
  silent: isLocalClient,  // 关键：只有本地连接才会自动批准
});
```

#### 判断逻辑

- `isLocalClient = true`：来自 `127.0.0.1` 或 `localhost` 的**直接连接**，自动批准（`silent: true`）
- `isLocalClient = false`：通过 nginx 代理的连接，检测到的远程 IP 是 `112.10.252.49`，需要手动批准

#### nginx 代理的影响

通过 nginx 反向代理访问时：
- `X-Forwarded-For` 头包含真实客户端 IP：`112.10.252.49`
- Gateway 识别为远程连接
- `silent: false` → 不会自动批准 → 需要手动批准

### 4. Pending 请求的 5 分钟 TTL

- 每个 pending pairing 请求有 **5 分钟有效期**（`PENDING_TTL_MS = 5 * 60 * 1000`）
- 超过 5 分钟后，请求自动过期并从 `pending.json` 中移除
- 浏览器反复刷新会创建新的 pending 请求（如果前一个已过期）

### 5. 为什么 `nodes pending` 显示为空

因为查询的是 **Node Pairing** 系统，而 Web UI 触发的是 **Device Pairing**。

## ✅ 解决方案

### 方案 1：批准 Device Pairing（推荐）

这是最安全的方式，完成配对后浏览器会记住认证状态。

#### 步骤 1：查看待批准的 Device Pairing 请求

```bash
pnpm moltbot devices list
```

**输出示例：**

```
Pending (1)
┌──────────────────────────────────────┬─────────────────────────────────┬──────────┬───────────────┐
│ Request                              │ Device                          │ Role     │ IP            │
├──────────────────────────────────────┼─────────────────────────────────┼──────────┼───────────────┤
│ 39b4c484-f9a3-481a-bf29-7794827275f4 │ 6c31678b9a6a9c7cee5fe2ef253027e │ operator │ 112.10.252.49 │
│                                      │ bcab2a47f71fd21c29012d782ddd60a │          │               │
│                                      │ 0b                              │          │               │
└──────────────────────────────────────┴─────────────────────────────────┴──────────┴───────────────┘
```

#### 步骤 2：批准 Pairing 请求

```bash
pnpm moltbot devices approve <requestId>
```

**示例：**

```bash
pnpm moltbot devices approve 39b4c484-f9a3-481a-bf29-7794827275f4
```

**成功输出：**

```
Approved 6c31678b9a6a9c7cee5fe2ef253027ebcab2a47f71fd21c29012d782ddd60a0b
```

#### 步骤 3：验证配对成功

```bash
pnpm moltbot devices list
```

应该看到新设备出现在 `Paired` 列表中。

#### 步骤 4：刷新浏览器

- 刷新 `https://moltbot.uran.vip`
- 应该可以正常连接，不再报 `pairing required` 错误

### 方案 2：使用带 Token 的 URL（临时访问）

如果只是临时访问或不想配对，可以使用带 token 的 URL 绕过 pairing 检查。

#### 步骤 1：获取 Gateway Token

```bash
pnpm moltbot config get gateway.auth.token
```

**输出示例：**

```
3c23f9584dae9d3fda2e68b8021bf03719652b6f09d17960
```

#### 步骤 2：生成带 Token 的 Dashboard URL

```bash
pnpm moltbot dashboard --no-open
```

**输出示例：**

```
Dashboard URL: http://127.0.0.1:18789/?token=3c23f9584dae9d3fda2e68b8021bf03719652b6f09d17960
```

#### 步骤 3：使用带 Token 的 URL 访问

```
https://moltbot.uran.vip/?token=3c23f9584dae9d3fda2e68b8021bf03719652b6f09d17960
```

⚠️ **注意：**
- Token 是敏感信息，不要泄露
- 每次访问都需要带 token 参数
- 浏览器不会记住认证状态

### 方案 3：禁用 Token 验证（不推荐）

⚠️ **强烈不推荐用于生产环境**，会让任何人都可以访问你的 gateway。

```bash
pnpm moltbot config unset gateway.auth.token
```

然后重启 gateway：

```bash
pkill -9 -f moltbot-gateway
nohup moltbot gateway run --bind loopback --port 18789 --force > /tmp/moltbot-gateway.log 2>&1 &
```

## 🔧 相关命令参考

### Device Pairing 命令

```bash
# 查看所有 device（pending + paired）
pnpm moltbot devices list

# 批准 pairing 请求
pnpm moltbot devices approve <requestId>

# 拒绝 pairing 请求
pnpm moltbot devices reject <requestId>

# 轮换 device token
pnpm moltbot devices rotate <deviceId> <role>

# 撤销 device token
pnpm moltbot devices revoke <deviceId> <role>
```

### Node Pairing 命令（用于 Pi 等节点）

```bash
# 查看 node pairing 状态
pnpm moltbot nodes status

# 查看待批准的 node pairing 请求
pnpm moltbot nodes pending

# 批准 node pairing 请求
pnpm moltbot nodes approve <requestId>

# 拒绝 node pairing 请求
pnpm moltbot nodes reject <requestId>
```

### Gateway 配置命令

```bash
# 查看 gateway token
pnpm moltbot config get gateway.auth.token

# 设置 gateway token
pnpm moltbot config set gateway.auth.token <token>

# 删除 gateway token（禁用认证）
pnpm moltbot config unset gateway.auth.token

# 生成带 token 的 dashboard URL
pnpm moltbot dashboard --no-open

# 查看 gateway 状态
pnpm moltbot gateway status

# 探测 gateway 连接
pnpm moltbot gateway probe
```

### Gateway 日志命令

```bash
# 查看 gateway 日志
tail -f /tmp/moltbot-gateway.log

# 查看最近的 pairing 相关日志
tail -100 /tmp/moltbot-gateway.log | grep -E "pairing|unauthorized"

# 查看 gateway 监听端口
ss -ltnp | grep moltbot
```

## 📁 配置文件位置

### Device Pairing 存储位置

```
~/.moltbot/devices/
├── pending.json    # 待批准的 device pairing 请求
└── paired.json     # 已配对的 devices
```

**注意：** `~/.clawdbot` 是 `~/.moltbot` 的符号链接（rebrand 迁移）。

### 查看 Pending 请求文件

```bash
cat ~/.moltbot/devices/pending.json
```

**示例输出：**

```json
{
  "39b4c484-f9a3-481a-bf29-7794827275f4": {
    "requestId": "39b4c484-f9a3-481a-bf29-7794827275f4",
    "deviceId": "6c31678b9a6a9c7cee5fe2ef253027ebcab2a47f71fd21c29012d782ddd60a0b",
    "publicKey": "_uWVl9uw3hANdJ2HNiRZGr0Uq6dMZidg-NPxV5DuPAQ",
    "platform": "Win32",
    "clientId": "moltbot-control-ui",
    "clientMode": "webchat",
    "role": "operator",
    "roles": ["operator"],
    "scopes": [
      "operator.admin",
      "operator.approvals",
      "operator.pairing"
    ],
    "remoteIp": "112.10.252.49",
    "silent": false,
    "isRepair": false,
    "ts": 1769605935094
  }
}
```

## 🐛 故障排查

### 问题 1：`nodes pending` 显示为空，但日志仍显示 `pairing required`

**原因：** 使用了错误的命令。Web UI 触发的是 Device Pairing，不是 Node Pairing。

**解决：**

```bash
# ❌ 错误：查询 node pairing
pnpm moltbot nodes pending

# ✅ 正确：查询 device pairing
pnpm moltbot devices list
```

### 问题 2：批准后仍然显示 `unknown requestId`

**原因：** Pending 请求已过期（超过 5 分钟 TTL）。

**解决：**

1. 刷新浏览器页面，触发新的 pairing 请求
2. 立即运行 `pnpm moltbot devices list` 查看新的 requestId
3. 在 5 分钟内批准请求

**加快流程：**

```bash
# 开两个终端窗口

# 终端 1：持续监控 pending 请求
watch -n 2 'pnpm moltbot devices list 2>&1 | grep -A 5 "Pending"'

# 终端 2：一旦看到新请求，立即批准
pnpm moltbot devices approve <requestId>
```

### 问题 3：批准后浏览器仍然报错

**可能原因：**

1. 浏览器缓存未清除
2. WebSocket 连接已建立但未刷新

**解决：**

1. 硬刷新浏览器：`Ctrl+Shift+R` (Windows/Linux) 或 `Cmd+Shift+R` (Mac)
2. 清除浏览器缓存和 Cookie
3. 尝试无痕模式打开

### 问题 4：nginx 代理导致无法自动批准

**原因：** Gateway 通过 `X-Forwarded-For` 检测到真实客户端 IP，判定为远程连接。

**解决方案：**

#### 方案 A：手动批准（推荐）

每次新设备/浏览器访问时手动批准一次。

#### 方案 B：配置 Control UI 允许不安全认证（不推荐）

⚠️ **仅用于开发环境**

```bash
pnpm moltbot config set gateway.controlUi.allowInsecureAuth true
```

重启 gateway 后，Control UI 连接将跳过 device pairing。

**风险：** 任何知道 URL 和 token 的人都可以访问。

## 🔐 安全建议

### 1. Device Pairing 的优势

- ✅ 每个设备/浏览器需要独立批准
- ✅ 可以随时撤销特定设备的访问权限
- ✅ 记录每个设备的平台、IP、最后使用时间

### 2. Token 认证的风险

- ⚠️ Token 泄露后任何人都可以访问
- ⚠️ 需要在 URL 中传递，可能被浏览器历史记录泄露

### 3. 最佳实践

1. **优先使用 Device Pairing**：首次访问批准一次，后续自动认证
2. **定期审查已配对设备**：`pnpm moltbot devices list`
3. **及时撤销不再使用的设备**：`pnpm moltbot devices revoke <deviceId> <role>`
4. **使用 HTTPS + nginx 反向代理**：保护传输层安全
5. **配置 nginx 基本认证**：添加额外的访问控制层

## 📚 相关文档

- **Pairing 文档**: https://docs.molt.bot/gateway/pairing
- **Gateway 配置**: https://docs.molt.bot/gateway
- **Control UI 文档**: https://docs.molt.bot/web/control-ui
- **Nginx 配置**: `/www/server/panel/vhost/nginx/moltbot.conf`

## 🔗 相关代码位置

```
src/gateway/server/ws-connection/message-handler.ts:624-677  # Device pairing 逻辑
src/infra/device-pairing.ts                                   # Device pairing 存储
src/cli/devices-cli.ts                                        # devices CLI 命令
src/cli/nodes-cli/                                            # nodes CLI 命令
```

## 📝 更新记录

- **2026-01-28**: 初始版本，记录 nginx 代理环境下的 device pairing 故障排查经验

## 💡 快速参考

### 一键批准最新的 Device Pairing 请求

```bash
# 查看并批准（手动复制 requestId）
pnpm moltbot devices list
pnpm moltbot devices approve <requestId>

# 或者使用脚本自动批准最新的请求
LATEST_REQUEST=$(cat ~/.moltbot/devices/pending.json | jq -r 'keys[0]')
if [ ! -z "$LATEST_REQUEST" ]; then
  pnpm moltbot devices approve "$LATEST_REQUEST"
else
  echo "No pending requests"
fi
```

### 查看 Gateway 实时日志（过滤 pairing 相关）

```bash
tail -f /tmp/moltbot-gateway.log | grep --color -E "pairing|unauthorized|device"
```

---

**文档维护者**: Claude Code
**最后更新**: 2026-01-28
**适用版本**: moltbot 2026.1.27-beta.1
**测试环境**: Ubuntu 22.04, nginx 反向代理
