# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in ZeroMonitor, please report it responsibly.

⚠️ **DO NOT** create a public GitHub issue for security vulnerabilities.

### Reporting Process

1. **Email:** Send details to the project maintainers at the email listed in the repository
2. **Information to include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

3. **Response time:** We aim to respond within 48 hours

4. **Disclosure:** We will work with you to fix the issue before public disclosure

## Security Best Practices

### For Users

#### Installation
- Always install from official releases: `pip install zeromonitor`
- Verify package integrity
- Keep dependencies updated

#### Configuration
- Never commit `.env` file containing credentials
- Use strong passwords for SMTP and system access
- Rotate credentials regularly
- Restrict file permissions on config files

#### Deployment
- Run on secure network
- Use SSH key authentication (not password)
- Enable firewall rules
- Monitor logs for suspicious activity
- Keep system packages updated

### For Developers

#### Code Security

**Credential Management:**
```python
# ✅ CORRECT: Use environment variables
smtp_password = os.getenv("SMTP_PASSWORD")

# ❌ WRONG: Hardcoded credentials
smtp_password = "my-secret-password"
```

**File Operations:**
```python
# ✅ CORRECT: Use secure permissions
os.chmod(config_file, 0o600)  # User read/write only

# ❌ WRONG: World-readable sensitive files
with open(credentials_file, "w") as f:  # Default permissions
    json.dump(credentials, f)
```

**Sensitive Data:**
- Never log passwords, API keys, or credentials
- Sanitize error messages
- Use secure hashing for passwords
- Don't store secrets in version control

**Dependencies:**
- Keep dependencies updated
- Review security advisories regularly
- Use `pip audit` to check for vulnerabilities
- Avoid dependencies with known vulnerabilities

#### Testing Security

- Test credential loading from environment
- Test permission restrictions on files
- Test encryption/decryption functions
- Test error handling without exposing secrets

```python
def test_smtp_password_from_env():
    """Verify SMTP password loads from environment."""
    os.environ["SMTP_PASSWORD"] = "test-password"
    interpreter = DataInterpreter(mock_bus, mock_config)
    assert interpreter.smtp_password == "test-password"
    assert interpreter.smtp_password != "hardcoded-value"
```

#### Code Review Checklist

Before merging any code:

- [ ] No hardcoded credentials or secrets
- [ ] No sensitive data in logs
- [ ] Proper error handling (no info leaks)
- [ ] Environment variables documented
- [ ] `.env` not committed (check .gitignore)
- [ ] File permissions appropriate
- [ ] Dependencies security reviewed
- [ ] SQL injection prevention (if applicable)
- [ ] Authentication properly implemented
- [ ] Authorization checks present

## Known Security Considerations

### SSH Key Management
- SSH keys are encrypted at rest
- Keys stored in secure paths: `/home/zero_monitor_storage/`
- Keys decrypted to RAM only during use: `/run/zero_monitor_decrypted/`

### Email Configuration
- SMTP credentials loaded from environment only
- No credentials logged or exposed in errors
- SSL/TLS connection enforced for SMTP

### Data at Rest
- Cache data stored in JSON format (unencrypted)
- Recommendations:
  - Store on encrypted filesystem
  - Restrict file permissions to user only
  - Regular backups with encryption

### Data in Transit
- SSH for remote command execution (encrypted)
- Optional SSL/TLS for web interfaces (if added)
- Event bus uses in-process queues (no network exposure)

## Dependency Security

### Checking for Vulnerabilities

```bash
# List all dependencies
pip freeze

# Check for known vulnerabilities
pip install pip-audit
pip-audit

# Or use safety
pip install safety
safety check
```

### Vulnerable Dependency Response

If a dependency has a known vulnerability:

1. Check if fix is available
2. Update if possible: `pip install --upgrade package-name`
3. If no fix available:
   - Assess risk and mitigations
   - Consider alternative package
   - Monitor for security patches

## Encryption & Cryptography

### Current Implementation
- Argon2 for password hashing
- AES encryption for vault
- ED25519 SSH keys

### Best Practices
- Use industry-standard algorithms
- Keep cryptography library updated
- Proper key derivation (Argon2 with good parameters)
- Secure random number generation

### Configuration
```python
# Argon2 parameters (in src/constants.py)
ARGON2_TIME_COST = 20           # CPU work
ARGON2_MEMORY_COST = 65536      # Memory in KiB
ARGON2_PARALLELISM = 4          # Parallel threads
```

Adjust if:
- Hashing too slow: decrease TIME_COST
- Hashing too fast: increase TIME_COST or MEMORY_COST
- Memory constraints: decrease MEMORY_COST

## Monitoring & Logging

### Security Relevant Logs
- Failed authentication attempts
- Credential errors
- File access errors
- Network connection failures
- Configuration changes

### Audit Trail
- All operations logged to `logs/system.log`
- Consider retention policy for sensitive logs
- Regular log review for suspicious activity

## Security Roadmap

### High Priority
- [ ] Add API authentication (if web UI added)
- [ ] Implement rate limiting for failed attempts
- [ ] Add audit logging for configuration changes
- [ ] Regular security dependency scanning in CI/CD

### Medium Priority
- [ ] Add encryption for cached metrics
- [ ] Implement TLS for any network communication
- [ ] Add security headers to web interface
- [ ] Regular penetration testing

### Low Priority
- [ ] Hardware security module (HSM) integration
- [ ] Biometric authentication options
- [ ] Zero-knowledge architecture options

## Compliance & Standards

### Followed Standards
- PEP 8 (Python style guide)
- OWASP Top 10 (where applicable)
- Common Weakness Enumeration (CWE) guidelines

### Encryption Standards
- NIST recommendations for key sizes
- FIPS 140-2 compliance objectives
- Industry best practices for SSH keys

## Questions?

For security-related questions:
- Review this document
- Check CONTRIBUTING.md
- Contact maintainers privately for sensitive questions
- DON'T discuss vulnerabilities publicly

---

**Last Updated:** April 2026
**Version:** 1.0

