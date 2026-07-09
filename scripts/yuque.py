#!/usr/bin/env python3
"""Yuque docs CLI — bundled with yuque-docs skill."""

from __future__ import annotations

import argparse
import html
import json
import os
import random
import re
import string
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

SKILL_ROOT = Path(__file__).resolve().parent.parent
COOKIE_FILE = SKILL_ROOT / "credentials" / "cookie.txt"
CONFIG_FILE = SKILL_ROOT / "credentials" / "config.json"

DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

AUTH_ERROR_MARKERS = ("401", "Unauthorized", "未登录", "login", "Cookie may be expired")


class AuthError(Exception):
    pass


def load_config() -> dict[str, str]:
    cfg: dict[str, str] = {
        "base_url": "https://fshows.yuque.com",
        "user_agent": DEFAULT_UA,
        "default_group": "tech-ozd0u",
    }
    if CONFIG_FILE.exists():
        cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
    cfg["base_url"] = os.environ.get("YUQUE_BASE_URL", cfg["base_url"]).rstrip("/")
    cfg["user_agent"] = os.environ.get("YUQUE_USER_AGENT", cfg["user_agent"])
    return cfg


def load_cookie() -> str:
    if os.environ.get("YUQUE_COOKIE"):
        return os.environ["YUQUE_COOKIE"].strip()
    if COOKIE_FILE.exists():
        return COOKIE_FILE.read_text(encoding="utf-8").strip()
    raise AuthError(
        f"Cookie 未配置。请将浏览器 Cookie 写入 {COOKIE_FILE}，"
        "或在对话中粘贴 Cookie 后由 AI 更新 credentials/cookie.txt"
    )


def save_cookie(cookie: str) -> None:
    COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
    COOKIE_FILE.write_text(cookie.strip(), encoding="utf-8")
    os.chmod(COOKIE_FILE, 0o600)


def extract_ctoken(cookie: str) -> str:
    m = re.search(r"(?:^|;\s*)yuque_ctoken=([^;]+)", cookie)
    if not m:
        raise AuthError("Cookie 缺少 yuque_ctoken，请重新从浏览器复制完整 Cookie")
    return m.group(1)


def uid() -> str:
    return "u" + "".join(random.choices(string.ascii_lowercase + string.digits, k=7))


def span(text: str, *, bold: bool = False, italic: bool = False, code: bool = False) -> str:
    sid = uid()
    cls = []
    if code:
        cls.append("ne-code")
    escaped = html.escape(text, quote=False)
    if bold:
        escaped = f"<strong>{escaped}</strong>"
    if italic:
        escaped = f"<em>{escaped}</em>"
    class_attr = f' class="{" ".join(cls)}"' if cls else ""
    return f'<span data-lake-id="{sid}" id="{sid}"{class_attr}>{escaped}</span>'


def paragraph(inner: str) -> str:
    pid = uid()
    return f'<p data-lake-id="{pid}" id="{pid}">{inner}</p>'


def heading(level: int, text: str) -> str:
    hid = uid()
    return (
        f'<h{level} data-lake-id="{hid}" id="{hid}">'
        f'<span class="ne-text">{html.escape(text)}</span></h{level}>'
    )


def markdown_inline(text: str) -> str:
  parts: list[str] = []
  pattern = re.compile(
      r"(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*]+\*)|(\[[^\]]+\]\([^)]+\))"
  )
  pos = 0
  for m in pattern.finditer(text):
      if m.start() > pos:
          parts.append(span(text[pos : m.start()]))
      token = m.group(0)
      if token.startswith("`"):
          parts.append(span(token[1:-1], code=True))
      elif token.startswith("**"):
          parts.append(span(token[2:-2], bold=True))
      elif token.startswith("*"):
          parts.append(span(token[1:-1], italic=True))
      elif token.startswith("["):
          lm = re.match(r"\[([^\]]+)\]\(([^)]+)\)", token)
          if lm:
              label, href = lm.groups()
              aid = uid()
              parts.append(
                  f'<a href="{html.escape(href)}" data-lake-id="{aid}" id="{aid}">'
                  f'<span class="ne-text">{html.escape(label)}</span></a>'
              )
      pos = m.end()
  if pos < len(text):
      parts.append(span(text[pos:]))
  return "".join(parts) if parts else span(text)


