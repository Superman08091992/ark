# RULES OF ENGAGEMENT (RoE)
## Security Testing Operational Guidelines

**Authorization Reference:** _____________________ (link to Authorization document)

**Date:** _____________________ (YYYY-MM-DD)

**Version:** 1.0

---

## Document Purpose

This Rules of Engagement (RoE) document defines the operational procedures, technical constraints, and tactical guidelines for security testing activities authorized under the linked Authorization document. This RoE is subordinate to and governed by the Authorization.

**Legal Status:** This document forms part of the legal agreement between the parties and must be followed strictly.

---

## 1. Scope Definition

### 1.1 In-Scope Assets (Technical Details)

**Reference:** See attached `scope.json` for machine-readable scope definition.

**IP Address Ranges:**
```
192.168.1.0/24
10.0.0.100-10.0.0.200
203.0.113.0/24
```

**Hostnames/Domains:**
```
test.example.com
*.staging.example.com (wildcard subdomains)
api-test.example.com
```

**Repositories:**
```
Repository: github.com/company/webapp
Branch: staging
Commit Range: abc123..def456 (if specific)
```

**Container Images:**
```
registry.example.com/webapp:staging
registry.example.com/api:v2.1.0
```

**Cloud Resources:**
```
AWS Account: 123456789012
Resource Tags: environment=staging, pentest=authorized
Region: us-east-1
```

**APIs & Endpoints:**
```
https://api-staging.example.com/v1/*
https://api-staging.example.com/v2/* (read-only methods only)
```

### 1.2 Explicitly Out-of-Scope

**The following are FORBIDDEN and will trigger emergency stop:**

```
# Production domains
*.example.com (except *.staging.example.com)
api.example.com
www.example.com

# Production IP ranges
203.0.113.0/23 (includes production)

# Third-party services
*.cloudfront.net (CDN - third party)
*.fastly.com (CDN - third party)

# Internal infrastructure
10.1.0.0/16 (corporate network)
172.16.0.0/12 (management network)

# Specific exclusions
database.prod.internal.example.com
backup.example.com
hr-systems.example.com
```

### 1.3 Scope Verification

**Before ANY testing activity:**
1. Verify target is in `scope.json`
2. Confirm target is within time window
3. Check exclusion list
4. Log scope verification result

**Automatic scope validation:** ☐ Enabled  ☐ Disabled (if disabled, explain: _____________)

---

## 2. Timing Constraints

### 2.1 Permitted Time Windows

**Non-Destructive Testing (Low Impact):**
- **Days:** Monday - Friday
- **Time:** 09:00 - 17:00 UTC
- **Activities:** SAST, container scans, passive reconnaissance, credentialed vulnerability scans

**Destructive Testing (High Impact):**
- **Days:** Saturday - Sunday
- **Time:** 23:00 - 05:00 UTC (overnight)
- **Activities:** Active exploitation, fuzzing, DoS testing (in lab), privilege escalation attempts
- **Approval Required:** Email confirmation from authorized signatory 24 hours before

### 2.2 Blackout Periods (NO TESTING)

**Absolute Blackout:**
```
2025-12-24 00:00 UTC - 2025-12-26 23:59 UTC (Holiday season)
2025-01-01 00:00 UTC - 2025-01-02 23:59 UTC (New Year)
[Add company-specific blackouts: quarter-end, product launches, etc.]
```

**Conditional Blackout:**
- During incident response (will be notified by emergency contact)
- During planned maintenance (calendar link: ________________)
- When system load > 80% CPU (automatic pause)

### 2.3 Time Zone Handling

**All times in this document are:** ☐ UTC  ☐ Local (specify: _________)

**Tester must:** Convert all times to UTC and log in UTC

---

## 3. Allowed Testing Methods

### 3.1 Passive Reconnaissance (Always Allowed in Scope)

- DNS enumeration (public records only)
- WHOIS lookups
- Certificate transparency logs
- Public source code review (GitHub, public repos)
- Search engine reconnaissance (Google dorking on authorized domains)
- OSINT (Open Source Intelligence) on authorized organization

**Rate Limit:** No more than 100 requests/minute per target

