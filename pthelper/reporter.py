from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import jinja2


class Reporter:
    def __new__(cls, mode):
        reporter_classes = {
            "docxtpl_jinja": DocxJinjaTemplateReporter,
            # Agrega aquí otras clases para otros valores del tercer parámetro

        }
        scanner_class = reporter_classes.get(mode, Reporter)
        return super(Reporter, cls).__new__(scanner_class)

    def __init__(self, mode):
        self.mode = mode

class DocxJinjaTemplateReporter(Reporter):
    tpl = DocxTemplate('templates/template.docx')
    jinja_env = jinja2.Environment(autoescape=True)
    tpl.replace_media('resources/corp_logo.png', 'resources/desired_corp_logo.png')

    context = {
        'corp_name': 'jtsec',
        'team_name': 'jcasado'

    }
    tpl.render(context)

    tpl.save('projects/tfm/tfm_demo.docx')
