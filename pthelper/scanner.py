import json
from colorama import init, Fore, Style

from nmap3 import nmap3


# Scanner class must receive an IP address and an array of ports.
class Scanner:
    def __new__(cls, ip_address, ports, mode):
        scanner_classes = {
            "nmap": NmapScanner,
            # Agrega aquí otras clases para otros valores del tercer parámetro
        }
        scanner_class = scanner_classes.get(mode, Scanner)
        return super(Scanner, cls).__new__(scanner_class)

    def __init__(self, ip_address, ports, mode):
        self.ip_address = ip_address
        self.ports = ports
        self.mode = mode
        self.parsed_ports = {}


class NmapScanner(Scanner):
    def __init__(self, ip_address, ports, mode):
        super().__init__(ip_address, ports, mode)

    def process_json(self, input_json):

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
        ## if "macaddress" in data:
        ## output_json[ip]["macaddress"] = {}
        ## for key in ["addr", "vendor"]:
        ## if key in data["macaddress"]:
        ## output_json[ip]["macaddress"][key] = data["macaddress"][key]

        print(json.dumps(output_json, indent=4))
        return json.dumps(output_json, indent=4)

    def performhostdiscovery(self):
        nmap_instance = nmap3.NmapHostDiscovery()
        results = nmap_instance.nmap_portscan_only(self.ip_address, args=f"-p{self.ports}")

        ip_address = list(results.keys())[0]
        ports_data = results[ip_address]['ports']

        for port in ports_data:
            port_id = port['portid']
            port_info = {
                'protocol': port['protocol'],
                'state': port['state'],
                'service_name': port['service']['name']
            }
            self.parsed_ports[port_id] = port_info

        return self.parsed_ports

    def performvulnerabilitydiscovery(self):
        print(Fore.LIGHTBLUE_EX + "Escaneando IP: " + self.ip_address)
        print("\n".join(
            [f"En el puerto {port} se está ejecutando el servicio {data['service_name']}." for port, data in
             self.parsed_ports.items()]))

        nmap_instance = nmap3.Nmap()
        vulscan = nmap_instance.nmap_version_detection(self.ip_address,
                                                       args=f"--script vulscan/vulscan.nse -p{self.ports}")

        return self.process_json(vulscan)
