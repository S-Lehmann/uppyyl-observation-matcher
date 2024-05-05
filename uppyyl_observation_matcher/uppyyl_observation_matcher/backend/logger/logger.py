"""The loggers."""

import logging
import sys
import pprint

from colorama import Fore

##################
# Pretty Printer #
##################
pp = pprint.PrettyPrinter(indent=4)

##########
# Logger #
##########
matcher_log = logging.getLogger('TraceMatcher')
matcher_log.setLevel(logging.DEBUG)

std_out_msg_formatter = logging.Formatter(f'[%(asctime)s]{Fore.CYAN}[%(name)6s]{Fore.RESET} %(message)s', "%H:%M:%S")
std_out_handler = logging.StreamHandler(sys.stdout)
std_out_handler.setFormatter(std_out_msg_formatter)
matcher_log.addHandler(std_out_handler)

gen_log = logging.getLogger('TraceGen')
gen_log.setLevel(logging.DEBUG)

std_out_msg_formatter = logging.Formatter(f'[%(asctime)s]{Fore.YELLOW}[%(name)6s]{Fore.RESET} %(message)s', "%H:%M:%S")
std_out_handler = logging.StreamHandler(sys.stdout)
std_out_handler.setFormatter(std_out_msg_formatter)
gen_log.addHandler(std_out_handler)

verifyta_log = logging.getLogger('VerifyTA')
verifyta_log.setLevel(logging.DEBUG)

std_out_msg_formatter = logging.Formatter(f'[%(asctime)s]{Fore.GREEN}[%(name)6s]{Fore.RESET} %(message)s', "%H:%M:%S")
std_out_handler = logging.StreamHandler(sys.stdout)
std_out_handler.setFormatter(std_out_msg_formatter)
verifyta_log.addHandler(std_out_handler)
