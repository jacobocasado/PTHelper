import json
import os
import jinja2

from docxtpl import DocxTemplate
from colorama import init, Fore

from config.pthelper_config import pthelper_config

class Reporter:

    def __init__(self, mode):
        self.set_mode(mode)

    def set_mode(self, mode):
        ModeClass = self.mode_classes.get(mode)
        if ModeClass is None:
            raise ValueError(f'Unsupported mode: {mode}')
        self.mode = ModeClass()

    def report(self):
        self.mode.report()

    def process(self, basic_context):
        self.mode.process(basic_context)


class DocxJinjaTemplateReporter(Reporter):
    def __init__(self):
        pass

    def report(self):
        super().set_mode('docxtpl_jinja')
        if not pthelper_config.PROJECTEXISTS:
            os.makedirs(pthelper_config.PROJECTPATH, exist_ok=True)

            corp_name = input('Insert the target name: ')
            corp_address = input('Insert the target contact e-mail address: ')
            config = {'corp_name': corp_name,
                      'corp_address': corp_address}

            with open(pthelper_config.CONFIGFILE, 'w') as f:
                json.dump(config, f)

        tpl = DocxTemplate('templates/template.docx')
        jinja_env = jinja2.Environment(autoescape=True)
        if os.path.exists(pthelper_config.DESIRED_CORP_LOGO):
            tpl.replace_media(pthelper_config.BASE_CORP_LOGO, pthelper_config.DESIRED_CORP_LOGO)

        config_file = open(pthelper_config.CONFIG_PATH)
        context = json.load(config_file)

        project_config_file = open(pthelper_config.CONFIGFILE)
        context_project = json.load(project_config_file)

        tpl.render(context)
        tpl.render(context_project)

        tpl.save('projects/tfm/tfm_demo.docx')

    def process(self, context):
        if os.path.exists(pthelper_config.RESULTSFILE):
            with open(pthelper_config.RESULTSFILE, 'r') as f:
                existing_data = json.load(f)
                found = False
                for row in existing_data['port_context_rows']:
                    if row['label'] == context['port_context_rows'][0]['label']:
                        row['cols'] = context['port_context_rows'][0]['cols']
                        found = True
                        break
                if not found:
                    existing_data['port_context_rows'].extend(context['port_context_rows'])
        else:
            existing_data = context

        with open(pthelper_config.RESULTSFILE, 'w') as f:
            json.dump(existing_data, f)


Reporter.mode_classes = {
        'docxtpl_jinja': DocxJinjaTemplateReporter,
    }