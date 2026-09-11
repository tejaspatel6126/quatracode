# UI/UX Design Specification

## 1. Purpose

This document defines the complete user interface and user experience
for the AI-Powered Web Security Configuration Auditor.

The application should look like a professional cybersecurity SaaS
product rather than a simple college project.

The UI must make complex security information understandable to:

- Small business owners
- Website administrators
- Developers
- IT teams
- Security students
- Hackathon judges

---

## 2. Design Goals

The interface must prioritize:

- Clarity
- Professional appearance
- Fast navigation
- Security-focused visualization
- Responsive design
- Accessibility
- Explainability
- Minimal user confusion

The user should understand the security condition of a website within
a few seconds of opening the scan result.

---

## 3. Frontend Technology

The frontend must use:

```
HTML5
CSS3
Vanilla JavaScript
```

No frontend framework is required.

Avoid unnecessary dependencies.

Recommended structure:

```
frontend/
|
+-- index.html
+-- login.html
+-- register.html
|
+-- dashboard.html
+-- scan.html
+-- results.html
+-- findings.html
+-- report.html
|
+-- css/
|   +-- base.css
|   +-- components.css
|   +-- dashboard.css
|   +-- scan.css
|   +-- results.css
|
+-- js/
    +-- api.js
    +-- auth.js
    +-- dashboard.js
    +-- scan.js
    +-- results.js
    +-- report.js
```

## 4. Design Language

The application should follow a modern cybersecurity SaaS visual
language.

Characteristics:

- Clean
- Technical
- Professional
- Minimal
- Trustworthy
- Data-focused

Avoid:

- Cartoon-style graphics
- Excessive gradients
- Excessive animations
- Gaming-style UI
- Unnecessary neon effects
- Overloaded dashboards

## 5. Color System

Use semantic colors rather than random colors.

Example:

| Purpose | Color Meaning |
|---|---|
| Primary | Brand / navigation |
| Success | Secure / passed |
| Warning | Medium risk |
| Danger | High / critical risk |
| Neutral | Informational |
| Background | Application surface |
| Border | UI separation |

Severity colors must remain consistent throughout the application.

## 6. Severity System

Use the following severity levels:

```
CRITICAL
HIGH
MEDIUM
LOW
INFO
```

Visual meaning:

```
CRITICAL -> Immediate attention
HIGH     -> Important action
MEDIUM   -> Recommended improvement
LOW      -> Minor improvement
INFO     -> Informational
```

The same severity representation must be used in:

- Dashboard
- Findings
- Scan results
- Reports
- AI explanations

## 7. Typography

Recommended:

Primary:
Inter / system sans-serif

Monospace:
JetBrains Mono / system monospace

Use monospace fonts for:

- URLs
- HTTP headers
- TLS versions
- Technical evidence
- Code
- API information

Use normal typography for explanations.

## 8. Application Layout

Main application layout:

```
+-------------------------------+
| Header                        |
+---------+---------------------+
| Sidebar | Main Content        |
|         |                     |
|         |                     |
|         |                     |
+---------+---------------------+
```

Desktop sidebar:

- Dashboard
- New Scan
- Scan History
- Reports
- Settings

Mobile:

```
Header
   |
Content
   |
Bottom / collapsible navigation
```

## 9. Header

The header should contain:

- Application logo
- Application name
- Current page
- User profile
- Logout option

Example:

```
SecureAudit                    User
------------------------------------
Security Dashboard
```

The header should remain visually lightweight.

## 10. Sidebar

Navigation:

```
Dashboard

Scans
  New Scan
  Scan History

Reports

Settings
```

Active navigation item must be visually distinguishable.

Do not use excessive icons.

## 11. Landing Page

The landing page should immediately explain the product.

Suggested structure:

```
--------------------------------------
AI-Powered Web Security Auditor

Find hidden HTTPS and web security
configuration weaknesses.

[ Enter Website URL ]

[ Start Security Scan ]
--------------------------------------
```

Supporting text:

```
Analyze TLS, HTTP headers, cookies,
redirects and third-party content.
```

## 12. URL Input