### 3.2 Network Scanning

**Tools Allowed:**
- nmap (all scan types)
- masscan (coordinate with ops team)
- zmap (coordinate with ops team)

**Scan Intensity:**
- **Low:** 1-10 packets/second
- **Medium:** 10-100 packets/second (business hours only)
- **High:** 100+ packets/second (maintenance window only, pre-approved)

**Scan Types Allowed:**
- ☐ TCP SYN scan
- ☐ TCP Connect scan
- ☐ UDP scan (limited ports: 53, 161, 500, 1194)
- ☐ Service version detection
- ☐ OS fingerprinting
- ☐ Script scanning (NSE scripts: safe category only)

**Scan Types Forbidden:**
- ☑ Aggressive scans during business hours
- ☑ Scans that trigger IDS/IPS alerts without prior coordination
- ☑ Scans of out-of-scope networks

### 3.3 Vulnerability Scanning

**Tools Allowed:**
- Nessus (credentialed + uncredentialed)
- OpenVAS
- Qualys (cloud-based)
- Custom scripts (must be reviewed and approved)

**Scan Profiles:**
- **Business Hours:** Safe checks only, no DoS plugins
- **Maintenance Window:** Full scans including exploit attempts

**Credentials:** Provided in secure manner (see Section 8)

### 3.4 Web Application Testing

**Tools Allowed:**
- Burp Suite Professional
- OWASP ZAP
- Nikto
- SQLMap (with caution - see limitations)
- Custom scripts (Python, Go)

**Testing Scope:**
- ☐ Authentication bypass
- ☐ Authorization flaws (IDOR, privilege escalation)
- ☐ Injection attacks (SQLi, XSS, XXE, SSRF, command injection)
- ☐ Business logic flaws
- ☐ Session management issues
- ☐ Cryptographic weaknesses
- ☐ API abuse

**Limitations:**
- **SQLMap:** Do not use `--os-shell` or `--os-pwn` without explicit approval
- **XSS:** Use harmless payloads (alert(1), no real malware)
- **File Upload:** Upload only harmless test files (txt, jpg), no webshells without approval
- **Rate Limiting:** Respect rate limits, do not DoS application

### 3.5 Container & Cloud Security

**Container Scanning:**
- Trivy (all severities)
- Grype
- Clair
- Docker Bench for Security

**Cloud Posture Assessment:**
- ScoutSuite (AWS, Azure, GCP)
- Prowler (AWS)
- CloudSploit

**Limitations:**
- ☑ Do not modify cloud resources (read-only unless explicitly authorized)
- ☑ Do not exfiltrate data from cloud storage (S3, Blob, etc.)
- ☑ Do not test shared infrastructure (multi-tenant services)

### 3.6 Active Exploitation

**⚠️ REQUIRES SEPARATE APPROVAL FOR EACH ATTEMPT**

**Pre-Exploitation Checklist:**
- ☐ Snapshot created and verified
- ☐ Isolated test environment confirmed
- ☐ Rollback plan documented
- ☐ Emergency contact notified
- ☐ Approval email received

**Allowed Exploits:**
- Proof-of-concept exploits demonstrating vulnerability
- Memory corruption exploits (buffer overflow, use-after-free)
- Privilege escalation (local)
- Remote code execution (in lab environment only)

**Forbidden Exploits:**
- ☑ Ransomware or destructive payloads
- ☑ Data exfiltration of personal information
- ☑ Lateral movement to out-of-scope systems
- ☑ Persistence mechanisms (backdoors, rootkits)
- ☑ Any exploit affecting production systems

**Exploitation Logging:**
- Every exploit attempt must be logged with: timestamp, target, exploit used, outcome
- Failed attempts must be logged
- Logs stored in immutable audit trail

### 3.7 Social Engineering

**⚠️ REQUIRES HR AND LEGAL PRE-APPROVAL**

**Allowed (with approval):**
- Phishing simulations (email-based)
- Pretexting (phone-based social engineering)
- Physical security testing (tailgating, badge cloning)

