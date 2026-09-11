# Deployment & Infrastructure Specification

## 1. Purpose

This document defines the deployment architecture and operational
requirements for the AI-Powered Web Security Configuration Auditor.

The deployment must provide:

- Secure application hosting
- HTTPS
- FastAPI application serving
- MySQL database connectivity
- Background scan processing
- AI provider integration
- Secure environment configuration
- Logging
- Health monitoring
- Database backup
- Failure recovery
- Safe deployment and rollback

---

## 2. Deployment Architecture

Recommended production architecture:

```
Internet
   |
 HTTPS
   |
 Nginx
   |
 FastAPI
   |
 +--------+---------+
 |        |         |
Scanner  MySQL     AI
Worker    DB      Provider
```

The scanner worker should be isolated from the public-facing API
where practical.

## 3. Deployment Components

The production system contains:

- Frontend
- Backend API
- Scanner Worker
- MySQL
- Nginx
- TLS Certificate
- AI Provider
- Logging
- Monitoring

## 4. Recommended Server

Minimum recommended production server:

```
CPU:
2+ vCPU

RAM:
4 GB+

Storage:
40 GB+

OS:
Ubuntu 22.04 LTS / Ubuntu 24.04 LTS

Database:
MySQL 8.x

Python:
3.11+
```

The exact requirements depend on scan concurrency and deployment size.

## 5. Development Environment

Local development:

```
Developer Machine
      |
Frontend
      |
FastAPI
      |
MySQL
      |
Mock AI
```

Recommended local tools:

- Python
- MySQL 8
- Git
- VS Code
- Browser

## 6. Project Structure

Recommended complete project:

```
security-auditor/
|
+-- app/
|   +-- api/
|   +-- ai/
|   +-- core/
|   +-- models/
|   +-- repositories/
|   +-- schemas/
|   +-- scanners/
|   +-- services/
|   +-- workers/
|
+-- frontend/
|
+-- tests/
|
+-- migrations/
|
+-- scripts/
|
+-- requirements.txt
+-- .env.example
+-- .gitignore
+-- README.md
```

## 7. Environment Separation

Maintain separate configurations:

- Development
- Testing
- Production

Never use production credentials in development or testing.

## 8. Environment Variables

Production secrets must be stored using environment variables.

Example:

```
APP_ENV=production

DATABASE_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/DB_NAME

SECRET_KEY=<secret>

AI_PROVIDER=<provider>
AI_MODEL=<model>
AI_API_KEY=<secret>

ALLOWED_ORIGINS=https://example.com

SCAN_TIMEOUT=15
SCAN_MAX_RESPONSE_SIZE=2097152
SCAN_MAX_REDIRECTS=5
```

Never hardcode secrets in source code.

## 9. .env Protection

The following must never be committed:

```
.env
.env.production
.env.local
```

`.gitignore` should contain:

```
.env
.env.*
!.env.example
```

The example file must contain placeholders only.

## 10. Production Secrets

Production secrets should be generated independently.

Examples:

- Application secret
- Database password
- AI API key
- Session secret
- JWT signing secret

Never reuse development secrets.

## 11. Database Deployment

MySQL 8.x is the recommended production database.

Example:

```
FastAPI
   |
SQLAlchemy
   |
MySQL 8.x
```

The database should not be directly exposed to the public Internet.

## 12. Database User

Create a dedicated application database user.

Example privileges:

```
SELECT
INSERT
UPDATE
DELETE
CREATE
ALTER
INDEX
```

Only grant the permissions required by the application.

Do not use:

```
root
```

as the application's production database account.

## 13. Database Network Security

MySQL should listen only on:

- Private network interface
- Localhost
- Internal database network

depending on infrastructure.

Avoid:

```
0.0.0.0:3306
```

unless explicitly protected by a private network/firewall.

## 14. Database Connection Pooling

SQLAlchemy should use connection pooling.

Recommended starting configuration:

```
Pool size:
10

Max overflow:
20

Pool recycle:
1800 seconds

Pool pre-ping:
Enabled
```

These values should be adjusted according to workload.

## 15. Database Migrations

Use Alembic for schema migrations.

Example:

```
Code Change
    |
Migration
    |
Alembic
    |
MySQL
```

Never manually modify production tables unless absolutely necessary.

## 16. Migration Workflow

Development:

```
alembic revision --autogenerate -m "description"
```

Review migration.

Then:

