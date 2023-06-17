import json
from colorama import init, Fore, Style
from nmap3 import nmap3

# Scanner class must receive an IP address and an array of ports.
# Example input: 192.168.1.1, [21,22,80,443]
class Scanner:
    def __new__(cls, ip_address, ports, mode):
        scanner_classes = {
            "nmap": NmapScanner
            # Add here future scanner modes with the flag that the user has to introduce and the children class name.
        }
        scanner_class = scanner_classes.get(mode, Scanner)
        return super(Scanner, cls).__new__(scanner_class)

    # Basic scanner initialization.
    def __init__(self, ip_address, ports, mode):
        self.ip_address = ip_address
        self.ports = ports
        self.mode = mode
        self.open_ports = []
        self.port_context = None
        init()
# Children class that uses Nmap3 library as the scanner type.
# This is the first Scanner type available.
class NmapScanner(Scanner):

    # Call the parent class (Scanner) to receive parameters.
    def __init__(self, ip_address, ports, mode):
        super().__init__(ip_address, ports, mode)
        print(Fore.MAGENTA + f"Initializing {mode} scanner module on {ip_address}. Be ready!")

    def parse_json(self, json_data):
        result = {}
        for ip, data in json_data.items():
            if isinstance(data, dict):
                result[ip] = {}
                cpe = []
                ports = []
                protocols = []
                services = []
                products = []
                versions = []
                for port in data.get('ports', []):
                    ports.append(port.get('portid'))
                    protocols.append(port.get('protocol'))
                    service = port.get('service', {})
                    service_name = service.get('name')
                    if service_name:
                        services.append(service_name)
                    product = service.get('product')
                    if product:
                        products.append(product)
                    version = service.get('version')
                    if version:
                        versions.append(version)
                    cpe.extend([c['cpe'] for c in port.get('cpe', [])])
                result[ip]['cpe'] = list(set(cpe))
                result[ip]['os'] = data.get('osmatch', {}).get('name')
                result[ip]['ports'] = ports
                result[ip]['protocols'] = list(set(protocols))
                result[ip]['services'] = list(set(services))
                result[ip]['products'] = list(set(products))
                result[ip]['versions'] = list(set(versions))
        return result
    def get_open_ports(self, json_data):
        for port_data in json_data:
            if port_data.get('state') == 'open':
                print(Fore.LIGHTMAGENTA_EX + f"[ENUM] Port {port_data.get('portid')} is OPEN.")
                print(Fore.MAGENTA + f"Adding the port to the advanced port scan phase.")
                self.open_ports.append(port_data.get('portid'))

    def openportdiscovery(self):
        # Instantiate the Nmap3 scanner.
        nmap_instance = nmap3.NmapHostDiscovery()
        # Perform the portscan on the specified port range by the user, and in the IP specified.
        results = nmap_instance.nmap_portscan_only(self.ip_address, args=f"-p{self.ports}")
        # We extract the open ports and save them in the instance.
        ports_data = results[self.ip_address]['ports']
        self.get_open_ports(ports_data)

    def performvulnerabilitydiscovery(self):
        nmap_instance = nmap3.Nmap()
        vulners_raw = nmap_instance.nmap_version_detection(self.ip_address,
                                                           args=f"-sV --script vulners -p{','.join(self.open_ports)}")

        print(vulners_raw)
        vulners_formatted = self.parse_json(vulners_raw)

        self.port_context = {
            'port_context_columns': ['Ports', 'Service', 'CPE', 'SCRIPTS'],
            'port_context_rows': [
                {
                    'label': f'{self.ip_address}',
                    'cols': [
                        '\n'.join(map(str, vulners_formatted[self.ip_address]['ports'])),
                        '\n'.join(vulners_formatted[self.ip_address]['services']),
                        '\n'.join(vulners_formatted[self.ip_address]['cpe'])
                    ]
                }
            ]
        }

        print(Fore.LIGHTMAGENTA_EX + f"[ENUM] Vulnerability scan finished. The results of the scan are the following:")

    def scan(self):

        self.openportdiscovery()

        self.performvulnerabilitydiscovery()

        return self.port_context
