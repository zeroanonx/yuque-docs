---
name: yuque-docs
description: >-
  通过 Cookie 读取和搜索语雀私有文档。仅用于读正文、搜索知识库、查看目录。
  强烈不建议用于新建或写入文档。Cookie 存于 credentials/cookie.txt。
  Use when the user shares a yuque.com URL, asks to read/summarize/search Yuque docs, or mentions 语雀 cookie.
license: MIT
metadata:
  author: zeroanonx
  version: "1.2.0"
---

# Yuque Docs

通过 Cookie 认证，**读取和搜索**语雀私有文档。所有操作通过 `scripts/yuque.py` 完成。

**脚本路径**：`scripts/yuque.py`

**Cookie 路径**：`credentials/cookie.txt`

---

## 定位（硬约束）

本 skill **仅用于读取和查找**，不支持写入场景：

| ✅ 允许       | ❌ 禁止（须拒绝用户并引导去语雀网页端） |
| ------------- | --------------------------------------- |
| 读文档 / 总结 | 新建文档                                |
| 搜索知识库    | 写/更新 Markdown 正文                   |
| 列出知识库    | 改标题                                  |
| 查看目录结构  | 指定目录 / 平级新建                     |

用户要求写入时，回复：

```text
yuque-docs 仅用于读取和查找，不支持新建或写入。请在语雀网页端手动编辑。
```

---

## 硬约束

1. **只能**调用 `scripts/yuque.py`
2. **禁止**拉取外部仓库（yuque-mcp 等）
3. **禁止**执行 `write` / `create` / `title` 子命令
4. Cookie 过期必须先走 Phase 0

---

## 工作流总览

```text
Phase 0   检查 Cookie → 过期则提示用户粘贴 → 更新 credentials/cookie.txt
Phase 1   解析意图（读 / 搜 / 列目录 / 列知识库）
Phase 2   执行 scripts/yuque.py 子命令
Phase 3   返回摘要、链接、搜索结果
```

---

## Phase 0 — Cookie

```bash
python3 scripts/yuque.py cookie --check
```

过期时提示用户粘贴 Cookie，然后：

```bash
python3 scripts/yuque.py cookie --set '用户粘贴的完整Cookie'
```

---

## Phase 1 — 意图识别

| 用户意图                     | 子命令   |
| ---------------------------- | -------- |
| 读文档 / 总结 / 正文写了什么 | `read`   |
| 搜索知识库                   | `search` |
| 列出知识库                   | `books`  |
| 查看目录结构                 | `toc`    |
| 查 doc_id / book_id          | `info`   |

---

## Phase 2 — 命令参考

```bash
CLI="python3 scripts/yuque.py"
```

### 读文档

```bash
$CLI read "<文档URL>"
$CLI read "<文档URL>" --format json
```

### 搜索

```bash
$CLI search "关键词" --book-url "<知识库URL>"
$CLI search "关键词" --group tech-ozd0u
```

### 列出知识库

```bash
$CLI books --group tech-ozd0u
```

### 查看目录

```bash
$CLI toc --book-url "<知识库URL>"
```

### 解析元信息

```bash
$CLI info "<文档URL>"
```

---

## Phase 3 — 回复用户

- **读**：结构化摘要 + 文档链接
- **搜**：列出匹配标题、链接
- **目录**：树形列出

---

## 故障排查

| 现象                     | 处理                        |
| ------------------------ | --------------------------- |
| exit code 2 / auth_error | Phase 0 更新 Cookie         |
| 搜索结果为空             | 换关键词或指定 `--book-url` |

## API 参考

详见 [rules/api.md](rules/api.md)
