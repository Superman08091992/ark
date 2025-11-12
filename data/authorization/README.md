# ARK Legal Authorization Framework for Penetration Testing

## Overview

This directory contains the **legal authorization framework** for ARK's penetration testing capabilities. This framework is a **critical security control** that prevents ARK from accessing systems outside authorized scope, which could result in criminal prosecution under computer misuse laws worldwide.

## ⚠️ CRITICAL LEGAL NOTICE

**Unauthorized penetration testing is ILLEGAL** in most jurisdictions and can result in:

- **Criminal prosecution** under laws such as:
  - Computer Fraud and Abuse Act (CFAA) - United States
  - Computer Misuse Act - United Kingdom
  - Similar computer crime laws worldwide
- **Civil liability** including damages, injunctions, and legal fees
- **Imprisonment** in severe cases
- **Professional consequences** including loss of certifications and employment

**ARK will REFUSE to execute penetration tests without:**

1. ✅ Signed authorization document
2. ✅ Valid scope definition (scope.json)
3. ✅ Rules of engagement agreement
4. ✅ Multi-factor authentication (MFA)
5. ✅ Human approval for high-risk activities

## Required Documents

### 1. Authorization to Perform Security Testing

**File:** `AUTHORIZATION_TEMPLATE.md`

**Purpose:** Legal authorization from asset owner granting permission for security testing

**Required Signatures:**
- Authorized signatory (asset owner)
- Testing party (lead tester)
- Optional: Legal counsel, CISO, HR (for social engineering)

**Key Sections:**
- Authorization details (ID, date, type)
- Requesting party information (with ID verification)
- Explicit in-scope and out-of-scope assets
- Allowed and forbidden activities
- Time windows and blackout periods
- Data handling and privacy requirements
- Rollback and emergency procedures
- Reporting and disclosure terms
- Liability and indemnification
- Legal compliance declarations

**Status:** ☐ Not Signed  ☐ In Progress  ☐ Signed and Active

---

### 2. Rules of Engagement (RoE)

**File:** `RULES_OF_ENGAGEMENT_TEMPLATE.md`

**Purpose:** Operational procedures and tactical guidelines for conducting security tests

**Required Signatures:**
- Tester acknowledgment
- Authorized signatory acknowledgment

**Key Sections:**
- Technical scope definition (IPs, hostnames, URLs, repos, containers, cloud)
- Timing constraints (business hours vs. maintenance windows)
- Allowed testing methods (passive, active, exploitation, social engineering)
- Prohibited actions (expanded list)
- Technical constraints (rate limits, resource thresholds)
- Operational procedures (pre-test checklist, monitoring, post-test)
- Snapshot and rollback procedures
- Credentials and access management
- Communication and escalation
- Evidence and audit trail requirements

**Status:** ☐ Not Signed  ☐ In Progress  ☐ Signed and Active

---

### 3. Scope Definition (Machine-Readable)

**File:** `../pentest/scope/scope_example.json`

**Purpose:** Machine-readable scope definition for automated validation

**Schema:** `../pentest/scope/scope_schema.json` (JSON Schema validation)

**Key Fields:**
- `authorization_id` - Links to authorization document
- `version` - Semantic versioning for scope changes
- `effective_date` / `expiration_date` - Validity period
- `scope_hash` - SHA-256 integrity verification
- `in_scope` - Explicitly authorized assets
- `out_of_scope` - Explicitly forbidden assets
- `time_windows` - Allowed testing times
- `allowed_methods` - Permitted testing techniques
- `technical_constraints` - Rate limits and thresholds
- `emergency_contacts` - 24/7 contact information

**Validation:** Enforced by `pentest/scope_validator.py`

**Status:** ☐ Not Created  ☐ Incomplete  ☐ Validated and Active

---

## Workflow: Setting Up Authorization

### Step 1: Complete Authorization Document

1. Open `AUTHORIZATION_TEMPLATE.md`
2. Fill in all required fields (marked with `_____`)
3. Define explicit in-scope assets (IPs, hostnames, repos, etc.)
4. Define explicit out-of-scope assets (production systems, third parties)
5. Specify allowed and forbidden testing methods
6. Set time windows and blackout periods
7. Define data handling procedures
8. Establish emergency contacts and rollback plan
9. Review with legal counsel
10. Obtain signatures from all required parties
11. Retain signed copy for legal record keeping (minimum 7 years)

### Step 2: Complete Rules of Engagement

1. Open `RULES_OF_ENGAGEMENT_TEMPLATE.md`
2. Reference the authorization document ID
3. Define technical scope details (IP ranges, CIDR blocks, URL patterns)
4. Set operational timing constraints
5. Specify allowed tools and techniques
6. Define rate limits and resource thresholds
7. Establish snapshot/rollback procedures
8. Configure credentials and access methods
9. Define communication channels and escalation matrix
10. Set evidence collection and audit requirements
11. Obtain acknowledgment signatures
12. Distribute to all relevant parties (tester, ops, security, legal)

### Step 3: Create Machine-Readable Scope

