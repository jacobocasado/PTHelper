import ipaddress
import json
import re

from colorama import Fore, Style
from nmap3 import nmap3
from functools import wraps

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
        self.ports = ports
        self.mode = mode
        self.open_ports = None
        self.port_contexts = []
        self.result = {}

# Children class that uses Nmap3 library as the scanner type.
# This is the first scanner type available.
class NmapScanner(Scanner):

    # Call the parent class (scanner) to receive parameters.
    @add_scanner_prefix
    def __init__(self, ip_address, ports, mode):
        super().__init__(ip_address, ports, mode)
        print(f"Initializing {mode} scanner module on {ip_address}.")

    def transform_json(self, input_json):
        for ip, data in input_json.items():
            if ip in ['runtime', 'stats', 'task_results']:
                continue

            ip_dict = {"OS": data.get('osmatch', {})}

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
                                is_exploitable = vuln.get('is_exploit', '')
                                cve_id = vuln.get('id', '')

                                if 'CVE' in cve_id:
                                    port_dict[portid][cve_id] = {"CVSS": cvss}
                                        # , "exploitable": is_exploitable} # Does not add extra info.

                ip_dict.update(port_dict)

            self.result[ip] = ip_dict

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

        return self.ip_open_ports

    @add_scanner_prefix
    def print_results(self):

        for ip, ip_dict in self.result.items():
            print(f"{ip} UP", end=". ")
            os_info = ip_dict.get('OS', None)
            if os_info:
                print(f"{os_info}")
            else:
                print(f"{Fore.RED}OS could not be detected.{Fore.RESET} There is not enough information to fingerprint the host.")
            print(Style.RESET_ALL)

            for port, value in ip_dict.items():
                if port != 'OS':
                    service = value.get('service', '')
                    version = value.get('version', '')

                    cves = [k for k in value.keys() if 'CVE' in k]
                    print(
                        f"{Fore.GREEN}El puerto {port}{Style.RESET_ALL} se encuentra abierto, con el servicio {Fore.MAGENTA}{service}{Style.RESET_ALL} versión {Fore.MAGENTA}{version}{Style.RESET_ALL}. {Fore.RED}Posee {len(cves)} cves asociadas:{Style.RESET_ALL}")

                    for cve in cves:
                        print(f"{Fore.RED}- {cve}{Style.RESET_ALL}")

            print("\n")

    def create_port_contexts(self):
        self.port_contexts = {
            'port_context_columns': ['Ports', 'Service', 'Version', 'CVEs'],
            'port_context_rows': []
        }

        for ip, data in self.result.items():
            os = data.get('OS', {})
            ports = []
            services = []
            versions = []
            cves = []
            for port, info in data.items():
                if port != 'OS':
                    ports.append(port)
                    services.append(info.get('service', ''))
                    versions.append(info.get('version', ''))

                    # Extract CVEs
                    cve_info = [key for key in info.keys() if key.startswith('CVE-')]
                    cves.append(", ".join(cve_info))

            port_context_rows = {
                'label': ip,
                'cols': ['\n'.join(map(str, ports)), '\n'.join(services), '\n'.join(versions), '\n'.join(cves)]
            }

            self.port_contexts['port_context_rows'].append(port_context_rows)

        return self.port_contexts

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
            self.transform_json(vulners_raw)
        self.print_results()

        # If create_port_contexts function needs all data at once, return here
        return self.create_port_contexts()

    # Define a method to perform a scan
    # This method performs open port discovery and vulnerability discovery, and then returns the port context
    def scan(self):
        self.openportdiscovery()
        self.performvulnerabilitydiscovery()
        return self.port_contexts, self.result