import dataclasses

@dataclasses.dataclass
class PTHelperConfig:
    # Configuration file for the pentester. Replace it also in the Reporter class if modified.
    CONFIG_PATH = 'config.json'
    # Specify the configuration file, to save user presets like name, language, email, etc.
    COMPATIBLE_LANGUAGES = ["ES"]
    COMPATIBLE_SCANNERS = ["nmap"]
    PROJECTPATH = None
    CONFIGFILE = None
    RESULTSFILE = None
    BASE_CORP_LOGO = 'resources/corp_logo.png'
    DESIRED_CORP_LOGO = None
    PROJECTEXISTS = False

