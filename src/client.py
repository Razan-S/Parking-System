import requests
import uuid
import platform
import cpuinfo
import subprocess
import json

def get_mac_address():
    mac = uuid.getnode()
    return ':'.join(['{:02x}'.format((mac >> ele) & 0xff) for ele in range(40, -1, -8)])

def get_cpu_info():
    try:
        info = cpuinfo.get_cpu_info()
        return info.get('brand_raw', platform.processor())
    except:
        return platform.processor()
    
def get_cpu_serial():
    try:
        system = platform.system()

        if system == "Windows":
            output = subprocess.check_output("wmic cpu get ProcessorId", shell=True)
            lines = output.decode().split("\n")
            serial = lines[1].strip()
            return serial

        elif system == "Linux":
            output = subprocess.check_output("cat /proc/cpuinfo", shell=True)
            for line in output.decode().split("\n"):
                if "Serial" in line or "ID" in line:
                    return line.split(":")[1].strip()
            return "Unknown-Linux"

        elif system == "Darwin":  # macOS
            output = subprocess.check_output("ioreg -l | grep IOPlatformSerialNumber", shell=True)
            serial = output.decode().split('=')[-1].strip().replace('"', '')
            return serial

        else:
            return "Unsupported OS"

    except Exception as e:
        return f"Error: {e}"
    
def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status() 
        ip_data = response.json()
        return ip_data['ip']
    except requests.RequestException as e:
        print(f"Error fetching IP address: {e}")
        return None
    
def ip_to_location(ip):
    try:
        response = requests.get(f'https://ipinfo.io/{ip}/json')
        response.raise_for_status()
        location_data = response.json()
        return json.dumps({
            "city": location_data.get('city', ''),
            "region": location_data.get('region', ''),
            "country": location_data.get('country', ''),
            "loc": location_data.get('loc', '')
        })
    except requests.RequestException as e:
        print(f"Error fetching location for IP {ip}: {e}")
        return None

def get_info():
    mac = get_mac_address()
    cpu_serial = get_cpu_serial()
    cpu_info = get_cpu_info()
    ip = get_public_ip()
    location = ip_to_location(ip) if ip else ''

    payload = {
        'mac': mac,
        'cpu_serial': cpu_serial,
        'cpu_info': cpu_info,
        'public_ip': ip,
        'location': location
    }

    return payload