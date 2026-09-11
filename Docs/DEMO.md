# AI-Powered Web Security Configuration Auditor
## Hackathon Demonstration Guide

---

## 1. Purpose

This document defines the official demonstration flow for the
AI-Powered Web Security Configuration Auditor.

The demo must clearly prove that the system can:

1. Accept a target web URL.
2. Validate the target safely.
3. Prevent SSRF and unauthorized internal access.
4. Inspect TLS configuration.
5. Inspect HTTP security configuration.
6. Detect security weaknesses.
7. Generate deterministic findings.
8. Calculate a risk score.
9. Store scan results.
10. Use AI to explain findings.
11. Generate a security report.

The primary demo principle is:

> Deterministic security analysis produces the truth.
> AI explains the truth.

---

## 2. Judge Narrative

The presentation should follow this story:

```
Target URL
    |
    v
Safe Validation
    |
    v
Security Scan
    |
    v
Findings
    |
    v
Risk Score
    |
    v
AI Explanation
    |
    v
Security Report
```

The system should be presented as a practical security
configuration auditing platform rather than an AI chatbot.

## 3. Demo Environment

Recommended environment:

| Component | Technology |
|---|---|
| Frontend | HTML / CSS / JavaScript |
| Backend | FastAPI |
| Database | MySQL 8.x |
| Scanner | Python |
| AI | Configured AI provider |
| Web Server | Nginx |
| OS | Ubuntu 22.04 / 24.04 |
| Browser | Chrome / Edge |

For development demonstration, the application may run locally.

For the final hackathon presentation, the application should
preferably run from a controlled server or local network.

## 4. Demo Target Policy

Only scan:

- A system owned by the team
- A deliberately vulnerable demo application
- A controlled test server
- A target where scanning authorization exists

Do not use the demo to scan:

- Random public websites
- Banking systems
- Government infrastructure
- Internal corporate systems
- Private IP addresses
- Cloud metadata services
- Third-party infrastructure without permission

The demo target should be intentionally configured with
known security weaknesses.

## 5. Recommended Demo Target

The best demonstration uses a controlled website containing
several intentionally weak configurations.

Example:

```
https://demo-target.example
```

The demo target may contain:

- Missing Content-Security-Policy
- Missing HSTS
- Missing Referrer-Policy
- Missing Permissions-Policy
- Missing X-Content-Type-Options
- Weak cookie configuration
- HTTP-to-HTTPS configuration weakness
- Weak TLS configuration
- Certificate configuration issue
- Unnecessary redirect
- Mixed-content references

The exact findings must match the scanner's implemented rules.

Do not manually fake scanner results.

## 6. Pre-Demo Checklist

Before presenting, verify the following.

**Application**
- [ ] Frontend loads correctly.
- [ ] Backend is running.
- [ ] Database is available.
- [ ] API health endpoint works.
- [ ] Readiness endpoint works.
- [ ] Authentication works.
- [ ] Scan creation works.
- [ ] Scan status updates correctly.
- [ ] Findings are displayed.
- [ ] Risk score is displayed.
- [ ] AI summary works.
- [ ] Report generation works.

**Scanner**
- [ ] Demo target is reachable.
- [ ] TLS inspection works.
- [ ] HTTP inspection works.
- [ ] Header inspection works.
- [ ] Cookie inspection works.
- [ ] Redirect inspection works.
- [ ] Finding generation works.
- [ ] Risk calculation works.

**Security**
- [ ] Localhost scanning is blocked.
- [ ] Private IP scanning is blocked.
- [ ] Cloud metadata scanning is blocked.
- [ ] Unsafe redirects are blocked.
- [ ] Scan timeout works.
- [ ] Response size limits work.

**AI**
- [ ] AI provider credentials are configured.
- [ ] AI explanation endpoint works.
- [ ] AI failure fallback works.
- [ ] AI cannot modify severity.
- [ ] AI cannot modify risk score.

## 7. Recommended Demo Duration

Target duration:

| Section | Time |
|---|---|
| Problem | 30 sec |
| Architecture | 30 sec |
| Scan | 60 sec |
| Findings | 45 sec |
| AI Explanation | 30 sec |
| SSRF Protection | 30 sec |
| Report | 30 sec |
| Closing | 15 sec |
| **Total** | **~4 min** |

The live demo should remain below 5 minutes.

## 8. Demo Flow

### Step 1 - Introduce the Problem

Opening statement:

