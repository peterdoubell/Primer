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
from html import escape, unescape
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
RESERVED_CLASSES = {"table-scroll", "primer-navbox"}
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

    # Geometry lifted off the maths images on the way past, keyed by the URL we
    # rewrite them to, and re-applied once the sanitizer has run. See
    # _restore_math_metrics.
    math_metrics = {}

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
        if _MATH_SRC_RE.search(src):
            style_m = re.search(r'style="([^"]*)"', attrs, re.IGNORECASE)
            if style_m:
                ex = {k.lower(): v for k, v in _EX_METRIC_RE.findall(style_m.group(1))}
                if ex:
                    math_metrics[new] = ex
        # Keep the intrinsic size the encyclopedia states (295 of 416 images in
        # a seven-article sample carry both). Rebuilding the tag from three
        # attributes threw them away, so every picture occupied no space until
        # it had loaded and the article reflowed under the reader once per
        # image — with figures set beside the prose, a caption appeared first,
        # alone, and then jumped as its picture arrived. `max-width: 100%` and
        # `height: auto` in the stylesheet keep these a ratio rather than a
        # size, so a wide image still fits a narrow column.
        box = ""
        for name in ("width", "height"):
            got = re.search(r'\b%s="(\d{1,5})"' % name, attrs, re.IGNORECASE)
            if got:
                box += ' {}="{}"'.format(name, got.group(1))
        return '<img loading="lazy"{} src="{}" alt="{}">'.format(
            box, escape(new, quote=True), escape(alt, quote=True))

    html = _IMG_RE.sub(fix_img, html)

    # Final defence in depth: allowlist sanitize, and only then add the markers
    # this renderer gives behaviour to. `data-primer-title` is what the client
    # navigates on and `table-scroll` is what it scrolls; both are applied here,
    # downstream of the sanitizer, so an article cannot mint either one. An
    # anchor with no `href` never reached the link rewriter at all, and could
    # simply declare its own destination.
    html = sanitize(html)
    html = _LINK_RE.sub(fix_link, html)
    html = _restore_math_metrics(html, math_metrics)
    return _fold_navboxes(_wrap_tables(html))


# Wikimedia's maths renderer, and the three ex-relative metrics it states.
_MATH_SRC_RE = re.compile(r"/media/math/render/(?:svg|png)/", re.IGNORECASE)
_EX_METRIC_RE = re.compile(r"\b(vertical-align|width|height)\s*:\s*(-?\d*\.?\d+)ex",
                           re.IGNORECASE)
_IMG_SRC_RE = re.compile(r'(?is)<img\b[^>]*?\ssrc="([^"]*)"[^>]*>')


def _restore_math_metrics(html: str, metrics: dict) -> str:
    """Give each rendered formula back its own size and baseline.

    Wikipedia states a formula's geometry in the image's `style`, in `ex` — not
    in width/height attributes, which none of them carry. `style` is not an
    allowed attribute and must never become one, so the values are lifted off
    before sanitizing and written back here, the way every other marker this
    renderer owns is applied downstream of it.

    Without them the browser falls back to the SVG's own root dimensions, which
    resolve against the *SVG's* default font size rather than the reader's. Two
    things followed from that: every formula sat at one frozen size whatever
    stage the reader was at, and every one of them sat off the baseline, since
    the real vertical-align values in these articles run from 0 to -3ex. `ex`
    resolves against the inherited font-size, so re-emitting the upstream
    numbers fixes the scale, the baseline, and stage-tracking together.

    Only numeric `ex` values reach this point — the regex that parses them
    accepts nothing else — and the declaration is rebuilt from those numbers
    rather than echoed, so no upstream string is ever written into a style.
    """
    if not metrics:
        return html

    def add_style(m):
        src = unescape(m.group(1))
        ex = metrics.get(src)
        if not ex:
            return m.group(0)
        decl = ";".join("{}:{}ex".format(k, v) for k, v in sorted(ex.items()))
        # The sanitizer emits void tags as `<img …>`, but do not depend on it:
        # a stray `/` carried into the attribute list would break the tag.
        head = m.group(0)[:-1].rstrip().rstrip("/").rstrip()
        return head + ' style="{}">'.format(decl)

    return _IMG_SRC_RE.sub(add_style, html)


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


_DIV_TAG_RE = re.compile(r"(?is)<div(?:\s[^>]*)?>|</div\s*>")
# The exact class token, not a substring: navbox-styles, navbox-inner and
# navbox-list are parts of a navigation box, not boxes themselves.
_NAVBOX_OPEN_RE = re.compile(
    r'(?is)<div\b[^>]*\sclass="(?:[^"]*\s)?navbox(?:\s[^"]*)?"[^>]*>')
_NAVBOX_TITLE_RE = re.compile(r'(?is)<t[hd]\b[^>]*\sclass="(?:[^"]*\s)?navbox-title'
                              r'(?:\s[^"]*)?"[^>]*>(.*?)</t[hd]\s*>')
_NAVBAR_RE = re.compile(r'(?is)<div\b[^>]*\sclass="(?:[^"]*\s)?navbar(?:\s[^"]*)?".*?</div\s*>')
_TAGS_RE = re.compile(r"(?s)<[^>]+>")


def _navbox_summary(inner: str) -> str:
    """The navigation box's own title, for the disclosure that now holds it."""
    m = _NAVBOX_TITLE_RE.search(inner)
    if not m:
        return "Related topics"
    # The title cell leads with the v·t·e template bar, whose three one-letter
    # links would otherwise turn every summary into "vteSir Isaac Newton".
    text = _TAGS_RE.sub(" ", _NAVBAR_RE.sub(" ", m.group(1)))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:120] or "Related topics"


def _fold_navboxes(html: str) -> str:
    """Fold each navigation box behind a closed disclosure.

    A navbox is the encyclopedia's footer of links to every related article. On
    Wikipedia most of them arrive collapsed; here they arrived open and stacked,
    and a long article ended in a wall of them — 12 boxes and about 15 000px of
    link soup at the foot of Isaac Newton, against 70 000px of article. That is
    not something a reader scrolls past, it is something a reader stops at.

    `<details>` keeps every link reachable and in the accessibility tree, which
    is what separates this from hiding the content: the box is closed, not gone.

    Applied after sanitizing, and `primer-navbox` is a reserved class, so an
    article cannot mint a disclosure of its own or fold the book's furniture
    away inside one.
    """
    if "navbox" not in html:
        return html
    out, pos = [], 0
    while True:
        m = _NAVBOX_OPEN_RE.search(html, pos)
        if not m:
            break
        # Walk to the matching </div> so nested boxes travel with their parent
        # rather than being folded a second time inside it.
        depth, end = 0, None
        for t in _DIV_TAG_RE.finditer(html, m.start()):
            depth += -1 if t.group(0).lower().startswith("</") else 1
            if depth == 0:
                end = t.end()
                break
        if end is None:
            break          # unclosed box: leave the rest of the article alone
        inner = html[m.start():end]
        out.append(html[pos:m.start()])
        out.append('<details class="primer-navbox"><summary>{}</summary>{}</details>'.format(
            escape(_navbox_summary(inner), quote=True), inner))
        pos = end
    out.append(html[pos:])
    return "".join(out)
