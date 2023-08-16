# The json module provides methods for dealing with JSON data
import json
# os module provides a way of using system dependent functionality
import os
# jinja2 is a full-featured template engine for Python
import jinja2
# docxtpl is a python library to generate MS Word .docx files
from docxtpl import DocxTemplate
# colorama allows coloring of console output in Windows
from colorama import init, Fore
# Importing the configuration settings for the application
from config.pthelper_config import general_config
# To get today's date.
from datetime import date

from rich.console import Console


# Class for the reporter which accepts different modes
class Reporter:
    def __new__(cls, mode):
        reporter_classes = {
            'docxtpl_jinja': DocxJinjaTemplateReporter
            # Add here future scanner modes with the flag that the user has to introduce and the children class name.
        }
        reporter_class = reporter_classes.get(mode, Reporter)
        return super(Reporter, cls).__new__(reporter_class)

    # Initialize the reporter with a mode
    def __init__(self, mode):
        self.mode = mode
        self.context = None
        self.console = Console()

    def create_port_contexts(self, exploiter_output):
        if os.path.exists(general_config.RESULTSFILE):
            # If the "results.json" file exists, read its content and update self.port_contexts
            with open(general_config.RESULTSFILE, 'r') as f:
                self.port_contexts = json.load(f)
        else:
            # If the "results.json" file doesn't exist, create a new self.port_contexts dictionary
            self.port_contexts = {
                'port_context_columns': ['Ports', 'Service', 'Version', 'CVEs'],
                'port_context_rows': []
            }

        # Convert the current port_context_rows IPs into a dictionary for easier update
        current_ips = {row['label']: row for row in self.port_contexts['port_context_rows']}

        for ip, data in exploiter_output.items():
            ports = []
            services = []
            versions = []
            cves = []
            for port, info in data.items():
                if isinstance(info, dict) and 'service' in info and 'version' in info:
                    ports.append(port)
                    services.append(info.get('service', ''))
                    versions.append(info.get('version', ''))

                    # Extract CVEs
                    cve_info = [key for key in info.keys() if key.startswith('CVE-')]
                    cves.append("\n".join(cve_info))

            port_context_row = {
                'label': ip,
                'cols': ['\n'.join(map(str, ports)), '\n'.join(services), '\n'.join(versions), '\n'.join(cves)]
            }

            # Check if the IP already exists in the current_ips dictionary
            if ip in current_ips:
                # If the IP exists, update its 'cols' data with the new values
                current_ips[ip]['cols'] = port_context_row['cols']
            else:
                # If the IP doesn't exist, add the new entry to the port_contexts dictionary
                self.port_contexts['port_context_rows'].append(port_context_row)

        # Save the updated/created self.port_contexts back to the "results.json" file
        with open(general_config.RESULTSFILE, 'w') as f:
            json.dump(self.port_contexts, f, indent=4)

        return self.port_contexts

# Class for a specific type of reporter that uses the DocxTemplate and Jinja2 for reporting
class DocxJinjaTemplateReporter(Reporter):
    def __init__(self, mode):
        super().__init__(mode)
        # If the project directory does not exist, create it
        if not general_config.PROJECTEXISTS:
            os.makedirs(general_config.PROJECTPATH, exist_ok=True)

            # Capture user input for corporation details
            corp_name = input('Insert the target name: ')
            corp_address = input('Insert the target contact e-mail address: ')
            config = {'corp_name': corp_name,
                      'corp_address': corp_address}

            # Write these details to a JSON configuration file
            with open(general_config.CONFIGFILE, 'w') as f:
                json.dump(config, f, indent=2)

        # Load configuration files into context for rendering the Jinja template
        with open(general_config.CONFIG_PATH) as config_file:
            self.context = json.load(config_file)

        with open(general_config.CONFIGFILE) as project_config_file:
            context_project = json.load(project_config_file)
            # Merge the two dictionaries
            self.context.update(context_project)

        with open(general_config.RESULTSFILE) as project_config_file:
            context_results = json.load(project_config_file)
            # Merge the results dictionary with the previous merged dictionaries
            self.context.update(context_results)

    def add_exploiter_info(self, exploiter_results):
        self.create_port_contexts(exploiter_results)

    def render(self):

        # Load a Word template using docxtpl
        tpl = DocxTemplate('templates/template.docx')
        # Create a Jinja2 environment with autoescape turned on for security
        jinja_env = jinja2.Environment(autoescape=True)

        # If a logo exists for the corporation, replace the existing one in the template with it
        if os.path.exists(general_config.DESIRED_CORP_LOGO):
            tpl.replace_media(general_config.BASE_CORP_LOGO, general_config.DESIRED_CORP_LOGO)

        # Update basic report things that do not depend on given context, as the report date, project name, etc.
        self.update_report_date(self.context)
        self.update_project_name()

        # Render the template with the context data
        tpl.render(self.context, jinja_env)

        # Save the rendered document
        tpl.save('projects/tfm/output.docx')

    def update_report_date(self, context):
        project_date = {
            "project_date": date.today()
        }
        self.context.update(project_date)

    def update_project_name(self):
        project_name = {
            "project_name": "TFM_DEMO"
        }
        self.context.update(project_name)

    def add_executive_summary(self, executive_summary):
        json = {
            "executive_summary": executive_summary
        }
        self.context.update(json)

    def add_finding_report(self, finding_dictionary):
        json = {
            'finding_dictionary': finding_dictionary
        }
        self.context.update(json)