```
Modern websites may use HTTPS and still contain serious
security configuration weaknesses.
```

Examples include:

- Missing security headers
- Weak TLS configuration
- Insecure cookies
- Unsafe redirects
- Mixed content
- Misconfigured HTTPS

The problem is that these weaknesses are often difficult to
identify manually.

## 9. Step 2 - Introduce the Solution

Say:

```
Our solution is an AI-powered Web Security Configuration
Auditor that automatically inspects a website's TLS and
HTTP security configuration.
```

Then emphasize:

```
The scanner itself is deterministic. AI is only used to
explain the technical findings in human-readable language.
```

This distinction is important.

## 10. Step 3 - Show the Dashboard

Open the application dashboard.

Show:

- Total scans
- Recent scans
- Risk distribution
- Critical findings
- High findings
- Medium findings
- Low findings

The dashboard should immediately communicate:

```
Security
Overview
   |
   +-- Scans
   +-- Findings
   +-- Risk
   +-- Reports
```

Do not spend too much time on dashboard design.

The scanner is the main feature.

## 11. Step 4 - Create a Scan

Navigate to:

```
New Scan
```

Enter the authorized demo URL.

Example:

```
https://demo-target.example
```

Click:

```
Start Scan
```

The UI should show:

```
Queued
  |
  v
Running
  |
  v
Completed
```

If the scan fails:

```
Running
  |
  v
Failed
```

The user must never see a false `"Completed"` state.

## 12. Step 5 - Explain the Scan Pipeline

While the scan is running, explain:

```
URL
 |
 v
Validation
 |
 v
SSRF Protection
 |
 v
TLS Scanner
 |
 v
HTTP Scanner
 |
 v
Finding Engine
 |
 v
Risk Engine
 |
 v
Database
```

Important explanation:

```
Every finding comes from deterministic security rules.

The AI is not involved in deciding whether a vulnerability
exists.
```

## 13. Step 6 - Show Scan Results

After completion, open the scan result.

Display:

- Target
- Scan status
- Start time
- Completion time
- Risk score
- Risk level
- Finding count

Example presentation:

```
Security Risk

Score: <calculated-score>
Level: <calculated-level>

Critical: <count>
High:     <count>
Medium:   <count>
Low:      <count>
```

Do not hard-code the final score in the UI.

The score must come from the risk engine.

## 14. Step 7 - Show Findings

Open the findings section.

Recommended finding structure:

```
Finding
--------------------------------
Title:
Missing Content-Security-Policy

Severity:
High

Category:
HTTP Security Headers

Evidence:
CSP header was not detected.

Recommendation:
Configure an appropriate CSP.
```

Each finding should provide:

- Title
- Severity
- Category
- Description
- Evidence
- Recommendation
- Confidence
- Detection rule

## 15. Finding Categories

The demo may show findings from categories such as:

**TLS**
- Certificate validity
- Certificate hostname
- Certificate chain
- TLS protocol support
- Weak TLS configuration

**HTTP Headers**
- Content-Security-Policy
- Strict-Transport-Security
- X-Content-Type-Options
- Referrer-Policy
- Permissions-Policy

**Cookies**
- Secure flag
- HttpOnly flag
- SameSite configuration
- Sensitive cookie exposure

**Redirects**
- HTTP-to-HTTPS behavior
- Unsafe redirects
- Redirect chain issues

**Content**
- Mixed content
- Unsafe third-party resources
- Security-relevant HTML configuration

## 16. Step 8 - Explain Deterministic Risk Scoring

Show the risk score.

Explain:

```
The risk engine evaluates findings using predefined,
deterministic rules.
```

Conceptually:

```
Finding
   |
   v
Severity
   |
   v
Impact
   |
   v
Risk Calculation
   |
   v
Final Score
```

The same scan result must produce the same score.

AI must not modify:

- Finding severity
- Finding confidence
- Risk score
- Detection result

## 17. Step 9 - Demonstrate AI Explanation

Open:

```
AI Summary
```

The AI should transform technical findings into a readable
security explanation.

Example:

```
Security Summary

The website has several HTTP security configuration
weaknesses. The most important issue is the absence of
Content-Security-Policy, which reduces protection against
certain classes of browser-side attacks.

Recommended actions include configuring CSP, enabling
appropriate security headers, and reviewing cookie
security attributes.
```

The AI should explain findings that already exist.

It must not invent additional vulnerabilities.

## 18. AI Architecture