```
alembic upgrade head
```

Production migrations must be reviewed before execution.

## 17. Database Backup

Production database must be backed up regularly.

Minimum recommendation:

```
Daily full backup
```

For larger deployments:

```
Daily full backup
+
Incremental backups
```

## 18. Backup Verification

A backup is not considered reliable until it has been tested.

Periodically:

```
Backup
  |
Restore to Test DB
  |
Verify Tables
  |
Verify Data
```

## 19. Backup Security

Database backups may contain sensitive scan information.

Protect backups using:

- Encryption
- Restricted access
- Secure storage
- Retention policies

Do not commit database dumps to Git.

## 20. Backend Server

FastAPI should run behind a production ASGI server.

Recommended:

```
Uvicorn
```

or:

```
Gunicorn + Uvicorn workers
```

Example:

```
gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -w 2 \
  -b 127.0.0.1:8000
```

The exact worker count depends on CPU and scan workload.

## 21. API Binding

The FastAPI application should not directly expose its application
port to the public Internet.

Preferred:

```
127.0.0.1:8000
```

or an internal private network interface.

Public traffic should enter through Nginx.

## 22. Nginx

Nginx acts as:

- Reverse proxy
- TLS termination
- Static file server
- Request size control
- Rate limiting layer
- Security header layer

Architecture:

```
Client
  |
 HTTPS
  |
Nginx
  |
FastAPI
```

## 23. Nginx Reverse Proxy

Example configuration concept:

```nginx
server {
    listen 443 ssl http2;
    server_name auditor.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

The exact configuration must be reviewed for the production
environment.

## 24. HTTP to HTTPS Redirect

HTTP traffic should redirect to HTTPS.

Example:

```
http://auditor.example.com
             |
            301
             |
https://auditor.example.com
```

Avoid serving authenticated application functionality over plain HTTP.

## 25. TLS Certificate

Use a valid TLS certificate.

Recommended:

```
Let's Encrypt
```

or an equivalent trusted certificate provider.

Certificate renewal should be automated.

## 26. HSTS

After confirming HTTPS is correctly configured, the production
application may use:

```
Strict-Transport-Security
```

Example:

```
max-age=31536000
```

Only enable stronger HSTS options after verifying that all required
subdomains support HTTPS.

## 27. Application Security Headers

The application should configure appropriate security headers.

Examples:

```
X-Content-Type-Options: nosniff

Referrer-Policy: strict-origin-when-cross-origin

Content-Security-Policy: appropriate-policy

Permissions-Policy: restricted-policy
```

The exact CSP must match the frontend's actual resources.

## 28. CORS

Configure explicit allowed origins.

Example:

```
ALLOWED_ORIGINS=https://auditor.example.com
```

Avoid unrestricted authenticated CORS.

Do not use:

```
*
```

for sensitive authenticated APIs unless specifically justified.

## 29. Static Frontend Deployment

The frontend can be served directly by Nginx.

Example:

```
Nginx
  |
  +-- /index.html
  +-- /css/
  +-- /js/
```

API traffic:

```
/api/
   |
FastAPI
```

This reduces unnecessary backend load.

## 30. Recommended Production Routing

```
/              -> Frontend
/login         -> Frontend
/dashboard     -> Frontend
/scans         -> Frontend

