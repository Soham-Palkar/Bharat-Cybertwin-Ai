"""CyberTwin AI Constants Module"""
import os

# MITRE ATT&CK Mapping for all implemented attack types
MITRE_ATTACK_MAPPING = {
    "bruteforce": {"id": "T1110", "name": "Brute Force"},
    "credential_stuffing": {"id": "T1110.004", "name": "Credential Stuffing"},
    "port_scan": {"id": "T1046", "name": "Network Service Scanning"},
    "impossible_travel": {"id": "T1078", "name": "Valid Accounts"},
    "phishing": {"id": "T1566", "name": "Phishing"},
    "exfiltration": {"id": "T1041", "name": "Exfiltration Over C2 Channel"},
    "privilege_escalation": {"id": "T1068", "name": "Exploitation for Privilege Escalation"},
    "ransomware": {"id": "T1486", "name": "Data Encrypted for Impact"},
    "insider_threat": {"id": "T1087", "name": "Account Discovery"},
}

# Containment Action Types
CONTAINMENT_ACTION_TYPES = [
    "block_ip",
    "disable_user",
    "force_mfa",
    "reset_password",
    "quarantine",
]

# Detection Window (from existing code for consistency)
DETECTION_WINDOW_MINUTES = 5

# Enable real containment actions? (BE CAREFUL!)
ENABLE_REAL_CONTAINMENT = os.getenv("ENABLE_REAL_CONTAINMENT", "false").lower() == "true"

# Username mapping for real containment (sim names → real OS usernames)
# REAL_USERNAMES = {
#     "admin": "CyberTwinTestUser",
#     "cybertwin": "CyberTwinTestUser",
# }