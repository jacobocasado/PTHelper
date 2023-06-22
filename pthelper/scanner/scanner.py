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
        self.port_context = None
        init() # Initialize the colorama

# Children class that uses Nmap3 library as the scanner type.
# This is the first scanner type available.
class NmapScanner(Scanner):

    # Call the parent class (scanner) to receive parameters.
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
                cves = []

                for port in data.get('ports', []):
                    port_cve = []
                    ports.append(port.get('portid'))
                    protocols.append(port.get('protocol'))
                    service = port.get('service', {})
                    service_name = service.get('name')
                    scripts = port.get('scripts')
                    if service_name:
                        services.append(service_name)
                    product = service.get('product')
                    if product:
                        products.append(product)
                    version = service.get('version')
                    if version:
                        versions.append(version)
                    cpe.extend([c['cpe'] for c in port.get('cpe', [])])
                    # Añadir CVEs
                    if scripts:
                        for script in scripts:
                            if 'data' in script:
                                for cpe_info, cpe_data in script['data'].items():
                                    if 'children' in cpe_data:
                                        for child in cpe_data['children']:
                                                port_cve.append({'id': child['id'], 'cvss': child['cvss'], 'exploitable': child['is_exploit'], })
                    cves.append(port_cve)

                    # TODO add this list into CVE and check for duplicates.
                    #keyword = product + ' ' + version
                    #print(keyword)
                    #searchresult = nvdlib.searchCVE(keywordSearch=keyword, keywordExactMatch=True)

                    # Imprimir los IDs de los CVEs encontrados
                    #for result in searchresult:
                     #   print(result)

                result[ip]['cpe'] = list(set(cpe))
                result[ip]['os'] = data.get('osmatch', {}).get('name')
                result[ip]['ports'] = ports
                result[ip]['protocols'] = list(set(protocols))
                result[ip]['services'] = list(set(services))
                result[ip]['products'] = list(set(products))
                result[ip]['versions'] = list(set(versions))
                result[ip]['cves'] = cves

        return result

    # Define a method to extract open ports from JSON data returned by nmap3
    # This method looks through the data for each port, and if the state of the port is 'open',
    # it prints a message and adds the port to the list of open ports for this instance
    def get_open_ports(self, json_data):
        for port_data in json_data:
            if port_data.get('state') == 'open':
                print(Fore.LIGHTMAGENTA_EX + f"[ENUM] Port {port_data.get('portid')} is OPEN.")
                print(Fore.MAGENTA + f"Adding the port to the advanced port scan phase.")
                self.open_ports.append(port_data.get('portid'))

    # Define a method to perform a scan of open ports
    # This method creates a new NmapHostDiscovery instance, and performs a scan on the IP and port range specified in the instance
    # It then extracts the open ports from the scan results using the get_open_ports method defined above
    def openportdiscovery(self):
        nmap_instance = nmap3.NmapHostDiscovery()
        results = nmap_instance.nmap_portscan_only(self.ip_address, args=f"-p{self.ports}")
        ports_data = results[self.ip_address]['ports']
        self.get_open_ports(ports_data)

    def print_info(self, context):
        from colorama import Fore, Style, init

        init(autoreset=True)  # Inicializar colorama
        # TODO


    # Define a method to perform a vulnerability discovery on the open ports
    # This method creates a new Nmap instance, performs a vulnerability scan on the open ports,
    # parses the raw results into a more readable format, and then saves these results to the port_context of the instance
    def performvulnerabilitydiscovery(self):
        nmap_instance = nmap3.Nmap()
        vulners_raw = nmap_instance.nmap_version_detection(self.ip_address,
                                                           args=f"--script vulners -p{','.join(self.open_ports)}")
        print(vulners_raw)
        vulners_formatted = self.parse_json(vulners_raw)
        print(vulners_formatted)
        self.port_context = {
            'port_context_columns': ['Ports', 'Service', 'CPE', 'CVE'],
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

    # Define a method to perform a scan
    # This method performs open port discovery and vulnerability discovery, and then returns the port context
    def scan(self):
        self.openportdiscovery()
        self.performvulnerabilitydiscovery()
        return self.port_context
