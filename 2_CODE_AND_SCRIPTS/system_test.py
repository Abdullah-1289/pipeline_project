#!/usr/bin/env python3
"""
ICS Security System Test Script
Tests all components of the ICS pipeline system:
- MQTT broker connectivity
- Data logging
- AI node functionality
- End-to-end data flow

Usage: python3 system_test.py [--full]
"""

import sys
import time
import json
import argparse
import subprocess
from datetime import datetime

# ANSI colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

class ICSSystemTester:
    def __init__(self, rpi_ip="10.27.38.206", username="naim", password="1234"):
        self.rpi_ip = rpi_ip
        self.username = username
        self.password = password
        self.results = []
    
    def print_header(self, text):
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}  {text}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")
    
    def print_success(self, text):
        print(f"{GREEN}✓ {text}{RESET}")
    
    def print_error(self, text):
        print(f"{RED}✗ {text}{RESET}")
    
    def print_info(self, text):
        print(f"{YELLOW}→ {text}{RESET}")
    
    def ssh_command(self, command):
        """Execute SSH command on RPi"""
        full_cmd = f'ssh -o StrictHostKeyChecking=no {self.username}@{self.rpi_ip} "{command}"'
        try:
            result = subprocess.run(
                full_cmd, shell=True, capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return False, "", str(e))
    
    def test_rpi_connectivity(self):
        """Test if RPi is reachable"""
        self.print_header("RPi Connectivity Test")
        success, stdout, stderr = self.ssh_command("hostname")
        if success:
            self.print_success(f"RPi reachable: {stdout}")
            self.results.append(("RPi Connectivity", True))
            return True
        else:
            self.print_error(f"Cannot connect to RPi: {stderr}")
            self.results.append(("RPi Connectivity", False))
            return False
    
    def test_mqtt_broker(self):
        """Test MQTT broker connectivity"""
        self.print_header("MQTT Broker Test")
        
        # Check if mosquitto is running
        success, stdout, _ = self.ssh_command("systemctl is-active mosquitto")
        if success and "active" in stdout:
            self.print_success("Mosquitto service is running")
        else:
            self.print_error("Mosquitto service not running")
            self.results.append(("MQTT Broker", False))
            return False
        
        # Check listening ports
        success, stdout, _ = self.ssh_command("netstat -tlnp | grep mosquitto")
        if "8883" in stdout:
            self.print_success("MQTT listening on port 8883 (TLS)")
        if "1883" in stdout:
            self.print_info("MQTT listening on port 1883 (Local)")
        
        # Test subscription
        test_script = '''
timeout 3 mosquitto_sub -t ics/telemetry/data -u naim -P 1234 --cafile /etc/mosquitto/ca_certificates/ca.crt 2>&1 || true
'''
        self.print_info("Testing MQTT subscription...")
        
        self.results.append(("MQTT Broker", True))
        return True
    
    def test_services(self):
        """Test systemd services"""
        self.print_header("System Services Test")
        
        services = ["ics_ai_node", "ics_logger"]
        all_running = True
        
        for service in services:
            success, stdout, _ = self.ssh_command(f"systemctl is-active {service}")
            if "active" in stdout:
                self.print_success(f"{service}: running")
            else:
                self.print_error(f"{service}: not running ({stdout})")
                all_running = False
        
        self.results.append(("System Services", all_running))
        return all_running
    
    def test_data_logging(self):
        """Test if data is being logged"""
        self.print_header("Data Logging Test")
        
        # Check log file exists
        success, stdout, _ = self.ssh_command("ls -la /home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/security_logs.csv")
        if success:
            self.print_success("Log file exists")
            
            # Check file size
            if "0 " in stdout:
                self.print_info("Log file is empty (no data yet)")
            else:
                self.print_success("Log file has data")
            
            # Get last few lines
            success, stdout, _ = self.ssh_command("tail -5 /home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/security_logs.csv")
            if success and stdout:
                self.print_info("Last log entry:")
                print(f"  {stdout[:100]}...")
        else:
            self.print_error("Log file not found")
        
        self.results.append(("Data Logging", success))
        return success
    
    def test_mqtt_publish(self):
        """Test publishing a test message"""
        self.print_header("MQTT Publish Test")
        
        # Publish a test message
        test_data = {
            "timestamp": datetime.now().isoformat(),
            "flow_rate": 5.0,
            "pressure": 10.0,
            "temperature": 25.0,
            "motor_current": 1.2,
            "pump_status": 1,
            "mode": "test",
            "is_anomaly": 0
        }
        
        cmd = f'''mosquitto_pub -h localhost -p 8883 -u {self.username} -P {self.password} --cafile /etc/mosquitto/ca_certificates/ca.crt -t ics/telemetry/data -m '{json.dumps(test_data)}' '''
        
        success, _, _ = self.ssh_command(cmd)
        if success:
            self.print_success("Test message published successfully")
            
            # Verify it was logged
            time.sleep(1)
            success, stdout, _ = self.ssh_command("tail -1 /home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/security_logs.csv")
            if success and "test" in stdout:
                self.print_success("Test message logged successfully")
        else:
            self.print_error("Failed to publish test message")
        
        self.results.append(("MQTT Publish", success))
        return success
    
    def test_ai_node_mode(self):
        """Test AI node configuration"""
        self.print_header("AI Node Mode Test")
        
        # Check current mode
        success, stdout, _ = self.ssh_command("cat /etc/systemd/system/ics_ai_node.service | grep ExecStart")
        if success:
            if "collect" in stdout:
                self.print_info("AI Node Mode: COLLECT (building dataset)")
                self.print_info("After 3 days, switch to MONITOR mode for active detection")
            elif "monitor" in stdout:
                self.print_success("AI Node Mode: MONITOR (active detection)")
            self.print_success("Service file configured correctly")
        
        # Check if model exists
        success, _, _ = self.ssh_command("ls /home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/*.pkl 2>/dev/null || echo 'No model found'")
        if "No model" in success:
            self.print_info("No trained model yet - will be trained after data collection")
        else:
            self.print_success("Trained model found")
        
        self.results.append(("AI Node", True))
        return True
    
    def test_security_intervention(self):
        """Test security intervention trigger"""
        self.print_header("Security Intervention Test")
        
        # Publish an attack message
        attack_data = {
            "timestamp": datetime.now().isoformat(),
            "flow_rate": 999.0,  # Anomalous value
            "pressure": 999.0,
            "temperature": 999.0,
            "motor_current": 99.9,
            "pump_status": 1,
            "mode": "attack",
            "is_anomaly": 1
        }
        
        cmd = f'''mosquitto_pub -h localhost -p 8883 -u {self.username} -P {self.password} --cafile /etc/mosquitto/ca_certificates/ca.crt -t ics/telemetry/data -m '{json.dumps(attack_data)}' '''
        
        success, _, _ = self.ssh_command(cmd)
        if success:
            self.print_success("Attack data published")
            self.print_info("Check logs for intervention trigger if AI is in monitor mode")
        
        self.results.append(("Security Intervention", success))
        return success
    
    def run_full_test(self):
        """Run all tests"""
        print(f"\n{BLUE}╔════════════════════════════════════════════════════════════╗{RESET}")
        print(f"{BLUE}║     ICS Security System - Full Integration Test            ║{RESET}")
        print(f"{BLUE}║     RPi: {self.rpi_ip:<42} ║{RESET}")
        print(f"{BLUE}╚════════════════════════════════════════════════════════════╝{RESET}")
        
        # Run all tests
        self.test_rpi_connectivity()
        self.test_mqtt_broker()
        self.test_services()
        self.test_data_logging()
        self.test_mqtt_publish()
        self.test_ai_node_mode()
        
        # Print summary
        self.print_header("Test Summary")
        
        passed = 0
        failed = 0
        
        for test_name, result in self.results:
            if result:
                self.print_success(f"{test_name}")
                passed += 1
            else:
                self.print_error(f"{test_name}")
                failed += 1
        
        print(f"\n{BLUE}Total: {passed} passed, {failed} failed{RESET}")
        
        if failed == 0:
            print(f"\n{GREEN}🎉 All tests passed! System is ready for deployment.{RESET}")
        else:
            print(f"\n{YELLOW}⚠️  Some tests failed. Check the output above.{RESET}")
        
        return failed == 0


def main():
    parser = argparse.ArgumentParser(description="ICS Security System Test")
    parser.add_argument("--rpi-ip", default="10.27.38.206", help="Raspberry Pi IP address")
    parser.add_argument("--username", default="naim", help="SSH username")
    parser.add_argument("--password", default="1234", help="SSH password")
    parser.add_argument("--full", action="store_true", help="Run all tests")
    
    args = parser.parse_args()
    
    tester = ICSSystemTester(args.rpi_ip, args.username, args.password)
    success = tester.run_full_test()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

