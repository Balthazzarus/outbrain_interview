from flask import Flask, jsonify
import os
import requests
import psutil
import platform
import socket

app = Flask(__name__)

# Function to check Consul server status
def get_consul_cluster_status():
    ip_address = "192.168.50.15"
    consul_port = 8500
    ssh_port = 22
    # Check if the host is reachable
    try:
        socket.create_connection((ip_address, ssh_port), timeout=1)
    except socket.error:
        return {"status": 0, "message": "Consul server is down"}
    
    # If host is reachable, try to connect to Consul HTTP API
    url = f"http://{ip_address}:{consul_port}/v1/agent/self"
    try:
        response = requests.get(url, timeout=1)
        response.raise_for_status()  # Raise HTTPError for 4xx or 5xx status codes
        return {"status": 1, "message": "Consul server is running"}
    except requests.exceptions.RequestException as e:
        return {"status": 0, "message": "Server is available but failed to connect to Consul server API"}

# Function to fetch Consul cluster summary
def get_consul_cluster_summary():
    url_reg_nodes = "http://192.168.50.15:8500/v1/catalog/nodes"
    url_reg_services = "http://192.168.50.15:8500/v1/catalog/services"
    url_leader = "http://192.168.50.15:8500/v1/status/leader"
    url_protocol_version = "http://192.168.50.15:8500/v1/agent/self"
    response_nodes = requests.get(url_reg_nodes)
    response_services = requests.get(url_reg_services)
    response_leader = requests.get(url_leader)
    response_protocol = requests.get(url_protocol_version)
    if response_nodes.status_code == 200:
        nodes = response_nodes.json()
        services = response_services.json()
        leader = response_leader.json()
        protocol = response_protocol.json()
        protocol_version = protocol["Stats"]["raft"]["protocol_version"]
        return {"registered_nodes": len(nodes),
                "registered_services": len(services),
                "leader" : leader,
                "protocol_version" :  protocol_version       }          
        
    else:
        return {"error": "Failed to retrieve Consul summary"}

# Function to fetch Consul cluster members
def get_consul_cluster_members():
    url = "http://192.168.50.15:8500/v1/agent/members"
    response = requests.get(url)
    if response.status_code == 200:
        members = response.json()
        names = [member.get("Name") for member in members]
        return {"registered_nodes" : names }
    else:
        return {"error": "Failed to retrieve Consul members"}
    
# Function to return system uptime in days in LINUX systems
def get_system_uptime():
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        uptime_days = uptime_seconds / (3600 * 24)  # Convert seconds to days
        return round(uptime_days)

# Function to get NIC infromation exclude "lo" 
def get_network_info():
    interfaces = psutil.net_if_addrs()
    network_info = {}
    
    for interface_name, addresses in interfaces.items():
        address_info = []
        if interface_name != "lo":
            for address in addresses:
                if address.family == socket.AF_INET and interface_name != "lo":
                    address_info.append({
                    "address": address.address,
                    "netmask": address.netmask,
                    "broadcast": address.broadcast
                    })
            network_info[interface_name] = address_info
    return network_info

# Function calculate GB and round it up
def bytes_to_gb(bytes_value):
    """
    Convert bytes to gigabytes (GB) and round up to the nearest whole number.
    """
    gb_value = bytes_value / (1024 ** 3)  # 1 GB = 1024^3 bytes
    return round(gb_value)

# Function to fetch system information
def get_system_info():
    # Get CPU information
    cpu_info = {
        "cpu_count": psutil.cpu_count(),
    }
    # Get memory information
    mem_info = {
        "total_memory": bytes_to_gb(psutil.virtual_memory().total),
    }
     #Get disk information
    disk_usage = psutil.disk_usage('/')
    disk_info = {
        "total_disk": bytes_to_gb(disk_usage.total), 
    }

    load_avg = os.getloadavg()

    uptime_info = {"uptime_days": get_system_uptime()}

    network_info = {"Interfaces": get_network_info()} 

    os_info = {
        "os": {
            "platform": platform.system(),
            "release" : platform.release(),
            "build" : platform.version()
        }
    }

    # Combine all information
    system_info = {
        "cpu": cpu_info,
        "memory": mem_info,
        "disk" : disk_info,
        "os": os_info,
        "System Up Time": uptime_info,
        "Load Avarage" : {"1 minutes" : load_avg[0],
                          "5 minutes" : load_avg[1],
                          "15 minutes" : load_avg[2]},
        "Network Info" : network_info
    }

    return system_info

@app.route('/v1/api/consulCluster/status', methods=['GET'])
def consul_cluster_status():
    return jsonify(get_consul_cluster_status())

@app.route('/v1/api/consulCluster/summary', methods=['GET'])
def consul_cluster_summary():
    return jsonify(get_consul_cluster_summary())

@app.route('/v1/api/consulCluster/members', methods=['GET'])
def consul_cluster_members():
    return jsonify(get_consul_cluster_members())

@app.route('/v1/api/consulCluster/systemInfo', methods=['GET'])
def system_info():
    return jsonify(get_system_info())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