The correct AI flow is:

```
Scanner
   |
   v
Findings
   |
   v
Risk Engine
   |
   +------> Database
   |
   v
AI Context
   |
   v
AI Explanation
```

Incorrect architecture:

```
URL
 |
 v
AI
 |
 v
"Maybe Vulnerable"
```

The second architecture must never be used.

## 19. Step 10 - Demonstrate SSRF Protection

This is one of the strongest security demonstrations.

Attempt to scan:

```
http://127.0.0.1
```

Expected result:

```
Scan Rejected

Reason:
Target resolves to a blocked local address.
```

Then demonstrate another blocked target:

```
http://169.254.169.254
```

Expected result:

```
Scan Rejected

Reason:
Target matches a blocked cloud metadata address.
```

The scanner must not make the request.

## 20. Why SSRF Protection Matters

Explain:

```
A web scanner accepts URLs from users. Without SSRF
protection, an attacker could use the scanner as a bridge
into internal infrastructure.
```

For example:

```
Attacker
   |
   v
Scanner
   |
   X
Private Network
```

Our design prevents that.

Correct behavior:

```
User URL
   |
   v
Validation
   |
   X
Blocked Target
```

## 21. Step 11 - Demonstrate Redirect Protection

If supported by the implementation, use a controlled
redirect test.

Example:

```
Demo URL
   |
   v
Redirect
   |
   v
Private IP
```

Expected result:

```
Redirect blocked
```

Explain:

```
SSRF protection is applied not only to the original URL,
but also to redirect destinations.

This prevents attackers from bypassing the initial URL
validation.
```

## 22. Step 12 - Show Report Generation

Open:

```
Report
```

The report should contain:

- Target information
- Scan metadata
- Risk summary
- Finding summary
- Detailed findings
- Evidence
- Recommendations
- AI-generated explanation
- Scan timestamp

The report should be suitable for:

- Developers
- Security teams
- System administrators
- Management

## 23. Recommended Report Story

The report should communicate:

```
What is wrong?
       |
       v
Why does it matter?
       |
       v
What evidence proves it?
       |
       v
How should it be fixed?
```

This makes the scanner useful beyond a simple
`"vulnerability found"` message.

## 24. Optional Before/After Demo

If time allows, demonstrate remediation.

**Before**

```
Weak Configuration
       |
       v
Scan
       |
       v
Findings
       |
       v
Higher Risk
```

Then fix the controlled demo server.

**After**

```
Improved Configuration
       |
       v
Scan Again
       |
       v
Fewer Findings
       |
       v
Lower Risk
```

This is one of the strongest possible demonstrations because
it proves that the scanner responds to real configuration
changes.

## 25. Demo Comparison

| Before | After |
|---|---|
| Weak headers | Secure headers |
| Insecure cookies | Secure cookies |
| Weak TLS | Strong TLS |
| More findings | Fewer findings |
| Higher risk | Lower risk |
| More recommendations | Fewer recommendations |

Only show this comparison if the demo target is fully
controlled.

## 26. Failure Demonstration

The system should also handle failures correctly.

Possible failures:

- Target unavailable
- DNS failure
- TLS handshake failure
- Timeout
- AI unavailable
- Database unavailable
- Invalid URL

Example:

```
Scan
 |
 v
Target Unavailable
 |
 v
Scan Failed
```

The system must not convert an infrastructure failure into
a false security finding.

## 27. AI Failure Fallback

If the AI provider becomes unavailable:

```
Scanner
   |
   v
Findings
   |
   v
Risk Score
   |
   v
Report
```

The scan must still complete.

Only the AI explanation should become unavailable.

Example:

```
AI Summary unavailable.

Deterministic scan results remain available.
```

This demonstrates that AI is not a single point of failure.

## 28. Database Demonstration

If judges ask where scan information is stored, explain:

```
User
 |
 v
Scan
 |
 +-- TLS Result
 +-- HTTP Result
 +-- Findings
 +-- Risk Score
 +-- AI Summary
 +-- Audit Data
```

MySQL stores the persistent scan information.

Do not expose database credentials during the demo.

## 29. Architecture Explanation for Judges

Use this short explanation:

```
The frontend communicates with FastAPI.
FastAPI validates requests and controls authorization.
The scan manager starts an isolated scan.
SSRF protection validates every destination.
Deterministic scanners inspect TLS, HTTP and content.
The finding engine converts observations into findings.
The risk engine calculates the security score.
MySQL stores the results.
Finally, AI explains the already verified findings.
```

