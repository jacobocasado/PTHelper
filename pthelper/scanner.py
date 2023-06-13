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
        self.parsed_ports = {}

# Children class that uses Nmap3 library as the scanner type.
# This is the first Scanner type available.
class NmapScanner(Scanner):

    # Call the parent class (Scanner) to receive parameters.
    def __init__(self, ip_address, ports, mode):
        super().__init__(ip_address, ports, mode)

    # Instance method to process the JSON that nmap3 returns after the vulnerability discovery
    # and return the information as specified in the Scanner class for the "performvulnerabilitydiscovery" method.
    def process_json(self, input_json):

        output_json = {}
        # We get the IP address from the Nmap3 JSON
        ip, data = next(iter(input_json.items()))
        output_json[ip] = {}

        # We look for ports in the JSON
        if "ports" in data:
            output_json[ip]["ports"] = []
            # For each of the ports we attach the useful information.
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
                # If the port has attached vulnerabilities, attach them.
                if "scripts" in port:
                    new_port["scripts"] = []
                    for script in port["scripts"]:
                        if "raw" in script:
                            raw_parts = script["raw"].split("\n\n")
                            new_port["scripts"].extend(raw_parts)
                output_json[ip]["ports"].append(new_port)

        print(json.dumps(output_json, indent=4))
        return json.dumps(output_json, indent=4)

    # Method that performs a port discovery on the host, identifying which of the ports are alive.
    # This method returns the specified format needed for the "performhosdiscovery" class method in Scanner.
    def performhostdiscovery(self):
        # Instantiate the Nmap3 scanner.
        nmap_instance = nmap3.NmapHostDiscovery()
        # Perform the portscan on the specified port range by the user, and in the IP specified.
        results = nmap_instance.nmap_portscan_only(self.ip_address, args=f"-p{','.join(map(str, self.ports))}")
        # We extract the port information from the nmap3 output.
        ports_data = results[self.ip_address]['ports']

        ports = []
        protocols = []
        states = []
        service_names = []

        # For each of the port, extract the information required for the Scanner class.
        for port in ports_data:
            port_id = port['portid']
            port_protocol = port['protocol']
            port_state = port['state']
            port_service_name = port['service']['name']

            ports.append(port_id)
            protocols.append(port_protocol)
            states.append(port_state)
            service_names.append(port_service_name)

            port_info = {
                'protocol': port_protocol,
                'state': port_state,
                'service_name': port_service_name
            }
            self.parsed_ports[port_id] = port_info

        # Return an array of the information PER HOST
        # TODO check if this can be a nested array so each row has again subrows.
        # This way each IP (row) has one subrow per open port.
        port_context = {
            'port_context_columns': ['Ports', 'Protocols', 'State', 'Service name'],
            'port_context_rows': [
                {
                    'label': f'{self.ip_address}',
                    'cols': [ports, protocols, service_names]
                }
            ]
        }

        return self.parsed_ports, port_context
    # Method that performs a vulneraiblity discovery on the ports found open by the scanner.
    # Returns the specified output for the Scanner method.
    def performvulnerabilitydiscovery(self):
        print(Fore.LIGHTBLUE_EX + "Scanning IP: " + self.ip_address)
        print("\n".join(
            [f"At {port} service {data['service_name']} is being executed." for port, data in
             self.parsed_ports.items()]))

        nmap_instance = nmap3.Nmap()
        vulscan = nmap_instance.nmap_version_detection(self.ip_address,
                                                       args=f"--script vulscan/vulscan.nse -p{self.ports}")

        return self.process_json(vulscan)
