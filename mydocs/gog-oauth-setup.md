# gog CLI OAuth 认证配置指南

## 📋 概述

本文档记录了如何为 moltbot 配置 gog CLI 的 Google OAuth 认证，以便访问 Gmail、Calendar、Drive、Contacts、Sheets 和 Docs 等 Google 服务。

## 🎯 目标

配置 gog CLI 使用 Google OAuth 认证，让 moltbot 能够通过 gog 命令访问 Google Workspace 服务。

## 📦 前置条件

- ✅ gog CLI 已安装（通过 Homebrew）
- ✅ Google 账号：huangchaojie5@gmail.com
- ✅ 服务器环境：可以 SSH 访问
- ✅ 本地浏览器：用于完成 OAuth 授权

## 🔧 配置步骤

### 1. 设置 Keyring 密码

gog 使用加密的 keyring 存储 OAuth tokens，需要设置密码：

```bash
export GOG_KEYRING_PASSWORD="gog-moltbot-2026"
```

**建议：** 将此环境变量添加到 `~/.bashrc` 或 `~/.profile` 中：

```bash
echo 'export GOG_KEYRING_PASSWORD="gog-moltbot-2026"' >> ~/.bashrc
source ~/.bashrc
```

### 2. 启动 OAuth 认证流程

运行以下命令启动认证：

```bash
gog auth add huangchaojie5@gmail.com --manual --services gmail,calendar,drive,contacts,sheets,docs
```

**参数说明：**
- `--manual`: 使用手动模式（适合远程服务器）
- `--services`: 指定要授权的服务列表

### 3. 获取 OAuth 授权 URL

gog 会显示类似以下的 OAuth URL：

```
Visit this URL to authorize:
https://accounts.google.com/o/oauth2/auth?client_id=160560236207-q01snaku53i2bqkki61m1hvj34fubvos.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A1&...
```

### 4. 在本地浏览器完成授权

1. **复制 OAuth URL** 到你的本地电脑浏览器
2. **选择账号**：huangchaojie5@gmail.com
3. **授予权限**：
   - Gmail（读取、发送、修改）
   - Calendar（管理日历）
   - Drive（访问文件）
   - Contacts（管理联系人）
   - Sheets（管理表格）
   - Docs（管理文档）
4. **点击"允许"或"Allow"**

### 5. 复制回调 URL

授权成功后，浏览器会跳转到：

```
http://localhost:1/?code=4/0ASc3gC0...&state=...
```

⚠️ **重要提示：**
- 浏览器会显示"无法访问此网站"或"ERR_CONNECTION_REFUSED" - **这是正常的！**
- 不要关闭页面，直接从地址栏复制**完整的 URL**
- 确保包含 `code=` 和 `state=` 参数

### 6. 粘贴回调 URL

回到 SSH 终端，将完整的回调 URL 粘贴到提示符处：

```
Paste redirect URL (Enter or Ctrl-D): http://localhost:1/?code=...&state=...
```

按 Enter 键完成认证。

### 7. 验证认证成功

运行以下命令验证：

```bash
export GOG_KEYRING_PASSWORD="gog-moltbot-2026"
gog auth list
```

**预期输出：**
```
huangchaojie5@gmail.com (default)
```

## 🧪 测试 gog 功能

### 测试 Gmail

搜索最近的邮件：

```bash
export GOG_KEYRING_PASSWORD="gog-moltbot-2026"
gog gmail search "newer_than:1d" --max 5
```

### 测试 Calendar

列出日历事件：

```bash
gog calendar events primary --from 2026-01-01T00:00:00Z --to 2026-12-31T23:59:59Z
```

### 测试 Drive

搜索文件：

```bash
gog drive search "type:document" --max 10
```

### 测试 Contacts

列出联系人：

```bash
gog contacts list --max 10
```

## 📁 配置文件位置

gog 的配置和 tokens 存储在：

```
~/.config/gogcli/
├── config.json          # gog 配置
├── credentials.json     # OAuth 客户端凭据
└── keyring/            # 加密的 OAuth tokens
    ├── token:default:huangchaojie5@gmail.com
    └── token:huangchaojie5@gmail.com
```

## 🔐 安全注意事项

1. **Keyring 密码保护**
   - `GOG_KEYRING_PASSWORD` 用于加密/解密 OAuth tokens
   - 不要在公共场合泄露此密码
   - 定期更换密码

2. **OAuth Tokens**
   - Tokens 存储在加密的 keyring 中
   - 不要手动编辑 keyring 文件
   - 如需重新认证，删除旧的 keyring 文件

3. **权限范围**
   - 只授予必要的服务权限
   - 定期审查 Google 账号的已授权应用

## 🔄 重新认证

