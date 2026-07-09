# Yuque API 参考（fshows 私有部署）

## 认证

| Header | 值 |
|--------|-----|
| Cookie | 完整浏览器 Cookie |
| x-csrf-token | Cookie 中 `yuque_ctoken` 的值 |
| User-Agent | Chrome 131+ |
| X-Requested-With | XMLHttpRequest |

## 常用端点

| 操作 | 方法 | 路径 |
|------|------|------|
| 检查登录 | GET | `/api/mine` |
| 团队信息 | GET | `/api/groups/{login}` |
| 知识库列表 | GET | `/api/groups/{group_id}/books?limit=100` |
| 文档列表 | GET | `/api/books/{book_id}/docs?offset=0&limit=200` |
| 读文档 | GET | `/api/docs/{doc_id}?book_id={book_id}` |
| 新建文档 | POST | `/api/docs` body: `{book_id, title, format:"lake", body}` |
| 更新文档 | PUT | `/api/docs/{doc_id}` body: `{book_id, title?, body?, format?}` |

## ID 解析

页面 HTML 中含 `decodeURIComponent("...")` → JSON appData：

- `appData.book.id` → book_id
- `appData.doc.id` → doc_id

## 正文格式

语雀使用 lake HTML：

```html
<!doctype lake><meta name="doc-version" content="1" /><p data-lake-id="u1" id="u1">...</p>
```

脚本 `markdown_to_lake()` 负责 Markdown → lake 转换。

## 搜索策略

企业版全局 `/api/search` 不可用；脚本通过遍历知识库文档列表，在标题/描述中关键词匹配。
