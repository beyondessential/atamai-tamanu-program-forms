# Style Guide

## Language

Use **Australian English** throughout all code, documentation, comments, and configuration.

## Writing Style

Be concise. Do not over-explain — prefer a clear, short statement over a lengthy justification.
In comments, docstrings, and documentation: say what something does, not why it is obvious.

## Python Style

- Type hints on all function signatures
- Docstrings on public functions — one line is enough unless the behaviour is non-obvious
- Prefer `??` style null checks as `value or default` in Python
- No unnecessary abstractions — if something is used once, keep it inline
