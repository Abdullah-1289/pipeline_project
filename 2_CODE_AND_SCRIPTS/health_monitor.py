#!/usr/bin/env python3
"""
ICS Security System Health Monitor
Monitors all system services and sends alerts if any fail.

Usage: 
    python3 health_monitor.py              # Run once
    python3 health_monitor.py --daemon     # Run continuously (for systemd service)

Install as systemd service:
    sudo cp health_monitor.service /etc/systemd/system/
    sudo systemctl enable health_monitor
    sudo systemctl start health_monitor
"""

import subprocess
import time
import json
import argparse
import sys
import os
from datetime import datetime
from pathlib import Path

# Configuration
SERVICES = ["mosquitto", "ics_ai_node", "ics_logger"]
CHECK_INTERVAL = 30  # seconds
LOG_FILE = "/home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/health_monitor.log"
ALERT_SCRIPT = None  # Optional: Path to script for email/SMS alerts

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def log_message(message, level="INFO"):
    """Log message to file and optionally print"""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] [{level}] {message}"
    
    with open(LOG_FILE, 'a') as f:
        f.write(log_entry + "\n")
    
    if level == "ERROR":
        print(f"{RED}{log_entry}{RESET}")
    elif level == "WARNING":
        print(f"{YELLOW}{log_entry}{RESET}")
    else:
        print(log_entry)


def check_service(service_name):
    """Check if a systemd service is running"""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True, text=True, timeout=10
        )
        is_active = result.stdout.strip() == "active"
        return is_active, result.stdout.strip()
    except Exception as e:
        return False, f"error: {e}"


def check_mqtt_ports():
    """Check if MQTT ports are listening"""
    try:
        result = subprocess.run(
            ["netstat", "-tlnp"],
            capture_output=True, text=True, timeout=10
        )
        ports = []
        if "8883" in result.stdout:
            ports.append(8883)
        if "1883" in result.stdout:
            ports.append(1883)
        return len(ports) > 0, ports
    except Exception as e:
        return False, [f"error: {e}"]


def check_disk_usage(max_percent=80):
    """Check disk usage of data directory"""
    try:
        result = subprocess.run(
            ["df", "-h", "--output=pcent", "/home/naim/pipeline_project/3_DATA_AND_ARTIFACTS"],
            capture_output=True, text=True, timeout=10
        )
        # Parse the percentage
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 2:
            usage = lines[1].strip().replace('%', '').replace(' ', '')
            percent = int(usage)
            return percent < max_percent, percent
    except Exception as e:
        return True, 0
    return True, 0


def check_log_file_recent(max_hours=1):
    """Check if log file has recent entries"""
    try:
        log_path = "/home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/security_logs.csv"
        if not os.path.exists(log_path):
            return True, None
        
        file_time = os.path.getmtime(log_path)
        current_time = time.time()
        hours_diff = (current_time - file_time) / 3600
        
        return hours_diff < max_hours, hours_diff
    except Exception as e:
        return True, None