**Forbidden:**
- ☑ Bribery or coercion
- ☑ Impersonation of law enforcement or emergency services
- ☑ Harassment or intimidation
- ☑ Testing of non-employees without consent
- ☑ Disclosure of confidential information obtained through social engineering

**Reporting:**
- Report all successful social engineering attempts to HR immediately
- De-identify individuals in final report (use role/title, not names)

### 3.8 Denial of Service (DoS) Testing

**⚠️ REQUIRES EXPLICIT APPROVAL AND ISOLATED ENVIRONMENT**

**Allowed:**
- DoS testing in isolated lab environment only
- Application-layer DoS (slowloris, slow POST)
- Resource exhaustion tests

**Forbidden:**
- ☑ DoS against production systems
- ☑ Distributed DoS (DDoS)
- ☑ Network-layer DoS (SYN flood, UDP flood) against shared infrastructure
- ☑ Any DoS that affects third parties

---

## 4. Technical Constraints

### 4.1 Rate Limiting

**HTTP/HTTPS Requests:**
- Maximum: 1000 requests/minute per target
- Fuzzing: 100 requests/minute per endpoint
- Credential stuffing: 10 attempts/minute (if authorized)

**Network Traffic:**
- Low intensity: 1-10 packets/second
- Medium intensity: 10-100 packets/second (business hours)
- High intensity: 100+ packets/second (maintenance window only)

### 4.2 Resource Utilization

**Target System Thresholds (automatic pause if exceeded):**
- CPU: > 80% utilization
- Memory: > 90% utilization
- Disk I/O: > 80% utilization
- Network bandwidth: > 80% utilization

**Monitoring:** Tester must monitor target system resources and pause testing if thresholds exceeded.

### 4.3 Data Handling Limits

**Data Collection:**
- Maximum data extraction: 100 MB per test session (unless approved)
- Personal data: 0 records (unless explicit approval with legal basis)
- Credentials: Encrypted storage only, deleted after test completion

**Data Retention:**
- Evidence: 90 days after report delivery
- Logs: 1 year (audit requirement)
- Exploit code: Deleted after report delivery (unless requested to retain)

---

## 5. Prohibited Actions (Expanded)

**The following actions are STRICTLY FORBIDDEN under all circumstances:**

### 5.1 Data Manipulation

- ☑ Modifying, deleting, or encrypting production data
- ☑ Inserting malicious data into databases
- ☑ Tampering with audit logs
- ☑ Modifying user accounts (unless test accounts created specifically for pentest)

### 5.2 System Disruption

- ☑ Crashing systems or applications
- ☑ Launching DoS attacks against production
- ☑ Exhausting system resources (CPU, memory, disk, network)
- ☑ Interfering with business operations

### 5.3 Data Exfiltration

- ☑ Downloading, copying, or exfiltrating personal data (PII)
- ☑ Exfiltrating credentials (except test credentials)
- ☑ Exfiltrating proprietary business data
- ☑ Storing unencrypted sensitive data

### 5.4 Lateral Movement

- ☑ Pivoting to out-of-scope systems
- ☑ Using compromised systems as attack platforms for other targets
- ☑ Scanning internal networks not explicitly in scope

### 5.5 Persistence & Backdoors

- ☑ Installing backdoors, rootkits, or persistence mechanisms
- ☑ Creating unauthorized user accounts
- ☑ Modifying system configurations for persistence
- ☑ Leaving exploit artifacts after testing

### 5.6 Malware & Exploits

- ☑ Uploading or executing real malware
- ☑ Using ransomware or wiper malware
- ☑ Distributing exploits to third parties
- ☑ Publishing 0-day exploits before coordinated disclosure

---

## 6. Operational Procedures

### 6.1 Pre-Test Checklist

**Before EVERY test session:**

```
☐ 1. Verify authorization is valid (not expired)
☐ 2. Verify target is in scope.json
☐ 3. Verify current time is within allowed window
☐ 4. Check blackout calendar
☐ 5. Create snapshot (if destructive testing)
☐ 6. Verify rollback plan
☐ 7. Notify emergency contact (if required)
☐ 8. Enable audit logging
☐ 9. Verify emergency stop procedure
☐ 10. Confirm insurance coverage (if required)
```

