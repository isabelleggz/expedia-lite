# 02 — Environment readiness

Purpose: Verify the project-local Python and JavaScript toolchains without silently changing the machine or dependency declarations.

## Copyable prompt

```text
Read AGENTS.md, README.md, and docs/verification.md. Work only inside expedia-agent.

Verify the Expedia Lite development environment before writing application code:
- report the operating system;
- confirm that backend/.venv/bin/python is the interpreter used for backend checks and that it is Python 3.10 or newer;
- import fastapi and pytest through that interpreter;
- report the Node.js and npm versions and executable paths;
- confirm Node.js satisfies the engines requirement in frontend/package.json;
- confirm frontend/package.json declares Vue; and
- run the existing frontend lint and production build.

Do not install, upgrade, or change dependencies. Do not install packages globally. If a machine-level change is required, explain the exact official installation method, administrator requirement, and affected location, then stop for permission. Never use sudo automatically or bypass managed-computer policy. Report every command, its evidence, and every failed or partial check; stop if the project is not ready.
```
