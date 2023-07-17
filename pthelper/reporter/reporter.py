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

# Class for the reporter which accepts different modes
class Reporter:
    def __new__(cls, mode, port_contexts):
        reporter_classes = {
            'docxtpl_jinja': DocxJinjaTemplateReporter
            # Add here future scanner modes with the flag that the user has to introduce and the children class name.
        }
        reporter_class = reporter_classes.get(mode, Reporter)
        return super(Reporter, cls).__new__(reporter_class)

    # Initialize the reporter with a mode
    def __init__(self, mode, scanner_output):
        self.mode = mode
        self.create_port_contexts(scanner_output)
        self.context = None

    def create_port_contexts(self, scanner_output):
        self.port_contexts = {
            'port_context_columns': ['Ports', 'Service', 'Version', 'CVEs'],
            'port_context_rows': []
        }
        for ip, data in scanner_output.items():
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
                    cves.append(", ".join(cve_info))

            port_context_rows = {
                'label': ip,
                'cols': ['\n'.join(map(str, ports)), '\n'.join(services), '\n'.join(versions), '\n'.join(cves)]
            }

            self.port_contexts['port_context_rows'].append(port_context_rows)

        return self.port_contexts

# Class for a specific type of reporter that uses the DocxTemplate and Jinja2 for reporting
class DocxJinjaTemplateReporter(Reporter):
    def __init__(self, mode, scan_output):
        super().__init__(mode, scan_output)
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

    def report(self):

        # Firstly, dump the contents of the scanner in the results file of the project.
        # For further manipulations and usage of the information.
        with open(general_config.RESULTSFILE, 'w') as f:
            json.dump(self.port_contexts, f, indent=4)
        # Load a Word template using docxtpl
        tpl = DocxTemplate('templates/template.docx')
        # Create a Jinja2 environment with autoescape turned on for security
        jinja_env = jinja2.Environment(autoescape=True)
        # If a logo exists for the corporation, replace the existing one in the template with it
        if os.path.exists(general_config.DESIRED_CORP_LOGO):
            tpl.replace_media(general_config.BASE_CORP_LOGO, general_config.DESIRED_CORP_LOGO)

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

        self.update_report_date(self.context)


        # Render the template with the context data
        tpl.render(self.context, jinja_env)

        # Save the rendered document
        tpl.save('projects/tfm/output.docx')

    def update_report_date(self, context):
        project_date = {
            "project_date": date.today()
        }
        self.context.update(project_date)

