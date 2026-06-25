# ORPHEUS PRIVACY POLICY

**Effective Date:** January 1, 2025  
**Last Updated:** June 24, 2025  
**Version:** 1.0

---

## 1. INTRODUCTION

ORPHEUS (Omni-Responsive Processing Matrix) is a privacy-first, locally-hosted AI command center designed to give users absolute control over their data. This Privacy Policy explains how ORPHEUS collects, uses, protects, and manages information.

**Key Principle:** ORPHEUS is engineered for **zero-knowledge architecture**. Your data never leaves your machine unless you explicitly consent to cloud integrations.

---

## 2. DATA OWNERSHIP & CONTROL

### 2.1 You Own Your Data
- All files, conversations, commands, and generated content created within ORPHEUS are **your exclusive property**.
- You retain 100% ownership and control of all data at all times.
- You can export, delete, or modify your data at any moment.

### 2.2 Local-First Architecture
- ORPHEUS runs entirely on your local machine by default.
- No data is transmitted to Anthropic, Google, OpenAI, or any third party without your explicit consent.
- Your workspace directory (`/workspace`) is a sandboxed environment under your exclusive control.

---

## 3. DATA COLLECTION

### 3.1 What Data ORPHEUS Collects

**Mandatory (Local Storage Only):**
- User account credentials (email, hashed password)
- Voice biometric enrollment data (hash only, never raw audio)
- Session tokens and authentication metadata
- User activity logs (commands executed, file operations, search queries)
- System metrics (CPU, RAM, disk usage for dashboard display only)

**Optional (Upon Your Consent):**
- Cloud LLM API usage (if you configure Google Gemini, OpenAI, or similar)
- Web search results (if you enable WebResearch agent)
- Custom file content (only when you request file operations)

### 3.2 What ORPHEUS Does NOT Collect
- ❌ Raw audio recordings (only cryptographic voice hashes)
- ❌ Biometric templates (only SHA-256 hashes for verification)
- ❌ Browsing history outside of explicit ORPHEUS commands
- ❌ Email or contact list data
- ❌ Location data
- ❌ Device identifiers (IMEI, UDID, etc.)
- ❌ Third-party app data
- ❌ Telemetry or analytics without explicit opt-in

### 3.3 Encryption at Rest & in Transit
- **Local Database:** SQLite with encrypted fields using Fernet (AES-128)
- **Sensitive Fields:** Passwords, API keys, and custom data use AES-256 encryption
- **Network Communication:** All WebSocket connections use TLS/SSL (HTTPS)
- **Master Key:** Derived from your environment variable (`ORPHEUS_MASTER_KEY`) using PBKDF2

---

## 4. VOICE & BIOMETRIC DATA

### 4.1 Voice Enrollment
- During initial setup, ORPHEUS records a brief voice sample (5-10 seconds) to create a voice profile.
- This recording is **immediately processed and discarded**. Only the cryptographic hash is retained.
- Voice hashes are stored locally using SHA-256 and never transmitted.

### 4.2 Voice Recognition
- When you issue voice commands, ORPHEUS compares the real-time audio against your stored voice hash.
- Raw audio from voice commands is processed by Faster-Whisper (local speech-to-text) and **not stored**.
- No audio files are saved to disk unless you explicitly choose to record them.

### 4.3 Biometric Data Rights
- You can revoke or update your voice profile at any time by running the setup script.
- Your voice data is never sold, shared, or used for any purpose beyond authentication.

---

## 5. CLOUD INTEGRATIONS & THIRD-PARTY SERVICES

### 5.1 Optional Cloud LLM Models
If you configure ORPHEUS to use cloud-based LLM providers:

