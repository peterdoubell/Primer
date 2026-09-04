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

# This runs on RAW upstream markup, where a `>` inside an attribute value is
# legal and unescaped, so it has to know where a quoted value begins and ends.
# `<img\b[^>]*>` did not: it stopped at that inner `>`, cut the tag in half and
# left the rest of the attribute in the document as text — an image whose alt is
# "a > b" lost its alt and spilled `b" title="x">` into the page.
#
# Two rules earn their keep here, and both were learned by breaking this:
#
#   A quote opens a value only directly after `=`. Allowed anywhere, a bare
#   apostrophe inside an *unquoted* value opened a run that paired with the next
#   apostrophe in the English prose: `<meta name=Newton's>` ran past its own `>`,
#   past "Newton's laws say F", and ended at a raw `>` in the body text, taking
#   the sentence with it.
#
#   Nothing may cross a `<`. An attribute value has to escape one (Parsoid
#   writes `&lt;ref />`, and no attribute in a seven-article sample holds a raw
#   `<`), so this bound stops any runaway at the start of the next tag.
#
# A tag that still cannot be read is declined rather than guessed at — the
# second branch is the plain first-`>` rule, bounded the same way.
_IMG_RE = re.compile(
    r'<img\b((?:=\s*"[^"<]*"|=\s*\'[^\'<]*\'|[^<>"\'])*|[^<>]*)>', re.IGNORECASE)
_RAW_ATTR_RE = {}
# Parsoid's <link>/<meta> carry template JSON in a single-quoted data-mw
# attribute holding things like `<ref name="x" />` — so their attribute values
# contain `>`, and `<link\b[^>]*>` cut the tag at that inner `>` and left the
# rest of the JSON in the document as text. Sixteen fragments across a
# seven-article sample, three of them mid-blockquote.
#
# Two passes, and the ORDER is the design. The first reads quoted values under
# the same two rules as _IMG_RE above and takes every well-formed tag. The
# second is the plain first-`>` rule, so by the time it runs the well-formed
# tags are already gone and it can only reach one whose quotes do not balance.
#
# Both are bounded by `<` as well as `>`, which means a tag whose quote never
# closes at all is declined by both and reaches the sanitizer, which cannot find
# its end either and escapes it as text. That is the one shape this leaves
# visible, and it is the right side of the trade: the alternative bound lets the
# second pass cut a well-formed tag at a `>` inside its JSON and put the
# remainder back in the reader's prose, which is the bug all of this is here to
# remove.
_VOID_META_RE = re.compile(
    r'(?i)<(?:link|meta)\b(?:=\s*"[^"<]*"|=\s*\'[^\'<]*\'|[^<>"\'])*>')
_BROKEN_VOID_META_RE = re.compile(r'(?i)<(?:link|meta)\b[^<>]*>')

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
# Every HTML void element, not only the five this renderer emits. This set is
# what tells the sanitizer a tag will never be closed, and `link`, `meta`,
# `base`, `input`, `area`, `source`, `track` and `embed` are all in
# DROP_WITH_CONTENT while being absent from it. A `<link>` not written
# self-closing therefore raised drop_depth with nothing to lower it, and the
# unclosed-drop-tag repair below then deleted every inline run between that tag
# and the next block element — a whole sentence, replaced by a space. Void
# elements never open a subtree, so they must never raise the depth at all.
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "source", "track", "wbr"}
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
# `primer-wikilink` belongs here for the same reason the other two do, and was
# the one that got missed: it is the class that makes a link look like part of
# this book. Forged onto an external anchor it cannot navigate anywhere — the
# client's handler reads data-primer-title, which is unforgeable, and calls
# preventDefault — but the reader still sees the book's own in-book styling on a
# link that middle-clicks straight out to whatever the article chose.
RESERVED_CLASSES = {
    "table-scroll", "primer-navbox", "primer-article-guide", "primer-wikilink",
}
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


_MAX_RAW_TAG_CHARS = 64 * 1024


def _looks_like_tag_start(html: str, index: int) -> bool:
    if index + 1 >= len(html):
        return False
    nxt = html[index + 1]
    return nxt.isascii() and (nxt.isalpha() or nxt in "/!?")


