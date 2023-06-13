import json
import os
import jinja2

from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm

class Reporter:
    def __new__(cls, mode, existingproject):
        reporter_classes = {
            "docxtpl_jinja": DocxJinjaTemplateReporter,
            # Agrega aquí otras clases para otros valores del tercer parámetro

        }

        scanner_class = reporter_classes.get(mode, Reporter)
        return super(Reporter, cls).__new__(scanner_class)

    def __init__(self, mode, existingproject):
        self.mode = mode
        self.PROJECTPATH = os.path.join('projects', existingproject)
        self.CONFIGFILE = os.path.join(self.PROJECTPATH, 'config.json')
        self.RESULTSFILE = os.path.join(self.PROJECTPATH, 'results.json')
        self.projectexists = os.path.exists(self.CONFIGFILE)
class DocxJinjaTemplateReporter(Reporter):
    def __init__(self, mode, existingproject):
        super().__init__(mode, existingproject)

        if self.projectexists == False:
            os.makedirs(self.PROJECTPATH, exist_ok=True)

            corp_name = input('Insert the target name: ')
            corp_address = input('Insert the target contact e-mail address: ')
            config = {'corp_name': corp_name,
                      'corp_address': corp_address}

            with open(self.CONFIGFILE, 'w') as f:
                json.dump(config, f)

        self.tpl = DocxTemplate('templates/template.docx')
        jinja_env = jinja2.Environment(autoescape=True)
        self.tpl.replace_media('resources/corp_logo.png', 'resources/desired_corp_logo.png')

        # TODO: Add these context information into a json configuration file that will be also specified as a program arg.
        # 1. add program arg into the constructor.
        # 2. with that program arg create a subfolder in projects folder, store a JSON with all the information.
        # 2.1 note into the TBD things the interactive option of the user to add these project parameters as prompt or cmdline and not change json.


        # Load OUR PERSONAL TOOL CONFIG FILE
        config_file = open('config.json')
        context = json.load(config_file)

        # Load the desired project CONFIG FILE
        project_config_file = open(self.CONFIGFILE)
        context_project = json.load(project_config_file)

        # TODO ver como se managea esto, si el escanner edita esto o le pasa el context al reporter.
        # Load the desired project RESULTS FILE
        #project_results_file = open(self.RESULTSFILE)
        #context_results = json.load(project_results_file)

        #context.update(context_project)
        #context.update(context_results)

        print(context)

        self.tpl.render(context)

        # this has to be an instance parameter.
        self.tpl.save('projects/tfm/tfm_demo.docx')

    def process(self, context):
        results_file = 'results.json'
        if os.path.exists(self.RESULTSFILE):
            with open(self.RESULTSFILE, 'r') as f:
                existing_data = json.load(f)
                # Buscar si la etiqueta ya existe en los datos existentes
                found = False
                for row in existing_data['port_context_rows']:
                    if row['label'] == context['port_context_rows'][0]['label']:
                        row['cols'] = context['port_context_rows'][0]['cols']
                        found = True
                        break
                # Si no se encuentra la etiqueta, agregar una nueva entrada
                if not found:
                    existing_data['port_context_rows'].extend(context['port_context_rows'])
        else:
            existing_data = context

        with open(self.RESULTSFILE, 'w') as f:
            json.dump(existing_data, f, indent=4)

        self.tpl.render(existing_data)
        self.tpl.save('projects/tfm/tfm_demo.docx')