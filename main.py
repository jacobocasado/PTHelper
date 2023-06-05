# This is a sample Python script.
import argparse
import ipaddress

# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import nmap3
import time
from colorama import init, Fore, Style

from scanner import Scanner

init()
import time
import colorama

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
    gradient = [Fore.LIGHTMAGENTA_EX, Fore.MAGENTA, Fore.BLUE, Fore.LIGHTBLUE_EX]
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
        print(Style.RESET_ALL)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process IP address and ports.')
    parser.add_argument('-ip', dest='ip_address', type=str, help='IP address to scan')
    parser.add_argument('-p', dest='ports', type=str, help='Ports to scan')
    args = parser.parse_args()

    try:
        ipaddress.ip_address(args.ip_address)
    except ValueError:
        print("Invalid IP address")
        exit(1)

    # TODO: instead of comma-separated list ports, retrieve a range (e.g., 1-65535)
    ports = args.ports.split(',')
    # TODO: class interface with colors and stuff, or, at least, comment it.
    fade_text()
    # TODO: perform scan methods, and add them to the diagram.
    # TODO: integration with the template scan. make the template also modular!
    scanner = Scanner(args.ip_address, ports, "nmap")
    print(2)