def _bound_malformed_markup(html: str) -> str:
    """Escape incomplete/nested tag starts before ``HTMLParser`` sees them.

    CPython's parser repeatedly rescans an unfinished start tag as more input
    arrives.  A string such as ``"<table " * n`` is therefore quadratic even
    though the sanitizer eventually treats it as text.  This linear preflight
    leaves complete tags byte-for-byte intact, including ``<`` and ``>`` inside
    a quoted value, while escaping a start that is superseded by another raw
    ``<`` outside quotes, runs past a generous tag-size ceiling, or is still
    unfinished at EOF.  When an unfinished quoted value contains further tag
    starts, every ``<`` in that bounded fragment is escaped together so none is
    exposed to the parser as a fresh incomplete candidate.
    """
    if "<" not in html:
        return html

    out = []
    last = 0
    tag_start = None
    quote = None
    after_equal = False
    i, size = 0, len(html)

    while i < size:
        char = html[i]
        if tag_start is None:
            if char == "<" and html.startswith("<!--", i):
                end = html.find("-->", i + 4)
                if end < 0:
                    out.extend((html[last:i], "&lt;"))
                    last = i + 1
                    i += 1
                else:
                    i = end + 3
                continue
            if char == "<" and _looks_like_tag_start(html, i):
                tag_start = i
                quote = None
                after_equal = False
            i += 1
            continue

        if char == "<" and quote is None:
            # The previous start never closed. Escape only its opening marker;
            # the remainder stays visible as text and this new start is then
            # evaluated independently.
            out.extend((html[last:tag_start], "&lt;"))
            last = tag_start + 1
            tag_start = i if _looks_like_tag_start(html, i) else None
            quote = None
            after_equal = False
            i += 1
            continue

        if quote is not None:
            if char == quote:
                quote = None
        elif after_equal:
            if char.isspace():
                pass
            elif char in "\"'":
                quote = char
                after_equal = False
            else:
                after_equal = False
        elif char == "=":
            after_equal = True
        elif char == ">":
            tag_start = None

        if tag_start is not None and i - tag_start >= _MAX_RAW_TAG_CHARS:
            out.extend((html[last:tag_start],
                        html[tag_start:i + 1].replace("<", "&lt;")))
            last = i + 1
            tag_start = None
            quote = None
            after_equal = False
        i += 1

    if tag_start is not None:
        out.extend((html[last:tag_start],
                    html[tag_start:].replace("<", "&lt;")))
        last = size
    if not out:
        return html
    out.append(html[last:])
    return "".join(out)


def _text_only_fallback(html: str) -> str:
    """Strip tag-shaped spans in one linear pass, then escape all text.

    This path is only used if ``HTMLParser`` itself fails.  A regex such as
    ``<[^>]+>`` is both an incomplete HTML parser and vulnerable to excessive
    backtracking on hostile malformed input; a small state machine is enough
    for the deliberately conservative text-only fallback.
    """
    out = []
    in_tag = False
    for char in html:
        if in_tag:
            if char == ">":
                in_tag = False
                out.append(" ")
        elif char == "<":
            in_tag = True
            out.append(" ")
        else:
            out.append(char)
    return escape("".join(out))