def markdown_to_lake(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        hm = re.match(r"^(#{1,6})\s+(.+)$", line)
        if hm:
            blocks.append(heading(len(hm.group(1)), hm.group(2).strip()))
            i += 1
            continue
        if re.match(r"^```", line):
            lang = line[3:].strip()
            i += 1
            code_lines: list[str] = []
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1
            code = html.escape("\n".join(code_lines))
            cid = uid()
            blocks.append(
                f'<pre data-lake-id="{cid}" id="{cid}"><code class="language-{html.escape(lang)}">{code}</code></pre>'
            )
            continue
        if line.strip().startswith("|") and "|" in line[1:]:
            table_lines = [line]
            i += 1
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            rows = [r.strip().strip("|").split("|") for r in table_lines]
            rows = [[c.strip() for c in r] for r in rows if any(c.strip() for c in r)]
            if len(rows) >= 2 and re.match(r"^[-:|\s]+$", "|".join(rows[1])):
                rows.pop(1)
            tid = uid()
            trs = []
            for ri, row in enumerate(rows):
                tag = "th" if ri == 0 else "td"
                tds = "".join(f"<{tag}><p>{markdown_inline(c)}</p></{tag}>" for c in row)
                trs.append(f"<tr>{tds}</tr>")
            blocks.append(f'<table data-lake-id="{tid}" id="{tid}"><tbody>{"".join(trs)}</tbody></table>')
            continue
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i]):
                items.append(re.sub(r"^[-*]\s+", "", lines[i]).strip())
                i += 1
            lid = uid()
            lis = "".join(f'<li data-lake-id="{uid()}" id="{uid()}">{markdown_inline(it)}</li>' for it in items)
            blocks.append(f'<ul data-lake-id="{lid}" id="{lid}">{lis}</ul>')
            continue
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i]).strip())
                i += 1
            lid = uid()
            lis = "".join(f'<li data-lake-id="{uid()}" id="{uid()}">{markdown_inline(it)}</li>' for it in items)
            blocks.append(f'<ol data-lake-id="{lid}" id="{lid}">{lis}</ol>')
            continue
        para_lines = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,6}\s|[-*]\s|\d+\.\s|```|\|)", lines[i]):
            para_lines.append(lines[i])
            i += 1
        blocks.append(paragraph(markdown_inline(" ".join(p.strip() for p in para_lines))))
    body = "".join(blocks) or paragraph(span(""))
    return f'<!doctype lake><meta name="doc-version" content="1" />{body}'


class LakeTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip = False
        self.in_a = False
        self.href = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag in ("script", "style"):
            self.skip = True
        if tag == "br":
            self.parts.append("\n")
        if tag in ("p", "div", "tr", "section", "blockquote"):
            self.parts.append("\n")
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.parts.append("\n" + "#" * int(tag[1]) + " ")
        if tag == "li":
            self.parts.append("\n- ")
        if tag in ("td", "th"):
            self.parts.append(" | ")
        if tag == "img":
            self.parts.append(f"[图片:{attrs_dict.get('alt') or '图片'}]")
        if tag == "a":
            self.in_a = True
            self.href = attrs_dict.get("href") or ""
        if tag == "card":
            name = attrs_dict.get("name") or ""
            value = attrs_dict.get("value") or ""
            useful = ""
            if value.startswith("data:"):
                try:
                    payload = unquote(value[5:])
                    data = json.loads(payload)
                    useful = str(data.get("src") or data.get("url") or data)[:200]
                except Exception:
                    useful = unquote(value[5:])[:200]
            self.parts.append(f"\n[[{name}:{useful}]]\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self.skip = False
        if tag in ("p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr", "table", "section", "blockquote"):
            self.parts.append("\n")
        if tag == "a" and self.in_a:
            if self.href and not self.href.startswith("javascript"):
                self.parts.append(f"({self.href})")
            self.in_a = False

    def handle_data(self, data: str) -> None:
        if self.skip:
            return
        if data.strip():
            self.parts.append(data)


def lake_to_text(content: str) -> str:
    parser = LakeTextExtractor()
    parser.feed(content)
    text = "".join(parser.parts)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return re.sub(r"[ \t]+\n", "\n", text).strip()


def parse_yuque_url(url: str) -> tuple[str, list[str]]:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    parts = [p for p in parsed.path.split("/") if p]
    return base, parts


class YuqueClient:
    def __init__(self, cookie: str, base_url: str | None = None, user_agent: str = DEFAULT_UA) -> None:
        self.cookie = cookie
        self.ctoken = extract_ctoken(cookie)
        self.base_url = (base_url or load_config()["base_url"]).rstrip("/")
        self.user_agent = user_agent

    def _curl(self, method: str, url: str, *, referer: str | None = None, body: dict[str, Any] | None = None, accept: str = "application/json") -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".yuque") as tmp:
            out_path = tmp.name
        try:
            cmd = [
                "curl", "-sS", "--http1.1", "--max-time", "120", "-X", method, "-o", out_path,
                "-H", f"Cookie: {self.cookie}",
                "-H", f"User-Agent: {self.user_agent}",
                "-H", f"Accept: {accept}",
                "-H", "X-Requested-With: XMLHttpRequest",
                "-H", f"x-csrf-token: {self.ctoken}",
            ]
            if referer:
                cmd.extend(["-H", f"Referer: {referer}"])
            if body is not None:
                cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(body, ensure_ascii=False)])
            cmd.append(url)
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=130)
            raw = Path(out_path).read_text(encoding="utf-8", errors="ignore")
            if proc.returncode != 0:
                raise AuthError(f"请求失败 ({proc.returncode}): {proc.stderr.strip() or raw[:200]}")
            if any(m in raw for m in ("当前浏览器版本过低", "module-error")) and accept == "text/html":
                raise AuthError("页面返回浏览器拦截，请检查 Cookie 是否有效")
            return raw
        finally:
            Path(out_path).unlink(missing_ok=True)

    def _request(self, method: str, path: str, *, referer: str | None = None, body: dict[str, Any] | None = None) -> dict[str, Any]:
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        raw = self._curl(method, url, referer=referer, body=body)
        if raw.strip().startswith("<"):
            raise AuthError("Cookie 可能已过期，请用户提供新 Cookie 并更新 credentials/cookie.txt")
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            raise AuthError(f"API 返回非 JSON，Cookie 可能已过期: {raw[:200]}") from e
        if isinstance(result, dict) and result.get("status") in (401, 403):
            raise AuthError(f"Cookie 已过期或无权限 ({result.get('status')}): {result.get('message')}")
        if isinstance(result, dict) and result.get("status") in (404, 422):
            raise SystemExit(f"API error {result.get('status')}: {result.get('message') or result}")
        return result

    def fetch_app_data(self, page_url: str) -> dict[str, Any]:
        html_text = self._curl("GET", page_url, accept="text/html")
        m = re.search(r'decodeURIComponent\("(%[^"]{50,})"\)', html_text)
        if not m:
            raise AuthError("无法解析页面，Cookie 可能已过期或 URL 无效")
        return json.loads(unquote(m.group(1)))

    def resolve_book(self, book_url: str) -> dict[str, Any]:
        base, parts = parse_yuque_url(book_url)
        if len(parts) < 2:
            raise SystemExit(f"知识库 URL 需为 /{{group}}/{{book}}: {book_url}")
        if base != self.base_url:
            self.base_url = base
        group_login, book_slug = parts[0], parts[1]
        page_url = f"{self.base_url}/{group_login}/{book_slug}"
        group = self._request("GET", f"/api/groups/{group_login}", referer=f"{self.base_url}/")["data"]
        books = self._request(
            "GET", f"/api/groups/{group['id']}/books?limit=100", referer=f"{self.base_url}/"
        ).get("data", [])
        book = next((b for b in books if b.get("slug") == book_slug), None)
        if not book:
            raise SystemExit(f"未找到知识库 slug={book_slug}，请检查 URL 或权限")
        return {
            "page_url": page_url,
            "group_login": group_login,
            "book_id": book["id"],
            "book_slug": book["slug"],
            "book_name": book["name"],
        }

    def resolve_doc(self, doc_url: str) -> dict[str, Any]:
        base, parts = parse_yuque_url(doc_url)
        if len(parts) < 3:
            raise SystemExit(f"文档 URL 需为 /{{group}}/{{book}}/{{doc}}: {doc_url}")
        if base != self.base_url:
            self.base_url = base
        group_login, book_slug, doc_slug = parts[0], parts[1], parts[2]
        page_url = f"{self.base_url}/{group_login}/{book_slug}/{doc_slug}"
        book = self.resolve_book(f"{self.base_url}/{group_login}/{book_slug}")
        doc = self._request(
            "GET",
            f"/api/docs/{doc_slug}?book_id={book['book_id']}",
            referer=page_url,
        )["data"]
        return {
            "page_url": page_url,
            "group_login": group_login,
            "book_id": book["book_id"],
            "book_name": book["book_name"],
            "book_slug": book_slug,
            "doc_id": doc["id"],
            "doc_slug": doc["slug"],
            "title": doc["title"],
            "url": page_url,
        }

    def get_doc(self, doc_id: int, book_id: int, referer: str) -> dict[str, Any]:
        return self._request("GET", f"/api/docs/{doc_id}?book_id={book_id}", referer=referer)["data"]

    def create_doc(self, book_id: int, title: str, body: str, referer: str) -> dict[str, Any]:
        payload = {"book_id": book_id, "title": title, "format": "lake", "body": body}
        return self._request("POST", "/api/docs", referer=referer, body=payload)["data"]

    def update_doc(self, doc_id: int, book_id: int, referer: str, **fields: Any) -> dict[str, Any]:
        payload = {"book_id": book_id, **fields}
        return self._request("PUT", f"/api/docs/{doc_id}", referer=referer, body=payload)["data"]

    def list_books(self, group_login: str) -> list[dict[str, Any]]:
        group = self._request("GET", f"/api/groups/{group_login}", referer=f"{self.base_url}/")["data"]
        result = self._request("GET", f"/api/groups/{group['id']}/books?limit=100", referer=f"{self.base_url}/")
        return result.get("data", [])

    def list_docs(self, book_id: int, *, offset: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        result = self._request(
            "GET",
            f"/api/books/{book_id}/docs?offset={offset}&limit={limit}",
            referer=f"{self.base_url}/",
        )
        return result.get("data", [])

    def search_docs(
        self,
        query: str,
        *,
        book_id: int | None = None,
        book: dict[str, Any] | None = None,
        group_login: str | None = None,
    ) -> list[dict[str, Any]]:
        q = query.lower()
        hits: list[dict[str, Any]] = []

        def match_doc(doc: dict[str, Any], book: dict[str, Any] | None = None) -> bool:
            hay = " ".join(
                str(doc.get(k) or "")
                for k in ("title", "description", "slug")
            ).lower()
            return q in hay

        def enrich(doc: dict[str, Any], book: dict[str, Any]) -> dict[str, Any]:
            group = (
                book.get("group_login")
                or (book.get("namespace", "").split("/")[0] if book.get("namespace") else None)
                or load_config()["default_group"]
            )
            slug = doc.get("slug")
            book_slug = book.get("slug") or book.get("book_slug")
            url = f"{self.base_url}/{group}/{book_slug}/{slug}" if group and book_slug and slug else None
            return {
                "title": doc.get("title"),
                "description": (doc.get("description") or "")[:120],
                "book_name": book.get("name"),
                "book_id": book.get("id"),
                "doc_id": doc.get("id"),
                "slug": slug,
                "url": url,
                "updated_at": doc.get("content_updated_at") or doc.get("updated_at"),
            }

        if book is not None:
            for doc in self.list_docs(book["book_id"], limit=200):
                if match_doc(doc, book):
                    hits.append(enrich(doc, book))
            return hits

        if book_id is not None:
            book_meta: dict[str, Any] = {"id": book_id, "slug": "", "name": "", "namespace": ""}
            for doc in self.list_docs(book_id, limit=200):
                if match_doc(doc):
                    hits.append(enrich(doc, book_meta))
            return hits

        books: list[dict[str, Any]] = []
        if group_login:
            books = self.list_books(group_login)
        else:
            books = self.list_books(load_config()["default_group"])

        for book in books:
            book["group_login"] = group_login or load_config()["default_group"]
            for doc in self.list_docs(book["id"], limit=200):
                if match_doc(doc, book):
                    hits.append(enrich(doc, book))
        return hits


def get_client() -> YuqueClient:
    cfg = load_config()
    return YuqueClient(load_cookie(), base_url=cfg["base_url"], user_agent=cfg["user_agent"])


def cmd_cookie(args: argparse.Namespace) -> None:
    if args.check:
        try:
            client = get_client()
            me = client._request("GET", "/api/mine", referer=client.base_url + "/")
            name = me.get("data", {}).get("publicName") or me.get("data", {}).get("login")
            print(json.dumps({"ok": True, "user": name, "cookie_file": str(COOKIE_FILE)}, ensure_ascii=False))
        except AuthError as e:
            print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
            sys.exit(1)
    elif args.set:
        save_cookie(args.set)
        print(json.dumps({"ok": True, "cookie_file": str(COOKIE_FILE)}, ensure_ascii=False))
    else:
        print(str(COOKIE_FILE))


def cmd_info(args: argparse.Namespace) -> None:
    print(json.dumps(get_client().resolve_doc(args.url), ensure_ascii=False, indent=2))


def cmd_read(args: argparse.Namespace) -> None:
    client = get_client()
    meta = client.resolve_doc(args.url)
    doc = client.get_doc(meta["doc_id"], meta["book_id"], meta["page_url"])
    content = doc.get("content") or doc.get("body") or ""
    text = lake_to_text(content) if content else ""
    if args.format == "json":
        print(json.dumps({**meta, "text": text, "content_html": content, "description": doc.get("description")}, ensure_ascii=False, indent=2))
    elif args.format == "markdown":
        print(text)
    else:
        print(f"# {doc.get('title') or meta['title']}\n\n{text}")


def cmd_title(args: argparse.Namespace) -> None:
    client = get_client()
    meta = client.resolve_doc(args.url)
    updated = client.update_doc(meta["doc_id"], meta["book_id"], meta["page_url"], title=args.title)
    print(json.dumps({"title": updated["title"], "url": meta["page_url"]}, ensure_ascii=False, indent=2))


def cmd_write(args: argparse.Namespace) -> None:
    client = get_client()
    meta = client.resolve_doc(args.url)
    raw = Path(args.file).read_text(encoding="utf-8")
    body = markdown_to_lake(raw) if args.markdown or args.file.endswith(".md") else raw
    fields: dict[str, Any] = {"body": body, "format": "lake"}
    if args.title:
        fields["title"] = args.title
    updated = client.update_doc(meta["doc_id"], meta["book_id"], meta["page_url"], **fields)
    print(json.dumps({"title": updated["title"], "url": meta["page_url"], "updated_at": updated["updated_at"]}, ensure_ascii=False, indent=2))


def cmd_create(args: argparse.Namespace) -> None:
    client = get_client()
    book = client.resolve_book(args.book_url)
    raw = Path(args.file).read_text(encoding="utf-8")
    body = markdown_to_lake(raw) if args.markdown or args.file.endswith(".md") else raw
    created = client.create_doc(book["book_id"], args.title, body, book["page_url"])
    url = f"{client.base_url}/{book['group_login']}/{book['book_slug']}/{created['slug']}"
    print(json.dumps({"title": created["title"], "url": url, "doc_id": created["id"]}, ensure_ascii=False, indent=2))


def cmd_books(args: argparse.Namespace) -> None:
    client = get_client()
    group = args.group or load_config()["default_group"]
    books = client.list_books(group)
    out = [
        {
            "id": b["id"],
            "name": b["name"],
            "slug": b["slug"],
            "url": f"{client.base_url}/{group}/{b['slug']}",
            "items_count": b.get("items_count"),
        }
        for b in books
    ]
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_search(args: argparse.Namespace) -> None:
    client = get_client()
    book = None
    book_id = args.book_id
    if args.book_url:
        book = client.resolve_book(args.book_url)
        book_id = book["book_id"]
    hits = client.search_docs(args.query, book_id=book_id, book=book, group_login=args.group)
    print(json.dumps(hits, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Yuque docs skill CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_cookie = sub.add_parser("cookie", help="Check or save cookie")
    p_cookie.add_argument("--check", action="store_true")
    p_cookie.add_argument("--set", help="Save cookie string to credentials/cookie.txt")
    p_cookie.set_defaults(func=cmd_cookie)

    p_info = sub.add_parser("info", help="Resolve doc URL")
    p_info.add_argument("url")
    p_info.set_defaults(func=cmd_info)

    p_read = sub.add_parser("read", help="Read document")
    p_read.add_argument("url")
    p_read.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    p_read.set_defaults(func=cmd_read)

    p_title = sub.add_parser("title", help="Update title")
    p_title.add_argument("url")
    p_title.add_argument("title")
    p_title.set_defaults(func=cmd_title)

    p_write = sub.add_parser("write", help="Write Markdown/lake body to existing doc")
    p_write.add_argument("url")
    p_write.add_argument("--file", required=True)
    p_write.add_argument("--title")
    p_write.add_argument("--markdown", action="store_true", help="Force Markdown conversion")
    p_write.set_defaults(func=cmd_write)

    p_create = sub.add_parser("create", help="Create new doc in a book")
    p_create.add_argument("--book-url", required=True)
    p_create.add_argument("--title", required=True)
    p_create.add_argument("--file", required=True)
    p_create.add_argument("--markdown", action="store_true")
    p_create.set_defaults(func=cmd_create)

    p_books = sub.add_parser("books", help="List books in a group")
    p_books.add_argument("--group", help="Group login, e.g. tech-ozd0u")
    p_books.set_defaults(func=cmd_books)

    p_search = sub.add_parser("search", help="Search docs by keyword in title/description")
    p_search.add_argument("query")
    p_search.add_argument("--book-url")
    p_search.add_argument("--book-id", type=int)
    p_search.add_argument("--group", help="Search all books in group")
    p_search.set_defaults(func=cmd_search)

    args = parser.parse_args()
    try:
        args.func(args)
    except AuthError as e:
        print(json.dumps({"ok": False, "auth_error": True, "message": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
