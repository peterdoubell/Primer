"""Rewrite AND sanitize encyclopedia HTML so it lives safely inside the Primer.

Article bodies come from live Wikipedia (anyone can edit) and ZIM archives, so
the HTML is untrusted. We therefore do two things:

1. **Rewrite** — internal wiki links become in-book navigation
   (data-primer-title), images load through our caching proxy, and relative ZIM
   asset URLs resolve under /zim/<archive>/.
2. **Sanitize** — a strict allowlist pass (stdlib HTMLParser, no regex games)
   drops every tag and attribute not on the allowlist: no <script>/<style>/
   <iframe>/<object>/<svg>/<math>/<form>, no on* handlers regardless of
   quoting, no javascript:/data: URLs. This closes stored-XSS from upstream
   content — the article HTML is injected into the DOM with innerHTML.
"""

import logging
import re
import urllib.parse
from html import escape
from html.parser import HTMLParser

log = logging.getLogger("primer.render")

_LINK_RE = re.compile(r'<a\b([^>]*?)href="([^"]*)"([^>]*)>', re.IGNORECASE)
_IMG_RE = re.compile(r'<img\b([^>]*?)>', re.IGNORECASE)
_SRCSET_RE = re.compile(r'\ssrcset="[^"]*"', re.IGNORECASE)
_SCRIPT_RE = re.compile(r'(?is)<script\b[^>]*>.*?</script>')
_STYLE_BLOCK_RE = re.compile(r'(?is)<style\b[^>]*>.*?</style>')
_STYLE_LINK_RE = re.compile(r'(?is)<link\b[^>]*>')
_META_RE = re.compile(r'(?is)<meta\b[^>]*>')

# Tags we keep. Everything else is dropped (its text content is kept unless the
# tag is in DROP_WITH_CONTENT).
ALLOWED_TAGS = {
    "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "dl", "dt", "dd",
    "table", "thead", "tbody", "tfoot", "tr", "td", "th", "caption", "colgroup", "col",
    "blockquote", "pre", "code", "kbd", "samp",
    "em", "i", "strong", "b", "u", "s", "sup", "sub", "small", "mark", "cite",
    "abbr", "time", "q", "span", "div", "a", "img",
    "figure", "figcaption", "section", "article", "header", "footer", "aside",
    "ruby", "rt", "rp", "wbr",
}
# Tags whose entire subtree (including text) is discarded.
DROP_WITH_CONTENT = {
    "script", "style", "iframe", "object", "embed", "svg", "math", "form",
    "input", "button", "textarea", "select", "option", "noscript", "template",
    "link", "meta", "audio", "video", "canvas", "map", "area", "base",
}
VOID_TAGS = {"br", "hr", "img", "col", "wbr"}
ALLOWED_ATTRS = {
    "href", "src", "alt", "title", "class", "colspan", "rowspan", "loading",
    "dir", "lang", "width", "height", "scope", "target", "rel",
}
# `target`/`rel` are allowed only in the exact safe forms we emit ourselves, so
# an upstream article cannot aim links at named frames.
#
# Class names this renderer emits and gives behaviour to. An article may carry
# whatever classes it likes except these: it cannot be allowed to dress its own
# markup as the book's furniture.
RESERVED_CLASSES = {"table-scroll"}
_NAV_ATTR_RE = re.compile(r"""\s*data-primer-title\s*=\s*(?:"[^"]*"|'[^']*'|\S+)""",
                          re.IGNORECASE)
# An inherited class= would win the duplicate-attribute fight against the one
# this renderer emits (browsers honour the first), so it is stripped first.
_CLASS_ATTR_RE = re.compile(r"""\sclass\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)""",
                            re.IGNORECASE)
