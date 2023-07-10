import dataclasses

@dataclasses.dataclass
class PTHelperConfig:

    COMPATIBLE_LANGUAGES = ["ES"]
    COMPATIBLE_SCANNERS = ["nmap"]

    # Specify the configuration file, to save user presets like name, language, email, etc.
    CONFIG_PATH = 'config/config.json'
    BASE_CORP_LOGO = 'resources/corp_logo.png'

    NVD_API_KEY = "98c59cce-e235-4274-ad9c-df428625c775"

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
    CHATGPT_PROXIES: dict = dataclasses.field(
        default_factory=lambda: {
            "http": "",
            "https": "",
        }
    )

pthelper_config = PTHelperConfig()
