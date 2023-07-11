# Third-party libraries/modules
import ipaddress
import os
import nvdlib

from colorama import Fore, Style
from nmap3 import nmap3
from functools import wraps

# Local configuration file of PTHelper
from config.pthelper_config import pthelper_config

# Wrapper to print [SCANNER] when the scanner prints a message.
# Made in order to differentiate between module outputs.
# Note that the Scanner module does not show scan info, only information about errors, and when it starts/ends
# doing some operations.
def add_scanner_prefix(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        print (f"{Fore.MAGENTA}[SCANNER]{Style.RESET_ALL}", end=" ") # Change here to any word
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
    def __init__(self, scanned_ips, scanned_ports, mode):

        # Depending on the mode, will be one children class or another.
        self.mode = mode

        # INPUT OF THE MODULE
        # Save the IPs and ports to scan in a variable
        self.scanned_ips = scanned_ips
        self.scanned_ports = scanned_ports

        # OUTPUT OF THE MODULE
        # Dictionary with scan results.
        self.scanner_output = {}

        # Informative message
        print(f"Initializing {mode} scanner module on {scanned_ips}.")

# Children class that uses Nmap3 library as the scanner type.
# This is the first scanner type available.
class NmapScanner(Scanner):

    # Call the parent class (scanner) to receive parameters.
    def __init__(self, ip_address, scanned_ports, mode):
        super().__init__(ip_address, scanned_ports, mode)
        # Variable to store the open ports in all the IPs, to perform further scan on these ports.
        self.ip_open_ports = {}

    # Define a method to perform a scan of open ports
    # This method creates a new NmapHostDiscovery instance, and performs a scan on the IP and port range specified in the instance
    @add_scanner_prefix
    def open_port_discovery(self):

        print(f"Starting port discovery on", self.scanned_ips, end=". \n")

        # Instanciate the nmap3 instance
        nmap_instance = nmap3.NmapHostDiscovery()
        # Extract the results from the nmap3 portscan only scan
        results = nmap_instance.nmap_portscan_only(self.scanned_ips, args=f"-p{self.scanned_ports}")

        # Iterate over all the elements in the results dictionary.
        for ip, data in results.items():
            # Skip entries that are not IPs (e.g., 'runtime', 'stats', etc.)
            # For that we just look for an IP address key in the dictionary.
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                continue

            # Extract port data from that IP.
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

        # If no open ports were found on any IP, terminate the program as the next phases don't have sense.
        if not self.ip_open_ports:
            print(f"No open ports found on any IP. Make sure you are inserting valid IP addresses.")
            exit(0)

    # Define a method to perform a vulnerability discovery on the open ports
    # This method creates a new Nmap instance, performs a vulnerability scan on the open ports,
    # and calls another method to parse the scan results of this vulnerability scan
    # and perform NVD queries to enhance the information obtained.
    @add_scanner_prefix
    def performvulnerabilitydiscovery(self):

        # Generate a set of all unique open ports across all IPs
        all_open_ports = {port for ports in self.ip_open_ports.values() for port in ports}
        # Join all unique open ports with commas
        ports_str = ','.join(all_open_ports)

        # Instantiate the nmap3 instance.
        nmap_instance = nmap3.Nmap()

        # Iterate over all IP addresses.
        for ip in self.ip_open_ports.keys():
            print(f"Performing vulnerability discovery on", ip)
            vulners_raw = nmap_instance.nmap_version_detection(
                ip,
                args=f"--script vulners -p{ports_str}"
            )
            # Calls a function that parses this scan for this IP and enhances it with extra information.
            self.parse_and_enhance_vulners(vulners_raw)

    # Method that takes the vulners raw dictionary and extracts the useful information for the assessment,
    # and stores it in a way that will be useful for the rest of the modules.
    # Also, the information gets enhanced as the CVE IDs are used to perform queries to the NVD using the CVE ID.
    @add_scanner_prefix
    def parse_and_enhance_vulners(self, input_json):
        # We ignore these JSON information as it is not useful for the assessment.
        for ip, data in input_json.items():
            if ip in ['runtime', 'stats', 'task_results']:
                continue

            # Save the useful information for each of the IPs
            ip_dict = {}

            # For each port of the IP containing information
            for port_info in data.get('ports', []):

                portid = port_info.get('portid', '') # Extract port number
                service = port_info.get('service', {}).get('name', 'Unknown') # Extract name of the service in port
                version = port_info.get('service', {}).get('version', 'Unknown') # Extract version of the service in port

                # Create a dict with all these values an the port ID as the key
                port_dict = {portid: {"service": service, "version": version}}

                # For each one of the scripts executed in the port
                for script in port_info.get('scripts', []):
                    # If the script name is VULNERS (we want that)
                    if script.get('name', '') == 'vulners':
                        # Extract the cve and cve data from the script data field
                        for cve, cve_data in script.get('data', {}).items():
                            # For each one of the vulns inside a cve (Don't know why vulners has this structure, but OK)
                            for vuln in cve_data.get('children', []):

                                # Obtain the CVSS and CVE ID of the vulnerability.
                                cve_id = vuln.get('id', '')
                                cvss = vuln.get('cvss', '')

                                # If the vuln is a CVE (there can be vulns that are not CVEs, but it is rare).
                                # Nevertheless, I do this to manage all situations :)
                                if 'CVE' in cve_id:
                                    # Try to perform a query to the NVD for that ID.
                                    try:
                                        # Perform the query.
                                        # TODO tamper with the delay field.
                                        r = nvdlib.searchCVE(cveId=cve_id, key=pthelper_config.NVD_API_KEY, delay=12)[0]

                                        # Store the CVE ID, the CVSS and also the CVSS score and CVE description
                                        # from the NVD query.
                                        port_dict[portid][cve_id] = {
                                                                    "cve": cve_id,
                                                                    "description": r.descriptions[0].value,
                                                                    "cvss": cvss,
                                                                    "score_type": r.score[0],
                                                                    "score": r.score[1],
                                                                    "severity": r.score[2]
                                                                    }
                                    # Sometimes (more than often) the NIST API is slow, or rejects the query.
                                    except Exception as e:

                                        # In that case, we just store the base information obtained without the NVD.
                                        port_dict[portid][cve_id] = {
                                                "cve": cve_id,
                                                "CVSS": cvss
                                        }

                                        # Go to the next IP to handle the exception.
                                        pass
                # Update the dictionary of IPs with that port.
                ip_dict.update(port_dict)

            # When all ports of that IP are parsed and enhanced, update the output dictionary.
            self.scanner_output[ip] = ip_dict

    # Method that uses another nmap module to perform an OS detection.
    # This method can only be executed as root, therefore, the check is performed before doing operations.
    @add_scanner_prefix
    def performosdiscovery(self):
        # nmap_os_detection can only be performed with sudo privileges.
        # This line if code ensures we are root. If not, we just print that the script is not running as root
        if os.geteuid() == 0:
            # Instantiate the scanner
            nmap_instance = nmap3.Nmap()
            # Perform the OS scan into the IPs in range
            os_results = nmap_instance.nmap_os_detection(self.scanned_ips)

            # For each of the IPs scanned
            for ip, attributes in self.scanner_output.items():
                # Extract the OS name and OS cpe
                os_name = os_results[ip]['osmatch'][0]['name']
                cpe = os_results[ip]['osmatch'][0]['name']

                # Save these values in a dictionary
                dict = {"os": os_name,
                        "os_cpe": cpe
                        }

                # Update the dictionary of that IP with those values
                self.scanner_output[ip].update(dict)

        else: # If the script is not run as ROOT, the OS and OS cpe are unknown as the scan can't be launched.

            dict = {"os": "Unknown",
                    "os_cpe": "Unknown"
                    }
            # Update these values
            for ip, attributes in self.scanner_output.items():
                self.scanner_output[ip].update(dict)

            print(
                f"PTHelper not running as root. OS scan will not work, losing this information for all the assessment.")
        pass

    # Define a method to perform a scan
    # This method performs open port discovery and vulnerability discovery, and then returns the port context
    def scan(self):

        self.open_port_discovery()

        self.performvulnerabilitydiscovery()

        self.performosdiscovery()

        print(self.scanner_output)
        return self.scanner_output