_ATTR_VALUE_WHITELIST = {
    "target": {"_blank"},
    "rel": {"noopener noreferrer", "noopener", "noreferrer"},
}
# Only these URL shapes may appear in href/src (no javascript:, data:, …).
_SAFE_URL = re.compile(r'^(#|/|https?://|\.{0,2}/)', re.IGNORECASE)


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.drop_depth = 0  # inside a DROP_WITH_CONTENT subtree
        self.open_tags = []  # what this article has actually opened

    def _emit(self, s):
        if self.drop_depth == 0:
            self.out.append(s)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in DROP_WITH_CONTENT:
            if tag not in VOID_TAGS:
                self.drop_depth += 1
            return
        if tag not in ALLOWED_TAGS:
            return  # unwrap: drop tag, keep children/text
        clean, used = [], set()
        for name, value in attrs:
            name = (name or "").lower()
            if name not in ALLOWED_ATTRS or name.startswith("on") or name in used:
                # `used` also drops duplicate attributes. Note this is also what
                # keeps `data-primer-title` out of article markup: the client
                # navigates on that attribute, and since it is not in
                # ALLOWED_ATTRS an article cannot hang it on a span and turn
                # arbitrary text into a link to anywhere. The renderer adds it
                # downstream of sanitize, where it cannot be forged.
                continue
            value = value or ""
            if name in ("href", "src"):
                v = value.strip()
                if not _SAFE_URL.match(v):
                    continue  # blocks javascript:, data:, vbscript:, etc.
            if name in _ATTR_VALUE_WHITELIST and value.strip().lower() not in _ATTR_VALUE_WHITELIST[name]:
                continue
            if name == "class":
                kept = [c for c in value.split() if c.lower() not in RESERVED_CLASSES]
                if not kept:
                    continue
                value = " ".join(kept)
            used.add(name)
            clean.append('{}="{}"'.format(name, escape(value, quote=True)))
        attr_str = (" " + " ".join(clean)) if clean else ""
        if tag in VOID_TAGS:
            self._emit("<{}{}>".format(tag, attr_str))
        else:
            self.open_tags.append(tag)
            self._emit("<{}{}>".format(tag, attr_str))

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        if tag in DROP_WITH_CONTENT or tag not in ALLOWED_TAGS:
            return
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in DROP_WITH_CONTENT:
            if tag not in VOID_TAGS and self.drop_depth > 0:
                self.drop_depth -= 1
            return
        if tag not in ALLOWED_TAGS or tag in VOID_TAGS:
            return
        # An article closing something it never opened would close one of the
        # book's own containers instead — a stray `</div>` at the top of an
        # article ends the reading column and throws the rest of the page out of
        # its layout. Drop what does not match.
        if tag not in self.open_tags:
            log.debug("dropped stray </%s> in article HTML", tag)
            return
        while self.open_tags:
            top = self.open_tags.pop()
            self._emit("</{}>".format(top))
            if top == tag:
                break

    def handle_data(self, data):
        self._emit(escape(data, quote=False))

    def handle_entityref(self, name):
        self._emit("&{};".format(name))

    def handle_charref(self, name):
        self._emit("&#{};".format(name))


def _flush(p):
    """Close whatever the article left hanging.

    An unclosed `<div>` swallows the rest of the page into the article. This has
    to run on *every* exit path — the repair branch below builds a second parse
    and returned it raw, so a malformed `<style>` next to an unclosed `<div>`
    still produced an unbalanced document.
    """
    for tag in reversed(p.open_tags):
        p.out.append("</{}>".format(tag))
    return "".join(p.out)


def sanitize(html: str) -> str:
    p = _Sanitizer()
    try:
        p.feed(html)
        p.close()
    except Exception:
        # On any parser failure, fall back to a text-only rendering.
        return escape(re.sub(r"(?s)<[^>]+>", " ", html))
    out = _flush(p)
    if p.drop_depth > 0:
        # An unclosed drop-tag (e.g. a malformed <style>) swallows everything
        # after it — sometimes the whole article, sometimes just the body. Any
        # unbalanced drop tag means content was lost, so always repair.
        log.warning("unclosed drop tag in article HTML; repairing (depth=%d)", p.drop_depth)
        # Drop the *contents* of the offending element up to the next block tag,
        # so a malformed <style> does not spill "body{}" into the article text.
        repaired = re.sub(
            r"(?is)<\s*(?:%s)\b[^>]*>.*?(?=<(?:p|div|h[1-6]|section|article|ul|ol|table)\b|$)"
            % "|".join(DROP_WITH_CONTENT), " ", html)
        p2 = _Sanitizer()
        try:
            p2.feed(repaired)
            p2.close()
            return _flush(p2)
        except Exception:
            return escape(re.sub(r"(?s)<[^>]+>", " ", html))
    return out


def _wiki_title_from_href(href: str) -> str:
    """Extract a page title from various wiki link shapes, else ''."""
    # Leading whitespace/control chars must not hide the scheme.
    href = (href or "").strip().lstrip("\x00\t\n\r\x0b\x0c")
    if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
        return ""
    # Reject any non-http URI scheme (javascript:, data:, vbscript:, …) that is
    # not a /wiki/ path — never treat it as an article title.
    scheme = re.match(r"^([a-z][a-z0-9+.-]*):", href, re.IGNORECASE)
    if scheme and scheme.group(1).lower() not in ("http", "https") and "/wiki/" not in href:
        return ""
    # An absolute link to some other site is an *external* link, not an article
    # in this book — only wiki paths and archive-relative paths are in-book.
    if re.match(r"^https?://", href, re.IGNORECASE) or href.startswith("//"):
        host = re.sub(r"^(?:https?:)?//([^/?#]+).*$", r"\1", href, flags=re.IGNORECASE).lower()
        if not (host.endswith(".wikipedia.org") or host.endswith(".wikimedia.org")
                or host in ("wikipedia.org", "wikimedia.org")):
            return ""
    m = re.search(r"/wiki/([^#?]+)", href)
    if not m:
        m = re.search(r"(?:^|/)([^/#?]+)$", href.split("#")[0])
    if not m:
        return ""
    raw = m.group(1)
    if raw.endswith(".html"):
        raw = raw[:-5]
    title = urllib.parse.unquote(raw).replace("_", " ")
    if ":" in title and title.split(":", 1)[0] in (
        "File", "Image", "Category", "Template", "Help", "Wikipedia", "Portal",
        "Special", "Talk", "User", "Module", "Draft",
    ):
        return ""
    return title.strip()


