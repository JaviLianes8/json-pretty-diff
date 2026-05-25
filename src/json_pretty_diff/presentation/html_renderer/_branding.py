"""Branding header components for the HTML renderer."""

from __future__ import annotations

import html
from typing import Iterable, Tuple

SOCIAL_LINKS: Tuple[Tuple[str, str, str], ...] = (
    (
        "LinkedIn",
        "https://www.linkedin.com/in/jlianes/",
        "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg",
    ),
    (
        "GitHub",
        "https://github.com/JaviLianes8/json-pretty-diff",
        "https://cdn.simpleicons.org/github/181717",
    ),
    (
        "Buy Me a Coffee",
        "https://buymeacoffee.com/jlianesglrs",
        "https://cdn.simpleicons.org/buymeacoffee/FFDD00",
    ),
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
        f'aria-label="{safe_label}">'  # noqa: DASA100 - keep formatting simple
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
            f"<div class=\"branding__links\">{_render_social_links(SOCIAL_LINKS)}</div>",
            (
                '<p class="branding__signature">'
                'Made with love by Javier Lianes García in Aranjuez '
                '<span class="branding__heart" role="img" aria-label="love">❤️</span>'
                '</p>'
            ),
            '</header>',
        ]
    )

__all__ = ["render_branding_header", "SOCIAL_LINKS"]
