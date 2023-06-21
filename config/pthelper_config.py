import dataclasses

@dataclasses.dataclass
class PTHelperConfig:
    # Configuration file for the pentester. Replace it also in the Reporter class if modified.
    CONFIG_PATH = 'config/config.json'
    # Specify the configuration file, to save user presets like name, language, email, etc.
    COMPATIBLE_LANGUAGES = ["ES"]
    COMPATIBLE_SCANNERS = ["nmap"]
    PROJECTPATH = None
    CONFIGFILE = None
    RESULTSFILE = None
    BASE_CORP_LOGO = 'resources/corp_logo.png'
    DESIRED_CORP_LOGO = None
    PROJECTEXISTS = False
    CONVERSATIONPATH = None
    OPENAI_API_KEY = "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"
    HISTORY_LENGTH = 20

    ERROR_WAIT_TIME = 5
    NLPAGENTMODEL = "gpt-3.5-turbo"
    NLPAGENTCONTEXT = "Cada vez que hables, tienes que decir KLK!!!"
    CHATGPT_PROXIES: dict = dataclasses.field(
        default_factory=lambda: {
            "http": "",
            "https": "",
        }
    )


pthelper_config = PTHelperConfig()
