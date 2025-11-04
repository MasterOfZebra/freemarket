# 🔒 Security Guidelines for FreeMarket

This document outlines security best practices implemented in the current architecture, focusing on authentication, token handling, data privacy, and deployment considerations.

1) Authentication
- JWT-based authentication with short-lived access tokens and long-lived refresh tokens.
- Refresh tokens are stored in HttpOnly, Secure cookies and rotated on each use.
- Server-side revocation store (Redis) tracks active refresh tokens per device/user; revoked tokens cannot be reused.
- Password hashing uses Argon2id (or bcrypt as fallback).

2) Token Rotation & Revocation
- On refresh, a new refresh token is issued and the old one is marked revoked in Redis.
- Logout clears the session cookie and revokes the refresh token.
- Rate limiting is applied to authentication endpoints to deter brute-force attempts.

3) Cookies & Security Headers
- Cookies are HttpOnly, Secure, and SameSite=Lax (or Strict depending on flow).
- All API responses include proper cache-control and CSRF protections where applicable.

4) Data Privacy & Access Control
- Minimal PII storage; allow user data export and account deletion.
- Access control enforces per-resource permissions for LK data (profiles, listings, exchanges).

5) Secrets & Secrets Management
- Environment variables used for sensitive data; secrets are injected at deployment time.
- Do not commit credentials to VCS.

6) Monitoring & Auditing
- Audit logs for login/logout/refresh events stored securely.
- Error logging excludes sensitive payloads.

7) Deployment Considerations
- TLS termination at Nginx; backend services communicate over internal networks.
- Redis-backed revocation, with proper TTLs to avoid unbounded growth.