def sanitize(html: str) -> str:
    # Metadata is a void element: even when its quotes are malformed, discard
    # the opening fragment at the first `>` and keep the prose that follows.
    # This must precede the generic malformed-tag preflight, which deliberately
    # escapes unknown incomplete starts as visible text.
    html = _VOID_META_RE.sub("", html)
    html = _BROKEN_VOID_META_RE.sub("", html)
    html = _bound_malformed_markup(html)
    p = _Sanitizer()
    try:
        p.feed(html)
        p.close()
    except Exception:
        # On any parser failure, fall back to a text-only rendering.
        return _text_only_fallback(html)
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
            return _text_only_fallback(html)
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
    html = _VOID_META_RE.sub("", html)
    html = _BROKEN_VOID_META_RE.sub("", html)
    # Metadata has its own conservative malformed-tag rule above. Bound every
    # other candidate before the raw image rewrite and again inside sanitize()
    # so neither stage sees a megabyte-long unfinished tag.
    html = _bound_malformed_markup(html)

    body = re.search(r"(?is)<body[^>]*>(.*)</body>", html)
    if body:
        html = body.group(1)

    # Geometry lifted off the maths images on the way past, keyed by the URL we
    # rewrite them to, and re-applied once the sanitizer has run. See
    # _restore_math_metrics.
    math_metrics = {}

    def raw_attr(attrs, name):
        """Read one real attribute, never a similarly suffixed data attribute.

        Parsoid puts ``data-file-width`` before ``width`` on most images.  The
        old ``\\bwidth`` search therefore found the file's original dimensions
        (often 180x185 for a 20px maintenance icon) and enlarged the thumbnail
        ninefold.  HTML attributes are whitespace-separated, so anchoring the
        name to whitespace/start is both simpler and exact.
        """
        pattern = _RAW_ATTR_RE.get(name)
        if pattern is None:
            pattern = re.compile(
                r'(?:^|\s)' + re.escape(name) +
                r'\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s"\'<>]+))',
                re.IGNORECASE,
            )
            _RAW_ATTR_RE[name] = pattern
        got = pattern.search(attrs)
        if not got:
            return None
        return next((value for value in got.groups() if value is not None), "")

    def best_srcset_source(value):
        """Choose the sharpest valid source while keeping srcset off the page.

        Every chosen URL is still rewritten through the image proxy below;
        the browser never contacts Wikimedia directly.  Wikimedia's REST HTML
        normally supplies one 2x candidate, while ZIM/older markup may use
        width descriptors.  Mixed descriptor kinds are invalid HTML, so a
        malformed set simply leaves the ordinary ``src`` in place.
        """
        if not value:
            return None
        ranked, kind = [], None
        for raw_candidate in unescape(value).split(","):
            parts = raw_candidate.strip().rsplit(None, 1)
            if len(parts) != 2:
                continue
            source, descriptor = parts
            try:
                if descriptor.endswith("x"):
                    candidate_kind, score = "x", float(descriptor[:-1])
                elif descriptor.endswith("w"):
                    candidate_kind, score = "w", float(descriptor[:-1])
                else:
                    continue
            except ValueError:
                continue
            if score <= 0 or not _SAFE_URL.match(source):
                continue
            if kind is None:
                kind = candidate_kind
            if candidate_kind != kind:
                return None
            ranked.append((score, source))
        return max(ranked, default=(0, None))[1]

    def fix_img(m):
        attrs = m.group(1)
        raw_src = raw_attr(attrs, "src")
        raw_alt = raw_attr(attrs, "alt")
        # These are read out of raw source, where the values are entity-escaped;
        # they must come back to their real form before being escaped (or
        # URL-quoted) once on the way out. Without this, every & reached the
        # image proxy as %26amp%3B — a parameter literally named "amp;…" — and a
        # formula's alt text spoke "&amp;=" where its LaTeX says "&=".
        alt = unescape(raw_alt) if raw_alt is not None else ""
        if raw_src is None:
            return ""
        src = best_srcset_source(raw_attr(attrs, "srcset")) or unescape(raw_src)
        if src.startswith("//"):
            src = "https:" + src
        if src.startswith("http"):
            new = "/api/image?url=" + urllib.parse.quote(src, safe="")
        elif base:
            new = base + src.lstrip("./")
        else:
            new = src
        if _MATH_SRC_RE.search(src):
            style = raw_attr(attrs, "style")
            if style:
                ex = {k.lower(): v for k, v in _EX_METRIC_RE.findall(style)}
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
            value = raw_attr(attrs, name)
            if value and re.fullmatch(r'\d{1,5}', value):
                box += ' {}="{}"'.format(name, value)
        # A very small, semantic slice of Wikipedia's image classes survives
        # reconstruction.  These are not layout hooks: they say the bitmap is
        # dark line-work on transparency and therefore needs inverting on the
        # night page.  Eight cached hieroglyphs carry the marker on the image
        # itself rather than on an ancestor; dropping it made sound image data
        # render as black ink on a black page.
        raw_class = raw_attr(attrs, "class") or ""
        presentation = " ".join(dict.fromkeys(
            token.lower() for token in raw_class.split()
            if token.lower() in {"skin-invert", "skin-invert-image"}
        ))
        class_attr = (' class="{}"'.format(presentation)) if presentation else ""
        return '<img loading="lazy"{}{} src="{}" alt="{}">'.format(
            box, class_attr, escape(new, quote=True), escape(alt, quote=True))

    html = _IMG_RE.sub(fix_img, html)

    # Final defence in depth: allowlist sanitize, and only then add the markers
    # this renderer gives behaviour to. `data-primer-title` is what the client
    # navigates on and `table-scroll` is what it scrolls; both are applied here,
    # downstream of the sanitizer, so an article cannot mint either one. An
    # anchor with no `href` never reached the link rewriter at all, and could
    # simply declare its own destination.
    html = sanitize(html)
    html = _rewrite_sanitized_tags(html, math_metrics)
    return _fold_navboxes(_wrap_tables(_fold_article_guides(html)))


