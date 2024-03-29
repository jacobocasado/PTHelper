import dataclasses


@dataclasses.dataclass
class GeneralConfig:
    COMPATIBLE_LANGUAGES = ["ES"]
    COMPATIBLE_SCANNERS = ["nmap"]

    # Specify the configuration file, to save user presets like name, language, email, etc.
    CONFIG_PATH = 'config/config.json'
    BASE_CORP_LOGO = 'resources/corp_logo.png'
    DESIRED_CORP_LOGO = None

    PROJECTPATH = None
    CONFIGFILE = None
    RESULTSFILE = None
    PROJECTEXISTS = False


@dataclasses.dataclass
class ScannerConfig:
    NVD_API_KEY = "API_KEY" # Put NVD API key here!

@dataclasses.dataclass
class AgentConfig:
    OPENAI_API_KEY = "API_KEY" # Put OpenAI Key here!
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
    TEMPERATURE = 0.00

@dataclasses.dataclass
class ExploiterConfig():
    EXPLOIT_PATH = '/tmp/exploits/' # This value is used just in case. In Exploiter class, this value is OVERWRITTEN!

general_config = GeneralConfig()
scanner_config = ScannerConfig()
agent_config = AgentConfig()
exploiter_config = ExploiterConfig()