The URL field is the primary interaction.

Example:

```
Website URL

https://example.com
```

Button:

```
Start Scan
```

Validation should happen before submission.

Invalid examples:

```
javascript:...
file://...
localhost
127.0.0.1
192.168.x.x
```

The frontend should show a friendly validation message.

Example:

```
Please enter a valid public HTTPS website.
```

Backend validation remains authoritative.

## 13. Scan Configuration

Optional scan configuration:

- Target URL
- Scan depth
- Third-party analysis
- AI explanation

For the hackathon version, keep configuration simple.

Recommended default:

```
Standard Security Scan
```

Advanced options may be added later.

## 14. Scan Start Flow

User interaction:

```
Enter URL
   |
Validate
   |
Start Scan
   |
Scan Created
   |
Progress Page
```

The UI should immediately confirm:

```
Scan started successfully.

Scan ID:
xxxxxxxx
```

## 15. Scan Progress Page

The progress page should clearly communicate that scanning is
currently running.

Example:

```
Security Scan in Progress

Target
example.com

[✓] URL validation
[✓] DNS validation
[✓] TLS analysis
[●] HTTP security analysis
[ ] Cookie analysis
[ ] Content analysis
[ ] Risk calculation
[ ] AI summary
```

The user should never think that the application is frozen.

## 16. Progress States

Each scanner stage can have:

```
PENDING
RUNNING
COMPLETED
FAILED
SKIPPED
```

Visual states:

```
✓ Completed
● Running
○ Pending
! Failed
— Skipped
```

## 17. Scan Polling

The frontend should poll:

```
GET /api/v1/scans/{scan_id}
```

Recommended polling interval:

```
2-3 seconds
```

Polling stops when:

```
COMPLETED
FAILED
CANCELLED
```

Do not continuously poll after completion.

## 18. Scan Completion

After completion:

```
Security Scan Complete

Risk Score
78 / 100

Risk Level
HIGH

[ View Results ]
```

The user should be automatically taken to the result page.

## 19. Dashboard

The dashboard is the main application screen.

Suggested layout:

```
+------------------------------------+
| Security Overview                 |
+------------------------------------+
| Risk Score | Scans | Findings     |
+------------------------------------+
| Recent Scans                      |
+------------------------------------+
| Severity Distribution             |
+------------------------------------+
```

## 20. Dashboard Metrics

Display:

- Total Scans
- Completed Scans
- High Risk Scans
- Critical Findings

Example:

```
Total Scans       24
Completed         21
High Risk          6
Critical Findings  2
```

Metrics should be compact.

## 21. Risk Score Card

Primary dashboard card:

```
Security Risk

78 / 100

HIGH
```

The score should be visually dominant.

Supporting text:

```
Based on 9 detected findings.
```

## 22. Risk Score Interpretation

Use:

```
0-19    Very Low
20-39   Low
40-59   Medium
60-79   High
80-100  Critical
```

The exact thresholds must match the backend risk engine.

The frontend must not calculate or alter the score.

## 23. Severity Summary

Example:

```
Findings

Critical    1
High        2
Medium      4
Low         2
Info        0
```

Use a simple visual distribution.

Do not rely only on color.

Severity must also be shown using text.

## 24. Recent Scans

Example table:

| Target | Score | Risk | Findings | Date |
|---|---|---|---|---|
| example.com | 78 | HIGH | 9 | Today |
| demo.site | 31 | LOW | 3 | Yesterday |
| test.org | 64 | HIGH | 6 | Yesterday |

Each scan should be clickable.

## 25. Scan Status Badge

Use:

```
COMPLETED
RUNNING
FAILED
CANCELLED
```

Example:

```
example.com    COMPLETED
demo.site      RUNNING
test.org       FAILED
```

## 26. Results Page

The results page is the most important screen.

Recommended structure:

```
Target
   |
Risk Overview
   |
Security Summary
   |
Findings
   |
AI Explanation
   |
Recommendations
```

## 27. Results Header

Example:

```
Security Scan Results

https://example.com

Scanned:
11 September 2026

Status:
COMPLETED

Actions:

[ Re-scan ]
[ Download Report ]
```

