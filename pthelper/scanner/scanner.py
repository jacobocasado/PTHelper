import ipaddress
import os

import nvdlib

from colorama import Fore, Style
from nmap3 import nmap3
from functools import wraps
from tqdm import tqdm

from config.pthelper_config import pthelper_config

def add_scanner_prefix(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        print (f"{Fore.MAGENTA}[SCANNER]{Style.RESET_ALL}", end=" ")
        return func(self, *args, **kwargs)
    return wrapper

# Define a scanner class that takes in ip_address, ports, and mode of scan
class Scanner:
    # Use __new__ to create a new instance of the scanner_class based on the provided mode
    def __new__(cls, ip_address, ports, mode):
        # A dictionary to map different scanning modes to respective classes
        scanner_classes = {
            "nmap": NmapScanner
            # For future scanner modes, add the user-defined flag and the corresponding child class name here
        }
        # Get the scanner_class from the dictionary, default is scanner itself
        scanner_class = scanner_classes.get(mode, Scanner)
        return super(Scanner, cls).__new__(scanner_class)

    # Initialize the scanner with ip_address, ports, and mode. Initialize open_ports list and port_context
    def __init__(self, ip_address, ports, mode):
        self.ip_address = ip_address
        self.os_cpe = None
        self.ports = ports
        self.mode = mode
        self.open_ports = None
        self.port_contexts = []
        self.parsed_scan_result = {}
        self.cveinfo = {}

# Children class that uses Nmap3 library as the scanner type.
# This is the first scanner type available.
class NmapScanner(Scanner):

    # Call the parent class (scanner) to receive parameters.
    @add_scanner_prefix
    def __init__(self, ip_address, ports, mode):
        super().__init__(ip_address, ports, mode)
        print(f"Initializing {mode} scanner module on {ip_address}.")

    def parse_scan_results(self, input_json):
        for ip, data in input_json.items():
            if ip in ['runtime', 'stats', 'task_results']:
                continue

            ip_dict = {}

            for port_info in data.get('ports', []):
                portid = port_info.get('portid', '')
                service = port_info.get('service', {}).get('name', '')
                version = port_info.get('service', {}).get('version', '')

                port_dict = {portid: {"service": service, "version": version}}

                for script in port_info.get('scripts', []):
                    if script.get('name', '') == 'vulners':
                        for cve, cve_data in script.get('data', {}).items():
                            for vuln in cve_data.get('children', []):
                                cvss = vuln.get('cvss', '')
                                cve_id = vuln.get('id', '')

                                if 'CVE' in cve_id:
                                    try:
                                        r = nvdlib.searchCVE(cveId=cve_id, key=pthelper_config.NVD_API_KEY, delay=12)[0]

                                        port_dict[portid][cve_id] = {
                                                                    "cve": cve_id,
                                                                    "cvss": cvss,
                                                                    "score_type": r.score[0],
                                                                    "score": r.score[1],
                                                                    "severity": r.score[2],
                                                                    "description": r.descriptions[0].value}

                                    except Exception as e:
                                        print(e)

                                        port_dict[portid][cve_id] = {
                                                "cve": cve_id,
                                                "CVSS": cvss
                                        }

                                        print('\nERROR-3: No se ha podido conectar con NVD o no se ha encontrado CVEs.')
                                        pass

                ip_dict.update(port_dict)

            self.parsed_scan_result[ip] = ip_dict

    # Define a method to perform a scan of open ports
    # This method creates a new NmapHostDiscovery instance, and performs a scan on the IP and port range specified in the instance
    # It then extracts the open ports from the scan results using the get_open_ports method defined above
    @add_scanner_prefix
    def openportdiscovery(self):
        print(f"Starting port discovery on", self.ip_address, end=". \n")
        nmap_instance = nmap3.NmapHostDiscovery()
        results = nmap_instance.nmap_portscan_only(self.ip_address, args=f"-p{self.ports}")

        self.ip_open_ports = {}

        # Iterate over all IP addresses in the results
        for ip, data in results.items():
            # Skip entries that are not IPs (e.g., 'runtime', 'stats', etc.)
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                continue

            # Extract port data
            ports_data = data['ports']
            open_ports = []

            # Iterate over all ports for the current IP
            for port_data in ports_data:
                # Check if port is open
                if port_data['state'] == 'open':
                    open_ports.append(port_data['portid'])

            # Add open ports for current IP to dictionary only if there is at least one open port
            if open_ports:
                self.ip_open_ports[ip] = open_ports

        # If no open ports were found on any IP, terminate the program
        if not self.ip_open_ports:
            print(f"No open ports found on any IP. Make sure you are inserting valid IP addresses.")
            exit(0)

        print(self.ip_open_ports)
        return self.ip_open_ports



    # Define a method to perform a vulnerability discovery on the open ports
    # This method creates a new Nmap instance, performs a vulnerability scan on the open ports,
    # parses the raw results into a more readable format, and then saves these results to the port_context of the instance
    @add_scanner_prefix
    def performvulnerabilitydiscovery(self):

        # Generate a set of all unique open ports across all IPs
        all_open_ports = {port for ports in self.ip_open_ports.values() for port in ports}
        # Join all unique open ports with commas
        ports_str = ','.join(all_open_ports)

        nmap_instance = nmap3.Nmap()

        # Iterate over all IP addresses
        for ip in self.ip_open_ports.keys():
            print(f"Performing vulnerability discovery on", ip)
            vulners_raw = nmap_instance.nmap_version_detection(
                ip,
                args=f"--script vulners -p{ports_str}"
            )
            print(vulners_raw)
            self.parse_scan_results(vulners_raw)

    @add_scanner_prefix
    def performosdiscovery(self):
        # nmap_os_detection can only be performed with sudo privileges.
        # This line if code ensures we are root. If not, we just print that the script is not running as root
        if os.geteuid() == 0:
            nmap_instance = nmap3.Nmap()
            os_results = nmap_instance.nmap_os_detection(self.ip_address)

            for ip, attributes in self.parsed_scan_result.items():
                os_name = os_results[ip]['osmatch'][0]['name']
                cpe = os_results[ip]['osmatch'][0]['name']

                dict = {"os": os_name,
                        "os_cpe": cpe
                        }

                self.parsed_scan_result[ip].update(dict)

        else:
            dict = {"os": "Unknown",
                    "os_cpe": "Unknown"
                    }
            for ip, attributes in self.parsed_scan_result.items():
                self.parsed_scan_result[ip].update(dict)

            print(
                f"PTHelper not running as root. OS scan will not work, losing this information for all the assessment.")
        pass

    # Define a method to perform a scan
    # This method performs open port discovery and vulnerability discovery, and then returns the port context
    def scan(self):

        self.openportdiscovery()

        self.performvulnerabilitydiscovery()

        self.performosdiscovery()

        print(self.parsed_scan_result)
        return self.parsed_scan_result