# PTHelper: A tool to help penetration testers during their assessments

![logo](https://i.imgur.com/V55gbCD.png)

## What is PTHelper?

PTHelper (Penetration Testing Helper) is a tool designed for and by pentester that tries to make infrastructure (at this moment) pentesting easier, by automating the penetration testing phases from the reconnaisance phase to the creation of an executive report.

This tool was created as a Master's thesis project. **For more information about this tool and the idea behind it, please check the official paper at** (URL).

## Setup and requirements
In order to install the tool, please install the dependences first with `pip install -r requirements.txt` in the root folder of the tool.
After that, execute `python3 pip install -e .` and use `pthelper` with the needed parameters. The parameters are:

The tool also needs the `nmap` and, obviously, the `python3` binary. **It is recommended to use the tool in Kali Linux, as the tool was developed and tested in this distribution.**
Remember to setup the correct OpenAI and NVD API key, located in the `config/pthelper_config.py` folder.

### Required arguments
- `--ip`: The IP address (or range of IPs) to include in the assessment. The tool will function over these IPs. 
- `--ports`: Port (or range of ports) to scan of the given IPs.
- `--scanner`: Type of Scanner that will be used. At this time, only `nmap` Scanner is available.
- `--exploiter`: Type of Exploiter that will be used. At this time, only `exploitdb` Exploiter is available.
- `--agent`: Type of NLPAgent that will be used. At this time, only `chatgpt` NLPAgent is available.
- `--reporter`: Type of Reporter that will be used. At this time, only `docxtpl` (_Docx_ Jinja3 framework) Reporter is available.
- `--project`: Project in which the results will be stored. The results of the tool usage, such as the exploits found by the Exploiter module or the generated report by the Reporter module will be downloaded in the specified project folder. If the specified project does not exist previously, the tool prompts the user for data about the target organization to be added in the report and creates a new project.

### Example usage
`pthelper --ip 10.129.129.66 --port 139 --scanner nmap --reporter docxtpl_jinja --project tfm --agent chatgpt --exploiter exploitdb`

Lastly, remember that this tool has been developed as a thesis project and probably has issues and problems.
This was an experimentation project with all the knowledge obtained in one year of cibersecurity learning, and a lot of effort was put into this project.
