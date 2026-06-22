"""
Containment Service - Handles real containment actions
WARNING: Only use in a controlled, test environment!
"""
import subprocess
import platform
import uuid
from typing import Tuple
from ..constants import ENABLE_REAL_CONTAINMENT


def execute_real_containment(action_type: str, target: str) -> Tuple[bool, str]:
    """
    Executes real containment actions (if enabled)
    Returns (success: bool, message: str)
    """
    if not ENABLE_REAL_CONTAINMENT:
        return True, "Real containment disabled - using simulation only"

    system = platform.system()

    if action_type == "block_ip":
        return _block_ip(target, system)
    elif action_type == "disable_user":
        return _disable_user(target, system)
    elif action_type == "reset_password":
        return _reset_password(target, system)
    elif action_type == "force_mfa":
        return _force_mfa(target, system)
    elif action_type == "quarantine":
        return _quarantine(target, system)
    else:
        return True, f"Real containment for {action_type} not implemented yet - using simulation"


def _block_ip(ip: str, system: str) -> Tuple[bool, str]:
    """Block an IP address using OS-specific firewall"""
    try:
        if system == "Windows":
            # Add Windows Firewall rule (requires admin!)
            rule_name = f"CyberTwin_Block_{ip.replace('.', '_')}"
            command = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}", "dir=in", "action=block",
                f"remoteip={ip}", "profile=any"
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return True, f"Successfully blocked IP {ip} (Windows Firewall rule '{rule_name}')"
        elif system == "Linux":
            # Add iptables rule
            command = ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return True, f"Successfully blocked IP {ip} (iptables rule added)"
        else:
            return False, f"Unsupported OS for IP blocking: {system}"
    except subprocess.CalledProcessError as e:
        return False, f"Failed to block IP {ip}: {e.stderr}"
    except Exception as e:
        return False, f"Error blocking IP {ip}: {str(e)}"


def _disable_user(username: str, system: str) -> Tuple[bool, str]:
    """Disable a local user account (OS-specific)"""
    try:
        if system == "Windows":
            command = ["net", "user", username, "/active:no"]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return True, f"Successfully disabled user '{username}' (Windows)"
        elif system == "Linux":
            command = ["usermod", "-L", username]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return True, f"Successfully disabled user '{username}' (Linux)"
        else:
            return False, f"Unsupported OS for user disable: {system}"
    except subprocess.CalledProcessError as e:
        return False, f"Failed to disable user '{username}': {e.stderr}"
    except Exception as e:
        return False, f"Error disabling user '{username}': {str(e)}"


def _reset_password(username: str, system: str) -> Tuple[bool, str]:
    """Reset a local user's password (OS-specific)"""
    temp_password = str(uuid.uuid4())[:12]
    try:
        if system == "Windows":
            command = ["net", "user", username, temp_password]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return True, f"Successfully reset password for '{username}' to: {temp_password} (save this!)"
        elif system == "Linux":
            command = ["bash", "-c", f"echo '{username}:{temp_password}' | chpasswd"]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return True, f"Successfully reset password for '{username}' to: {temp_password} (save this!)"
        else:
            return False, f"Unsupported OS for password reset: {system}"
    except subprocess.CalledProcessError as e:
        return False, f"Failed to reset password for '{username}': {e.stderr}"
    except Exception as e:
        return False, f"Error resetting password for '{username}': {str(e)}"


def _force_mfa(username_or_ip: str, system: str) -> Tuple[bool, str]:
    """
    Force MFA (demonstration only, since local accounts don't have built-in MFA)
    For Windows: Creates a registry key
    For Linux: Adds a note to /etc/motd
    """
    try:
        if system == "Windows":
            import winreg
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\CyberTwin")
            winreg.SetValueEx(key, "ForceMFA", 0, winreg.REG_SZ, "1")
            winreg.CloseKey(key)
            return True, f"Forced MFA for '{username_or_ip}' (demo only, created registry key)"
        elif system == "Linux":
            with open("/etc/motd", "a") as f:
                f.write(f"\n[CyberTwin: MFA required for {username_or_ip}\n")
            return True, f"Forced MFA for '{username_or_ip}' (demo only, updated /etc/motd)"
        else:
            return False, f"Unsupported OS for force MFA: {system}"
    except Exception as e:
        return False, f"Failed to force MFA for '{username_or_ip}': {str(e)}"


def _quarantine(identifier: str, system: str) -> Tuple[bool, str]:
    """Quarantine a device/IP (block most network access)"""
    try:
        if system == "Windows":
            # Quarantine: Block all inbound traffic except local
            rule_name = "CyberTwin_Quarantine"
            command = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}", "dir=in", "action=block"
            ]
            # Apply to target IP? Wait, no — for quarantine: Let's create a more specific rule that blocks all inbound except local? Or just block all inbound? Let's block all inbound to quarantine device!
            command = [
                "netsh", "advfirewall", "firewall", "add", "rule",
                "name=CyberTwin_Quarantine",
                "dir=in", "action=block", "profile=any", "remoteip=any"
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return True, "Successfully quarantined: Blocked all inbound traffic (Windows)"
        elif system == "Linux":
            # Add iptables rule to block all inbound except local
            command1 = ["iptables", "-P", "INPUT", "DROP"]
            command2 = ["iptables", "-A", "INPUT", "-i", "lo", "-j", "ACCEPT"]
            result1 = subprocess.run(command1, capture_output=True, text=True, check=True)
            result2 = subprocess.run(command2, capture_output=True, text=True, check=True)
            return True, "Successfully quarantined: Blocked all inbound except localhost (Linux iptables)"
        else:
            return False, f"Unsupported OS for quarantine: {system}"
    except subprocess.CalledProcessError as e:
        return False, f"Failed to quarantine: {e.stderr}"
    except Exception as e:
        return False, f"Error quarantining: {str(e)}"
