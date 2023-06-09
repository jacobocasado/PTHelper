import colorama

colorama.init()

banner = [
    "██████  ████████ ██   ██ ███████ ██      ██████  ███████ ██████  ",
    "██   ██    ██    ██   ██ ██      ██      ██   ██ ██      ██   ██ ",
    "██████     ██    ███████ █████   ██      ██████  █████   ██████  ",
    "██         ██    ██   ██ ██      ██      ██      ██      ██   ██ ",
    "██         ██    ██   ██ ███████ ███████ ██      ███████ ██   ██ ",
    "",
    ""
]

class Banner:

    def fade_text():
        colorama.init()
        gradient = [colorama.Fore.LIGHTMAGENTA_EX, colorama.Fore.MAGENTA, colorama.Fore.BLUE,
                    colorama.Fore.LIGHTBLUE_EX]
        for line in banner:
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