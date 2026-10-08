# Coding standards

Judgement rules for review. Mechanical rules (formatting, `print`, logging style, state keys) are enforced by ruff and the tests.

- Use the vocabulary in `GLOSSARY.md`. Say "Marketing Angle", not "marketing strategy" or "angle input".
- An agent raises on failure. It never returns stand-in output such as an empty page or placeholder copy.
- Each agent has a test asserting what its prompt receives.
- Tests assert the final graph state or the HTTP response.
- A ticket that changes a prompt includes a real smoke run, within the spending ceiling the ticket states.