def get_system_metrics():
    """Get system metrics (CPU temp, memory, etc.)"""
    metrics = {}
    
    # CPU temperature (RPi)
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_c = int(f.read()) / 1000
            metrics["cpu_temp_c"] = round(temp_c, 1)
    except:
        metrics["cpu_temp_c"] = None
    
    # Memory usage
    try:
        result = subprocess.run(
            ["free", "-m"],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.split('\n')
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 6:
                metrics["memory_used_mb"] = int(parts[2])
                metrics["memory_total_mb"] = int(parts[1])
    except:
        pass
    
    return metrics


def run_health_check():
    """Run a single health check and return status"""
    status = {
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "mqtt_ports": [],
        "disk_ok": True,
        "log_fresh": True,
        "metrics": {}
    }
    
    all_healthy = True
    
    # Check services
    for service in SERVICES:
        is_active, status_str = check_service(service)
        status["services"][service] = status_str
        if not is_active:
            all_healthy = False
    
    # Check MQTT ports
    ports_ok, ports = check_mqtt_ports()
    status["mqtt_ports"] = ports
    if not ports_ok:
        all_healthy = False
    
    # Check disk usage
    disk_ok, disk_pct = check_disk_usage()
    status["disk_ok"] = disk_ok
    status["disk_percent"] = disk_pct
    if not disk_ok:
        all_healthy = False
    
    # Check log file freshness
    log_fresh, hours = check_log_file_recent()
    status["log_fresh"] = log_fresh
    status["log_hours_old"] = round(hours, 1) if hours else None
    if not log_fresh:
        all_healthy = False
    
    # Get system metrics
    status["metrics"] = get_system_metrics()
    
    return all_healthy, status


def send_alert(status):
    """Send alert when issues detected"""
    issues = []
    
    for service, service_status in status["services"].items():
        if service_status != "active":
            issues.append(f"Service {service}: {service_status}")
    
    if status["mqtt_ports"] != [8883, 1883]:
        issues.append(f"MQTT ports not fully available: {status['mqtt_ports']}")
    
    if not status["disk_ok"]:
        issues.append(f"Disk usage high: {status['disk_percent']}%")
    
    if not status["log_fresh"]:
        issues.append(f"Log file stale: {status['log_hours_old']} hours old")
    
    if issues:
        message = f"ICS Security System ALERT:\n" + "\n".join(issues)
        log_message(message, "ERROR")
        
        # TODO: Add email/SMS alert integration here
        # Example: send_email_alert(message)
        # Example: send_sms_alert(message)


def print_status(status):
    """Print formatted status"""
    print("\n" + "="*60)
    print("  ICS Security System - Health Status")
    print("="*60)
    print(f"Timestamp: {status['timestamp']}")
    print()
    
    # Services
    print("Services:")
    for service, service_status in status["services"].items():
        icon = "✓" if service_status == "active" else "✗"
        color = GREEN if service_status == "active" else RED
        print(f"  {color}{icon}{RESET} {service}: {service_status}")
    
    # MQTT Ports
    print("\nMQTT Ports:")
    expected_ports = {8883: "TLS (external)", 1883: "Local"}
    for port in status["mqtt_ports"]:
        print(f"  {GREEN}✓{RESET} Port {port}: {expected_ports.get(port, 'Unknown')}")
    for port in [8883, 1883]:
        if port not in status["mqtt_ports"]:
            print(f"  {RED}✗{RESET} Port {port}: NOT LISTENING")
    
    # Disk
    disk_status = f"{GREEN}OK{RESET}" if status["disk_ok"] else f"{RED}HIGH{RESET}"
    print(f"\nDisk Usage: {disk_status} ({status['disk_percent']}%)")
    
    # Log freshness
    log_status = f"{GREEN}OK{RESET}" if status["log_fresh"] else f"{RED}STALE{RESET}"
    log_age = status['log_hours_old'] if status['log_hours_old'] else "N/A"
    print(f"Log Freshness: {log_status} ({log_age} hours ago)")
    
    # System metrics
    metrics = status["metrics"]
    print("\nSystem Metrics:")
    if metrics.get("cpu_temp_c"):
        temp_color = GREEN if metrics["cpu_temp_c"] < 70 else YELLOW if metrics["cpu_temp_c"] < 80 else RED
        print(f"  {temp_color}CPU Temp: {metrics['cpu_temp_c']}°C{RESET}")
    if metrics.get("memory_used_mb"):
        mem_pct = (metrics["memory_used_mb"] / metrics["memory_total_mb"]) * 100
        mem_color = GREEN if mem_pct < 70 else YELLOW if mem_pct < 90 else RED
        print(f"  {mem_color}Memory: {metrics['memory_used_mb']}MB / {metrics['memory_total_mb']}MB{RESET}")
    
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="ICS Security System Health Monitor")
    parser.add_argument("--daemon", action="store_true", help="Run continuously as daemon")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    args = parser.parse_args()
    
    log_message("Health monitor started", "INFO")
    
    if args.daemon or args.once:
        # Daemon mode
        while True:
            healthy, status = run_health_check()
            print_status(status)
            
            if not healthy:
                send_alert(status)
            
            if args.once:
                break
            
            time.sleep(CHECK_INTERVAL)
    else:
        # Single run
        healthy, status = run_health_check()
        print_status(status)
        
        if not healthy:
            send_alert(status)
            sys.exit(1)
        else:
            print(f"{GREEN}All systems healthy{RESET}")
            sys.exit(0)


if __name__ == "__main__":
    main()

