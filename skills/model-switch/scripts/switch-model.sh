#!/usr/bin/env bash
# switch-model.sh — 在 MINMAX 和 openai-codex/gpt-5.3-codex 之间切换默认模型
#
# 用法:
#   ./switch-model.sh openai-codex   切换到 openai-codex/gpt-5.3-codex
#   ./switch-model.sh minimax        切换回之前保存的 MINIMAX 模型
#   ./switch-model.sh status          显示当前默认模型
#   ./switch-model.sh                 同 status

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_FILE="$SCRIPT_DIR/.model-state"
TARGET_MODEL="openai-codex/gpt-5.3-codex"
PROJECT_DIR="/home/cjie/dev/moltbot"

# 凭证存储路径（多个可能位置）
CRED_AUTH_PROFILES_NEW="$HOME/.clawdbot/auth-profiles.json"
CRED_AUTH_PROFILES_OLD="$HOME/.clawdbot/auth-profiles.json"
CRED_CONFIG="$HOME/.clawdbot/openclaw.json"

# ─── 辅助函数 ────────────────────────────────────────────

# 调用 openclaw CLI（需从项目目录通过 pnpm 运行）
# pnpm 会在 stdout 前输出横幅行，用 --silent 抑制；
# 作为安全兜底，还是 tail -1 只取最后一行实际值
run_openclaw() {
    cd "$PROJECT_DIR" && pnpm --silent openclaw "$@"
}

get_current_model() {
    run_openclaw config get agents.defaults.model.primary 2>/dev/null | tail -1
}

# 检查 openai-codex 凭证是否存在
# 查找顺序：auth-profiles.json（新/旧）+ moltbot.json 里的 auth.profiles
check_openai_creds() {
    # 检查独立凭证文件
    for f in "$CRED_AUTH_PROFILES_NEW" "$CRED_AUTH_PROFILES_OLD"; do
        if [[ -f "$f" ]] && grep -q "openai-codex" "$f" 2>/dev/null; then
            return 0
        fi
    done
    # 检查主配置文件里的 auth.profiles（实际存储位置）
    if [[ -f "$CRED_CONFIG" ]] && grep -q '"openai-codex' "$CRED_CONFIG" 2>/dev/null; then
        return 0
    fi
    return 1
}

# 检查 minimax 凭证是否存在
check_minimax_creds() {
    # 方法1: 检查环境变量
    if [[ -n "${MINIMAX_API_KEY:-}" ]]; then
        return 0
    fi

    # 方法2: 检查 auth-profiles.json 中是否有 minimax 凭证
    for f in "$CRED_AUTH_PROFILES_NEW" "$CRED_AUTH_PROFILES_OLD"; do
        if [[ -f "$f" ]] && grep -q '"minimax' "$f" 2>/dev/null; then
            return 0
        fi
    done

    # 方法3: 检查主配置文件的 auth.profiles 是否有实际凭证数据
    # 注意：仅有配置定义不够，需要有实际的credentials
    if [[ -f "$CRED_CONFIG" ]]; then
        # 检查是否有minimax的实际凭证（不只是配置定义）
        if grep -q '"minimax:default"' "$CRED_CONFIG" 2>/dev/null; then
            # 进一步检查是否有credentials目录下的文件或环境变量
            if [[ -d "$HOME/.clawdbot/credentials" ]]; then
                if grep -r "minimax" "$HOME/.clawdbot/credentials/" 2>/dev/null | grep -q "api"; then
                    return 0
                fi
            fi
        fi
    fi

    return 1
}

# ─── status ──────────────────────────────────────────────

cmd_status() {
    local current
    current="$(get_current_model)"
    if [[ -z "$current" ]]; then
        echo "当前未设置默认模型。"
    else
        echo "当前默认模型: $current"
    fi
}

# ─── 切换到 openai-codex ─────────────────────────────────

cmd_openai_codex() {
    # 验证凭证
    if ! check_openai_creds; then
        echo "❌ 未找到 openai-codex 凭证。"
        echo ""
        echo "请先手动完成 OAuth 授权："
        echo "  cd $PROJECT_DIR && pnpm openclaw models auth login --provider openai-codex"
        echo ""
        echo "终端会显示一个 URL，在本地浏览器打开并完成登录后，将重定向 URL 粘贴回终端。"
        exit 1
    fi

    local current
    current="$(get_current_model)"

    # 仅在当前模型不是 openai-codex 时保存状态（避免覆盖之前的 MINIMAX 名称）
    if [[ -n "$current" && "$current" != "$TARGET_MODEL" ]]; then
        echo "$current" > "$STATE_FILE"
        echo "已保存当前模型到状态文件: $current"
    fi

    run_openclaw config set agents.defaults.model.primary "$TARGET_MODEL"
    echo "✅ 已切换到: $TARGET_MODEL"
}

