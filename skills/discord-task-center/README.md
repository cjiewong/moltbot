# Discord Task Center Skill

使用 Discord Forum 频道标签管理 AI 任务的轻量级任务管理系统。

## 功能特性

### 1. 动态模型切换

通过修改 Forum 线程的标签来切换 AI 模型：

- 读取当前线程标签识别使用的模型
- 修改标签即可切换到其他模型
- 支持 `openai-codex/gpt-5.2` 和 `minimax/MiniMax-M2.5` 两个模型

### 2. 任务状态管理

通过标签标记任务状态：

- `进行中` - 正在进行的任务
- `已归档` - 已完成或归档的任务
- `待处理` - 等待开始的任务

### 3. 自动任务创建

创建新的 Forum 线程并自动打上标签：

- 默认模型：`openai-codex/gpt-5.2`
- 默认状态：`进行中`
- 自动开始任务推进

## 安装

将 `discord-task-center.skill` 文件导入到你的 OpenClaw 环境中。

## 使用示例

### 查看当前模型

```
你：我现在用的是什么模型？
AI：读取线程标签 → 识别模型标签 → 回复模型名称
```

### 切换模型

```
你：切换到 MiniMax
AI：获取线程信息 → 找到 MiniMax 标签 ID → 更新 appliedTags → 确认切换
```

### 归档任务

```
你：归档这个任务
AI：获取线程信息 → 替换状态标签为"已归档" → 确认归档
```

### 创建新任务

```
你：新建一个任务用 MiniMax
AI：获取可用标签 → 创建线程并打上 MiniMax + 进行中标签 → 开始工作
```

## 辅助脚本

### 查看 Forum 标签

```bash
python3 scripts/get_forum_tags.py <channel_id>
```

### 创建任务线程

```bash
python3 scripts/create_task_thread.py <channel_id> "任务标题" --model minmax --status 进行中
```

## 技术细节

- 使用 Discord API v10
- Forum 频道类型：ChannelType.GuildForum (15)
- 每个线程最多 5 个标签
- 标签使用 Snowflake ID（不是名称）

## 文件结构

```
discord-task-center/
├── SKILL.md                          # 主技能文档
├── scripts/
│   ├── get_forum_tags.py            # 获取 Forum 标签工具
│   └── create_task_thread.py        # 创建任务线程工具
└── references/
    ├── discord-api.md               # Discord API 参考
    └── model-mapping.md             # 模型映射参考
```

## 注意事项

1. 标签 ID 必须从频道的 `available_tags` 中获取
2. 修改标签时会替换所有标签，需要保留不相关的标签
3. 模型切换在下一轮对话时生效
4. Bot 需要有管理线程和标签的权限

## 作者

Created for moltbot project - Discord task management via forum tags.
