# Import needed libraries
import openai  # pip install openai

from config.pthelper_config import agent_config
from pthelper.nlpagent.agent.chatgpt.chatgpt_api import ChatGPTAPI
from pthelper.nlpagent.prompts.prompts import NLPAgentPrompt
# Base NLPAgent class.
class NLPAgent:

    def __new__(cls, mode):
        # A dictionary to map different agent modes to respective classes
        nlpagent_classes = {
            "chatgpt": ChatGPTAPIAgent
            # For future nlpagent modes, add the user-defined flag and the corresponding child class name here
        }
        # Get the agent_class from the dictionary, default is chatgpt itself
        nlpagent_class = nlpagent_classes.get(mode, NLPAgent)
        return super(NLPAgent, cls).__new__(nlpagent_class)

    def __init__(self, mode):
        self.mode = mode

# Children class that uses ChatGPT agent with ChatGPTAPI library as the NLPAgent type.
# This is the first NLPAgent type available.
class ChatGPTAPIAgent(NLPAgent):

    def __init__(self, mode):
        super().__init__(mode)
        # Initialize ChatGPTAPI
        self.api = ChatGPTAPI()
        # Load the API key from OpenAI. If it does not exist, exit the program.
        openai.api_key = agent_config.OPENAI_API_KEY # Load the API Key from the configuration file.
        if (openai.api_key == None):
            print(f"OpenAI API key needed to use the NLPagent class with chatgpt mode. Edit the configuration file"
                  f"of PTHelper and try again.")
            exit(0)

    # Method to create an executive summary given the output of the Exploiter module.
    def create_executive_summary(self, exploiter_output):
        executive_summary, conversation_id = self.api.start_conversation_with_context(NLPAgentPrompt.executive_summary)
        response = self.api.send_message(str(exploiter_output), conversation_id)
        return response

    # Method that performs the "findings" section of the report with mitigations and security rationales.
    # Uses information from the Exploiter module to create these prompts.
    def perform_finding_report(self, exploiter_output):

        # Initializes the findings array empty
        self.findings = []

        # Create a new conversation using a prompt to generate mitigation steps for the findings.
        mitigation_response, mitigation_conversation_id = self.api.start_conversation_with_context(
            NLPAgentPrompt.mitigation_steps)

        # Create a new conversation using a prompt to generate rationales about the severity of the vulnerabilities.
        severity_response, severity_conversation_id = self.api.start_conversation_with_context(
            NLPAgentPrompt.severity_rationale
        )

        # Start with Finding 1.
        finding_counter = 1
        # Iterate through the scanner output and look for CVEs. Each CVE is a finding:
        # For each of the scanned IPs
        for ip, services in exploiter_output.items():
            # For each port of the IP
            for port, details in services.items():
                if isinstance(details, dict):
                    for key, value in details.items():
                        # Obtain the service of the port.
                        service = details['service']
                        if isinstance(value, dict):  # Check if value is a dictionary
                            # Get the CVE info section of the dictionary.
                            cve_info = value.get('cve', None)
                            if cve_info:
                                # Extract information about the CVE.
                                description = value.get('description', None)
                                cvss = value.get('cvss', None)
                                severity = value.get('severity', None)

                                # Obtain mitigation steps from ChatGPT API given the vulnerability
                                mitigation = self.api.send_message(str(value), mitigation_conversation_id)
                                # Obtain a severity rationale given the vulnerability
                                severity_rationale = self.api.send_message(str(description + "Severity of this vulnerability is " + str(severity)), severity_conversation_id)

                                # Obtain the exploits of the vulnerability that were found with the Exploiter module.
                                exploits = value.get('exploits', None)

                                # For each of the vulnerabilities, create an array to save all the associated exploits found.
                                exploit_array = []
                                # If there are exploits, append them to the array.
                                if exploits:
                                    for key, value in exploits.items():
                                        exploit = {
                                            'id': key,
                                            'description': value.get('description', None),
                                            'url': value.get('url', None),
                                        }
                                        exploit_array.append(exploit)

                                # Attach all the associated information of the vulnerability into a dictionary
                                # that will serve as context for the report.
                                info = {
                                    'finding_counter':finding_counter,
                                    'ip': ip,
                                    'port': port,
                                    'service': service,
                                    'cve': cve_info,
                                    'cvss':cvss,
                                    'severity':severity,
                                    'severity_rationale':severity_rationale,
                                    'description': description,
                                    'mitigation': mitigation,
                                    'exploits': exploit_array
                                }

                                finding_counter = finding_counter + 1
                                # Attach the finding to the finding array.
                                self.findings.append(info)

            return self.findings