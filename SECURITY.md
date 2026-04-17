# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly:

1. **Email**: [rudrasarker130@gmail.com](mailto:rudrasarker130@gmail.com)
2. **Subject**: `[SECURITY] NexusAgent Vulnerability Report`
3. **Include**: Steps to reproduce, affected versions, potential impact

**Do NOT** open a public issue for security vulnerabilities.

We will acknowledge receipt within 48 hours and aim to resolve within 7 days.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | ✅       |
| 0.1.x   | ❌       |

## Security Features

- **No telemetry**: NexusAgent does not send any data externally
- **Local execution**: All processing happens on your machine
- **Sandboxed skills**: Auto-generated skills run in isolated subprocesses
- **No network by default**: Only connects when explicitly configured (Ollama, API calls)

## Known Limitations

- Plugin code runs in the same process (use sandbox for untrusted code)
- No authentication on the web dashboard (bind to localhost only)
- No input validation on model API keys (handle with care)
