import json

from colorama import init, Fore, Style
from nmap3 import nmap3

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
        self.open_ports = []
        self.port_contexts = []
        init() # Initialize the colorama

# Children class that uses Nmap3 library as the scanner type.
# This is the first scanner type available.
class NmapScanner(Scanner):

    # Call the parent class (scanner) to receive parameters.
    def __init__(self, ip_address, ports, mode):
        super().__init__(ip_address, ports, mode)
        print(f"[SCAN] Initializing {mode} scanner module on {ip_address}. Be ready!")

    def transform_json(self, input_json):
        result = []
        for ip, data in input_json.items():
            if ip in ['runtime', 'stats', 'task_results']:
                continue

            ip_dict = {"IP": ip, "OS": data.get('osmatch', {})}

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
                                    port_dict[portid][cve_id] = {"CVSS": cvss, "exploitable": is_exploitable}

                ip_dict.update(port_dict)

            result.append(ip_dict)

        return result

    # Define a method to extract open ports from JSON data returned by nmap3
    # This method looks through the data for each port, and if the state of the port is 'open',
    # it prints a message and adds the port to the list of open ports for this instance
    def get_open_ports(self, json_data):
        for port_data in json_data:
            if port_data.get('state') == 'open':
                print(f"[SCAN] Port {port_data.get('portid')} is OPEN.")
                print(f"[SCAN] Adding the port to the advanced port scan phase.")
                self.open_ports.append(port_data.get('portid'))

    # Define a method to perform a scan of open ports
    # This method creates a new NmapHostDiscovery instance, and performs a scan on the IP and port range specified in the instance
    # It then extracts the open ports from the scan results using the get_open_ports method defined above
    def openportdiscovery(self):
        print(f"[SCAN] Starting port discovery on ", self.ip_address)
        nmap_instance = nmap3.NmapHostDiscovery()
        results = nmap_instance.nmap_portscan_only(self.ip_address, args=f"-p{self.ports}")
        ports_data = results[self.ip_address]['ports']
        self.get_open_ports(ports_data)

    def print_results(self, transformed_json):

        for ip_dict in transformed_json:
            print(f"{Fore.LIGHTGREEN_EX}[INFO] IP: {ip_dict['IP']} IS UP.")
            print(f"[INFO] {ip_dict['OS'] if ip_dict['OS'] else 'OS could not be detected'}.")
            print(Style.RESET_ALL)

            for key, value in ip_dict.items():
                if key not in ['IP', 'OS']:
                    port = key
                    service = value.get('service', '')
                    version = value.get('version', '')

                    cves = [k for k in value.keys() if 'CVE' in k]
                    print(
                        f"{Fore.GREEN}El puerto {port}{Style.RESET_ALL} se encuentra abierto, con el servicio {Fore.MAGENTA}{service}{Style.RESET_ALL} versión {Fore.MAGENTA}{version}{Style.RESET_ALL}. {Fore.RED}Posee {len(cves)} cves asociadas:{Style.RESET_ALL}")

                    for cve in cves:
                        print(f"{Fore.RED}- {cve}{Style.RESET_ALL}")

            print("\n")

    def create_port_contexts(self, transformed_data):
        self.port_contexts = {
            'port_context_columns': ['Ports', 'Service', 'Version'],
            'port_context_rows': []
        }

        for data in transformed_data:
            ip = data['IP']
            os = data['OS']
            del data['IP']
            del data['OS']

            ports = []
            services = []
            cpe = []
            for port, info in data.items():
                ports.append(port)
                services.append(info.get('service', ''))
                cpe.append(info.get('version', ''))

            port_context_rows = {
                'label': ip,
                'cols': ['\n'.join(map(str, ports)), '\n'.join(services), '\n'.join(cpe)]
            }

            self.port_contexts['port_context_rows'].append(port_context_rows)

        return self.port_contexts

    # Define a method to perform a vulnerability discovery on the open ports
    # This method creates a new Nmap instance, performs a vulnerability scan on the open ports,
    # parses the raw results into a more readable format, and then saves these results to the port_context of the instance
    def performvulnerabilitydiscovery(self):

        print(f"Performing vulnerability discovery on", self.ip_address)
        nmap_instance = nmap3.Nmap()
        vulners_raw = nmap_instance.nmap_version_detection(self.ip_address,
                                                           args=f"--script vulners -p{','.join(self.open_ports)}")
        self.print_results(self.transform_json(vulners_raw))

        return(self.create_port_contexts(self.transform_json(vulners_raw)))

    # Define a method to perform a scan
    # This method performs open port discovery and vulnerability discovery, and then returns the port context
    def scan(self):
        self.openportdiscovery()
        self.performvulnerabilitydiscovery()
        return self.port_contexts
