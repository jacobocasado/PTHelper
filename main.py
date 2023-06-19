import ipaddress
import json
import os
import re

from Scanner.scanner import Scanner
from banner import Banner
from Reporter.reporter import Reporter
import argparse

# TODO Comment everything
# TODO Conversational Agent as a module that can be loaded. Experimental in the report. Used for webapp pentest.
# TODO gettext python so the output and the report is language-modular.

if __name__ == '__main__':


    # Configuration file for the pentester. Replace it also in the Reporter class if modified.
    CONFIG_PATH = 'config.json'
    # Specify the configuration file, to save user presets like name, language, email, etc.
    COMPATIBLE_LANGUAGES = ["ES"]
    COMPATIBLE_SCANNERS = ["nmap"]

    # Call the banner function to show the banner
    Banner.fade_text()

    # Instance the argument parser
    parser = argparse.ArgumentParser()
    # Add the argument to process the IP address
    parser.add_argument('-ip', dest='ip_address', type=str, help='IP address to scan')

    # Add the argument to process the port range
    def check_ports(value):
        # Comprueba si el valor es un rango de puertos
        if re.match(r'^\d+-\d+$', value):
            ports = value.split('-')
            start, end = int(ports[0]), int(ports[1])
            if start > end:
                raise argparse.ArgumentTypeError(f"El rango de puertos {value} no es válido")
        # Comprueba si el valor es una lista de puertos separados por comas
        elif re.match(r'^\d+(,\d+)*$', value):
            ports = [int(port) for port in value.split(',')]
        else:
            raise argparse.ArgumentTypeError(f"El formato de puertos {value} no es válido")
        return value

    parser.add_argument('-p', dest='ports', type=check_ports, help='Ports to scan')

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
    scanner = Scanner(args.ip_address, args.ports, args.scanner)
    # Perform basic port scanning and parsing into a defined output
    # (read README.md to see the output format and implement the scanner classes accordingly).
    basic_context = scanner.scan()

    # If the reporter tool mode and the project is specified by the user,
    # instance the Reporter object.
    if args.reporter and args.project:
        # TODO management of specifying report but not project and viceversa.
        reporter = Reporter(args.reporter, args.project)
        # TODO see what do I do with the context.
        reporter.process(basic_context)