## 30. Key Differentiators

The following points should be emphasized.

### 30.1 Deterministic Security Engine

The security decision does not depend on an LLM.

```
Rules -> Findings -> Risk
```

This improves:

- Repeatability
- Auditability
- Reliability
- Explainability

### 30.2 AI as an Explanation Layer

AI makes technical results easier to understand.

```
Security Data
     |
     v
AI
     |
     v
Human-readable Explanation
```

AI does not become the security authority.

### 30.3 SSRF-First Architecture

Because the product itself performs network requests,
SSRF is treated as a first-class security problem.

The scanner protects:

- Localhost
- Private IPv4
- Local IPv6
- Link-local addresses
- Cloud metadata endpoints
- Unsafe redirects
- DNS rebinding scenarios

### 30.4 Actionable Findings

The system provides:

```
Problem
  +
Evidence
  +
Impact
  +
Recommendation
```

Instead of only:

```
VULNERABLE
```

### 30.5 Full Scan Lifecycle

The platform provides:

```
Create
  |
Scan
  |
Analyze
  |
Score
  |
Explain
  |
Report
```

This makes it closer to a real security product.

## 31. Judge Talking Points

Use these points during the presentation.

**Problem** — HTTPS alone does not guarantee a secure web configuration.

**Solution** — We automatically audit TLS and HTTP security configuration.

**Security** — The scanner itself is protected against SSRF and unsafe destinations.

**AI** — AI explains deterministic findings instead of inventing them.

**Risk** — Risk scoring is deterministic and reproducible.

**Reporting** — Findings contain evidence and actionable remediation.

**Reliability** — AI failure does not invalidate the underlying scan.

**Scalability** — Scanning is separated from the API layer and can be
processed asynchronously.

## 32. Likely Judge Questions

**Q1. Why use AI?**

Answer: AI improves the usability of security results by translating
technical findings into understandable explanations and
remediation guidance.

**Q2. Can AI create a false vulnerability?**

Answer: It should not. The authoritative findings come from the
deterministic scanner and finding engine. AI receives those
findings as context and is explicitly constrained not to
create or modify security results.

**Q3. What happens if the AI service goes down?**

Answer: The deterministic scanner continues working. Findings,
risk scores and reports remain available. Only the AI
explanation becomes unavailable.

**Q4. How do you prevent SSRF?**

Answer: User-controlled URLs are validated before any network
connection. Local, private, loopback, link-local and cloud
metadata destinations are blocked. Redirect destinations
are validated again.

**Q5. Can the scanner attack internal networks?**

Answer: The scanner is explicitly designed not to connect to
blocked private or local destinations. Network egress and
target validation are part of the security architecture.

**Q6. How is the risk score calculated?**

Answer: The risk engine applies deterministic scoring rules to
verified findings. The same findings produce the same score.

**Q7. Why not let AI perform the entire scan?**

Answer: LLM output is probabilistic. Security decisions require
repeatability and evidence. Therefore, we use deterministic
scanners for security decisions and AI only for explanation.

**Q8. What technologies are used?**

Answer: FastAPI and Python on the backend, MySQL for persistence,
HTML/CSS/JavaScript for the frontend, and an AI provider
for controlled explanation generation.

**Q9. Can this work on multiple websites?**

Answer: Yes. The architecture is URL-driven and supports multiple
authorized scan targets while enforcing validation,
authorization and resource limits.

**Q10. Can it be extended?**

Answer: Yes. New deterministic scanners can be added for additional
TLS, HTTP, cookie and web security checks without changing
the core architecture.

## 33. What NOT to Demonstrate

Never demonstrate:

- Scanning random websites
- Scanning government systems
- Scanning banking systems
- Scanning private company infrastructure
- Exploiting vulnerabilities
- Credential attacks
- Brute force
- Port scanning outside the defined scope
- Data extraction
- Cloud metadata retrieval
- Bypassing SSRF controls

The project is a defensive configuration auditor.

## 34. Demo Safety Rule

Use:

```
Controlled Target
      |
      v
Authorized Scan
      |
      v
Security Analysis
```

Never:

```
Unknown Target
      |
      v
Aggressive Scanning
```

The goal is to demonstrate security auditing, not offensive
exploitation.

## 35. Screenshot Plan

Recommended screenshots for the final presentation:

**Screenshot 1 — Dashboard**