## 28. Risk Overview

Use a large risk card:

```
Overall Risk

78

HIGH

9 Findings
```

Below it:

```
1 Critical
2 High
4 Medium
2 Low
```

## 29. Security Categories

Display scan categories:

- TLS Security
- HTTP Headers
- Cookies
- Redirects
- Content Security
- Third-Party Resources

Example:

```
TLS Security          Good
HTTP Headers          Needs Attention
Cookies               Needs Attention
Redirects             Good
Content Security      Warning
Third-Party Resources Good
```

## 30. Findings List

Each finding should be represented as a card.

Example:

```
HIGH

Insecure Authentication Cookie

The Secure attribute is missing from a security-sensitive cookie.

Confidence: 97%

[ View Details ]
```

## 31. Finding Details

Expanded finding:

```
Insecure Authentication Cookie

Severity
HIGH

Confidence
97%

What was detected
The cookie does not contain the Secure attribute.

Why it matters
The cookie may be exposed if transmitted over an
unencrypted HTTP connection.

Evidence
Secure = false
HttpOnly = true
SameSite = Lax

Recommended action
Enable the Secure attribute for applicable
authentication cookies.
```

## 32. Evidence Section

Evidence should be visually separated.

Example:

```
Observed Evidence

Set-Cookie:
session_id=...;
HttpOnly;
SameSite=Lax
```

Never display sensitive cookie values.

Sensitive values must be redacted.

Example:

```
session_id=[REDACTED]
```

## 33. Technical Evidence

For HTTP headers:

```
Content-Security-Policy
Status: Missing
```

For TLS:

```
TLS 1.2
Supported: Yes

TLS 1.3
Supported: Yes
```

For redirects:

```
HTTP -> HTTPS
Status: 301
```

## 34. AI Explanation

AI content should have a clearly separate visual section.

Example:

```
AI Security Explanation

What this means
Your website is missing a browser security
policy that helps control which resources can
run on the page.

Why it matters
A strong policy can reduce the impact of certain
script injection attacks.

Recommended action
Configure an appropriate Content-Security-Policy
header.
```

Label:

```
AI Generated
```

## 35. AI Disclaimer

Use a small disclaimer:

```
AI explanations are generated from verified scan
findings. The scanner's technical findings and
risk score remain authoritative.
```

This improves transparency.

## 36. Recommendations

Display recommendations in priority order.

Example:

```
Priority Actions

1. Fix insecure authentication cookies
   Priority: HIGH

2. Add missing security headers
   Priority: MEDIUM

3. Review third-party resources
   Priority: MEDIUM
```

## 37. Finding Filters

Allow users to filter findings.

Filters:

```
All
Critical
High
Medium
Low
Info
```

Optional:

```
Category
Status
Confidence
```

Keep the default interface simple.

## 38. Search Findings

Provide:

```
Search findings...
```

Users can search by:

- Finding title
- Finding code
- Category
- Description

Example:

```
Search:
cookie

Results:

INSECURE_COOKIE
MISSING_SAMESITE
```

## 39. Empty State

If no vulnerabilities are found:

```
Security Configuration Looks Good

No significant security configuration weaknesses
were detected during this scan.

[ View Technical Results ]
```

Do not claim:

```
Your website is completely secure.
```

The scanner only checks supported security controls.

## 40. Failed Scan State

Example:

```
Scan Failed

The security scan could not be completed.

Reason:
The target did not respond within the configured
network timeout.

[ Try Again ]
```

Do not expose internal stack traces.

## 41. Cancelled Scan

Example:

```
Scan Cancelled

The scan was stopped before completion.

[ Start New Scan ]
```

## 42. Report Page

Report page should resemble a professional security assessment.

Structure:

```
Security Assessment Report

Target
Scan Date
Risk Score
Risk Level

Executive Summary

Security Findings

Technical Evidence

Recommendations

Scan Limitations
```

## 43. Report Header

Example:

```
WEB SECURITY CONFIGURATION REPORT

Target:
example.com

Risk:
HIGH

Score:
78 / 100

Generated:
11 September 2026
```

