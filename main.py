# This is a sample Python script.
import argparse
import ipaddress
import colorama

from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import jinja2

from scanner import Scanner

# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

colorama.init()

ascii_art = [
    "██████  ████████ ██   ██ ███████ ██      ██████  ███████ ██████  ",
    "██   ██    ██    ██   ██ ██      ██      ██   ██ ██      ██   ██ ",
    "██████     ██    ███████ █████   ██      ██████  █████   ██████  ",
    "██         ██    ██   ██ ██      ██      ██      ██      ██   ██ ",
    "██         ██    ██   ██ ███████ ███████ ██      ███████ ██   ██ ",
    "",
    ""
]


def fade_text():
    colorama.init()
    gradient = [colorama.Fore.LIGHTMAGENTA_EX, colorama.Fore.MAGENTA, colorama.Fore.BLUE, colorama.Fore.LIGHTBLUE_EX]
    for line in ascii_art:
        gradient_idx = 0
        for char in line:
            if char == " ":
                print(" ", end="")
            else:
                color = gradient[gradient_idx % len(gradient)]
                print(color + char, end="")
                gradient_idx += 1
                # time.sleep(0.005)
        print(colorama.Style.RESET_ALL)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process IP address and ports.')
    parser.add_argument('-ip', dest='ip_address', type=str, help='IP address to scan')
    parser.add_argument('-p', dest='ports', type=str, help='Ports to scan')
    parser.add_argument('-scanner', dest='scanner', type=str, help='Scanner tool to use (available: nmap)')
    args = parser.parse_args()

    try:
        ipaddress.ip_address(args.ip_address)
    except ValueError:
        print("Invalid IP address")
        exit(1)

    ports = []
    if '-' in args.ports:
        start_port, end_port = args.ports.split('-')
        for port in range(int(start_port), int(end_port) + 1):
            ports.append(port)
    else:
        ports = args.ports.split(',')

    # TODO: class interface with colors and stuff, or, at least, comment it.
    fade_text()
    # TODO: perform scan methods, and add them to the diagram.
    # TODO: integration with the template scan. make the template also modular!
    scanner = Scanner(args.ip_address, ports, args.scanner)

    tpl = DocxTemplate('templates/template.docx')
    jinja_env = jinja2.Environment(autoescape=True)
    tpl.replace_media('resources/corp_logo.png', 'resources/desired_corp_logo.png')

    context = {
        'corp_name': 'jtsec',
        'team_name': 'jcasado'

    }
    tpl.render(context)

    tpl.save('projects/tfm/tfm_demo.docx')
