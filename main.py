# This is a sample Python script.
import argparse
import ipaddress
import json
import os

from scanner import Scanner
from reporter import Reporter
from banner import Banner
from reporter import Reporter


# TODO Comment everything
# TODO Conversational Agent as a module that can be loaded. Experimental in the report. Used for webapp pentest.
# TODO gettext python so the output and the report is language-modular.

if __name__ == '__main__':

    # Specify the configuration file, to save user presets like name, language, email, etc.
    CONFIG_PATH = 'config.json'
    COMPATIBLE_LANGUAGES = ["ES"]
    COMPATIBLE_SCANNERS = ["nmap"]
    # Call the banner function to show the banner
    Banner.fade_text()

    # Instance the argument parser
    parser = argparse.ArgumentParser()
    # Add the argument to process the IP address
    parser.add_argument('-ip', dest='ip_address', type=str, help='IP address to scan')
    # Add the argument to process the port range
    parser.add_argument('-p', dest='ports', type=str, help='Ports to scan')
    # Add the argument to specify the type of scanner to use
    # TODO check the scanner is in the scanner list
    parser.add_argument('-scanner', dest='scanner', type=str, help='Scanner tool to use (available: nmap)')
    # Add the argument to specify the type of reporter to use
    # TODO check the reporter is in the reporter list.
    parser.add_argument('-reporter', dest='reporter', type=str, help='Reporter tool to use (available: docxtpl)')
    # Add the argument to specify the project to work in
    parser.add_argument('-project', dest='project', type=str, help='Project to store information (e.g., TFM)')
    # Add more arguments here...

    # Parse all the arguments
    args = parser.parse_args()

    # Code block to check if the IP address has an IP address format
    # TODO: Pass this into a function.
    try:
        ipaddress.ip_address(args.ip_address)
    except ValueError:
        print("Invalid IP address")
        exit(1)

    # Code block to check if the port argument is a port range and if they are, parse the ports into a vector.
    # TODO: Pass this into a function.
    ports = []
    if '-' in args.ports:
        start_port, end_port = args.ports.split('-')
        for port in range(int(start_port), int(end_port) + 1):
            ports.append(port)
    else: # If it not in port range and comma list, just add the ports.
        ports = args.ports.split(',')

    # If there is no configuration file found in the route, configure the tool.
    # Most of the configuration is used later, to add it in the report template dinamically.
    # Generally executed on first tool usage. Delete the file in CONFIG_PATH to restart the configuration.
    if not os.path.exists(CONFIG_PATH):
        print("Looks like this is the first time you have opened the tool. \n"
              "Let's perform a basic configuration! The information you insert will appear in the reports.")

        # Asking for the user information for templating purposes.
        team_name = input('Organization name (or personal name): ')
        team_abbreviature = input('Abbreviature for Organization name (or personal name): ')
        pentester_name = input('Your name: ')
        pentester_email = input('Your e-mail address: ')
        # For the language, ensure that the user-specified lanuage is in the language list.
        # The language list is in the COMPATIBLE_LANGUAGES variable.
        default_language = input(f"Your preferred language (available: {COMPATIBLE_LANGUAGES}): ")
        while default_language not in COMPATIBLE_LANGUAGES:
            print("This tool is not available in the specified language (yet).")
            print(f"The available languages are: {COMPATIBLE_LANGUAGES}")
            default_language = input(f"Your preferred language (available: {COMPATIBLE_LANGUAGES}): ")

        default_scanner = input(f"Your preferred scanner type (available: {COMPATIBLE_SCANNERS}): ")
        while default_scanner not in COMPATIBLE_SCANNERS:
            print("This tool does not use the specified scanner type.")
            print(f"The available scanner types are: {COMPATIBLE_SCANNERS}")
            default_scanner = input(f"Your preferred scanner type (available: {COMPATIBLE_SCANNERS}): ")
        # TODO ask default reporter
        # TODO ask default planner

        # Create a dictionary with all this user configuration.
        # The keys of this dictionary must match the ones used in the DOCX template!
        # Do not forget to add your new variable inside!
        config = {'team_name': team_name,
                  'team_abbreviature': team_abbreviature,
                  'pentester_name': pentester_name,
                  'pentester_email': pentester_email,
                  'default_language': default_language,
                  'default_scanner': default_scanner
                  }
        # Dump the dictionary into the file in CONFIG_PATH
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f)

    # TODO: class interface with colors and stuff, or, at least, comment it.
    # TODO: perform scan methods, and add them to the diagram.
    # TODO: integration with the template scan. make the template also modular!


    # Instance the Scanner object with the IP address, the ports as an array and the scanner mode.
    print(ports)
    scanner = Scanner(args.ip_address, ports, args.scanner)
    # Perform basic port scanning and parsing into a defined output
    # (read README.md to see the output format and implement the scanner classes accordingly).
    parsed_ports, port_context = scanner.performhostdiscovery()
    print(parsed_ports)
    # Perform vulnerability scanning over these ports and parsing into a defined output
    # (read README.md to see the output format and implement the scanner classes accordingly).
    parsed_vulns = scanner.performvulnerabilitydiscovery()
    print(parsed_vulns)

    # If the reporter tool mode and the project is specified by the user,
    # instance the Reporter object.
    if args.reporter and args.project:
        # TODO management of specifying report but not project and viceversa.
        reporter = Reporter(args.reporter, args.project)
        reporter.process(port_context)

