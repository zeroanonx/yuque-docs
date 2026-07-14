# yuque-docs

让 AI 通过 Cookie **读取和查找**语雀私有文档的 Skill。

> **强烈不建议用本 skill 写文档**（新建、改标题、写正文等）。企业版语雀目录 API 不可用，写入容易丢格式/图片，且无法可靠挂到指定目录。请只在语雀网页端编辑，本 skill 仅用于**读**和**搜**。

---

## 安装

```bash
npx skills add https://github.com/zeroanonx/yuque-docs --skill yuque-docs
```

```bash
npx skills add zeroanonx/yuque-docs --skill yuque-docs
```

## 推荐使用 zero-tui安装

[zero-tui](https://npmx.dev/package/zero-tui)

```bash
zero-tui -> skills add  -> [关键字] zeroanonx/yuque-docs
```

## 使用前必读

1. **Cookie 是登录凭证，只粘贴给 AI 用于读取文档，不要公开分享**
2. **只读、只搜**——写文档请用语雀网页端

安装后重新开启 Agent 会话。

---

## 能做什么（推荐）

| 能力       | 说明                         |
| ---------- | ---------------------------- |
| 读文档     | 读取正文，总结内容或回答问题 |
| 搜索知识库 | 按关键词搜索文档标题和描述   |
| 列出知识库 | 查看团队下有哪些知识库       |
| 查看目录   | 查看知识库的文档目录结构     |

## 不建议做什么

| 能力             | 说明                              |
| ---------------- | --------------------------------- |
| 写 Markdown 正文 | 易丢图片/画板，请在语雀网页端编辑 |
| 新建文档         | 企业版无法自动挂目录，请手动创建  |
| 改标题           | 请在语雀网页端修改                |

---

## 怎么用

### 第一次使用

1. 在 Cursor 对话里说：

```text
/yuque-docs，读一下这个文档：https://fshows.yuque.com/...
```

2. AI 发现还没有 Cookie，会提示你获取并**粘贴到聊天框**
3. 你把 Cookie 发给它，AI 会自动保存并继续执行

### 日常使用（推荐）

```text
/yuque-docs，读一下这个文档：https://fshows.yuque.com/...
```

```text
/yuque-docs，这篇文档正文写了什么：https://fshows.yuque.com/...
```

```text
/yuque-docs，搜索一下知识库里有没有「vpn」相关的文档
```

### 若要求写文档

请明确拒绝，并建议用户去语雀网页端操作：

```text
本 skill 仅用于读取和查找，不支持新建或写入。请在语雀中手动编辑。
```

### Cookie 过期时

**把新 Cookie 粘贴到聊天框发给 AI**，它会自动更新并继续。

---

## 如何获取 Cookie

1. 浏览器打开语雀并登录（如 [https://fshows.yuque.com](https://fshows.yuque.com)）
2. 按 `F12` 打开开发者工具
3. 切换到 **「网络 / Network」** 面板
4. 刷新页面
5. 点击任意一条发往语雀域名的请求（如 `fshows.yuque.com`）
6. 右侧 **「标头 / Headers」** → **「请求标头 / Request Headers」**
7. 找到 **`Cookie`**，复制整段值（从 `lang=zh-cn` 到末尾，**不要带 `Cookie:` 前缀**）
8. 粘贴到 Cursor 聊天框发给 AI

Cookie 会过期，过期后按同样步骤重新获取并粘贴即可。

---

## 注意

- Cookie 是登录凭证，只粘贴给 AI 用于读取文档，不要公开分享
- **只读、只搜**——写文档请用语雀网页端
