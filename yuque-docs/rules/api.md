# Yuque API

## 认证

| Header       | 值                            |
| ------------ | ----------------------------- |
| Cookie       | 完整浏览器 Cookie             |
| x-csrf-token | Cookie 中 `yuque_ctoken` 的值 |
| User-Agent   | Chrome 131+                   |

## 本 skill 使用的端点（只读）

| 操作       | 方法 | 路径                                 |
| ---------- | ---- | ------------------------------------ |
| 检查登录   | GET  | `/api/mine`                          |
| 知识库列表 | GET  | `/api/groups/{group_id}/books`       |
| 文档列表   | GET  | `/api/books/{book_id}/docs`          |
| 读目录     | GET  | `/api/books/{book_id}/toc`           |
| 读文档     | GET  | `/api/docs/{slug}?book_id={book_id}` |

## 不建议使用的端点

以下端点存在于脚本中但 **skill 禁止使用**：

| 操作     | 方法 | 路径                       | 原因             |
| -------- | ---- | -------------------------- | ---------------- |
| 新建文档 | POST | `/api/docs`                | 目录无法自动挂载 |
| 更新文档 | PUT  | `/api/docs/{doc_id}`       | 易丢图片/格式    |
| 更新目录 | PUT  | `/api/books/{book_id}/toc` | 企业版 404       |

## 搜索策略

全局 `/api/search` 不可用；脚本遍历知识库文档列表，在标题/描述中关键词匹配。
