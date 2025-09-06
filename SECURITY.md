# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security bugs seriously. We appreciate your efforts to responsibly disclose your findings.

### Where to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to security@chainsync.com.

### What to Include

Please include the following information in your report:

- Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### Response Timeline

- We will acknowledge receipt of your vulnerability report within 3 business days
- We will provide a detailed response within 7 business days indicating next steps
- We will work with you to understand and resolve the issue quickly
- We will notify you when the issue has been fixed

### Responsible Disclosure

We request that you:

- Give us reasonable time to investigate and mitigate an issue before making any information public
- Make a good faith effort to avoid privacy violations and disruptions to others
- Only interact with accounts you own or with explicit permission of the account holder

### Recognition

We believe in giving credit where credit is due. We will:

- Acknowledge your responsible disclosure publicly (with your permission)
- Include your name in our Hall of Fame (if you wish)
- Consider monetary rewards for exceptional discoveries (at our discretion)

## Security Measures

### Data Protection
- All data is stored locally by default
- Optional cloud features require explicit configuration
- No data is transmitted without user consent
- Sensitive configuration is stored in environment variables

### Authentication & Authorization
- No authentication required for local-only mode
- Optional JWT-based authentication for production deployments
- Role-based access control for multi-user scenarios

### Input Validation
- All user inputs are validated using Pydantic/Zod schemas
- File uploads are restricted by type and size
- SQL injection protection through SQLAlchemy ORM
- XSS protection through proper output encoding

### Dependency Management
- Regular dependency updates through automated tools
- Security scanning of dependencies
- Minimal dependency footprint
- Pinned versions in production builds

## Best Practices for Users

### Local Development
- Use strong secret keys in production
- Keep dependencies updated
- Use HTTPS in production environments
- Regularly backup your data

### Production Deployment
- Use environment variables for sensitive configuration
- Implement proper network security
- Monitor for security events
- Follow principle of least privilege

## Contact

For general security questions or concerns, please contact security@chainsync.com.

For urgent security matters, please use the subject line "URGENT SECURITY ISSUE" in your email.