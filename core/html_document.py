import logging
import re

logger = logging.getLogger(__name__)

DOCUMENT_START = re.compile(r"<!doctype html|<html", re.IGNORECASE)
DOCUMENT_END = "</html>"


def ends_document(html: str) -> bool:
    """True when nothing but whitespace follows the closing `</html>`."""
    return html.rstrip().lower().endswith(DOCUMENT_END)


def extract_html_document(reply: str, source: str) -> str:
    """Returns the HTML document inside a model reply, dropping any prose or
    markdown fences around it: from the first `<!DOCTYPE html>`/`<html` to the
    last `</html>`. A reply with no document start comes back stripped. Logs a
    warning naming `source` (the agent) when text was dropped."""
    html = _extract(reply)
    if html != reply.strip():
        logger.warning("Dropped text around the HTML document in the %s reply", source)
    return html


def _extract(reply: str) -> str:
    start = DOCUMENT_START.search(reply)
    if start is None:
        return reply.strip()
    end = reply.lower().rfind(DOCUMENT_END)
    if end < start.start():
        return reply[start.start() :].strip()
    return reply[start.start() : end + len(DOCUMENT_END)]
