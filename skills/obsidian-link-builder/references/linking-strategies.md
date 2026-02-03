# 链接识别策略详解

本文档详细说明 obsidian-link-builder skill 使用的多种链接识别策略。

## 策略概述

该 skill 结合以下四种策略来识别潜在的链接机会：

1. **概念匹配** (Concept Matching)
2. **标签相似度** (Tag Similarity)
3. **目录邻近性** (Directory Proximity)
4. **标题相似度** (Title Similarity)

## 1. 概念匹配策略

### 工作原理
从文件中提取关键概念，包括：
- 标题和子标题
- **加粗文本**（通常表示重要概念）
- `代码标记`中的技术术语（限 3 个词以内）

然后查找其他文件中出现相同概念的情况。

### 权重
- 基础权重：0.4
- 这是最重要的策略，因为共享概念通常意味着强相关性

### 示例
```
文件 A: "30-AI Learning/docs/claude code/SKILLS/Claude Code Skills.md"
概念: ["Skills", "Claude Code", "MCP", "docx", "pdf"]

文件 B: "30-AI Learning/docs/claude code/SKILLS/SKILLS.md"
概念: ["Skills", "Claude Code", "skills资源库"]

匹配: "Skills", "Claude Code" → 建议链接
```

## 2. 标签相似度策略

### 工作原理
提取文件的标签（从 frontmatter 和内联 #标签），查找共享相同标签的文件。

### 权重
- 基础权重：0.3
- 标签是用户明确添加的分类，表示主题相关性

### 标签提取位置
1. **Frontmatter 标签**:
   ```yaml
   ---
   tags: [ai, claude, skills]
   ---
   ```

2. **内联标签**:
   ```markdown
   这是关于 #claude-code 和 #skills 的笔记
   ```

### 示例
```
文件 A: tags: [claude-code, skills, ai-tools]
文件 B: tags: [claude-code, mcp, ai-tools]

共享标签: claude-code, ai-tools → 建议链接
```

## 3. 目录邻近性策略

### 工作原理
基于文件的目录位置判断相关性：
- 同一目录的文件：权重 0.2
- 父子目录关系：权重 0.1

### 权重说明
- 同目录权重：0.2
- 相关目录权重：0.1
- 目录结构通常反映内容组织，同目录文件往往相关

### 示例
```
30-AI Learning/docs/claude code/
├── SKILLS/
│   ├── Claude Code Skills.md  ← 同目录
│   ├── SKILLS.md              ← 同目录
│   └── 别问原理.md             ← 同目录
└── SubAgent.md                ← 父目录

SKILLS/ 目录下的文件会互相建议链接
```

## 4. 标题相似度策略

### 工作原理
比较文件标题中的词汇重叠度：
- 提取标题中的所有单词
- 计算共同单词数量
- 至少需要 2 个共同单词才会建议

### 权重计算
```
权重 = 0.3 × (共同单词数 / max(标题A单词数, 标题B单词数))
```

### 示例
```
文件 A: "Claude Code Skills 使用指南"
单词: [claude, code, skills, 使用, 指南]

文件 B: "Claude Code SubAgent 功能"
单词: [claude, code, subagent, 功能]

共同单词: [claude, code]
相似度: 2/5 = 0.4
最终权重: 0.3 × 0.4 = 0.12
```

## 综合评分机制

### 分数累加
当多个策略同时匹配同一对文件时，分数会累加：

```
总分 = 概念匹配分数 + 标签匹配分数 + 目录邻近分数 + 标题相似分数
```

### 置信度计算

| 条件 | 置信度 |
|------|--------|
| 分数 ≥ 0.7 且策略数 ≥ 3 | high |
| 分数 ≥ 0.5 且策略数 ≥ 2 | medium |
| 其他 | low |

### 示例
```
文件对: A ↔ B

匹配策略:
- 概念匹配: "Claude Code" → +0.4
- 标签匹配: #claude-code → +0.3
- 同目录: → +0.2
- 标题相似: → +0.12

总分: 1.02 (上限 1.0)
策略数: 4
置信度: high
```

## 策略模式

### Conservative（保守）
- 最小分数：0.7
- 每文件最大链接数：5
- 适用场景：希望保持笔记简洁，只添加高度相关的链接

### Balanced（平衡）- 默认
- 最小分数：0.5
- 每文件最大链接数：10
- 适用场景：在链接丰富度和可读性之间取得平衡

### Aggressive（积极）
- 最小分数：0.3
- 每文件最大链接数：20
- 适用场景：构建密集的知识图谱，尽可能多地建立连接

## 避免重复链接

系统会自动检测现有链接，避免重复添加：

### 检测的链接格式
1. **Wikilinks**: `[[Note Name]]`, `[[Note Name|Alias]]`
2. **Markdown links**: `[Text](path/to/note.md)`

### 检测逻辑
在建议链接之前，会检查：
- 目标文件是否已经被链接
- 使用标题或文件路径进行匹配
- 忽略已存在的链接

## 最佳实践

### 1. 选择合适的策略模式
- 新 vault 或链接稀疏：使用 `balanced` 或 `aggressive`
- 已有丰富链接：使用 `conservative`
- 特定目录优化：使用 `balanced`

### 2. 分阶段添加链接
```bash
# 第一轮：只添加高置信度链接
--confidence high

# 第二轮：添加中等置信度链接
--confidence medium

# 评估后决定是否添加低置信度链接
--confidence low
```

### 3. 使用 dry-run 预览
```bash
# 先预览会添加什么链接
--dry-run

# 确认后再实际执行
```

### 4. 定期重新分析
- 添加新文件后重新运行分析
- 更新标签或重构目录后重新分析
- 定期优化链接网络

## 局限性

### 当前不支持
1. **语义相似度**：不使用 AI 模型进行深度语义分析
2. **内容摘要**：不分析文件的完整内容语义
3. **时间序列**：不考虑文件创建/修改时间
4. **引用关系**：不分析文献引用或参考关系

### 未来可能改进
- 集成 embedding 模型进行语义匹配
- 分析文件内容的主题分布
- 考虑文件的重要性权重
- 支持自定义链接规则