# Wikimedia's maths renderer, and the three ex-relative metrics it states.
_MATH_SRC_RE = re.compile(r"/media/math/render/(?:svg|png)/", re.IGNORECASE)
_EX_METRIC_RE = re.compile(r"\b(vertical-align|width|height)\s*:\s*(-?\d*\.?\d+)ex",
                           re.IGNORECASE)


def _has_class(attrs, token: str) -> bool:
    wanted = token.lower()
    return any(name.lower() == "class" and wanted in (value or "").lower().split()
               for name, value in attrs)


def _start_tag(tag: str, attrs) -> str:
    rendered = "".join(' {}="{}"'.format(name, escape(value or "", quote=True))
                       for name, value in attrs)
    return "<{}{}>".format(tag, rendered)


class _StreamingHTMLPass(HTMLParser):
    """Copy normalized markup in one pass, with hooks for structural rewrites.

    These passes run only after ``sanitize``. Using HTMLParser here avoids the
    overlapping wildcard patterns that made a failed match rescan the same long
    attribute run from every possible starting point.
    """
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.out = []

    def _emit(self, text):
        self.out.append(text)

    def _raw_start(self, tag, attrs):
        return self.get_starttag_text() or _start_tag(tag, attrs)

    def handle_starttag(self, tag, attrs):
        self._emit(self._raw_start(tag, attrs))

    def handle_startendtag(self, tag, attrs):
        self._emit(self._raw_start(tag, attrs))

    def handle_endtag(self, tag):
        self._emit("</{}>".format(tag))

    def handle_data(self, data):
        self._emit(data)

    def handle_entityref(self, name):
        self._emit("&{};".format(name))

    def handle_charref(self, name):
        self._emit("&#{};".format(name))

    def handle_comment(self, data):
        self._emit("<!--{}-->".format(data))

    def handle_decl(self, decl):
        self._emit("<!{}>".format(decl))

    def handle_pi(self, data):
        self._emit("<?{}>".format(data))

    def result(self):
        return "".join(self.out)


def _run_html_pass(html: str, parser: _StreamingHTMLPass) -> str:
    """Run a downstream enhancement; on parser failure keep sanitized markup."""
    try:
        parser.feed(html)
        parser.close()
        return parser.result()
    except Exception as exc:
        # Input has already passed the security sanitizer. Losing an enhancement
        # is safer than losing the article, and returning this string cannot add
        # anything the allowlist did not approve.
        log.warning("post-sanitize markup pass failed: %s", exc)
        return html