def rewrite_article(html: str, base: str = "") -> str:
    """base is the URL prefix for ZIM-relative assets, e.g. /zim/<id>/A/."""
    html = _SCRIPT_RE.sub("", html)
    html = _STYLE_BLOCK_RE.sub("", html)
    html = _STYLE_LINK_RE.sub("", html)
    html = _META_RE.sub("", html)
    html = _SRCSET_RE.sub("", html)

    body = re.search(r"(?is)<body[^>]*>(.*)</body>", html)
    if body:
        html = body.group(1)

    def fix_link(m):
        pre, href, post = m.group(1), m.group(2), m.group(3)
        # Whatever else an anchor carried, it does not get to keep the attribute
        # the client navigates on: this renderer decides where a link goes.
        pre = _NAV_ATTR_RE.sub(" ", pre or "")
        post = _NAV_ATTR_RE.sub(" ", post or "")
        title = _wiki_title_from_href(href)
        if title:
            # The article's own class= would win the duplicate-attribute fight
            # (browsers honour the first), silently dropping the class the
            # reader's click handler and the link styling both key on. Strip
            # any inherited class and re-emit ours as the only one.
            pre_nc = _CLASS_ATTR_RE.sub(" ", pre)
            post_nc = _CLASS_ATTR_RE.sub(" ", post)
            return '<a{}href="#" data-primer-title="{}"{} class="primer-wikilink">'.format(
                pre_nc, escape(title, quote=True), post_nc
            )
        if href.startswith("http"):
            return '<a{}href="{}"{} target="_blank" rel="noopener noreferrer">'.format(
                pre, escape(href, quote=True), post)
        return '<a{}href="#"{}>'.format(pre, post)

    def fix_img(m):
        attrs = m.group(1)
        src_m = re.search(r'src="([^"]*)"', attrs, re.IGNORECASE)
        alt_m = re.search(r'alt="([^"]*)"', attrs, re.IGNORECASE)
        alt = alt_m.group(1) if alt_m else ""
        if not src_m:
            return ""
        src = src_m.group(1)
        if src.startswith("//"):
            src = "https:" + src
        if src.startswith("http"):
            new = "/api/image?url=" + urllib.parse.quote(src, safe="")
        elif base:
            new = base + src.lstrip("./")
        else:
            new = src
        return '<img loading="lazy" src="{}" alt="{}">'.format(
            escape(new, quote=True), escape(alt, quote=True))

    html = _IMG_RE.sub(fix_img, html)

    # Final defence in depth: allowlist sanitize, and only then add the markers
    # this renderer gives behaviour to. `data-primer-title` is what the client
    # navigates on and `table-scroll` is what it scrolls; both are applied here,
    # downstream of the sanitizer, so an article cannot mint either one. An
    # anchor with no `href` never reached the link rewriter at all, and could
    # simply declare its own destination.
    html = sanitize(html)
    html = _LINK_RE.sub(fix_link, html)
    return _wrap_tables(html)


_TABLE_OPEN_RE = re.compile(r"(?is)<table(\s[^>]*)?>")
_TABLE_CLOSE_RE = re.compile(r"(?is)</table\s*>")


def _wrap_tables(html: str) -> str:
    """Put each table inside its own scroll container.

    A wide table used to be made `display: block` by the stylesheet, which is
    the usual trick for making it scroll — and it strips every row and cell out
    of the accessibility tree. One encyclopedia article had 23 tables whose 26
    rows and 50 cells were simply not there. The table stays a table; the
    wrapper does the scrolling, and is focusable so a keyboard can reach it.

    Applied after sanitizing so the wrapper cannot be forged by article markup.
    """
    if "<table" not in html.lower():
        return html
    out, depth, pos, opened, seq = [], 0, 0, 0, 0
    for m in re.finditer(r"(?is)<table(?:\s[^>]*)?>|</table\s*>", html):
        out.append(html[pos:m.start()])
        tag = m.group(0)
        if tag.lower().startswith("</"):
            out.append(tag)
            # A stray closing tag must not drive the depth negative: doing so
            # suppressed the wrapper on every table after it in the article.
            if depth > 0:
                depth -= 1
                if depth == 0:
                    out.append("</div>")
                    opened -= 1
        else:
            if depth == 0:
                seq += 1
                out.append('<div class="table-scroll" tabindex="0" role="region" '
                           'aria-label="Table {}">'.format(seq))
                opened += 1
            depth += 1
            out.append(tag)
        pos = m.end()
    out.append(html[pos:])
    # An unclosed <table> would otherwise leave the wrapper hanging open and
    # swallow the rest of the article.
    out.append("</div>" * max(0, opened))
    return "".join(out)