# ─── 验证并修复 MINIMAX 配置 ─────────────────────────────

# MiniMax-M2.1 总是返回 thinking 块，必须正确配置：
# 1. reasoning=true (模型支持推理)
# 2. thinkingDefault=low (agent 启用推理显示)
# 3. authHeader=true (发送 Authorization Bearer 头部)
verify_minimax_config() {
    local reasoning thinking_default auth_header fixed=0
    reasoning="$(run_openclaw config get models.providers.minimax.models.0.reasoning 2>/dev/null | tail -1)"
    thinking_default="$(run_openclaw config get agents.defaults.thinkingDefault 2>/dev/null | tail -1)"
    auth_header="$(run_openclaw config get models.providers.minimax.authHeader 2>/dev/null | tail -1)"

    if [[ "$reasoning" != "true" ]]; then
        echo "⚠️  检测到 reasoning 配置错误 (当前: $reasoning)，正在修复..."
        run_openclaw config set models.providers.minimax.models.0.reasoning true >/dev/null 2>&1
        echo "✅ reasoning 配置已修复为 true"
        fixed=1
    fi

    if [[ "$thinking_default" != "low" && "$thinking_default" != "medium" && "$thinking_default" != "high" ]]; then
        echo "⚠️  检测到 thinkingDefault 配置错误 (当前: $thinking_default)，正在修复..."
        run_openclaw config set agents.defaults.thinkingDefault low >/dev/null 2>&1
        echo "✅ thinkingDefault 配置已修复为 low"
        fixed=1
    fi

    if [[ "$auth_header" != "true" ]]; then
        echo "⚠️  检测到 authHeader 配置错误 (当前: $auth_header)，正在修复..."
        run_openclaw config set models.providers.minimax.authHeader true >/dev/null 2>&1
        echo "✅ authHeader 配置已修复为 true"
        fixed=1
    fi

    return $fixed
}

# ─── 切换回 MINIMAX ──────────────────────────────────────

cmd_minimax() {
    # 验证凭证
    if ! check_minimax_creds; then
        echo "❌ 未找到 minimax 凭证。"
        echo ""
        echo "请先配置 minimax API 密钥："
        echo "  方法1: 设置环境变量"
        echo "    export MINIMAX_API_KEY='your-api-key'"
        echo ""
        echo "  方法2: 通过 openclaw 配置（如果支持）"
        echo "    cd $PROJECT_DIR && pnpm openclaw models auth login --provider minimax"
        echo ""
        echo "配置完成后，请重新运行此脚本。"
        exit 1
    fi

    if [[ ! -f "$STATE_FILE" ]]; then
        echo "❌ 状态文件不存在，无法恢复之前的模型。"
        echo ""
        echo "请手动设置模型:"
        echo "  cd $PROJECT_DIR && pnpm openclaw config set agents.defaults.model.primary \"<你的MINIMAX模型名>\""
        exit 1
    fi

    local saved_model
    saved_model="$(cat "$STATE_FILE" | tr -d '[:space:]')"

    if [[ -z "$saved_model" ]]; then
        echo "❌ 状态文件为空，无法恢复模型。"
        exit 1
    fi

    run_openclaw config set agents.defaults.model.primary "$saved_model"

    # 验证并修复 reasoning 配置
    if verify_minimax_config; then
        echo ""
    fi

    echo "✅ 已切换回: $saved_model"
    echo "⏳ 网关将自动重启以应用配置（约 3-5 秒）"
}

# ─── 入口 ────────────────────────────────────────────────

CMD="${1:-status}"

case "$CMD" in
    openai-codex|openai)
        cmd_openai_codex
        ;;
    minimax|minmax)
        cmd_minimax
        ;;
    status)
        cmd_status
        ;;
    *)
        echo "用法: $0 {openai-codex|minimax|status}"
        echo ""
        echo "  openai-codex  切换到 openai-codex/gpt-5.3-codex"
        echo "  minimax       切换回之前保存的 MINIMAX 模型"
        echo "  status        显示当前默认模型"
        exit 1
        ;;
esac
