import json
import os

from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import jinja2

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
        self.projectexists = os.path.exists(os.path.join('projects', existingproject, 'config.json'))

class DocxJinjaTemplateReporter(Reporter):
    def __init__(self, mode, existingproject):
        super().__init__(mode, existingproject)
        self.project_path = os.path.join('projects', existingproject)

        if self.projectexists == False:
            os.makedirs(self.project_path)
            with open(os.path.join(self.project_path, 'results.json'), 'w') as f:
                json.dump({}, f)
            company_name = input('Introduce el nombre de la empresa: ')
            config = {'company_name': company_name}
            config_path = os.path.join(self.project_path, 'config.json')
            with open(config_path, 'w') as f:
                json.dump(config, f)

    tpl = DocxTemplate('templates/template.docx')
    jinja_env = jinja2.Environment(autoescape=True)
    tpl.replace_media('resources/corp_logo.png', 'resources/desired_corp_logo.png')

    # TODO: Add these context information into a json configuration file that will be also specified as a program arg.
    # 1. add program arg into the constructor.
    # 2. with that program arg create a subfolder in projects folder, store a JSON with all the information.
    # 2.1 note into the TBD things the interactive option of the user to add these project parameters as prompt or cmdline and not change json.
    context = {
        'corp_name': 'jtsec',
        # maybe some config from a general tool config file, as the team name.
        'team_name': 'jcasado'

    }
    tpl.render(context)

    # this has to be an instance parameter.
    # tpl.save('projects/tfm/tfm_demo.docx')