**Google Gemini:**
- API calls are transmitted to Google's servers
- Subject to Google's Privacy Policy: https://policies.google.com/privacy
- Your prompts may be retained for improvement purposes (see Google's API documentation)

**OpenAI (GPT-4o, etc.):**
- API calls are transmitted to OpenAI's servers
- Subject to OpenAI's Privacy Policy: https://openai.com/privacy
- Your prompts may be logged and reviewed for safety

**Ollama (Local):**
- ✅ **Fully local.** No data transmission. Recommended for maximum privacy.

### 5.2 Web Search Integration
If you enable the WebResearch agent:
- **DuckDuckGo:** Queries are sent to DuckDuckGo API. [DuckDuckGo Privacy Policy](https://duckduckgo.com/privacy)
- **SearXNG (Optional):** Can be configured to use self-hosted SearXNG instances for zero tracking.

### 5.3 Your Responsibility
You are responsible for reviewing third-party privacy policies before integrating external services. ORPHEUS provides clear configuration options to avoid unwanted data sharing.

---

## 6. DATA STORAGE & RETENTION

### 6.1 Local Storage Duration
- **Account Data:** Retained for the lifetime of your ORPHEUS installation
- **Activity Logs:** Kept for 90 days by default; configurable via `.env`
- **Session Data:** Cleared upon logout or 30-day inactivity
- **Temporary Files:** Cleaned up automatically upon command completion

### 6.2 Encrypted Logs
- All system logs are encrypted using Fernet encryption
- Logs are stored in `/logs/` directory with restricted file permissions (600)
- Only you can decrypt logs using your master encryption key

### 6.3 Workspace Retention
- All files in `/workspace/` are under your exclusive control
- ORPHEUS does not automatically delete workspace content
- You are responsible for managing your own workspace storage

---

## 7. DATA SHARING & DISCLOSURE

### 7.1 We Do NOT Share Your Data
ORPHEUS does **not** sell, rent, lease, or share your personal data with any third party, except as required by law.

### 7.2 Legal Disclosure
We may disclose your data only if:
- Required by valid court order, subpoena, or law enforcement request
- Necessary to prevent fraud, abuse, or harm
- Required by applicable data protection laws (GDPR, CCPA, etc.)

In such cases, we will attempt to notify you in advance unless prohibited by law.

### 7.3 No Third-Party Analytics
- ORPHEUS does not use Google Analytics, Mixpanel, Amplitude, or similar tracking tools
- No usage metrics are sent externally
- You have complete visibility into what data is collected via the activity logs

---

## 8. USER RIGHTS & GDPR COMPLIANCE

### 8.1 Right to Access
You have the right to request access to all personal data ORPHEUS holds about you. This includes:
- Account information
- Activity logs
- Encrypted data fields
- Session history

**To Request:** Export your data from the admin dashboard or use the CLI command: `python -m orpheus.export_user_data <email>`

### 8.2 Right to Deletion ("Right to Be Forgotten")
You have the absolute right to delete your account and all associated data.

**To Delete:**
1. Navigate to Settings > Account > Delete Account
2. Or use CLI: `python -m orpheus.delete_user <email>`
3. All data will be permanently deleted within 30 days

### 8.3 Right to Data Portability
You can export all your data in a machine-readable format (JSON) at any time.

### 8.4 Right to Rectification
You can correct inaccurate personal data at any time through your account settings.

### 8.5 Right to Object
You can opt out of:
- Activity logging (still required for security, but will be anonymized)
- Cloud LLM integrations
- Web search data collection

---

## 9. SECURITY & SAFEGUARDS

### 9.1 Encryption Standards
- **Master Key:** AES-256 using Fernet (symmetric encryption)
- **Password Storage:** PBKDF2 with SHA-256, salted with 256 bits
- **Voice Biometrics:** SHA-256 hashing with unique per-user salt
- **Database Fields:** Encrypted using cryptography.fernet.Fernet

### 9.2 Access Control
- Role-based access control (RBAC): Admin, User, Guest
- Session tokens are cryptographically signed using itsdangerous
- All authentication is local; no credentials transmitted externally (unless cloud LLM is enabled)

### 9.3 Audit Logging
- Every action (login, command execution, file operations) is logged
- Logs are encrypted and tamper-evident
- Logs include timestamp, IP address, user agent, and action description

### 9.4 Rate Limiting & Abuse Prevention
- Authentication attempts are rate-limited (5 attempts per IP per 15 minutes)
- Command execution is monitored for dangerous operations
- Dangerous commands (rm -rf, etc.) are blocked at the harness level

### 9.5 Vulnerability Disclosure
If you discover a security vulnerability in ORPHEUS:
1. **Do NOT** post it publicly
2. Email security details to: [security@orpheus-ai.local]
3. We will acknowledge within 48 hours and provide timeline for fix
4. You will be credited in security advisories (optional)

---

## 10. CHILDREN & MINORS

ORPHEUS is not intended for children under 13 years of age. We do not knowingly collect data from minors. If we learn that we have collected personal data from a child under 13, we will delete such data promptly.

---

## 11. INTERNATIONAL DATA TRANSFERS

Since ORPHEUS is local-first:
- Your data does NOT cross international borders by default
- If you configure cloud LLM (Google, OpenAI), your data may be processed internationally per their policies
- You are responsible for reviewing third-party jurisdiction policies

---

## 12. DATA RETENTION & DELETION

### 12.1 Automatic Retention Periods
| Data Type | Retention | Reason |
|-----------|-----------|--------|
| Activity Logs | 90 days | Security audit trail |
| Session Data | 30 days | Security & performance |
| Workspace Files | Indefinite | Your data ownership |
| Voice Profile | Until revoked | Biometric authentication |
| Account Data | Until deletion | Service provision |

### 12.2 Permanent Deletion
Upon account deletion:
1. All account records are irreversibly encrypted with temporary key
2. Encryption key is destroyed
3. Data becomes unrecoverable within 30 days

---

## 13. COOKIES & TRACKING

ORPHEUS uses **strictly necessary cookies** only:
- `orpheus_session`: Stores your encrypted session token (HttpOnly, Secure)
- **No third-party cookies**
- **No tracking pixels or beacons**
- You can clear cookies at any time; you'll be logged out

---

## 14. CONTACT & PRIVACY REQUESTS

### 14.1 Privacy Inquiries
For any privacy-related questions or data requests:

**Email:** [privacy@orpheus-ai.local]  
**Response Time:** 30 days (GDPR standard)

### 14.2 Data Subject Access Request (DSAR)
To request a copy of your personal data:

1. Email your request to privacy@orpheus-ai.local with subject: "DSAR Request"
2. Include your email address and specific data categories
3. We will provide your data in JSON/CSV format within 30 days

### 14.3 Complaints & Escalation
If you believe ORPHEUS violates your privacy rights:
1. Contact privacy@orpheus-ai.local with detailed complaint
2. If unresolved within 60 days, you may file complaint with your local data protection authority

---

## 15. POLICY UPDATES & CHANGES

We may update this Privacy Policy as ORPHEUS evolves. We will:
- Post new versions on this page with updated "Last Modified" date
- Notify you of material changes via email (if applicable)
- Obtain your explicit consent before implementing material changes

You agree to review this policy periodically. Continued use of ORPHEUS after changes indicates acceptance.

---

## 16. DISCLAIMER

ORPHEUS is provided "AS IS" without warranty. While we implement industry-leading encryption and security practices, **no system is 100% secure**. We recommend:
- Using strong, unique passwords
- Keeping ORPHEUS updated
- Securing your machine against malware
- Using hardware security modules (HSM) for ultra-sensitive deployments

---

## 17. DEFINITIONS

- **Encryption:** Conversion of data into a code to prevent unauthorized access
- **Hashing:** One-way conversion of data; cannot be reversed to recover original
- **Biometric Data:** Unique physical characteristics (voice, fingerprints)
- **Master Key:** Root encryption key derived from your environment variable
- **Cloud LLM:** Language models hosted by third parties (Gemini, OpenAI, etc.)
- **WebSocket:** Real-time bidirectional communication protocol

---

**ORPHEUS Privacy Policy © 2025. All rights reserved.**

---

For the most current version, visit: [https://orpheus-ai.local/privacy](#)
