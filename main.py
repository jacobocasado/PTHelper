# This is a sample Python script.

# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import nmap3
from colorama import init, Fore, Style
init()

class Address:
    def __init__(self, ip_address, ports):
        self.ip_address = ip_address
        self.ports = ports

def create_address_from_json(json_data):
    ip_address = list(json_data.keys())[0]
    ports_data = json_data[ip_address]['ports']
    ports = {}
    for port in ports_data:
        port_id = port['portid']
        port_info = {
            'protocol': port['protocol'],
            'state': port['state'],
            'service_name': port['service']['name']
        }
        ports[port_id] = port_info
    return Address(ip_address, ports)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    nmap = nmap3.Nmap()
    os_results = nmap.nmap_os_detection("10.0.1.3")

    nmap = nmap3.NmapHostDiscovery()
    results = nmap.nmap_portscan_only("10.0.1.3", args="-p21,22")
    print(results)

    address = create_address_from_json(results)
    print(address.ip_address)
    print(address.ports)
    print(Fore.RED + "IP: " + address.ip_address)

    nmap = nmap3.Nmap()
    vulscan = nmap.nmap_version_detection("10.0.1.3", args="--script vulscan/vulscan.nse -p21")
    print(vulscan)