### 6.2 During Testing

**Continuous Monitoring:**
- Monitor target system resources every 5 minutes
- Log all activities in real-time
- Watch for security alerts or anomalies
- Maintain communication with ops team (if required)

**Escalation Triggers:**
- Immediate escalation if out-of-scope asset accessed
- Immediate escalation if personal data discovered
- Immediate escalation if production system impacted
- Immediate escalation if security violation occurs

### 6.3 Post-Test Checklist

**After EVERY test session:**

```
☐ 1. Restore snapshots (if required)
☐ 2. Verify system integrity
☐ 3. Delete temporary files and artifacts
☐ 4. Secure evidence (encrypt and hash)
☐ 5. Update audit log with session summary
☐ 6. Notify emergency contact (if required)
☐ 7. Document findings in secure location
☐ 8. Delete credentials from testing system
☐ 9. Verify no persistence mechanisms left behind
☐ 10. Submit session report to authorized signatory
```

---

## 7. Snapshot & Rollback Procedures

### 7.1 Snapshot Requirements

**When snapshots are REQUIRED:**
- Before any active exploitation
- Before any destructive testing (fuzzing, DoS, configuration changes)
- Before testing in maintenance window

**Snapshot Method:**
- Virtual machines: VMware/Hyper-V snapshot
- Containers: Docker/Kubernetes snapshot
- Databases: Full backup + transaction log backup
- Cloud: EBS snapshot (AWS), managed disk snapshot (Azure)

**Snapshot Verification:**
- Test restore before testing begins
- Verify snapshot integrity (checksums)
- Document snapshot location and timestamp

### 7.2 Rollback Plan

**Automatic Rollback Triggers:**
- Test execution fails with critical error
- Security violation detected
- System performance degradation > 80%
- Emergency stop command issued
- Timeout exceeded (default: 4 hours per test session)

**Rollback Procedure:**
```bash
1. Pause all testing activities immediately
2. Notify emergency contact
3. Verify snapshot location: /path/to/snapshot
4. Execute rollback command: [specific command]
5. Verify system integrity: [verification steps]
6. Estimated rollback time: 30 minutes
7. Confirm rollback completion with authorized signatory
```

**Rollback Validation:**
- Compare system state before/after rollback
- Verify data integrity
- Test critical business functions
- Document rollback in audit log

---

## 8. Credentials & Access Management

### 8.1 Credential Handling

**Credential Provisioning:**
- Method: ☐ Encrypted email  ☐ Secure portal  ☐ Password manager (1Password, Keeper)
- Credentials provided: ☐ Test accounts  ☐ Read-only accounts  ☐ Admin accounts (justify: ______)

**Credential Storage:**
- Encrypted at rest: AES-256
- Encrypted in transit: TLS 1.3
- Storage location: [Specify secure password manager or encrypted vault]
- Access control: MFA required

**Credential Deletion:**
- Timing: Within 24 hours of test completion
- Method: Secure wipe (overwrite 3 times)
- Verification: Deletion confirmed by authorized signatory

### 8.2 Privileged Access

**If admin/root access is required:**
- Justification: _____________________________________
- Approval: Email from authorized signatory + security officer
- Logging: All privileged commands logged and reviewed
- MFA: Required for all privileged access

---

## 9. Communication & Escalation

### 9.1 Communication Channels

**Primary Channel:**
- Method: ☐ Slack  ☐ Email  ☐ Phone  ☐ Ticketing System
- Contact: _____________________________________
- Response SLA: _______ minutes

**Emergency Channel (24/7):**
- Method: Phone
- Primary: _____________________ (Name, Number)
- Secondary: _____________________ (Name, Number)
- Emergency keyword: "PENTEST-EMERGENCY-[AUTH-ID]"

### 9.2 Escalation Matrix

**Level 1 - Informational:**
- Trigger: Routine findings, low-severity vulnerabilities
- Action: Document in daily report
- Notification: None required

**Level 2 - Warning:**
- Trigger: Medium-severity vulnerabilities, unexpected system behavior
- Action: Notify primary contact within 4 hours
- Notification: Email

