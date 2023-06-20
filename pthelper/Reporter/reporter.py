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

# Class for the Reporter which accepts different modes
class Reporter:
    def __new__(cls, mode):
        reporter_classes = {
            'docxtpl_jinja': DocxJinjaTemplateReporter
            # Add here future scanner modes with the flag that the user has to introduce and the children class name.
        }
        reporter_class = reporter_classes.get(mode, Reporter)
        return super(Reporter, cls).__new__(reporter_class)

    # Initialize the Reporter with a mode
    def __init__(self, mode):
        self.mode = mode

# Class for a specific type of Reporter that uses the DocxTemplate and Jinja2 for reporting
class DocxJinjaTemplateReporter(Reporter):
    def __init__(self, mode):
        super().__init__(mode)


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

        # Render the template with the context data
        tpl.render(context)
        tpl.render(context_project)

        # Save the rendered document
        tpl.save('projects/tfm/tfm_demo.docx')

    def process(self, context):
        # If a results file exists
        if os.path.exists(pthelper_config.RESULTSFILE):
            # Load existing data from the file
            with open(pthelper_config.RESULTSFILE, 'r') as f:
                existing_data = json.load(f)
                # flag to check if a match is found
                found = False
                # Loop through each row in the existing data's 'port_context_rows'
                for row in existing_data['port_context_rows']:
                    # If a row label matches the incoming context label, update the columns and break the loop
                    if row['label'] == context['port_context_rows'][0]['label']:
                        row['cols'] = context['port_context_rows'][0]['cols']
                        found = True
                        break
                # If no match found, append new 'port_context_rows' from context
                if not found:
                    existing_data['port_context_rows'].extend(context['port_context_rows'])
        else:
            # If results file doesn't exist, existing data is the incoming context
            existing_data = context

        # Write back the data to the results file
        with open(pthelper_config.RESULTSFILE, 'w') as f:
            json.dump(existing_data, f)