Show:
- Scan count
- Risk summary
- Recent scans

**Screenshot 2 — New Scan**

Show:
- Target URL input
- Scan button

**Screenshot 3 — Scan Progress**

Show:
```
Queued -> Running -> Completed
```

**Screenshot 4 — Findings**

Show:
- Severity
- Finding title
- Evidence
- Recommendation

**Screenshot 5 — Risk Summary**

Show:
- Score
- Risk level
- Severity distribution

**Screenshot 6 — AI Explanation**

Show:
- Executive summary
- Explanation
- Recommendations

**Screenshot 7 — SSRF Protection**

Show:
- Target rejected

without exposing sensitive infrastructure details.

**Screenshot 8 — Report**

Show:
- Scan summary
- Findings
- Recommendations

## 36. Video Demo Plan

If recording a video, follow this sequence:

```
00:00 Problem
00:30 Solution
01:00 Dashboard
01:20 Create Scan
02:00 Findings
02:45 Risk Score
03:10 AI Explanation
03:40 SSRF Protection
04:10 Report
04:40 Closing
```

Keep the cursor movement deliberate.

Avoid unnecessary navigation.

## 37. Emergency Demo Fallback

If live scanning fails during presentation:

Use a previously completed scan from the controlled demo
environment.

Show:

- Scan result
- Findings
- Risk score
- AI explanation
- Report

Then explain:

```
The live target is temporarily unavailable, so we are
showing the previously completed authorized scan result.
```

Never fake a successful live scan.

## 38. Emergency AI Fallback

If AI fails:

Show the deterministic findings and say:

```
The AI service is currently unavailable, but the core
security analysis is independent of the AI layer.
```

Then demonstrate:

```
Finding
   |
   v
Evidence
   |
   v
Risk
   |
   v
Recommendation
```

This actually reinforces the architecture.

## 39. Final 30-Second Pitch

Use the following closing:

```
Our project is an AI-powered Web Security Configuration
Auditor designed to identify hidden TLS and web security
weaknesses.

The important part is that AI does not decide whether a
website is vulnerable. Our deterministic security engine
performs the analysis, calculates the risk, and preserves
the evidence.

AI then converts those verified results into explanations
that developers and security teams can understand.

At the same time, the scanner protects itself against SSRF,
unsafe redirects and unauthorized internal access.

So the result is not just an AI demo, but a security-focused
auditing platform designed around reliability, safety and
actionable remediation.
```

## 40. Final Demo Checklist

Before starting the presentation:

- [ ] Application running
- [ ] Database connected
- [ ] Demo target available
- [ ] Authentication working
- [ ] Scan creation working
- [ ] Scanner working
- [ ] Findings working
- [ ] Risk engine working
- [ ] AI working
- [ ] Report working
- [ ] SSRF blocking verified
- [ ] Backup scan available
- [ ] Screenshots available
- [ ] Environment variables hidden
- [ ] Credentials hidden

## 41. Demo Success Criteria

The demonstration is successful if judges can clearly see:

```
Authorized URL
      |
      v
Safe Validation
      |
      v
Real Security Scan
      |
      v
Verified Findings
      |
      v
Deterministic Risk
      |
      v
AI Explanation
      |
      v
Actionable Report
```

The most important proof points are:

- The scanner detects real configuration weaknesses.
- Findings contain evidence.
- Risk scoring is deterministic.
- AI explains rather than invents.
- SSRF protection works.
- Results are persistent.
- Reports are actionable.
- The system remains useful even when AI is unavailable.

## 42. Final Principle

The project should never be presented as:

```
"AI scans websites and tells us whether they are secure."
```

Instead, present it as:

```
"A deterministic web security auditing engine enhanced
with AI-powered explanation."
```

That distinction is central to the project's technical
credibility.

## 43. Demo Architecture Summary

```
             USER
              |
              v
           FRONTEND
              |
              v
            API
              |
              v
       SAFE VALIDATION
              |
              v
       SCAN CONTROLLER
              |
              v
           SCANNER
          /       \
         v         v
       TLS        HTTP
         \         /
          v       v
         FINDINGS
             |
             v
         RISK ENGINE
          /       \
         v         v
       MySQL       AI
                    |
                    v
                SUMMARY
                    |
                    v
                 REPORT
```

## 44. Final Message

The demo should prove one simple idea:

```
Security decisions come from deterministic evidence.
AI makes that evidence easier to understand.
```

This is the core identity of the project.