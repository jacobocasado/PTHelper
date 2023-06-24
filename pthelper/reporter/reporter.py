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
from config.pthelper_config import pthelper_config

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

# Class for a specific type of reporter that uses the DocxTemplate and Jinja2 for reporting
class DocxJinjaTemplateReporter(Reporter):
    def __init__(self, mode):
        super().__init__(mode)

    def process(self, port_contents):
        with open(pthelper_config.RESULTSFILE, 'w') as f:
            json.dump(port_contents, f, indent=4)
    def report(self):
        # If the project directory does not exist, create it
        if not pthelper_config.PROJECTEXISTS:
            os.makedirs(pthelper_config.PROJECTPATH, exist_ok=True)

            # Capture user input for corporation details
            corp_name = input('Insert the target name: ')
            corp_address = input('Insert the target contact e-mail address: ')
            config = {'corp_name': corp_name,
                      'corp_address': corp_address}

            # Write these details to a JSON configuration file
            with open(pthelper_config.CONFIGFILE, 'w') as f:
                json.dump(config, f)

        # Load a Word template using docxtpl
        tpl = DocxTemplate('templates/template.docx')
        # Create a Jinja2 environment with autoescape turned on for security
        jinja_env = jinja2.Environment(autoescape=True)
        # If a logo exists for the corporation, replace the existing one in the template with it
        if os.path.exists(pthelper_config.DESIRED_CORP_LOGO):
            tpl.replace_media(pthelper_config.BASE_CORP_LOGO, pthelper_config.DESIRED_CORP_LOGO)

        # Load configuration files into context for rendering the Jinja template
        config_file = open(pthelper_config.CONFIG_PATH)
        context = json.load(config_file)

        project_config_file = open(pthelper_config.CONFIGFILE)
        context_project = json.load(project_config_file)

        project_config_file = open(pthelper_config.RESULTSFILE)
        context_results = json.load(project_config_file)
        tpl.render(context_results)

        # Render the template with the context data
        tpl.render(context)
        tpl.render(context_project)

        # Save the rendered document
        tpl.save(os.path.join(pthelper_config.PROJECTPATH, 'output.docx'))