class _SanitizedTagPass(_StreamingHTMLPass):
    """Rewrite links and images without searching tag text with regexes."""
    def __init__(self, math_metrics):
        super().__init__()
        self.math_metrics = math_metrics or {}

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "a":
            href = next((value or "" for name, value in attrs
                         if name.lower() == "href"), None)
            if href is None:
                return super().handle_starttag(tag, attrs)
            title = _wiki_title_from_href(href)
            if title:
                kept = [(name, value) for name, value in attrs
                        if name.lower() not in ("href", "class", "data-primer-title")]
                kept.extend((("href", "#"), ("data-primer-title", title),
                             ("class", "primer-wikilink")))
            elif href.lower().startswith(("http://", "https://")):
                kept = [(name, value) for name, value in attrs
                        if name.lower() not in ("href", "target", "rel",
                                                "data-primer-title")]
                kept.extend((("href", href), ("target", "_blank"),
                             ("rel", "noopener noreferrer")))
            else:
                kept = [(name, value) for name, value in attrs
                        if name.lower() not in ("href", "data-primer-title")]
                kept.append(("href", "#"))
            self._emit(_start_tag("a", kept))
            return

        if tag == "img":
            src = next((value or "" for name, value in attrs
                        if name.lower() == "src"), None)
            if src is None:
                return super().handle_starttag(tag, attrs)
            if src.startswith("//"):
                src = "https:" + src
            if src.lower().startswith(("http://", "https://")):
                src = "/api/image?url=" + urllib.parse.quote(src, safe="")

            kept, wrote_src = [], False
            for name, value in attrs:
                lower = name.lower()
                if lower == "style":
                    continue             # only the numeric metrics below may return
                if lower == "src":
                    if wrote_src:
                        continue
                    kept.append(("src", src))
                    wrote_src = True
                else:
                    kept.append((name, value))
            ex = self.math_metrics.get(src)
            if ex:
                decl = ";".join("{}:{}ex".format(k, v) for k, v in sorted(ex.items()))
                kept.append(("style", decl))
            self._emit(_start_tag("img", kept))
            return

        super().handle_starttag(tag, attrs)


def _rewrite_sanitized_tags(html: str, math_metrics: dict) -> str:
    """Apply link/image behavior in a single linear parser pass."""
    if "<a" not in html.lower() and "<img" not in html.lower():
        return html
    return _run_html_pass(html, _SanitizedTagPass(math_metrics))


class _TableWrapperPass(_StreamingHTMLPass):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.opened = 0
        self.sequence = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "table":
            if self.depth == 0:
                self.sequence += 1
                self._emit('<div class="table-scroll" tabindex="0" role="region" '
                           'aria-label="Table {}">'.format(self.sequence))
                self.opened += 1
            self.depth += 1
        super().handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        super().handle_endtag(tag)
        if tag.lower() == "table" and self.depth > 0:
            self.depth -= 1
            if self.depth == 0:
                self._emit("</div>")
                self.opened -= 1

    def result(self):
        return super().result() + "</div>" * max(0, self.opened)


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
    return _run_html_pass(html, _TableWrapperPass())


class _NavboxSummaryPass(HTMLParser):
    """Extract a navbox title while ignoring its v/t/e toolbar."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.capturing = False
        self.done = False
        self.depth = 0
        self.skip_depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self.done:
            return
        if not self.capturing:
            if tag in ("th", "td") and _has_class(attrs, "navbox-title"):
                self.capturing = True
                self.depth = 1
            return

        nonvoid = tag not in VOID_TAGS
        if nonvoid:
            self.depth += 1
        if self.skip_depth:
            if nonvoid:
                self.skip_depth += 1
        elif tag == "div" and _has_class(attrs, "navbar"):
            self.parts.append(" ")
            self.skip_depth = 1
        else:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if not self.capturing or self.done:
            return
        if self.skip_depth:
            self.skip_depth -= 1
        else:
            self.parts.append(" ")
        self.depth -= 1
        if self.depth <= 0:
            self.capturing = False
            self.done = True

    def handle_data(self, data):
        if self.capturing and not self.skip_depth:
            self.parts.append(data)

    def result(self):
        if not self.done:
            return "Related topics"
        text = " ".join("".join(self.parts).split()).strip()
        return text[:120] or "Related topics"


def _navbox_summary(inner: str) -> str:
    """The navigation box's own title, for the disclosure that now holds it."""
    parser = _NavboxSummaryPass()
    try:
        parser.feed(inner)
        parser.close()
    except Exception:
        return "Related topics"
    return parser.result()