## 44. Executive Summary

Example:

```
Executive Summary

The scan identified several web security configuration
weaknesses that should be reviewed.

The highest-priority findings relate to cookie security
and browser security headers.

This report reflects the controls tested by the scanner
and does not represent a complete penetration test.
```

## 45. Scan Limitations

Always include:

```
This automated assessment checks selected TLS, HTTP,
cookie, redirect and content security controls.

It does not guarantee that the target application is
free from vulnerabilities.

Only authorized systems should be scanned.
```

## 46. Settings Page

Settings may contain:

- Account
- Security
- AI Preferences
- Scan Preferences

For hackathon MVP, settings should remain minimal.

## 47. Authentication UI

Login:

```
Welcome Back

Email
[________________]

Password
[________________]

[ Login ]
```

Register:

```
Create Account

Name
Email
Password
Confirm Password

[ Create Account ]
```

## 48. Form Validation

Validation messages must be clear.

Bad:

```
422 Unprocessable Entity
```

Good:

```
Please enter a valid email address.
```

Backend errors should be translated into user-friendly messages.

## 49. Loading States

Every asynchronous action should have a loading state.

Examples:

```
Starting scan...
Loading findings...
Generating AI explanation...
Generating report...
```

Buttons should be disabled while the corresponding action is running.

## 50. Toast Notifications

Use lightweight notifications for:

- Scan started
- Scan cancelled
- Report generated
- AI summary generated
- Scan deleted

Example:

```
✓ Scan started successfully.
```

Do not use intrusive popups for normal operations.

## 51. Modal Usage

Use modals only when confirmation is required.

Example:

```
Delete Scan?

This will permanently remove the scan
and its associated results.

[ Cancel ] [ Delete ]
```

Avoid using modals for basic information.

## 52. Responsive Design

The application must work on:

- Desktop
- Laptop
- Tablet
- Mobile

Recommended breakpoints:

```
Mobile:
< 768px

Tablet:
768px - 1024px

Desktop:
> 1024px
```

## 53. Mobile Layout

On mobile:

```
Header
   |
Risk Score
   |
Findings
   |
Recommendations
```

Tables should become cards or horizontally scrollable containers.

Do not force desktop-sized tables onto small screens.

## 54. Accessibility

The application should support:

- Keyboard navigation
- Visible focus states
- Semantic HTML
- Accessible form labels
- Sufficient text contrast
- Meaningful button labels
- Screen-reader-friendly status messages

Do not communicate information using color alone.

Example:

Bad:

```
Red = High
```

Good:

```
HIGH
```

with supporting visual styling.

## 55. Security UI Principles

Never expose:

- API keys
- Passwords
- Session tokens
- Database credentials
- Internal server IPs
- Raw exception traces

Redact sensitive technical information.

## 56. URL Display

Long URLs should be visually truncated.

Example:

```
https://example.com/very/long/path/...
```

Provide a way to view the full URL if required.

Never execute URLs directly from displayed content.

## 57. Security Evidence Redaction

Sensitive values must be masked.

Example:

```
Authorization:
Bearer [REDACTED]

Cookie:
session=[REDACTED]
```

The backend should perform redaction before sending data
to the frontend whenever possible.

## 58. AI Loading UI

When AI explanation is being generated:

```
AI Security Explanation

Analyzing verified scan findings...

[ Loading ]
```

Do not display fake progress percentages.

## 59. AI Failure UI

If AI fails:

```
AI explanation unavailable

The security findings and risk score are still available.

[ View Technical Explanation ]
```

The scan must remain useful.

## 60. Dashboard Quick Action

The dashboard should have a prominent:

```
+ New Security Scan
```

button.

This should be the primary CTA.

## 61. Navigation Rules

The user should reach important actions within a few clicks.

Recommended:

```
Dashboard -> New Scan -> Results
```

and:

```
Dashboard -> Scan History -> Results
```

## 62. Scan History

Display:

| Target | Score | Level | Status | Date |
|---|---|---|---|---|
| example.com | 78 | HIGH | Completed | Today |
| site.com | 42 | MEDIUM | Completed | Yesterday |