1. Copy `../pentest/scope/scope_example.json` to `scope.json`
2. Update `authorization_id` to match signed authorization
3. Fill in `in_scope` assets:
   - `ip_addresses` - Individual IPs and CIDR ranges
   - `hostnames` - Fully qualified domain names
   - `wildcard_domains` - Subdomain wildcards (e.g., `*.staging.example.com`)
   - `urls` - Specific URL patterns with allowed HTTP methods
   - `repositories` - Source code repos with branches
   - `containers` - Container images with registries and tags
   - `cloud_resources` - Cloud provider resources with tags
4. Fill in `out_of_scope` assets (production, third parties)
5. Configure `time_windows` with timezone and allowed hours
6. Configure `allowed_methods` (enable/disable testing techniques)
7. Set `technical_constraints` (rate limits, resource thresholds)
8. Add `emergency_contacts` (primary and secondary, 24/7)
9. Calculate and update `scope_hash` (validator will calculate if placeholder)
10. Validate with: `python3 pentest/scope_validator.py`

### Step 4: Validate Scope

```bash
# Run scope validator
python3 pentest/scope_validator.py

# Expected output:
# ✅ Scope loaded and validated
# 📋 Scope Summary
# 🧪 Testing Validation Examples

# Check audit log
cat data/pentest/logs/scope_validation.log
```

### Step 5: Enable ARK Pentest Mode

**⚠️ TODO: Integrate with ARK authorization system**

This will require:
1. HRM approval toggle for pentest mode
2. MFA verification before enabling
3. Multi-actor approval (at least 2 humans)
4. Automatic scope validation before any test
5. Real-time scope checking during execution
6. Emergency stop capability

---

## Scope Validator

**File:** `../pentest/scope_validator.py`

**Purpose:** Automated validation of targets against authorized scope

**Key Features:**
- ✅ IP address and CIDR range validation
- ✅ Hostname and wildcard domain matching
- ✅ URL path and HTTP method validation
- ✅ Time window enforcement (business hours vs. maintenance)
- ✅ Blackout period detection
- ✅ Automatic scope expiration checking
- ✅ Cryptographic scope integrity verification (SHA-256)
- ✅ Method authorization checking
- ✅ Append-only audit logging

**Usage:**

```python
from pentest.scope_validator import ScopeValidator

# Initialize validator with scope file
validator = ScopeValidator(Path("data/pentest/scope/scope.json"))

# Validate IP address
result = validator.validate_ip("192.168.1.100")
if result.result == ValidationResult.ALLOWED:
    # Proceed with testing
    pass
else:
    # Block testing - log violation
    print(f"❌ {result.message}")

# Validate hostname
result = validator.validate_hostname("api-staging.example.com")

# Validate URL with HTTP method
result = validator.validate_url("https://api-staging.example.com/v1/users", method="POST")

# Check time window
result = validator.check_time_window("low_impact")

# Check if testing method is allowed
result = validator.check_method_allowed("active_exploitation")
if result.requires_approval:
    # Request human approval before proceeding
    pass
```

**Validation Results:**
- `ALLOWED` - Target is authorized, proceed with testing
- `DENIED` - Target not in scope, block testing
- `OUT_OF_SCOPE` - Target explicitly forbidden, block testing
- `REQUIRES_APPROVAL` - Target allowed but requires explicit approval
- `BLACKOUT_PERIOD` - Testing forbidden during blackout period
- `EXPIRED` - Authorization has expired, renewal required
- `INVALID_SCOPE` - Scope file is invalid or tampered

---

## Audit Trail

All validation checks are logged to an **append-only audit log**:

**Location:** `../pentest/logs/scope_validation.log`

**Format:** JSON lines (one JSON object per line)

**Example Entry:**

```json
{
  "timestamp": "2025-11-12T02:35:00.123456Z",
  "result": "denied",
  "target": "8.8.8.8",
  "target_type": "ip",
  "message": "IP not found in authorized scope (default deny)",
  "scope_id": "AUTH-2025-001",
  "matching_rule": null
}
```

**Retention:** 7 years (compliance requirement)

**Integrity:** Cryptographically signed entries (SHA-256 hashes)

---

## Security Best Practices

### 1. Principle of Least Privilege

- ✅ Only authorize the minimum necessary scope
- ✅ Use specific IPs/hostnames instead of broad CIDR ranges when possible
- ✅ Restrict testing to non-production environments
- ✅ Exclude third-party services and shared infrastructure
- ✅ Limit time windows to maintenance periods for high-impact tests

### 2. Defense in Depth

- ✅ Multi-layer validation (scope validator + HRM approval + MFA)
- ✅ Cryptographic integrity verification (SHA-256 hashing)
- ✅ Automatic expiration (time-bound authorizations)
- ✅ Append-only audit logging (tamper-evident)
- ✅ Emergency stop capability (24/7 contact)

### 3. Default Deny

- ✅ Anything not explicitly in scope is denied by default
- ✅ Out-of-scope rules override in-scope rules (explicit deny wins)
- ✅ Unknown testing methods are denied
- ✅ Outside time windows are denied

