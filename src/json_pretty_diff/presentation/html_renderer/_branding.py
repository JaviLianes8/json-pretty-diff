"""Branding header components for the HTML renderer."""

from __future__ import annotations

import base64
import html
from typing import Iterable, Tuple

# Small drawings of the three marks made for this report (the marks belong to their owners),
# embedded so the report shows them offline and opening it contacts nobody (1.1.1 loaded
# them from two CDNs).
_LINKEDIN = (
    '<rect width="32" height="32" rx="6" fill="#0a66c2"/>'
    '<rect x="7" y="13" width="4" height="12" fill="#fff"/>'
    '<circle cx="9" cy="8.5" r="2.4" fill="#fff"/>'
    '<path d="M14 13h3.8v1.7c.7-1.1 2-2 4-2 3.6 0 4.2 2.3 4.2 5.4V25h-4v-6c0-1.5-.1-3.2-2-3.2'
    's-2.2 1.5-2.2 3.1V25H14z" fill="#fff"/>'
)
_GITHUB = (
    '<circle cx="16" cy="16" r="16" fill="#181717"/>'
    '<path d="M9.2 11.2 9.8 6l3.9 2.9a10 10 0 0 1 4.6 0L22.2 6l.6 5.2a7 7 0 0 1 1.4 4.6'
    'c-.4 4.4-3.3 5.8-8.2 5.8s-7.8-1.4-8.2-5.8a7 7 0 0 1 1.4-4.6z" fill="#fff"/>'
    '<path d="M13.6 21.4v4.6m4.8-4.6v4.6" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/>'
)
_COFFEE = (
    '<circle cx="16" cy="16" r="16" fill="#ffdd00"/>'
    '<path d="M9.5 12.5h12l-1.5 11.6a2 2 0 0 1-2 1.7h-5a2 2 0 0 1-2-1.7z" fill="#0d0c22"/>'
    '<path d="M21.3 14.6h1.4a2.8 2.8 0 0 1 0 5.6h-1.9" fill="none" stroke="#0d0c22" stroke-width="1.8"/>'
    '<path d="M13.2 10c0-1.4 1.4-1.4 1.4-2.8m2.8 2.8c0-1.4 1.4-1.4 1.4-2.8" fill="none" stroke="#0d0c22"'
    ' stroke-width="1.3" stroke-linecap="round"/>'
)


def _icon(drawing: str) -> str:
    """Wraps a drawing in an SVG document and returns it as a ``data:`` URI."""

    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">{drawing}</svg>'
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("ascii")).decode("ascii")


SOCIAL_LINKS: Tuple[Tuple[str, str, str], ...] = (
    ("LinkedIn", "https://www.linkedin.com/in/jlianes/", _icon(_LINKEDIN)),
    ("GitHub", "https://github.com/JaviLianes8/json-pretty-diff", _icon(_GITHUB)),
    ("Buy Me a Coffee", "https://buymeacoffee.com/jlianesglrs", _icon(_COFFEE)),
)


def _render_social_link(label: str, href: str, icon: str) -> str:
    """Builds the anchor tag for a single social link."""

    safe_label = html.escape(label, quote=True)
    safe_href = html.escape(href, quote=True)
    safe_icon = html.escape(icon, quote=True)
    return (
        '<a class="branding__link" '
        f'href="{safe_href}" '
        'target="_blank" '
        'rel="noopener noreferrer" '
        f'aria-label="{safe_label}">'
        f'<img src="{safe_icon}" alt="{html.escape(label)} icon" '
        'width="32" height="32" loading="lazy" />'
        "</a>"
    )


def _render_social_links(links: Iterable[Tuple[str, str, str]]) -> str:
    """Renders the navigation element containing all social links."""

    return "".join(_render_social_link(*link) for link in links)


def render_branding_header() -> str:
    """Returns the header with social navigation and signature banner."""

    return "\n".join(
        [
            '<header class="branding">',
            f'<div class="branding__links">{_render_social_links(SOCIAL_LINKS)}</div>',
            (
                '<p class="branding__signature">'
                "Made with love by Javier Lianes García in Aranjuez "
                '<span class="branding__heart" role="img" aria-label="love">❤️</span>'
                "</p>"
            ),
            "</header>",
        ]
    )


__all__ = ["SOCIAL_LINKS", "render_branding_header"]