Actions:

- View
- Report
- Delete

## 63. Confirmation Before Delete

Deletion must require confirmation.

Example:

```
Delete this scan?

This action cannot be undone.

[ Cancel ]
[ Delete Scan ]
```

## 64. Error Page

For unexpected application errors:

```
Something went wrong.

We could not complete this request.

Request ID:
req_xxxxxxxxx

[ Return to Dashboard ]
```

The request ID helps debugging without exposing internal details.

## 65. 404 Page

Example:

```
Page Not Found

The page you requested does not exist.

[ Go to Dashboard ]
```

## 66. API Error Mapping

Frontend should map backend errors.

Example:

```
INVALID_URL
    ->
Please enter a valid website URL.

SSRF_BLOCKED
    ->
This target cannot be scanned.

SCAN_NOT_FOUND
    ->
The requested scan could not be found.

AI_UNAVAILABLE
    ->
AI explanation is temporarily unavailable.
```

## 67. Frontend State Management

Since the application uses Vanilla JavaScript, state should remain
simple.

Example:

```js
const scanState = {
    id: null,
    status: null,
    progress: null,
    results: null
};
```

Avoid creating unnecessary global state.

## 68. API Client

All API requests should go through a centralized client.

Example:

```
js/
|
+-- api.js
```

Responsibilities:

- Request creation
- Authentication handling
- JSON parsing
- Error handling
- Request ID handling

Pages should not duplicate API request logic.

## 69. Component Strategy

Reusable UI components should include:

- Navbar
- Sidebar
- Button
- Input
- Card
- Badge
- RiskCard
- FindingCard
- SeverityBadge
- Toast
- Modal
- LoadingState
- EmptyState
- ErrorState

Components can be implemented using reusable HTML/CSS/JS functions.

## 70. Risk Visualization

Use simple visualizations.

Recommended:

```
Risk Score
78 / 100
```

and:

```
████████████████░░░░
```

Do not make the visualization more important than the number.

## 71. Severity Visualization

Example:

```
Critical  █
High      ██
Medium    ████
Low       ██
Info
```

Exact chart implementation can use CSS or lightweight JavaScript.

## 72. Technical vs Human View

The results page should support two levels of information.

### Human View
- What happened?
- Why does it matter?
- What should I do?

### Technical View
- Detection
- Evidence
- Headers
- TLS details
- Cookie attributes

This allows the same application to serve both business owners
and developers.

## 73. Information Hierarchy

Every results page should follow:

```
Risk
 |
Most Important Findings
 |
Why They Matter
 |
How To Fix
 |
Technical Evidence
```

Users should not have to read raw technical data to understand
the primary security problem.

## 74. Demo Mode Consideration

For the hackathon demonstration, the UI should make the full
workflow easy to understand.

Recommended demo:

```
Landing Page
      |
Enter Target
      |
Start Scan
      |
Live Progress
      |
Risk Score
      |
Findings
      |
AI Explanation
      |
Report
```

The complete flow should be achievable quickly.

## 75. Hackathon Visual Priorities

The judges should immediately notice:

- Professional dashboard
- Real security scan
- Deterministic risk score
- Detailed findings
- AI explanation
- Remediation guidance
- Security-focused architecture

Do not hide the main result behind multiple screens.

## 76. Recommended Result Layout

Final result screen:

```
+--------------------------------------+
| Security Scan Results                |
| example.com                          |
+--------------------------------------+
|                                      |
|          78 / 100                    |
|             HIGH                     |
|                                      |
+--------------------------------------+
| 1 Critical | 2 High | 4 Medium      |
+--------------------------------------+
|                                      |
| Top Security Findings                |
|                                      |
| [HIGH] Insecure Cookie               |
| [HIGH] Missing Security Header       |
| [MED]  Third-Party Resource          |
|                                      |
+--------------------------------------+
| AI Security Explanation              |
|                                      |
| What this means...                   |
| Why it matters...                    |
| Recommended action...                |
+--------------------------------------+
```

## 77. UI Performance

The frontend should:

