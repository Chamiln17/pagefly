import re

DOCUMENT_START = re.compile(r"<!doctype html|<html", re.IGNORECASE)
DOCUMENT_END = "</html>"


def extract_html_document(reply: str) -> str:
    """Returns the HTML document inside a model reply, dropping any prose or
    markdown fences around it: from the first `<!DOCTYPE html>`/`<html` to the
    last `</html>`. A reply with no document start comes back stripped."""
    start = DOCUMENT_START.search(reply)
    if start is None:
        return reply.strip()
    end = reply.lower().rfind(DOCUMENT_END)
    if end < start.start():
        return reply[start.start() :].strip()
    return reply[start.start() : end + len(DOCUMENT_END)]