如果需要重新认证（例如密码错误或 token 过期）：

### 方法1：删除旧的 keyring

```bash
rm -f ~/.config/gogcli/keyring/*
export GOG_KEYRING_PASSWORD="gog-moltbot-2026"
gog auth add huangchaojie5@gmail.com --manual --services gmail,calendar,drive,contacts,sheets,docs
```

### 方法2：使用 gog auth remove

```bash
export GOG_KEYRING_PASSWORD="gog-moltbot-2026"
gog auth remove huangchaojie5@gmail.com
gog auth add huangchaojie5@gmail.com --manual --services gmail,calendar,drive,contacts,sheets,docs
```

## 🐛 故障排查

### 问题1：`no TTY available for keyring file backend password prompt`

**原因：** 未设置 `GOG_KEYRING_PASSWORD` 环境变量

**解决：**
```bash
export GOG_KEYRING_PASSWORD="gog-moltbot-2026"
```

### 问题2：`aes.KeyUnwrap(): integrity check failed`

**原因：** Keyring 密码不正确或 keyring 文件损坏

**解决：**
```bash
# 删除旧的 keyring 并重新认证
rm -f ~/.config/gogcli/keyring/*
export GOG_KEYRING_PASSWORD="gog-moltbot-2026"
gog auth add huangchaojie5@gmail.com --manual --services gmail,calendar,drive,contacts,sheets,docs
```

### 问题3：`state mismatch`

**原因：** 使用了不同 OAuth 流程生成的回调 URL

**解决：** 确保在同一个 `gog auth add` 进程中完成整个流程：
1. 运行 `gog auth add`
2. 复制 gog 显示的 OAuth URL
3. 在浏览器授权
4. 复制回调 URL
5. 粘贴到同一个 gog 进程中

### 问题4：OAuth 授权失败

**可能原因：**
- Google 账号安全设置阻止
- 网络连接问题
- OAuth 客户端凭据无效

**解决：**
1. 检查 Google 账号安全设置
2. 确认网络连接正常
3. 验证 `~/.config/gogcli/credentials.json` 存在且有效

## 📚 常用 gog 命令

### Gmail

```bash
# 搜索邮件
gog gmail search 'newer_than:7d' --max 10

# 发送邮件
gog gmail send --to recipient@example.com --subject "Hello" --body "Message"

# 创建草稿
gog gmail drafts create --to recipient@example.com --subject "Draft" --body "Content"
```

### Calendar

```bash
# 列出事件
gog calendar events primary --from 2026-01-01T00:00:00Z --to 2026-12-31T23:59:59Z

# 创建事件
gog calendar create primary --summary "Meeting" --from 2026-01-28T10:00:00Z --to 2026-01-28T11:00:00Z

# 查看颜色
gog calendar colors
```

### Drive

```bash
# 搜索文件
gog drive search "query" --max 10

# 列出文件
gog drive list --max 20
```

### Contacts

```bash
# 列出联系人
gog contacts list --max 20
```

### Sheets

```bash
# 读取数据
gog sheets get <sheetId> "Sheet1!A1:D10" --json

# 更新数据
gog sheets update <sheetId> "Sheet1!A1:B2" --values-json '[["A","B"],["1","2"]]'

# 追加数据
gog sheets append <sheetId> "Sheet1!A:C" --values-json '[["x","y","z"]]'
```

### Docs

```bash
# 导出文档
gog docs export <docId> --format txt --out /tmp/doc.txt

# 查看文档内容
gog docs cat <docId>
```

## 🔗 相关资源

- **gog CLI 官网**: https://gogcli.sh
- **gog GitHub**: https://github.com/steipete/gogcli
- **Google OAuth 文档**: https://developers.google.com/identity/protocols/oauth2
- **moltbot gog 技能文档**: `/home/cjie/dev/moltbot/skills/gog/SKILL.md`

## 📝 更新记录

- **2026-01-28**: 初始版本，完成 huangchaojie5@gmail.com 的 OAuth 认证配置

## 💡 提示

1. **设置默认账号**：
   ```bash
   export GOG_ACCOUNT=huangchaojie5@gmail.com
   ```
   这样就不需要每次都指定 `--account` 参数

2. **脚本化使用**：
   使用 `--json` 和 `--no-input` 参数进行脚本化操作：
   ```bash
   gog gmail search "query" --json --no-input
   ```

3. **环境变量持久化**：
   将常用环境变量添加到 `~/.bashrc`：
   ```bash
   export GOG_KEYRING_PASSWORD="gog-moltbot-2026"
   export GOG_ACCOUNT=huangchaojie5@gmail.com
   ```

---

**文档维护者**: Claude Code
**最后更新**: 2026-01-28
**适用版本**: gog v0.9.0
