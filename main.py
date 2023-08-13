import json
import os
import re
import argparse


from pthelper.banner.banner import Banner
from pthelper.scanner.scanner import Scanner
from pthelper.reporter.reporter import Reporter
from pthelper.exploiter.exploiter import Exploiter
from pthelper.nlpagent.agent.chatgpt.chatgptagent import NLPAgent
from config.pthelper_config import general_config

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
    default_language = input(f"Your preferred language (available: {general_config.COMPATIBLE_LANGUAGES}): ")
    while default_language not in general_config.COMPATIBLE_LANGUAGES:
        print("This tool is not available in the specified language (yet).")
        print(f"The available languages are: {general_config.COMPATIBLE_LANGUAGES}")
        default_language = input(f"Your preferred language (available: {general_config.COMPATIBLE_LANGUAGES}): ")

    default_scanner = input(f"Your preferred scanner type (available: {general_config.COMPATIBLE_SCANNERS}): ")
    while default_scanner not in general_config.COMPATIBLE_SCANNERS:
        print("This tool does not use the specified scanner type.")
        print(f"The available scanner types are: {general_config.COMPATIBLE_SCANNERS}")
        default_scanner = input(f"Your preferred scanner type (available: {general_config.COMPATIBLE_SCANNERS}): ")
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
    with open(general_config.CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

# Defining a function to parse command line arguments
def parse_args():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser()

    # Add accepted arguments with their descriptions and types
    parser.add_argument('--ip', dest='ip_address', type=str, help='IP address to scan')
    parser.add_argument('--port', dest='ports', type=check_ports, help='Ports to scan')
    parser.add_argument('--scanner', dest='scanner', type=str, help='scanner tool to use (available: nmap)')
    parser.add_argument('--exploiter', dest='exploiter', type=str, help='Tool to retrieve exploit scripts (e.g., exploitdb)')
    parser.add_argument('--reporter', dest='reporter', type=str, help='reporter tool to use (available: docxtpl)')
    parser.add_argument('--project', dest='project', type=str, help='Project to store information (e.g., TFM)')
    parser.add_argument('--agent', dest='agent', type=str, help='NLP Agent (e.g., chatgpt)')
    # Parse the arguments
    args = parser.parse_args()

    # Update pthelper configuration with provided information
    general_config.PROJECTPATH = os.path.join('projects', args.project)
    general_config.CONFIGFILE = os.path.join(general_config.PROJECTPATH, 'config.json')
    general_config.RESULTSFILE = os.path.join(general_config.PROJECTPATH, 'results.json')
    general_config.PROJECTEXISTS = os.path.exists(general_config.CONFIGFILE)
    general_config.CONVERSATIONFILE = os.path.join(general_config.PROJECTPATH, 'conversation_id.txt')

    # If this is the first time using the tool, user information is requested
    if not os.path.exists(general_config.CONFIG_PATH):
        initial_setup()

    # Return parsed arguments
    return args

def main():
    # Display the banner
    Banner.display()

    # Parse command line arguments
    args = parse_args()

    # Create a Scanner object with specified IP, ports and scanner type
    scanner = Scanner(args.ip_address, args.ports, args.scanner)

    # Perform the scan and get the scan context
    scan_results = scanner.scan()

    exploiter = Exploiter(args.exploiter, scan_results)
    exploiter_results = exploiter.exploit()

    agent = NLPAgent(args.agent)
    executive_summary = agent.create_executive_summary(exploiter_results)
    print(executive_summary)

    # If a reporting tool and project was specified, create a Reporter object
    if args.reporter and args.project:
        reporter = Reporter(args.reporter)
        reporter.add_exploiter_info(exploiter_results)
        reporter.add_executive_summary(executive_summary)
        reporter.render()



# Main script entry point
if __name__ == '__main__':
    main()