- Minimize unnecessary API calls
- Lazy-load large result sections
- Avoid excessive animations
- Avoid loading unnecessary libraries
- Cache static assets
- Keep JavaScript modular

The results page should remain responsive even with many findings.

## 78. Animation Guidelines

Use subtle animations only for:

- Loading
- Progress
- Toast appearance
- Card transitions

Avoid:

- Constant moving elements
- Excessive glowing effects
- Large animated backgrounds
- Distracting transitions

Cybersecurity software should feel reliable, not like a gaming website.

## 79. Browser Support

Primary support:

- Chrome
- Edge
- Firefox
- Safari

Use modern web APIs where appropriate but avoid unnecessary
browser-specific features.

## 80. Frontend Security

The frontend must:

- Escape dynamic content
- Avoid unsafe innerHTML where possible
- Sanitize rendered user-controlled text
- Avoid storing sensitive credentials unnecessarily
- Use secure authentication mechanisms
- Avoid exposing internal API information

Never trust scanner output simply because it came from the backend.

## 81. XSS Protection

Dynamic content must be inserted safely.

Prefer:

```js
element.textContent = value;
```

instead of:

```js
element.innerHTML = value;
```

when HTML rendering is not required.

If HTML rendering is necessary, use strict sanitization.

## 82. CSRF Considerations

If cookie-based authentication is used:

- Use CSRF protection
- Use Secure cookies
- Use HttpOnly cookies
- Use SameSite appropriately

If token-based authentication is used, follow the project's
authentication architecture and avoid exposing tokens unnecessarily.

## 83. API Request UX

Every API request should handle:

- Loading
- Success
- Failure
- Timeout
- Unauthorized

Example:

```
Loading...
   |
Success -> Update UI
   |
Failure -> Friendly error
```

## 84. Authentication Expiry

If the backend returns:

```
401 Unauthorized
```

the frontend should:

- Clear invalid local authentication state.
- Redirect to login.
- Show:

```
Your session has expired. Please log in again.
```

## 85. Security Report Download

The report button:

```
Download Report
```

should request the backend-generated report.

Example:

```
GET /api/v1/scans/{scan_id}/report
```

The frontend should not independently reconstruct security findings
for the downloadable report.

## 86. Print-Friendly Report

The report page should support printing.

Use CSS:

```css
@media print {
    .sidebar,
    .navigation,
    .action-buttons {
        display: none;
    }
}
```

The printed report should remain readable.

## 87. UI Testing

Frontend tests should cover:

- Login
- Registration
- URL validation
- Scan creation
- Scan progress
- Result loading
- Finding filters
- AI explanation
- Report generation
- Error states
- Responsive layout

## 88. Security UI Testing

Verify:

- XSS-safe rendering
- Sensitive data redaction
- Safe URL display
- Authentication expiry
- Unauthorized scan access
- Safe error messages
- No secret exposure

## 89. Design Definition of Done

The UI/UX implementation is complete when:

- [ ] Landing page implemented
- [ ] Login implemented
- [ ] Registration implemented
- [ ] Dashboard implemented
- [ ] New Scan page implemented
- [ ] Scan progress implemented
- [ ] Scan results implemented
- [ ] Findings implemented
- [ ] AI explanation implemented
- [ ] Report page implemented
- [ ] Scan history implemented
- [ ] Settings implemented
- [ ] Loading states implemented
- [ ] Error states implemented
- [ ] Empty states implemented
- [ ] Responsive layout implemented
- [ ] Accessibility basics implemented
- [ ] Sensitive evidence redaction implemented
- [ ] XSS-safe rendering implemented
- [ ] Print-friendly report implemented
- [ ] Frontend API client centralized
- [ ] Security-focused visual hierarchy implemented

## 90. Final UX Principle

The application should answer three questions immediately:

1. How secure is this website?
2. What is wrong?
3. What should I fix first?

The UI should make these answers obvious without requiring the user
to understand cybersecurity terminology.

The final product should feel like a real security SaaS platform:

```
Scan -> Understand -> Prioritize -> Fix
```

The complexity remains inside the security engine.

The user sees clarity.