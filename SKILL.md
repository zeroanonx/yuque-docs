---
name: yuque-docs
description: >-
  通过 Cookie 读写语雀私有文档：读正文、写 Markdown、改标题、新建文档、搜索知识库。
  Cookie 存于 skill 内 credentials/cookie.txt；过期时提示用户粘贴新 Cookie 并由 AI 更新后重试。
  Use when the user shares a yuque.com URL, asks to read/write/edit Yuque docs, search knowledge base, or mentions 语雀 cookie.
license: MIT
metadata:
  author: zeroanonx
  version: "1.0.0"
---

# Yuque Docs

通过 Cookie 认证，读写语雀私有文档。所有操作通过本 skill 内置脚本完成。

**脚本路径**：`scripts/yuque.py`（相对于本 skill 根目录）

**Cookie 路径**：`credentials/cookie.txt`（相对于本 skill 根目录）

---

## 工作流总览

```text
Phase 0   检查 Cookie 是否有效
            └─ 无效/过期 → 提示用户粘贴 → AI 更新 credentials/cookie.txt → 重试
Phase 1   解析用户意图（读 / 写 / 搜 / 新建 / 改标题）
Phase 2   执行 scripts/yuque.py 子命令
Phase 3   向用户返回结果（摘要、链接、确认信息）
```

**硬约束：Cookie 过期时不得反复重试，必须先完成 Phase 0 更新 Cookie。**

---

## Phase 0 — Cookie 检查与更新

### 0.1 每次操作前先检查

```bash
python3 scripts/yuque.py cookie --check
```

- 返回 `{"ok": true}` → 继续
- `credentials/cookie.txt` 不存在 → 进入 **0.2 首次配置**
- 返回 `auth_error` 或 exit code `2` → 进入 **0.2 Cookie 过期/缺失**

也可根据以下特征判断需要用户提供 Cookie：

- 输出含 `401` / `Unauthorized` / `Cookie 未配置` / `Cookie 可能已过期`
- `read` / `info` 无法解析页面
- `cookie --check` 的 `ok` 为 `false`

### 0.2 首次使用或 Cookie 过期 — 提示用户粘贴

向用户说明（首次与过期用同一套话术）：

```text
需要语雀 Cookie 才能继续。请按以下步骤获取，并直接粘贴到聊天框发给我：

1. 浏览器打开 https://fshows.yuque.com 并登录
2. F12 → 网络(Network) → 刷新页面 → 点任意 fshows.yuque.com 请求
3. 标头(Headers) → 请求标头(Request Headers) → 复制 Cookie 整段值
4. 粘贴到对话中发给我（不要带 "Cookie:" 前缀）

我会自动保存并继续你的操作。
```

**禁止**要求用户自行执行命令行或手动编辑文件；新用户应在聊天框粘贴 Cookie。

### 0.3 AI 更新 Cookie（硬约束）

用户粘贴 Cookie 后，**AI 必须立即写入**：

```text
credentials/cookie.txt
```

写入方式：

```bash
python3 scripts/yuque.py cookie --set '用户粘贴的完整Cookie'
```

或直接编辑 `credentials/cookie.txt`（单行，不含 `Cookie:` 前缀）。

写入后再次执行 `cookie --check` 确认 `ok: true`，**然后重试原操作**。

### 安全

- 禁止将 Cookie 写入项目代码或其他 skill
- 禁止在回复中完整回显 Cookie
- `credentials/cookie.txt` 已在 `.gitignore` 中

---

## Phase 1 — 意图识别

| 用户意图 | 子命令 |
|---------|--------|
| 读文档 / 总结 / 正文写了什么 | `read` |
| 写/更新正文（Markdown） | `write` |
| 只改标题 | `title` |
| 新建文档 | `create` |
| 搜索知识库 | `search` |
| 列出知识库 | `books` |
| 查 doc_id / book_id | `info` |

---

## Phase 2 — 命令参考

在 skill 根目录执行（或写绝对路径）：

```bash
CLI="python3 scripts/yuque.py"
```

### 读文档

```bash
$CLI read "<文档URL>"
$CLI read "<文档URL>" --format json      # 含原始 lake HTML
$CLI read "<文档URL>" --format markdown  # 纯 Markdown 风格文本
```

### 写 Markdown 正文（已有文档）

1. 将 Markdown 写入临时文件，如 `/tmp/yuque-edit.md`
2. 执行：

```bash
$CLI write "<文档URL>" --file /tmp/yuque-edit.md --markdown
# 同时改标题
$CLI write "<文档URL>" --file /tmp/yuque-edit.md --markdown --title "新标题"
```

`.md` 文件会自动按 Markdown 转换；复杂表格/代码块已支持基础转换。

### 改标题

```bash
$CLI title "<文档URL>" "新标题"
```

### 新建文档

```bash
$CLI create \
  --book-url "https://fshows.yuque.com/tech-ozd0u/il2goo" \
  --title "文档标题" \
  --file /tmp/new-doc.md \
  --markdown
```

返回 JSON 含新文档 `url`。

### 搜索知识库

```bash
# 在整个团队下所有知识库搜索（默认 tech-ozd0u）
$CLI search "补贴"

# 指定团队
$CLI search "前端" --group tech-ozd0u

# 只在某个知识库内搜索
$CLI search "插件" --book-url "https://fshows.yuque.com/tech-ozd0u/il2goo"
```

### 列出知识库

```bash
$CLI books --group tech-ozd0u
```

### 解析文档元信息

```bash
$CLI info "<文档URL>"
```

---

## Phase 3 — 回复用户

完成后告知：

- 操作类型（读/写/新建/搜索）
- 文档标题与 URL
- 读操作：给出结构化摘要，而非全文堆砌
- 写操作：确认已更新，附文档链接
- 新建：附新文档链接

---

## 写 Markdown 正文的标准流程

```text
1. cookie --check
2. read 原文（了解现有结构；全新文档可跳过）
3. 在对话或临时 .md 文件中准备 Markdown 内容
4. write --file xxx.md --markdown
5. read 验证（可选）
6. 向用户确认结果
```

**覆盖整篇正文时**：先用 `read` 确认不会误删重要图片/画板；图片在正文中会变为 `[[image:...]]` 占位符，重写会丢失原图。

**局部修改时**：读出全文 → 在 Markdown 中改对应段落 → `write` 整篇回去。

---

## 配置

`credentials/config.json`：

```json
{
  "base_url": "https://fshows.yuque.com",
  "default_group": "tech-ozd0u"
}
```

---

## 故障排查

| 现象 | 处理 |
|------|------|
| exit code 2 / auth_error | Phase 0 更新 Cookie |
| 浏览器版本过低 | 必须用脚本（内置 Chrome UA），禁止裸 curl |
| 搜索结果为空 | 换关键词；或指定 `--book-url` |
| 写入后格式异常 | 检查 Markdown 表格/列表语法；必要时 `read --format json` 对比 |

## API 参考

详见 [rules/api.md](rules/api.md)
