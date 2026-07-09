---
name: yuque-docs
description: >-
  通过 Cookie 读写语雀私有文档：读正文、写 Markdown、改标题、新建文档、搜索知识库。
  Cookie 存于 skill 内 credentials/cookie.txt；过期时提示用户粘贴新 Cookie 并由 AI 更新后重试。
  Use when the user shares a yuque.com URL, asks to read/write/edit Yuque docs, search knowledge base, or mentions 语雀 cookie.
license: MIT
metadata:
  author: zeroanonx
  version: "1.1.0"
---

# Yuque Docs

通过 Cookie 认证，读写语雀私有文档。**所有操作只能**通过本 skill 内置脚本 `scripts/yuque.py` 完成。

**脚本路径**：`scripts/yuque.py`（相对于本 skill 根目录）

**Cookie 路径**：`credentials/cookie.txt`（相对于本 skill 根目录）

---

## 硬约束（违反即停止）

1. **只能**调用 `scripts/yuque.py`，禁止自行写 Python/curl 穷举 API
2. **禁止**拉取外部仓库（如 yuque-mcp、GitHub raw）替代本 skill
3. **禁止**反复尝试 TOC/目录相关接口；目录挂载**最多尝试 1 次**（脚本内置）
4. Cookie 过期必须先走 Phase 0，不得带着无效 Cookie 重试

---

## 工作流总览

```text
Phase 0   检查 Cookie 是否有效
            └─ 无效/过期 → 提示用户粘贴 → AI 更新 credentials/cookie.txt → 重试
Phase 1   解析用户意图（读 / 写 / 搜 / 新建 / 改标题 / 指定目录新建）
Phase 2   执行 scripts/yuque.py 子命令（一次到位，不穷举）
Phase 3   向用户返回结果（摘要、链接、目录挂载说明）
```

---

## Phase 0 — Cookie 检查与更新

### 0.1 每次操作前先检查

```bash
python3 scripts/yuque.py cookie --check
```

- 返回 `{"ok": true}` → 继续
- `credentials/cookie.txt` 不存在 → 进入 **0.2**
- 返回 `auth_error` 或 exit code `2` → 进入 **0.2**

### 0.2 提示用户粘贴 Cookie

```text
需要语雀 Cookie 才能继续。请按以下步骤获取，并直接粘贴到聊天框发给我：

1. 浏览器打开 https://fshows.yuque.com 并登录
2. F12 → 网络(Network) → 刷新页面 → 点任意 fshows.yuque.com 请求
3. 标头(Headers) → 请求标头(Request Headers) → 复制 Cookie 整段值
4. 粘贴到对话中发给我（不要带 "Cookie:" 前缀）

我会自动保存并继续你的操作。
```

**禁止**要求用户自行执行命令行或手动编辑文件。

### 0.3 AI 更新 Cookie

用户粘贴后，立即执行：

```bash
python3 scripts/yuque.py cookie --set '用户粘贴的完整Cookie'
```

再 `cookie --check` 确认后重试原操作。

---

## Phase 1 — 意图识别

| 用户意图 | 子命令 |
|---------|--------|
| 读文档 / 总结 / 正文写了什么 | `read` |
| 写/更新正文（Markdown） | `write` |
| 只改标题 | `title` |
| 新建文档（知识库根级） | `create` |
| **指定目录 / 与某文档平级新建** | `create --after-url` |
| 查看知识库目录结构 | `toc` |
| 搜索知识库 | `search` |
| 列出知识库 | `books` |
| 查 doc_id / book_id | `info` |

### 解析「在某目录下平级新建」

用户说：「在 A 目录下，与 B 文档平级新建」

- **A**：父级目录文档 URL（如 `.../fvtnv7ucbpwsn2yb`，忽略 `#锚点`）
- **B**：参考文档 URL（如 `.../vdwc2om3snx6otuh`）
- 执行时用 `--after-url B`，脚本会自动尝试挂到 B 的同级

**不要**自行解析 TOC uuid，**不要**穷举 `PUT /toc` 变体。

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

### 写 Markdown 正文

```bash
$CLI write "<文档URL>" --file /tmp/edit.md --markdown
```

### 改标题

```bash
$CLI title "<文档URL>" "新标题"
```

### 新建文档（根级）

```bash
$CLI create \
  --book-url "https://fshows.yuque.com/utr6gw/xldmve" \
  --title "文档标题" \
  --file /tmp/new-doc.md \
  --markdown
```

### 新建文档（与参考文档平级）

```bash
$CLI create \
  --book-url "https://fshows.yuque.com/utr6gw/xldmve" \
  --title "AI Harness 介绍" \
  --file /tmp/new-doc.md \
  --markdown \
  --after-url "https://fshows.yuque.com/utr6gw/xldmve/vdwc2om3snx6otuh"
```

返回 JSON 字段：

| 字段 | 含义 |
|------|------|
| `toc_placed` | 是否自动挂到目录（企业版通常为 `false`） |
| `toc_message` | 目录挂载结果说明 |
| `manual_toc_hint` | 需用户手动拖目录时的操作指引 |
| `url` | 新文档链接 |

### 查看目录结构

```bash
$CLI toc --book-url "https://fshows.yuque.com/utr6gw/xldmve"
```

### 搜索 / 列出知识库

```bash
$CLI search "关键词" --book-url "<知识库URL>"
$CLI books --group tech-ozd0u
```

---

## Phase 3 — 回复用户

### 新建文档成功但目录未自动挂载（常见）

企业版 `fshows.yuque.com` **不支持**目录 API 自动挂载。按以下模板回复：

```text
文档已创建：
- 标题：{title}
- 链接：{url}

目录未能自动挂载（企业版限制）。请手动操作：
1. 打开知识库侧边栏
2. 找到「{父目录名}」
3. 将「{新标题}」拖到「{参考文档}」同级位置

{manual_toc_hint}
```

**不要**继续尝试其他 API，**不要**说「正在穷举接口」。

### 其他操作

- 读：结构化摘要 + 链接
- 写/改标题：确认已更新 + 链接

---

## 写 Markdown 正文的标准流程

```text
1. cookie --check
2. read 原文（可选）
3. 准备 Markdown 写入临时 .md 文件
4. write --file xxx.md --markdown
5. 向用户确认结果
```

---

## 故障排查

| 现象 | 处理 |
|------|------|
| exit code 2 / auth_error | Phase 0 更新 Cookie |
| `toc_placed: false` | 正常，告知用户手动拖目录 |
| 搜索结果为空 | 换关键词或指定 `--book-url` |

## API 参考

详见 [rules/api.md](rules/api.md)
