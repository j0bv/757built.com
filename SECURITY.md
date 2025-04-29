# Security Policy

## Reporting a Vulnerability

We take the security of 757Built.com seriously. If you believe you've found a security vulnerability in our code, please follow these steps:

1. **Do not disclose the vulnerability publicly** until we've had a chance to address it.
2. **Email us** at security@757built.com with details about the vulnerability.
3. **Include the following information**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)

## What to Expect

- We will acknowledge receipt of your vulnerability report within 3 business days.
- We will provide an estimated timeline for addressing the vulnerability.
- We will keep you informed about the progress of fixing the issue.
- Once fixed, we will publicly acknowledge your responsible disclosure (unless you prefer to remain anonymous).

## Security Best Practices for Deployments

If you're deploying this codebase, follow these security recommendations:

1. **Environment Variables**: Always use environment variables for sensitive configuration. Never hardcode credentials.
2. **API Keys**: Restrict API keys to only the permissions they need.
3. **Database**: Use strong, unique passwords and restrict database access to only necessary IPs.
4. **Keep Updated**: Regularly update dependencies to patch security vulnerabilities.
5. **Rate Limiting**: Implement rate limiting on API endpoints to prevent abuse.
6. **HTTPS**: Always use HTTPS in production environments.
7. **Audit Logs**: Maintain logs of system access and changes.

Thank you for helping keep 757Built.com secure! 