**Level 3 - Critical:**
- Trigger: High/critical vulnerabilities, active exploitation, data exposure
- Action: Notify emergency contact immediately
- Notification: Phone call + email

**Level 4 - Emergency Stop:**
- Trigger: Out-of-scope asset accessed, production impacted, personal data exposed, security violation
- Action: Stop all testing immediately, notify emergency contact
- Notification: Phone call + emergency keyword

### 9.3 Reporting Schedule

**Daily Status Updates:**
- Timing: End of each test session
- Method: Email to primary contact
- Content: Summary of activities, findings, issues

**Weekly Summary:**
- Timing: Friday EOD
- Method: Email to authorized signatory
- Content: High-level progress, key findings, upcoming activities

**Final Report:**
- Timing: Within 14 days of test completion
- Method: Encrypted PDF delivered via secure portal
- Content: Executive summary, technical findings, remediation recommendations, evidence

---

## 10. Evidence & Audit Trail

### 10.1 Evidence Collection

**What to collect:**
- Screenshots of vulnerabilities
- HTTP request/response pairs (sensitive data redacted)
- Exploit proof-of-concept code
- Log files (target system logs if accessible)
- Network traffic captures (PCAP files)
- Command history and outputs

**Evidence Format:**
- Screenshots: PNG with timestamp overlay
- PCAPs: Filtered to relevant traffic only
- Logs: Plain text with timestamps
- Code: Text files with syntax highlighting

**Evidence Storage:**
- Location: `/data/pentest/evidence/[AUTH-ID]/`
- Encryption: AES-256, key stored separately
- Access control: Tester + authorized signatory only
- Backup: Encrypted backup to secure cloud storage

### 10.2 Chain of Custody

**Evidence Manifest:**
```json
{
  "authorization_id": "AUTH-2025-001",
  "evidence_id": "EVID-001",
  "collected_by": "Tester Name",
  "collected_at": "2025-11-12T14:30:00Z",
  "file_name": "screenshot_sqli_poc.png",
  "file_hash": "sha256:abc123...",
  "file_size": 1048576,
  "description": "SQL injection proof-of-concept in login form",
  "chain_of_custody": [
    {
      "timestamp": "2025-11-12T14:30:00Z",
      "action": "collected",
      "actor": "Tester Name"
    },
    {
      "timestamp": "2025-11-12T14:35:00Z",
      "action": "encrypted",
      "actor": "Tester Name"
    }
  ]
}
```

**Cryptographic Hashing:**
- All evidence files: SHA-256 hash
- Manifest file: Signed with tester's PGP key
- Integrity verification before report delivery

### 10.3 Immutable Audit Log

**Audit Log Format:**
```json
{
  "timestamp": "2025-11-12T14:30:00Z",
  "authorization_id": "AUTH-2025-001",
  "event_type": "test_start | test_end | vulnerability_found | scope_violation | emergency_stop",
  "actor": "Tester Name",
  "target": "192.168.1.100",
  "action": "nmap -sV -p- 192.168.1.100",
  "result": "success | failure | error",
  "details": "Discovered 5 open ports",
  "log_hash": "sha256:def456..."
}
```

**Audit Log Properties:**
- Append-only (no modification or deletion)
- Cryptographically signed with each entry
- Backed up to immutable storage (S3 with versioning, WORM storage)
- Retention: 7 years (compliance requirement)

---

## 11. Legal & Compliance

### 11.1 Jurisdiction & Applicable Law

**Governing Law:** _____________________________________

**Dispute Resolution:** ☐ Arbitration  ☐ Litigation  ☐ Mediation

**Venue:** _____________________________________

### 11.2 Data Protection Compliance

**GDPR (if applicable):**
- Legal basis for processing: ☐ Legitimate interest  ☐ Consent  ☐ Contract
- Data Protection Officer notified: ☐ Yes  ☐ No  ☐ N/A
- Data Processing Agreement: Attached ☐ Yes  ☐ No

**CCPA (if applicable):**
- Consumer notice provided: ☐ Yes  ☐ No  ☐ N/A
- Opt-out mechanism: _____________________________________

