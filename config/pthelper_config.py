import dataclasses

@dataclasses.dataclass
class PTHelperConfig:

    COMPATIBLE_LANGUAGES = ["ES"]
    COMPATIBLE_SCANNERS = ["nmap"]

    # Configuration file for the pentester. Replace it also in the reporter class if modified.
    CONFIG_PATH = 'config/config.json'
    BASE_CORP_LOGO = 'resources/corp_logo.png'
    # Specify the configuration file, to save user presets like name, language, email, etc.

    PROJECTPATH = None
    CONFIGFILE = None
    RESULTSFILE = None
    DESIRED_CORP_LOGO = None
    PROJECTEXISTS = False

    OPENAI_API_KEY = "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"
    CONVERSATIONPATH = None
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
