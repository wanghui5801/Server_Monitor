import psutil
import requests
import time
import platform
import socket
from datetime import datetime, timedelta
import os

SERVER_URL = "http://localhost:5000/update_status"
NODE_NAME = "default"

def get_server_type():
    """Through system characteristics to determine the server type"""
    if platform.system() == "Windows":
        try:
            import wmi
            w = wmi.WMI()
            for item in w.Win32_ComputerSystem():
                if item.Model.lower().find('virtual') != -1:
                    return "VPS"
        except:
            pass
    else:
        # Linux detection - Check product name
        try:
            with open('/sys/class/dmi/id/product_name') as f:
                product_name = f.read().strip().lower()
                # Common virtualization products
                virt_products = [
                    'kvm',
                    'vmware',
                    'virtualbox',
                    'xen',
                    'openstack',
                    'qemu',
                    'amazon ec2',
                    'google compute engine',
                    'microsoft corporation virtual machine',
                    'alibaba cloud ecs',
                    'virtual machine',
                    'bochs'
                ]
                
                if any(virt in product_name for virt in virt_products):
                    return "VPS"
                
                # If not a known virtual machine, it's likely a dedicated server
                return "Dedicated Server"
        except:
            # Fallback to basic detection if file can't be read
            try:
                import subprocess
                result = subprocess.run(['systemd-detect-virt'], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip() != 'none':
                    return "VPS"
            except:
                pass
    
    # Default to Dedicated Server if no virtualization detected
    return "Dedicated Server"

def get_location():
    """
    Get server location information
    """
    try:
        ip = requests.get('https://api.ipify.org').text
        response = requests.get(f'http://ip-api.com/json/{ip}')
        data = response.json()
        if data['status'] == 'success':
            return {
                'country_code': data['countryCode'].lower(),
                'city': data['city']
            }
    except Exception as e:
        print(f"Error getting location: {e}")
    return {
        'country_code': 'unknown',
        'city': 'Unknown'
    }

def get_system_uptime():
    """Get system uptime"""
    try:
        return int((time.time() - psutil.boot_time()) / 86400)  # Convert to days
    except Exception as e:
        print(f"Error getting uptime: {e}")
        return 0

def get_system_load():
    """Get system load"""
    try:
        if platform.system() == "Windows":
            # Windows uses CPU usage instead of load
            return psutil.cpu_percent(interval=1)
        else:
            # Linux/Unix systems use loadavg
            cpu_count = psutil.cpu_count()
            load1, _, _ = psutil.getloadavg()
            return (load1 / cpu_count) * 100
    except Exception as e:
        print(f"Error getting system load: {e}")
        return 0.0

def get_system_info():
    """Get system detailed information"""
    cpu_info = {
        'model': '',
        'cores': psutil.cpu_count(logical=False),
        'threads': psutil.cpu_count()
    }
    
    try:
        if platform.system() == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            cpu_info['model'] = winreg.QueryValueEx(key, "ProcessorNameString")[0]
            winreg.CloseKey(key)
        elif platform.system() == "Linux":
            with open('/proc/cpuinfo') as f:
                for line in f:
                    if "model name" in line:
                        cpu_info['model'] = line.split(':')[1].strip()
                        break
        elif platform.system() == "Darwin":
            cpu_info['model'] = os.popen('sysctl -n machdep.cpu.brand_string').read().strip()
    except Exception as e:
        print(f"Error getting CPU info: {e}")
        cpu_info['model'] = platform.processor() or "Unknown CPU"

    return {
        'cpu': cpu_info,
        'memory_total': psutil.virtual_memory().total,
        'disk_total': psutil.disk_usage('/').total if platform.system() != "Windows" 
                     else psutil.disk_usage('C:\\').total
    }

def get_system_type():
    """Get the specific operating system type"""
    system = platform.system().lower()
    if system == "linux":
        # Detect the specific Linux distribution
        try:
            with open('/etc/os-release') as f:
                os_info = {}
                for line in f:
                    if '=' in line:
                        k,v = line.rstrip().split('=', 1)
                        os_info[k] = v.strip('"')
            
            if 'ID' in os_info:
                return os_info['ID']  # Return debian, ubuntu, centos, etc.
        except:
            pass
        return 'linux'
    elif system == "windows":
        return 'windows'
    elif system == "darwin":
        return 'macos'
    return system

def get_system_stats():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    # Select disk path based on system type
    if platform.system() == "Windows":
        disk = psutil.disk_usage('C:\\')
    else:
        disk = psutil.disk_usage('/')
    
    net_io = psutil.net_io_counters()
    
    # Get network speed
    time.sleep(1)
    net_io_after = psutil.net_io_counters()
    bytes_sent = net_io_after.bytes_sent - net_io.bytes_sent
    bytes_recv = net_io_after.bytes_recv - net_io.bytes_recv
    
    return {
        "node_name": NODE_NAME,
        "type": get_server_type(),
        "location": get_location(),
        "uptime": get_system_uptime(),
        "load": get_system_load(),
        "load_percent": get_system_load(),  # Add load percentage
        "network_speed": {
            "up": bytes_sent,
            "down": bytes_recv
        },
        "traffic": {
            "sent": net_io.bytes_sent / (1024 * 1024 * 1024),
            "received": net_io.bytes_recv / (1024 * 1024 * 1024)
        },
        "cpu": cpu_usage,
        "memory": memory.percent,
        "disk": disk.percent,
        "status": {
            "text": "Running",  # Status types: running, stopped, error
            "type": "running"  # For CSS style judgment: running, stopped, error
        },
        "system_info": get_system_info(),
        "os_type": get_system_type()
    }

def main():
    retry_count = 0
    max_retries = 3
    
    while True:
        try:
            stats = get_system_stats()
            response = requests.post(SERVER_URL, json=stats, timeout=5)
            if response.status_code != 200:
                print(f"Error sending data: {response.status_code}")
                retry_count += 1
            else:
                retry_count = 0  # Reset retry count
                
            if retry_count >= max_retries:
                print("Continuous failure, please check network connection and server status")
                time.sleep(30)  # Wait for a long time before trying again
                retry_count = 0
                
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            retry_count += 1
        except Exception as e:
            print(f"Error: {e}")
            retry_count += 1
            
        time.sleep(5)

if __name__ == "__main__":
    try:
        if platform.system() == "Windows":
            # Check administrator privileges
            import ctypes
            import sys
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("Please run with administrator privileges")
                sys.exit(1)
            # Import Windows specific dependencies
            try:
                import wmi
                import win32api
            except ImportError:
                print("Please install Windows dependencies: pip install wmi pywin32")
                sys.exit(1)
        main()
    except KeyboardInterrupt:
        print("\nMonitor stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        if platform.system() == "Windows":
            print("Please ensure required dependencies are installed: pip install psutil requests wmi pywin32")
        else:
            print("Please ensure required dependencies are installed: pip install psutil requests")
