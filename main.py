import ipaddress
import json
import os
import re
import openai
import argparse

from nlpagent.agent.chatgpt.chatgpt_api import ChatGPTAPI
from scanner.scanner import Scanner
from banner.banner import Banner
from reporter.reporter import Reporter
from config.pthelper_config import pthelper_config

# TODO Comment everything
# TODO Conversational Agent as a module that can be loaded. Experimental in the report. Used for webapp pentest.
# TODO gettext python so the output and the report is language-modular.

def check_ports(value):
    # This function is used to verify if the provided value represents a valid port range or list.

    # Check if the value represents a port range, indicated by the format 'start-end'
    if re.match(r'^\d+-\d+$', value):
        # If the value represents a port range, split it into start and end values
        ports = value.split('-')
        start, end = int(ports[0]), int(ports[1])

        # If the start value is greater than the end value, raise an error
        if start > end:
            raise argparse.ArgumentTypeError(f"The port range {value} is invalid")

    # Check if the value represents a list of ports separated by commas
    elif re.match(r'^\d+(,\d+)*$', value):
        # If the value represents a list of ports, convert each port from string to integer
        ports = [int(port) for port in value.split(',')]

    # If the value does not represent a valid port range or list, raise an error
    else:
        raise argparse.ArgumentTypeError(f"The ports format {value} is invalid")

    # Return the validated value
    return value

def initial_setup():
    # User information is requested
    team_name = input('Organization name (or personal name): ')
    # Asking for the user information for templating purposes.
    team_abbreviature = input('Abbreviature for Organization name (or personal name): ')
    pentester_name = input('Your name: ')
    pentester_email = input('Your e-mail address: ')
    # For the language, ensure that the user-specified lanuage is in the language list.
    # The language list is in the COMPATIBLE_LANGUAGES variable.
    default_language = input(f"Your preferred language (available: {pthelper_config.COMPATIBLE_LANGUAGES}): ")
    while default_language not in pthelper_config.COMPATIBLE_LANGUAGES:
        print("This tool is not available in the specified language (yet).")
        print(f"The available languages are: {pthelper_config.COMPATIBLE_LANGUAGES}")
        default_language = input(f"Your preferred language (available: {pthelper_config.COMPATIBLE_LANGUAGES}): ")

    default_scanner = input(f"Your preferred scanner type (available: {pthelper_config.COMPATIBLE_SCANNERS}): ")
    while default_scanner not in pthelper_config.COMPATIBLE_SCANNERS:
        print("This tool does not use the specified scanner type.")
        print(f"The available scanner types are: {pthelper_config.COMPATIBLE_SCANNERS}")
        default_scanner = input(f"Your preferred scanner type (available: {pthelper_config.COMPATIBLE_SCANNERS}): ")
    # TODO use default config if specified, if not, ask user for it.

    # Create a dictionary with the user information
    config = {'team_name': team_name,
              'team_abbreviature': team_abbreviature,
              'pentester_name': pentester_name,
              'pentester_email': pentester_email,
              'default_language': default_language,
              'default_scanner': default_scanner
              }

    # Store the dictionary as a JSON file
    with open(pthelper_config.CONFIG_PATH, 'w') as f:
        json.dump(config, f)

# Defining a function to parse command line arguments
def parse_args():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()

    # Add accepted arguments with their descriptions and types
    parser.add_argument('-ip', dest='ip_address', type=str, help='IP address to scan')
    parser.add_argument('-p', dest='ports', type=check_ports, help='Ports to scan')
    parser.add_argument('-scanner', dest='scanner', type=str, help='scanner tool to use (available: nmap)')
    parser.add_argument('-reporter', dest='reporter', type=str, help='reporter tool to use (available: docxtpl)')
    parser.add_argument('-project', dest='project', type=str, help='Project to store information (e.g., TFM)')

    # Parse the arguments
    args = parser.parse_args()

    # Update pthelper configuration with provided information
    pthelper_config.PROJECTPATH = os.path.join('projects', args.project)
    pthelper_config.CONFIGFILE = os.path.join(pthelper_config.PROJECTPATH, 'config.json')
    pthelper_config.RESULTSFILE = os.path.join(pthelper_config.PROJECTPATH, 'results.json')
    pthelper_config.DESIRED_CORP_LOGO = os.path.join('projects', args.project, 'corp_logo.png')
    pthelper_config.PROJECTEXISTS = os.path.exists(pthelper_config.CONFIGFILE)
    pthelper_config.CONVERSATIONFILE = os.path.join(pthelper_config.PROJECTPATH, 'conversation_id.txt')

    # Validate the entered IP address
    # try:
    #     ipaddress.ip_interface(args.ip_address)
    # except ValueError:
    #     print("Invalid IP address or CIDR notation. Please insert an IP address with valid format (can be with a CIDR)")
    #     exit(1)

    # If this is the first time using the tool, user information is requested
    if not os.path.exists(pthelper_config.CONFIG_PATH):
        initial_setup()

    # Return parsed arguments
    return args

# Main script entry point
if __name__ == '__main__':
    # Display the banner
    Banner.display()

    # Parse command line arguments
    args = parse_args()

    # Create a Scanner object with specified IP, ports and scanner type
    scanner = Scanner(args.ip_address, args.ports, args.scanner)

    # Perform the scan and get the scan context
    scan_context = scanner.scan()

    # If a reporting tool and project was specified, create a Reporter object
    if args.reporter and args.project:
        reporter = Reporter(args.reporter)
        reporter.report(scan_context)

    # Initialize ChatGPTAPI
    chatgpt = ChatGPTAPI()
    openai.api_key = pthelper_config.OPENAI_API_KEY
    # Comment to be completed...



