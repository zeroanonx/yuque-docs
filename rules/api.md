# Yuque API 参考（fshows 企业版）

## 认证

| Header | 值 |
|--------|-----|
| Cookie | 完整浏览器 Cookie |
| x-csrf-token | Cookie 中 `yuque_ctoken` 的值 |
| User-Agent | Chrome 131+ |
| X-Requested-With | XMLHttpRequest |

## 可用端点

| 操作 | 方法 | 路径 | 状态 |
|------|------|------|------|
| 检查登录 | GET | `/api/mine` | ✅ |
| 团队信息 | GET | `/api/groups/{login}` | ✅ |
| 知识库列表 | GET | `/api/groups/{group_id}/books` | ✅ |
| 文档列表 | GET | `/api/books/{book_id}/docs` | ✅ |
| 读目录 | GET | `/api/books/{book_id}/toc` | ✅ |
| 读文档 | GET | `/api/docs/{slug}?book_id={book_id}` | ✅ |
| 新建文档 | POST | `/api/docs` | ✅ |
| 更新文档 | PUT | `/api/docs/{doc_id}` | ✅ |
| **更新目录** | PUT | `/api/books/{book_id}/toc` | ❌ 404 |

## 目录挂载限制

企业版 `fshows.yuque.com` 的 `PUT /api/books/{id}/toc` 返回 **404**。

脚本 `create --after-url` 会尝试一次挂载；失败后返回 `manual_toc_hint`，由用户在侧边栏手动拖动。

**禁止** AI 穷举其他 TOC 接口。

## 新建文档（平级）

```bash
python3 scripts/yuque.py create \
  --book-url "https://fshows.yuque.com/{group}/{book}" \
  --title "标题" \
  --file content.md \
  --markdown \
  --after-url "https://fshows.yuque.com/{group}/{book}/{参考文档slug}"
```

## 正文格式

语雀使用 lake HTML，脚本 `markdown_to_lake()` 负责 Markdown 转换。