/api/*         -> FastAPI
```

Nginx performs the routing.

## 31. Background Scanner

Security scans should not block the API request for the entire scan.

Preferred architecture:

```
POST /scans
      |
Create Scan
      |
Queue / Worker
      |
Scanner
      |
Database
```

The API immediately returns the scan identifier.

## 32. Worker Process

The worker performs:

- URL validation
- DNS validation
- TLS scanning
- HTTP scanning
- Cookie analysis
- Content analysis
- Finding generation
- Risk calculation
- Database updates
- AI processing

The worker must use the same security controls as the API layer.

## 33. Worker Isolation

The scanner worker should have:

- Limited network access
- Limited filesystem permissions
- Limited database permissions
- CPU limits
- Memory limits
- Timeout controls

The worker must never have unnecessary system privileges.

## 34. Scanner Network Policy

The scanner should only connect to approved target destinations.

The network layer must enforce:

- Allowed Scheme
- Allowed Ports
- Public IP
- DNS Validation
- Redirect Validation
- Timeout
- Response Size

## 35. Scanner Worker Failure

If a worker crashes:

```
Worker Crash
    |
Scan remains FAILED
or
Scan returns to QUEUED
```

depending on retry policy.

A scan must not remain permanently stuck in:

```
RUNNING
```

## 36. Worker Retry Policy

Only retry transient failures.

Potential retry:

- Temporary network timeout
- Temporary AI provider failure
- Temporary database connection failure

Do not repeatedly retry:

- SSRF blocked
- Invalid URL
- Unauthorized target
- Invalid configuration

## 37. Retry Limits

Recommended:

```
Maximum scanner retries:
2

Maximum AI retries:
1-2
```

Avoid infinite retries.

## 38. Rate Limiting

Production API should implement rate limiting.

Protect:

- Login
- Registration
- Scan creation
- AI generation
- Report generation

Example:

```
Scan creation:
10 requests/minute/user
```

Exact limits may be adjusted after testing.

## 39. Scan Concurrency

Limit simultaneous scans.

Example:

```
Per user:
2 concurrent scans

Global:
10 concurrent scans
```

The actual values depend on server capacity.

## 40. Resource Limits

Each scan should have:

- Network timeout
- Maximum response size
- Maximum redirects
- Maximum processing time
- Maximum HTML size
- Maximum extracted resources

This prevents resource exhaustion.

## 41. Filesystem Security

The scanner should not write arbitrary user-controlled paths.

Use a dedicated temporary directory.

Example:

```
/tmp/security-auditor/
```

Temporary files should be removed after processing.

## 42. Application Permissions

Run the application as a non-root user.

Example:

```
security-auditor
```

Avoid:

```
root
```

for FastAPI and scanner processes.

## 43. Systemd Service

For a traditional Linux deployment, use systemd.

Example:

```ini
[Unit]
Description=Web Security Auditor API
After=network.target

[Service]
User=security-auditor
WorkingDirectory=/opt/security-auditor
EnvironmentFile=/opt/security-auditor/.env
ExecStart=/opt/security-auditor/venv/bin/gunicorn \
    app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -w 2 \
    -b 127.0.0.1:8000

Restart=always

[Install]
WantedBy=multi-user.target
```

## 44. Worker Service

The scanner worker should have its own service.

Example:

```ini
[Unit]
Description=Web Security Auditor Scanner Worker
After=network.target

[Service]
User=security-auditor
WorkingDirectory=/opt/security-auditor
EnvironmentFile=/opt/security-auditor/.env
ExecStart=/opt/security-auditor/venv/bin/python \
    -m app.workers.scanner_worker

Restart=always

[Install]
WantedBy=multi-user.target
```

## 45. Service Management

Start:

```
sudo systemctl start security-auditor
```

Enable at boot:

```
sudo systemctl enable security-auditor
```

Check:

```
sudo systemctl status security-auditor
```

Restart:

```
sudo systemctl restart security-auditor
```

## 46. Logs

Application logs should include:

- Timestamp
- Request ID
- Scan ID
- User ID where appropriate
- Component
- Event
- Duration
- Result

Avoid sensitive information.

## 47. Log Levels

Recommended:

```
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Production default:

```
INFO
```

Debug logging should not expose secrets.

## 48. Security Event Logging

Record important security events:

- Authentication failure
- Authorization failure
- SSRF blocked
- Invalid scan target
- Rate limit triggered
- AI safety rejection
- Unexpected scanner failure

Example:

```
SECURITY_EVENT
event=SSRF_BLOCKED
request_id=req_xxx
scan_id=scan_xxx
```

## 49. Request IDs

Every API request should have a request identifier.

Example:

```
req_01HXXXX
```

The ID should appear in:

- Response header
- Application logs
- Error messages

This helps debugging.

## 50. Health Endpoint

The API must expose:

```
GET /api/v1/health
```

Example:

```json
{
  "status": "ok"
}
```

This checks whether the application process is alive.

## 51. Readiness Endpoint

The application should expose:

```
GET /api/v1/health/ready
```

It should verify important dependencies.

Example:

```
FastAPI
   |
   +-- MySQL
   |
   +-- Worker
```

A dependency failure should be reported appropriately.

## 52. Health Check Security

Health endpoints should not expose:

- Database passwords
- Connection strings
- API keys
- Internal infrastructure details
- Stack traces

Only return safe operational information.

## 53. Monitoring

Recommended monitoring:

- CPU
- RAM
- Disk
- API latency
- Error rate
- Scan queue
- Active scans
- Worker failures
- Database connections
- AI failures

For the hackathon MVP, basic system monitoring is sufficient.

## 54. Disk Monitoring

Monitor disk usage because logs, temporary files, reports and
database backups can consume storage.

Alert when usage reaches a configured threshold.

Example:

```
Disk > 80%
    |
WARNING
```

## 55. Database Monitoring

Monitor:

- Connection count
- Slow queries
- Database size
- Failed queries
- Lock waits
- Backup status

## 56. AI Monitoring

Track:

- AI requests
- Successful responses
- Failures
- Timeouts
- Latency
- Token usage
- Fallback usage

Do not log AI secrets.

## 57. Deployment Pipeline

Recommended deployment process:

```
Developer
   |
Git Push
   |
Tests
   |
Security Checks
   |
Build
   |
Deploy
   |
Migration
   |
Health Check
   |
Live
```

## 58. Pre-Deployment Checklist

Before deployment:

- [ ] Tests passing
- [ ] Security tests passing
- [ ] Environment variables configured
- [ ] Database backup completed
- [ ] Migration reviewed
- [ ] TLS certificate valid
- [ ] Nginx configuration tested
- [ ] Worker configured
- [ ] Rate limits configured
- [ ] Logging configured

## 59. Deployment Steps

Typical deployment:

```
git pull
```

Create/update environment:

```
cp .env.example .env
```

Install dependencies:

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run migrations:

```
alembic upgrade head
```

Restart services:

```
sudo systemctl restart security-auditor
sudo systemctl restart security-auditor-worker
```

Verify:

```
curl https://auditor.example.com/api/v1/health
```

## 60. Production Dependency Installation

Use pinned or controlled versions.

Example:

```
fastapi==<tested-version>
uvicorn==<tested-version>
gunicorn==<tested-version>
sqlalchemy==<tested-version>
alembic==<tested-version>
pymysql==<tested-version>
```

Do not blindly deploy untested dependency upgrades.

## 61. Dependency Security

Regularly review dependencies for:

- Known vulnerabilities
- Unsupported versions
- Malicious packages
- Unnecessary dependencies

Only install required packages.

## 62. Git Deployment Rules

Never deploy directly from unreviewed local changes.

Recommended:

```
Feature Branch
    |
Pull Request
    |
Tests
    |
Review
    |
Main
    |
Production
```

## 63. Versioning

Tag stable releases.

Example:

```
v1.0.0
v1.1.0
v1.2.0
```

This makes rollback easier.

## 64. Rollback

If deployment fails:

```
Current Release
      |
Failure
      |
Previous Stable Release
```

Rollback should restore:

- Application code
- Compatible database state
- Worker version
- Frontend assets

## 65. Database Rollback Warning

Database migrations can be more difficult to roll back than
application code.

Before migration:

```
Database Backup
```

For destructive migrations:

```
Backup
+
Migration Review
+
Test Restore
```

## 66. Zero-Downtime Considerations

For a small hackathon deployment, brief downtime is acceptable.

For production:

```
Load Balancer
     |
+----+----+
|         |
API 1    API 2
```

allows rolling deployments.

## 67. Docker Deployment

Docker may be used for reproducible deployment.

Example architecture:

```
Docker
 |
 +-- nginx
 +-- api
 +-- worker
 +-- mysql
```

For production, managed MySQL can be used instead of a MySQL
container.

## 68. Docker API Example

Conceptual Dockerfile:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app.main:app",
     "-k", "uvicorn.workers.UvicornWorker",
     "-w", "2",
     "-b", "0.0.0.0:8000"]
```

The exact Python version should match the tested application version.

## 69. Docker Security

Containers should:

- Run as non-root
- Use minimal base images
- Avoid unnecessary packages
- Use read-only filesystem where practical
- Limit CPU
- Limit memory
- Store secrets outside the image

Never place secrets inside the Dockerfile.

## 70. Docker Compose

Development may use:

```
docker-compose
    |
    +-- api
    +-- worker
    +-- mysql
```

Example:

```yaml
services:

  api:
    build: .
    depends_on:
      - mysql

  worker:
    build: .
    depends_on:
      - mysql

  mysql:
    image: mysql:8
```

Production configuration should be hardened before use.

## 71. Frontend Deployment

If static frontend files are served by Nginx:

```
frontend/
    |
    +-- index.html
    +-- dashboard.html
    +-- css/
    +-- js/
```

Nginx serves these files directly.

## 72. Frontend API Configuration

Do not hardcode environment-specific API URLs throughout the
JavaScript code.

Use a centralized configuration.

Example:

```js
const API_BASE_URL = "/api/v1";
```

This allows the frontend and backend to share the same domain.

## 73. Same-Origin Deployment

Recommended:

```
https://auditor.example.com
       |
       +-- /
       |   Frontend
       |
       +-- /api/
           FastAPI
```

Advantages:

- Simpler CORS
- Easier authentication
- Cleaner deployment
- Fewer browser security complications

## 74. Production Authentication

Authentication must use secure mechanisms.

If cookie-based authentication is used:

```
Secure
HttpOnly
SameSite
```

must be configured appropriately.

If token-based authentication is used, follow the project's
authentication specification.

## 75. Session Security

Sessions must:

- Expire appropriately
- Be invalidated on logout
- Not contain unnecessary data
- Not be exposed to JavaScript when HttpOnly cookies are used

## 76. Firewall

Only required ports should be exposed.

Typical public ports:

```
80
443
```

Potentially:

```
22
```

for restricted SSH administration.

Do not expose:

```
3306
8000
8001
```

publicly unless there is a specific secured requirement.

## 77. SSH Security

For Linux administration:

- Disable password authentication where practical
- Use SSH keys
- Restrict SSH access
- Avoid root login
- Use firewall rules
- Monitor failed login attempts

## 78. Network Segmentation

Recommended:

```
Internet
   |
Nginx
   |
API
   |
Worker
   |
MySQL
```

MySQL should not be directly reachable from the Internet.

## 79. Scanner Isolation

The scanner is the highest-risk component because it initiates
outbound network connections.

Therefore:

```
API
 |
Worker
 |
SSRF Protection
 |
Target
```

The worker must never accept arbitrary network destinations
without validation.

## 80. Production SSRF Protection

Production deployment must maintain all SSRF protections from
SECURITY.md.

These include:

- Scheme validation
- Host validation
- DNS validation
- IP classification
- Private IP blocking
- Loopback blocking
- Link-local blocking
- Metadata endpoint blocking
- Redirect validation
- Port restrictions
- Connection timeouts

## 81. Scanner Egress Controls

Where infrastructure allows it, restrict outbound traffic.

Recommended:

```
Worker
  |
Allowed external HTTP/HTTPS
```

The worker should not have unrestricted access to internal
infrastructure.

Application-level SSRF protection remains mandatory even when
network controls exist.

## 82. Production Logging Privacy

Do not log complete:

- Cookie headers
- Authorization headers
- Passwords
- API keys
- Database URLs
- AI API keys

Use redaction:

```
Authorization: [REDACTED]
Cookie: [REDACTED]
```

## 83. Error Handling

Production errors should be safe.

User sees:

```
Something went wrong.

Request ID:
req_xxxxx
```

Logs contain the detailed internal error.

Never return:

- Traceback
- SQL query
- Database password
- Filesystem path

to the user.

## 84. Maintenance Mode

For major maintenance, the frontend may display:

```
Scheduled Maintenance

The security auditor is temporarily unavailable.

Please try again later.
```

Existing scan results should remain available when possible.

## 85. Graceful Shutdown

The API and worker should handle shutdown gracefully.

When stopping:

```
SIGTERM
   |
Stop accepting new work
   |
Finish or safely cancel current work
   |
Close DB connections
   |
Exit
```

Do not abruptly terminate active operations unless required.

## 86. Scanner Cleanup

After every scan:

```
Temporary resources
      |
Cleanup
```

Ensure:

- Network connections closed
- Temporary files deleted
- Database sessions closed
- Worker resources released

## 87. Production Smoke Test

After deployment:

1. Open application
2. Login
3. Start authorized demo scan
4. Verify scan status
5. Verify findings
6. Verify risk score
7. Verify AI summary
8. Verify report
9. Verify logout

## 88. Health Verification

After restart:

```
curl https://auditor.example.com/api/v1/health
```

Expected:

```json
{
  "status": "ok"
}
```

Then:

```
curl https://auditor.example.com/api/v1/health/ready
```

Expected healthy dependency status.

## 89. Nginx Verification

Before reload:

```
sudo nginx -t
```

Only reload after configuration validation succeeds.

```
sudo systemctl reload nginx
```

## 90. Service Verification

Check:

```
sudo systemctl status security-auditor
sudo systemctl status security-auditor-worker
sudo systemctl status nginx
```

All required services must be running.

## 91. Deployment Failure Handling

If the application fails after deployment:

```
Check logs
   |
Check health endpoint
   |
Check database
   |
Check worker
   |
Check Nginx
   |
Rollback if required
```

Do not repeatedly restart services without identifying the cause.

## 92. Incident Response

For a security incident:

1. Identify affected component.
2. Restrict access if necessary.
3. Preserve relevant logs.
4. Stop malicious activity.
5. Rotate compromised credentials.
6. Patch the vulnerability.
7. Test the fix.
8. Deploy the fix.
9. Review impact.
10. Add a regression test.

## 93. Secret Rotation

Secrets should be rotatable.

Potential rotation targets:

- Database password
- Application secret
- AI API key
- Authentication signing key

After rotation:

```
Update Secret
     |
Restart Required Services
     |
Health Check
```

## 94. Production Data Retention

Define retention for:

- Scan results
- Reports
- Audit logs
- AI explanations
- Application logs

Only retain data for as long as necessary.

## 95. Scan Data Privacy

Scan results may contain technical information about websites.

Therefore:

- Restrict access
- Protect database
- Avoid unnecessary public exposure
- Redact sensitive evidence
- Delete data according to retention policy

## 96. AI Provider Security

If an external AI provider is used:

- Keep API key server-side
- Never expose it to frontend
- Send only sanitized data
- Use HTTPS
- Apply provider-specific privacy controls
- Handle provider failure safely

The browser must never call the AI provider directly using
the server's secret key.

## 97. Production Architecture Summary

```
                    Internet
                       |
                     HTTPS
                       |
                     Nginx
                    /     \
             Frontend     API
                           |
                    Authentication
                           |
                      Scan Manager
                           |
                        Worker
                           |
                    SSRF Protection
                           |
                  TLS / HTTP Scanner
                           |
                     Finding Engine
                           |
                      Risk Engine
                      /        \
                   MySQL        AI
                      \        /
                        Report
```

## 98. Minimum Production Stack

For the hackathon MVP:

- Ubuntu VPS
- Nginx
- FastAPI
- Uvicorn/Gunicorn
- Python
- MySQL 8.x
- Scanner Worker
- AI Provider
- HTTPS
- systemd

This is sufficient for a strong demonstration.

## 99. Recommended Production Hardening

Before real-world use:

- [ ] HTTPS enforced
- [ ] Firewall enabled
- [ ] SSH hardened
- [ ] Database private
- [ ] Non-root application user
- [ ] Secrets externalized
- [ ] Rate limiting enabled
- [ ] SSRF protection verified
- [ ] Worker isolation enabled
- [ ] Backups configured
- [ ] Backup restoration tested
- [ ] Logs protected
- [ ] Monitoring configured
- [ ] Dependency security review complete
- [ ] Incident response process defined

## 100. Deployment Definition of Done

Deployment is complete when:

- [ ] Frontend is accessible
- [ ] HTTPS works
- [ ] HTTP redirects to HTTPS
- [ ] FastAPI is running
- [ ] Worker is running
- [ ] MySQL is connected
- [ ] Alembic migrations are applied
- [ ] Health endpoint works
- [ ] Readiness endpoint works
- [ ] Authentication works
- [ ] Scan creation works
- [ ] Scanner worker processes scans
- [ ] Findings are stored
- [ ] Risk score is generated
- [ ] AI explanation works
- [ ] AI fallback works
- [ ] Reports work
- [ ] Logs work
- [ ] Rate limits work
- [ ] SSRF protections are active
- [ ] Database backup exists
- [ ] Rollback procedure is documented

## 101. Final Deployment Principle

The production system should follow:

```
Secure by Design
      +
Least Privilege
      +
Defense in Depth
      +
Observable
      +
Recoverable
```

The most important infrastructure rule is:

```
The scanner must never become a bridge from the public Internet
into the application's private infrastructure.
```

Production deployment must therefore preserve the same security
boundaries defined during application development.

## 102. Final Architecture Rule

```
Internet
   |
Nginx
   |
API
   |
Worker
   |
Validated Target
```

Never:

```
Internet
   |
API
   |
Unrestricted Network Access
```

The deployment is successful only when the application remains
secure not just during normal operation, but also during failures,
unexpected input, service outages and malicious scanning targets.