**Breach Notification:**
- If personal data exposed during testing: Notify within 72 hours
- Notification recipients: DPO, authorized signatory, legal counsel

### 11.3 Third-Party Compliance

**Cloud Provider Terms of Service:**
- AWS: ☐ Reviewed and compliant
- Azure: ☐ Reviewed and compliant
- GCP: ☐ Reviewed and compliant
- Other: _____________________________________

**Penetration Testing Notification:**
- AWS: Submitted via https://aws.amazon.com/security/penetration-testing/
- Azure: No pre-approval required for most services (verify current policy)
- GCP: No pre-approval required (verify current policy)

---

## 12. Insurance & Liability

### 12.1 Insurance Requirements

**Professional Liability Insurance:**
- Provider: _____________________________________
- Policy Number: _____________________________________
- Coverage Amount: $_____________________________________
- Expiration: _____________________________________

**Cyber Liability Insurance:**
- Provider: _____________________________________
- Policy Number: _____________________________________
- Coverage Amount: $_____________________________________
- Expiration: _____________________________________

**Certificate of Insurance:** Attached ☐ Yes  ☐ No

### 12.2 Liability Limitations

**Liability Cap:** $_____________________________________

**Exclusions (tester not liable for):**
- Damages resulting from actions within authorized scope
- Damages resulting from following authorized procedures
- Damages disclosed in advance and accepted by authorized signatory

**Tester remains liable for:**
- Gross negligence or willful misconduct
- Actions outside authorized scope
- Violations of law or regulation
- Breach of confidentiality

---

## 13. Quality Assurance

### 13.1 Testing Standards

**Methodologies:**
- ☐ OWASP Testing Guide
- ☐ PTES (Penetration Testing Execution Standard)
- ☐ NIST SP 800-115
- ☐ OSSTMM
- ☐ Custom methodology (describe: ___________________)

**Tool Versions:**
- Document all tool versions in final report
- Use latest stable versions (not beta/alpha)

### 13.2 Peer Review

**Findings Review:**
- All critical/high findings: Reviewed by second tester
- False positive check: Verify exploitability
- Report review: Reviewed by senior tester before delivery

---

## 14. Amendments & Change Control

### 14.1 RoE Amendments

**Process for changing RoE:**
1. Tester proposes change in writing
2. Authorized signatory reviews and approves/rejects
3. If approved, updated RoE signed by both parties
4. New version number assigned

**Version Control:**
- Current Version: 1.0
- Previous Versions: (list with change summary)

### 14.2 Emergency Scope Changes

**If urgent scope change needed:**
1. Email request to authorized signatory
2. Wait for written approval (email acceptable)
3. Update scope.json and calculate new hash
4. Log change in audit trail

---

## 15. Document Control

**Document Version:** 1.0

**Template Version:** ARK-RoE-2025-v1

**Effective Date:** _____________________________________

**Expiration Date:** _____________________ (same as Authorization)

**Review Schedule:** Every 90 days or when Authorization is renewed

**Distribution:**
- Tester: Copy retained in secure location
- Authorized Signatory: Copy retained for legal records
- Legal Counsel: Copy provided for review
- Security Team: Copy provided for operational awareness

---

## 16. Acknowledgment & Acceptance

### 16.1 Tester Acknowledgment

**I acknowledge that I have read, understood, and agree to follow this Rules of Engagement document. I understand that deviation from these rules may result in:**
- Immediate termination of testing authorization
- Legal liability for unauthorized access
- Criminal prosecution
- Civil damages

**Signature:** _____________________________________

**Printed Name:** _____________________________________

**Date:** _____________________________________

---

### 16.2 Authorized Signatory Acknowledgment

**I acknowledge that this Rules of Engagement document accurately reflects our agreement and operational requirements.**

**Signature:** _____________________________________

**Printed Name:** _____________________________________

**Title:** _____________________________________

**Date:** _____________________________________

---

**END OF RULES OF ENGAGEMENT DOCUMENT**

**RETAIN THIS DOCUMENT WITH AUTHORIZATION FOR LEGAL RECORD KEEPING**
