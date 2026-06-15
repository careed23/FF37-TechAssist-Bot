# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this repository, please report it privately to the project maintainer at:

- Email: careed23@outlook.com

Do not use public GitHub Issues for sensitive security reports.

## Supported Versions

This repository is a proof-of-concept and currently maintained on the `main` branch.

## Supported Dependencies

The project depends on:

- Python 3.10+ with `flask`, `pyyaml`, and `rich`
- React/Vite frontend dependencies in `web-frontend/package.json`

Please notify maintainers if you discover a vulnerability in any dependency.

## How We Handle Reports

1. We will acknowledge your report within a reasonable time.
2. We may request additional information to reproduce the issue.
3. Security fixes will be merged and released as soon as possible.
4. Public disclosure may occur after a fix is available.

## Safe Contribution Practices

- Avoid committing secrets or credentials.
- Use the issue templates for bug reports and feature requests.
- Keep security-sensitive data out of YAML flow definitions and logs.
