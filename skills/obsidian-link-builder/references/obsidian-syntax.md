# Obsidian 链接语法参考

本文档说明 Obsidian 支持的链接格式和语法规则。

## 链接格式类型

### 1. Wikilinks（维基链接）

Obsidian 的原生链接格式，简洁直观。

#### 基本语法
```markdown
[[文件名]]
```

#### 带别名的链接
```markdown
[[文件名|显示文本]]
```

#### 链接到标题
```markdown
[[文件名#标题]]
[[文件名#标题|显示文本]]
```

#### 链接到块
```markdown
[[文件名#^block-id]]
```

#### 示例
```markdown
查看 [[Claude Code Skills]] 了解更多信息。
这是 [[SKILLS|Skills 资源库]]的介绍。
参考 [[SubAgent#什么是 SubAgent]] 章节。
```

### 2. Markdown Links（Markdown 链接）

标准 Markdown 链接格式，兼容性更好。

#### 基本语法
```markdown
[显示文本](文件路径.md)
```

#### 相对路径
```markdown
[Skills](./SKILLS/Claude Code Skills.md)
[SubAgent](../claude code/SubAgent.md)
```

#### 绝对路径（从 vault 根目录）
```markdown
[Skills](/30-AI Learning/docs/claude code/SKILLS.md)
```

#### 链接到标题
```markdown
[SubAgent 功能](SubAgent.md#什么是-subagent)
```

#### 示例
```markdown
查看 [Claude Code Skills](./SKILLS/Claude Code Skills.md) 了解更多。
参考 [SubAgent 文档](../claude code/SubAgent.md#功能介绍)。
```

## 链接路径解析

### Wikilinks 路径解析
Obsidian 会在整个 vault 中搜索匹配的文件名：
- 不需要指定路径
- 自动查找同名文件
- 如果有多个同名文件，会提示选择

### Markdown Links 路径解析
需要明确指定相对或绝对路径：
- 相对路径：相对于当前文件
- 绝对路径：从 vault 根目录开始

## 本 Vault 的配置

根据 `.obsidian/app.json` 配置：

```json
{
  "useMarkdownLinks": true,
  "newLinkFormat": "relative"
}
```

### 配置说明
- **useMarkdownLinks**: `true` - 使用 Markdown 链接格式
- **newLinkFormat**: `relative` - 使用相对路径

### 实际应用
在本 vault 中创建链接时应使用：
```markdown
[显示文本](相对路径/文件.md)
```

## 嵌入（Embeds）

### 嵌入整个文件
```markdown
![[文件名]]
```

### 嵌入特定标题
```markdown
![[文件名#标题]]
```

### 嵌入图片
```markdown
![[image.png]]
![[image.png|300]]  # 指定宽度
```

### 嵌入 PDF
```markdown
![[document.pdf]]
![[document.pdf#page=3]]  # 特定页面
```

## 链接到标题的规则

### 标题 ID 生成规则
Markdown 链接中的标题锚点需要转换：

1. **转为小写**
2. **空格转为连字符**
3. **移除特殊字符**
4. **中文保持不变**

#### 示例转换
```
原标题: "什么是 SubAgent"
锚点: #什么是-subagent

原标题: "Claude Code Skills"
锚点: #claude-code-skills

原标题: "3.2 万人收藏"
锚点: #32-万人收藏
```

### Wikilinks 标题链接
```markdown
[[文件名#原始标题]]  # 使用原始标题，不需要转换
```

### Markdown Links 标题链接
```markdown
[文本](文件.md#转换后的锚点)  # 需要按规则转换
```

## 块引用

### 创建块 ID
在段落末尾添加 `^block-id`：
```markdown
这是一个段落。^my-block-id
```

### 引用块
```markdown
[[文件名#^block-id]]
![[文件名#^block-id]]  # 嵌入块
```

## 链接建议的最佳实践

### 1. 选择合适的链接格式
- **Wikilinks**: 简洁，适合快速链接，vault 内部使用
- **Markdown Links**: 兼容性好，适合需要导出或分享的文档

### 2. 使用相对路径
```markdown
# 推荐
[Skills](./SKILLS/Claude Code Skills.md)

# 避免（绝对路径在移动文件时会失效）
[Skills](/30-AI Learning/docs/claude code/SKILLS/Claude Code Skills.md)
```

### 3. 添加有意义的显示文本
```markdown
# 好
查看 [Claude Code Skills 使用指南](./SKILLS/Claude Code Skills.md)

# 不够好
查看 [这里](./SKILLS/Claude Code Skills.md)
```

### 4. 链接到具体章节
```markdown
# 更精确
参考 [SubAgent 功能介绍](SubAgent.md#什么是-subagent)

# 不够精确
参考 [SubAgent](SubAgent.md)
```

## 链接验证

### 有效链接特征
- 目标文件存在
- 路径正确
- 标题锚点匹配（如果链接到标题）
- 块 ID 存在（如果链接到块）

### 常见问题

#### 1. 链接失效
```markdown
# 原因：文件被移动或重命名
[旧链接](old-path/file.md)  # ❌

# 解决：更新路径
[新链接](new-path/file.md)  # ✅
```

#### 2. 标题锚点不匹配
```markdown
# 错误：标题改变但链接未更新
[链接](file.md#old-heading)  # ❌

# 正确：更新锚点
[链接](file.md#new-heading)  # ✅
```

#### 3. 相对路径错误
```markdown
# 错误：路径层级不对
[链接](../wrong/path.md)  # ❌

# 正确：正确的相对路径
[链接](../../correct/path.md)  # ✅
```

## 自动链接添加的考虑

### 插入位置选择

#### 1. 内联插入（推荐）
在提到相关概念的地方直接插入链接：
```markdown
Claude Code 提供了强大的 [Skills 系统](./SKILLS/Claude Code Skills.md)。
```

#### 2. 章节末尾
在相关章节末尾添加"相关链接"：
```markdown
## 相关笔记

- [Claude Code Skills](./SKILLS/Claude Code Skills.md)
- [SubAgent 功能](./SubAgent.md)
```

#### 3. 文档末尾
在文档最后添加"相关资源"章节：
```markdown
## 相关资源

- [Claude Code Skills 使用指南](./SKILLS/Claude Code Skills.md)
- [SubAgent 功能介绍](./SubAgent.md)
- [MCP 服务器开发](./mcp/MCP-builder.md)
```

### 避免过度链接
- 同一概念在同一段落中只链接一次
- 避免在标题中添加链接
- 保持文本的可读性
- 不要链接过于通用的词汇

### 链接文本选择
```markdown
# 好：使用描述性文本
了解更多关于 [Claude Code Skills 系统](./SKILLS.md)

# 不好：使用通用文本
点击 [这里](./SKILLS.md) 了解更多

# 好：使用目标文件的标题
参考 [Claude Code Skills](./SKILLS/Claude Code Skills.md)

# 不好：使用文件名
参考 [claude-code-skills.md](./SKILLS/Claude Code Skills.md)
```
