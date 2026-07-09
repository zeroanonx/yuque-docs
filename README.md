# yuque-docs

让 AI 通过 Cookie 读写语雀私有文档的 Cursor Skill。

把语雀链接丢给 AI，它可以帮你操作私有文档，无需手动登录后台。

---

## 安装

```bash
npx skills add https://github.com/zeroanonx/yuque-docs --skill yuque-docs
```

```bash
npx skills add zeroanonx/yuque-docs --skill yuque-docs
```

安装后重新开启 Agent 会话。

---

## 能做什么

| 能力        | 说明                               |
| ----------- | ---------------------------------- |
| 读文档      | 读取正文，总结内容或回答问题       |
| 写 Markdown | 用 Markdown 写正文，自动同步到语雀 |
| 新建文档    | 在指定知识库下创建新文档           |
| 搜索知识库  | 按关键词搜索文档标题和描述         |

---

## 怎么用

### 第一次使用

1. 在 Cursor 对话里直接说你想做的事，例如：

```text
用 yuque-docs skill，读一下这个文档：https://fshows.yuque.com/...
```

2. AI 发现还没有 Cookie，会提示你获取并**粘贴到聊天框**
3. 你把 Cookie 发给它，AI 会自动保存并继续执行

**不需要自己跑命令行，也不需要手动编辑文件。**

### 日常使用

直接在对话里说即可：

```text
用 yuque-docs skill，读一下这个文档：https://fshows.yuque.com/...
```

```text
用 yuque-docs skill，把这篇文档标题改成「前端技术文档」
```

```text
用 yuque-docs skill，在本地生活知识库新建一篇文档，标题是 xxx，内容是 ...
```

```text
用 yuque-docs skill，搜索一下知识库里有没有「补贴」相关的文档
```

### Cookie 过期时

和操作失败时一样：**把新 Cookie 粘贴到聊天框发给 AI**，它会自动更新并继续。

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

- Cookie 是登录凭证，只粘贴给 AI 用于操作你的文档，不要公开分享
- 覆盖写入正文时，原文档中的图片和画板可能会丢失，改动前可以让 AI 先读一遍原文
