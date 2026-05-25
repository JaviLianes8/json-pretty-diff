"""JavaScript snippet generator for the full JSON table filter."""

from __future__ import annotations

def render_full_json_filter_script(table_id: str) -> str:
    """Builds the JavaScript snippet that powers the full JSON filter."""

    return f"""
<script>
(function() {{
    var filterInput = document.querySelector('[data-json-filter][data-json-target="{table_id}"]');
    var table = document.getElementById('{table_id}');
    if (!filterInput || !table) {{
        return;
    }}
    var preElements = table.querySelectorAll('tbody pre');
    Array.prototype.forEach.call(preElements, function(pre) {{
        pre.setAttribute('data-original-text', pre.textContent || '');
    }});
    var filterContainer = filterInput.closest('.full-json-filter');
    var matches = [];

    function escapeHtml(value) {{
        return value
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }}

    function highlightText(text, query) {{
        if (!query) {{
            return escapeHtml(text);
        }}
        var lowerText = text.toLowerCase();
        var lowerQuery = query.toLowerCase();
        var result = '';
        var lastIndex = 0;
        var index = lowerText.indexOf(lowerQuery);
        while (index !== -1) {{
            result += escapeHtml(text.slice(lastIndex, index));
            result += '<mark class="full-json-highlight">' + escapeHtml(text.slice(index, index + query.length)) + '</mark>';
            lastIndex = index + query.length;
            index = lowerText.indexOf(lowerQuery, lastIndex);
        }}
        result += escapeHtml(text.slice(lastIndex));
        return result;
    }}

    function ensureMatchVisible(target) {{
        if (!target) {{
            return;
        }}
        if (!filterContainer) {{
            target.scrollIntoView({{ behavior: 'smooth', block: 'center', inline: 'nearest' }});
            return;
        }}

        var spacer = 16; // Match the 1rem top offset applied via CSS.
        var filterRect = filterContainer.getBoundingClientRect();
        var offset;

        if (filterRect.top <= spacer) {{
            offset = filterRect.bottom + spacer;
        }} else {{
            offset = filterRect.top + filterRect.height + spacer;
        }}

        var targetRect = target.getBoundingClientRect();
        var absoluteTop = window.scrollY + targetRect.top;
        var desiredTop = Math.max(absoluteTop - offset, 0);

        if (typeof window.scrollTo === 'function') {{
            window.scrollTo({{ top: desiredTop, behavior: 'smooth' }});
        }} else {{
            window.scroll(0, desiredTop);
        }}
    }}

    function performSearch(query) {{
        Array.prototype.forEach.call(preElements, function(pre) {{
            var original = pre.getAttribute('data-original-text');
            if (original === null) {{
                original = pre.textContent || '';
                pre.setAttribute('data-original-text', original);
            }}
            pre.innerHTML = highlightText(original, query);
        }});
        matches = Array.prototype.slice.call(table.querySelectorAll('mark.full-json-highlight'));
        if (matches.length) {{
            ensureMatchVisible(matches[0]);
        }}
    }}

    filterInput.addEventListener('input', function(event) {{
        performSearch(event.target.value);
    }});
}})();
</script>
""".strip()

__all__ = ["render_full_json_filter_script"]