class _ArticleGuideSummaryPass(HTMLParser):
    """Read the subject name from a Wikipedia ``table.sidebar``.

    Sidebars normally call their subject ``sidebar-title`` (or the pretitle
    variant).  The fallback is deliberately generic because a disclosure with
    the wrong inferred subject is worse than one simply called Article guide.
    """
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.capturing = False
        self.depth = 0
        self.done = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self.done:
            return
        if not self.capturing:
            classes = next((value or "" for name, value in attrs
                            if (name or "").lower() == "class"), "")
            tokens = {token.lower() for token in classes.split()}
            if tag in ("th", "td", "div") and tokens.intersection(
                    {"sidebar-title", "sidebar-title-with-pretitle"}):
                self.capturing = True
                self.depth = 1
            return
        if tag not in VOID_TAGS:
            self.depth += 1
        self.parts.append(" ")

    def handle_endtag(self, tag):
        if not self.capturing or self.done:
            return
        self.parts.append(" ")
        self.depth -= 1
        if self.depth <= 0:
            self.capturing = False
            self.done = True

    def handle_data(self, data):
        if self.capturing:
            self.parts.append(data)

    def result(self):
        text = " ".join("".join(self.parts).split()).strip()[:100]
        return (text + " topics") if text else "Article guide"


def _article_guide_summary(inner: str) -> str:
    parser = _ArticleGuideSummaryPass()
    try:
        parser.feed(inner)
        parser.close()
    except Exception:
        return "Article guide"
    return parser.result()


class _ArticleGuideFolderPass(_StreamingHTMLPass):
    """Fold each outer Wikipedia topic sidebar into a named disclosure."""
    def __init__(self):
        super().__init__()
        self.buffer = None
        self.table_depth = 0

    def _emit(self, text):
        (self.buffer if self.buffer is not None else self.out).append(text)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        raw = self._raw_start(tag, attrs)
        if self.buffer is None and tag == "table" and _has_class(attrs, "sidebar"):
            self.buffer = [raw]
            self.table_depth = 1
            return
        self._emit(raw)
        if self.buffer is not None and tag == "table":
            self.table_depth += 1

    def handle_endtag(self, tag):
        tag = tag.lower()
        self._emit("</{}>".format(tag))
        if self.buffer is not None and tag == "table":
            self.table_depth -= 1
            if self.table_depth == 0:
                inner = "".join(self.buffer)
                self.buffer = None
                self.out.append(
                    '<details class="primer-article-guide"><summary>{}</summary>{}</details>'.format(
                        escape(_article_guide_summary(inner), quote=True), inner))

    def result(self):
        if self.buffer is not None:
            self.out.extend(self.buffer)
            self.buffer = None
        return super().result()


def _fold_article_guides(html: str) -> str:
    """Keep upstream subject navigation available without opening a wall.

    ``sidebar-collapse`` / ``mw-collapsed`` are behavior hooks in Wikipedia's
    own JavaScript.  That script is intentionally absent here, so every group
    arrived expanded.  A native closed ``details`` restores the promised
    toggle without importing upstream code or hiding any of its links.
    """
    if "sidebar" not in html.lower():
        return html
    return _run_html_pass(html, _ArticleGuideFolderPass())


class _NavboxFolderPass(_StreamingHTMLPass):
    def __init__(self):
        super().__init__()
        self.buffer = None
        self.div_depth = 0

    def _emit(self, text):
        (self.buffer if self.buffer is not None else self.out).append(text)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        raw = self._raw_start(tag, attrs)
        if self.buffer is None and tag == "div" and _has_class(attrs, "navbox"):
            self.buffer = [raw]
            self.div_depth = 1
            return
        self._emit(raw)
        if self.buffer is not None and tag == "div":
            self.div_depth += 1

    def handle_endtag(self, tag):
        tag = tag.lower()
        self._emit("</{}>".format(tag))
        if self.buffer is not None and tag == "div":
            self.div_depth -= 1
            if self.div_depth == 0:
                inner = "".join(self.buffer)
                self.buffer = None
                self.out.append(
                    '<details class="primer-navbox"><summary>{}</summary>{}</details>'.format(
                        escape(_navbox_summary(inner), quote=True), inner))

    def result(self):
        if self.buffer is not None:
            self.out.extend(self.buffer)
            self.buffer = None
        return super().result()


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
    if "navbox" not in html.lower():
        return html
    return _run_html_pass(html, _NavboxFolderPass())