### 4. Human Oversight

- ✅ MFA required for enabling pentest mode
- ✅ Multi-actor approval for high-risk activities
- ✅ Human approval required for active exploitation
- ✅ Emergency stop accessible to authorized personnel

---

## Legal Compliance Checklist

Before ANY penetration testing:

### Authorization
- ☐ Signed authorization document obtained
- ☐ Authorized signatory identity verified (government ID, corporate officer record)
- ☐ Scope explicitly defined (in-scope and out-of-scope assets)
- ☐ Time windows and blackout periods established
- ☐ Allowed and forbidden activities documented
- ☐ Emergency contacts and rollback plan defined

### Legal Review
- ☐ Legal counsel reviewed authorization
- ☐ Applicable laws and regulations reviewed (CFAA, Computer Misuse Act, etc.)
- ☐ Data protection compliance confirmed (GDPR, CCPA, etc.)
- ☐ Third-party terms of service reviewed (cloud providers, CDNs)
- ☐ Export controls reviewed (if applicable)
- ☐ Insurance coverage verified (professional liability, cyber liability)

### Technical Controls
- ☐ Scope definition file created and validated (scope.json)
- ☐ Scope hash calculated and verified (integrity check)
- ☐ Scope validator tested and operational
- ☐ Audit logging enabled (append-only, immutable)
- ☐ Snapshot/rollback procedures established
- ☐ MFA and human approval controls configured

### Operational Readiness
- ☐ Pre-test checklist prepared
- ☐ Emergency stop procedure documented and tested
- ☐ Communication channels established (primary and emergency)
- ☐ Credentials provisioned securely (encrypted, MFA)
- ☐ Evidence collection procedures defined
- ☐ Reporting and disclosure timeline agreed

### Post-Authorization
- ☐ Authorization document retained for legal records (7 years minimum)
- ☐ Scope definition file backed up (encrypted, version controlled)
- ☐ All parties notified of authorization activation
- ☐ Monitoring and alerting configured
- ☐ Periodic scope review scheduled (every 90 days or at renewal)

---

## Emergency Procedures

### Emergency Stop

**Triggers:**
- Out-of-scope asset accessed
- Production system impacted
- Personal data exposed
- Security violation detected
- Authorized signatory requests stop

**Procedure:**
1. **STOP ALL TESTING IMMEDIATELY**
2. Contact emergency contact: `[Phone number from authorization]`
3. Use emergency keyword: `PENTEST-EMERGENCY-[AUTH-ID]`
4. Wait for acknowledgment (within 5 minutes)
5. Secure all evidence (encrypt and hash)
6. Execute rollback plan (restore snapshots)
7. Document incident in audit log
8. Submit incident report to authorized signatory within 24 hours

### Authorization Revocation

**Process:**
1. Written notice from authorized signatory OR
2. Email to [emergency contact email] OR
3. Phone call with verbal revocation code

**Upon revocation:**
- All testing activities cease immediately
- All evidence secured according to data handling procedures
- Final report submitted (if required)
- Credentials deleted securely
- Authorization marked as revoked in audit log

---

## Document Retention

**Legal Requirement:** Retain all authorization documents, scope definitions, audit logs, and evidence for **minimum 7 years** after test completion.

**Storage Requirements:**
- Encrypted at rest (AES-256)
- Backup to secure, immutable storage (WORM, S3 versioning)
- Access control (authorized personnel only, MFA required)
- Audit logging of document access

**Retention Schedule:**
- Authorization documents: 7 years
- Rules of engagement: 7 years
- Scope definitions: 7 years
- Audit logs: 7 years
- Evidence: 90 days (unless legal hold)
- Reports: 7 years

---

## Version Control

**Document Version:** 1.0

**Template Version:** ARK-AUTH-2025-v1

**Last Updated:** 2025-11-12

**Change Log:**
```
v1.0 - 2025-11-12 - Initial authorization framework creation
  - Created AUTHORIZATION_TEMPLATE.md
  - Created RULES_OF_ENGAGEMENT_TEMPLATE.md
  - Created scope schema and example
  - Implemented scope_validator.py
  - Created README documentation
```

---

## Support and Questions

For legal questions about authorization:
- Consult with licensed attorney in your jurisdiction
- Review applicable computer misuse laws
- Check cloud provider terms of service

For technical questions about the framework:
- Review this README
- Examine scope_validator.py source code
- Run validator demo: `python3 pentest/scope_validator.py`
- Check audit logs: `data/pentest/logs/scope_validation.log`

---

## Disclaimer

This authorization framework is provided as a tool to help enforce legal boundaries for security testing. It does not constitute legal advice. **Consult with a licensed attorney** before conducting any penetration testing activities. The authors and contributors are not liable for any unauthorized access or legal violations resulting from misuse of this framework.

**USE AT YOUR OWN RISK. ALWAYS OBTAIN PROPER AUTHORIZATION BEFORE TESTING.**
