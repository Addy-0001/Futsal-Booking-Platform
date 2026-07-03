"""
HTML sanitization for user-authored rich text (CKEditor ticket replies/messages).

Rich text from customers is untrusted, so we allow only a safe subset of tags and
attributes. Base64 images (data: URLs) are permitted so pasted/embedded screenshots
survive. Uses `nh3` (fast, maintained); falls back to `bleach`, then to full escape.
"""
from django.utils.html import escape, strip_tags

ALLOWED_TAGS = {
    "p", "br", "hr", "span", "div",
    "strong", "b", "em", "i", "u", "s", "strike", "sub", "sup", "mark",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li", "blockquote",
    "pre", "code",
    "a", "img", "figure", "figcaption",
    "table", "thead", "tbody", "tr", "th", "td",
}

ALLOWED_ATTRS = {
    "*": {"class"},
    "a": {"href", "title", "target", "class"},
    "img": {"src", "alt", "width", "height", "class"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
    "code": {"class"},
    "pre": {"class"},
}

# data: needed for embedded base64 images from the editor.
URL_SCHEMES = {"http", "https", "mailto", "tel", "data"}


def sanitize_html(value: str) -> str:
    if not value:
        return ""
    try:
        import nh3

        return nh3.clean(
            value,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            url_schemes=URL_SCHEMES,
            link_rel="noopener noreferrer nofollow",
        )
    except ImportError:
        pass
    try:
        import bleach

        attrs = {k: list(v) for k, v in ALLOWED_ATTRS.items()}
        cleaned = bleach.clean(
            value, tags=list(ALLOWED_TAGS), attributes=attrs,
            protocols=list(URL_SCHEMES), strip=True,
        )
        return cleaned
    except ImportError:
        # No sanitizer library available. Degrade to clean PLAIN TEXT (tags removed)
        # rather than escaping — escaping would show literal "<p>" tags to users.
        return escape(strip_tags(value))
