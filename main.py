# This is a sample Python script.
import argparse
import ipaddress

from scanner import Scanner
from reporter import Reporter
from banner import Banner

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

    # TODO: class interface with colors and stuff, or, at least, comment it.
    # TODO: perform scan methods, and add them to the diagram.
    # TODO: integration with the template scan. make the template also modular!
    scanner = Scanner(args.ip_address, ports, args.scanner)
    scanner.performhostdiscovery()
    scanner.performvulnerabilitydiscovery()

    reporter = Reporter(args.reporter)

