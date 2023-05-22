# This is a sample Python script.
import argparse
import ipaddress
import json

# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import nmap3
import time
from colorama import init, Fore, Style
init()
import time
import colorama

ascii_art = [
    "██████  ████████ ██   ██ ███████ ██      ██████  ███████ ██████  ",
    "██   ██    ██    ██   ██ ██      ██      ██   ██ ██      ██   ██ ",
    "██████     ██    ███████ █████   ██      ██████  █████   ██████  ",
    "██         ██    ██   ██ ██      ██      ██      ██      ██   ██ ",
    "██         ██    ██   ██ ███████ ███████ ██      ███████ ██   ██ ",
    "",
    ""
]

def fade_text():
    colorama.init()
    gradient = [Fore.LIGHTMAGENTA_EX, Fore.MAGENTA, Fore.BLUE, Fore.LIGHTBLUE_EX]
    for line in ascii_art:
        gradient_idx = 0
        for char in line:
            if char == " ":
                print(" ", end="")
            else:
                color = gradient[gradient_idx % len(gradient)]
                print(color + char, end="")
                gradient_idx += 1
                # time.sleep(0.005)
        print(Style.RESET_ALL)



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

def process_json(input_json):

    check_host_alive(input_json)

    output_json = {}
    # Procesamos solo el primer elemento, que es la IP. El resto de campos son ruido de vulners de momento.
    ip, data = next(iter(input_json.items()))
    output_json[ip] = {}
    if "ports" in data:
        output_json[ip]["ports"] = []
        for port in data["ports"]:
            new_port = {}
            for key in ["protocol", "portid"]:
                if key in port:
                    new_port[key] = port[key]
            if "cpe" in port:
                if len(port["cpe"]) == 1:
                    new_port["cpe"] = port["cpe"][0]["cpe"]
                else:
                    new_port["cpe"] = [cpe["cpe"] for cpe in port["cpe"]]
            if "scripts" in port:
                new_port["scripts"] = []
                for script in port["scripts"]:
                    if "raw" in script:
                        raw_parts = script["raw"].split("\n\n")
                        new_port["scripts"].extend(raw_parts)
            output_json[ip]["ports"].append(new_port)
    if "macaddress" in data:
        output_json[ip]["macaddress"] = {}
        for key in ["addr", "vendor"]:
            if key in data["macaddress"]:
                output_json[ip]["macaddress"][key] = data["macaddress"][key]

    print(json.dumps(output_json, indent=4))
    return json.dumps(output_json, indent=4)


def check_host_alive(dictionary):
    for key, value in dictionary.items():
        if isinstance(value, dict):
            state = value.get("state")
            if isinstance(state, dict) and state.get("state") == "down":
                print(f"Error: Host {key} is down.\nMake sure host is correcly introduced and is reachable (aka. maybe you need proxychains).")
                exit(1)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process IP address and ports.')
    parser.add_argument('-ip', dest='ip_address', type=str, help='IP address to scan')
    parser.add_argument('-p', dest='ports', type=str, help='Ports to scan')
    args = parser.parse_args()

    try:
        ipaddress.ip_address(args.ip_address)
    except ValueError:
        print("Invalid IP address")
        exit(1)

    ports = args.ports.split(',')

    fade_text()

    nmap = nmap3.Nmap()
    os_results = nmap.nmap_os_detection(args.ip_address)

    nmap = nmap3.NmapHostDiscovery()
    results = nmap.nmap_portscan_only(args.ip_address, args=f"-p{args.ports}")

    address = create_address_from_json(results)

    print(Fore.LIGHTBLUE_EX + "Escaneando IP: " + address.ip_address)
    print("\n".join([f"En el puerto {port} se está ejecutando el servicio {data['service_name']}." for port, data in address.ports.items()]))

    nmap = nmap3.Nmap()
    vulscan = nmap.nmap_version_detection(args.ip_address, args=f"--script vulscan/vulscan.nse -p{args.ports}")

    print(vulscan)

    process_json(vulscan)