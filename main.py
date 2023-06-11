# This is a sample Python script.
import argparse
import ipaddress
import json
import os

from scanner import Scanner
from reporter import Reporter
from banner import Banner
from reporter import Reporter

# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    Banner.fade_text()

    parser = argparse.ArgumentParser(description='Process IP address and ports.')
    parser.add_argument('-ip', dest='ip_address', type=str, help='IP address to scan')
    parser.add_argument('-p', dest='ports', type=str, help='Ports to scan')
    parser.add_argument('-scanner', dest='scanner', type=str, help='Scanner tool to use (available: nmap)')
    parser.add_argument('-reporter', dest='reporter', type=str, help='Reporter tool to use (available: docxtpl)')
    parser.add_argument('-project', dest='project', type=str, help='Project to store information (e.g., TFM)')

    args = parser.parse_args()

    try:
        ipaddress.ip_address(args.ip_address)
    except ValueError:
        print("Invalid IP address")
        exit(1)

    ports = []
    if '-' in args.ports:
        start_port, end_port = args.ports.split('-')
        for port in range(int(start_port), int(end_port) + 1):
            ports.append(port)
    else:
        ports = args.ports.split(',')

    CONFIG_PATH = 'config.json'

    if not os.path.exists(CONFIG_PATH):
        print("Looks like this is the first time you have opened the tool. \n"
              "Let's perform a basic configuration! The information you insert will appear in the reports.")

        team_name = input('Organization name (or personal name): ')
        team_abbreviature = input('Abbreviature for Organization name (or personal name): ')
        pentester_name = input('Your name: ')
        pentester_email = input('Your e-mail address: ')

        config = {'team_name': team_name,
                  'team_abbreviature' : team_abbreviature,
                  'pentester_name': pentester_name,
                  'pentester_email': pentester_email
                  }
        # TODO ask for default toolset, as scanner, reporter, etc.
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f)

    # TODO: class interface with colors and stuff, or, at least, comment it.
    # TODO: perform scan methods, and add them to the diagram.
    # TODO: integration with the template scan. make the template also modular!
    scanner = Scanner(args.ip_address, ports, args.scanner)
    parsed_ports = scanner.performhostdiscovery()
    print(parsed_ports)
    parsed_vulns = scanner.performvulnerabilitydiscovery()
    print(parsed_vulns)

    if args.project:
        reporter = Reporter(args.reporter, args.project)

