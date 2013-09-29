#!/usr/bin/env python
#-*- coding: utf-8 -*-
#
import cmd
import os
import os.path
import sys
import re
import glob
import subprocess
import ConfigParser

__author__ = "Tomas Pelka <pelka@feec.vutbr.cz>"

class ShellError(Exception):
    "pyTeXshell exception"
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)



class TeXshell(cmd.Cmd):
    """TeX shell interpreter."""
    __VERSION__ = 0.3
    PS1 = ">> "
    PROMPT_PREFIX = '[pyTeXshell]' 
    prompt = "%s %s" % (PROMPT_PREFIX, PS1)
    intro = """##################################
# Welcome to pyTeXshell ver.:%s #
##################################
Type help or ? for help.
For changing prompt use prompt command.
For exit run ^D or EOF or exit.

Every project should have separed root!
----------------------------------------""" % __VERSION__

    HOME = os.environ['HOME']
    doc_header = 'Documentation:'
    misc_header = 'Miscellaneous:'
    undoc_header = 'Undocumented:'
    ruler = '-'
    config = '.config'

    def __init__(self, completekey='tab', stdin=None, stdout=None):
        if stdin is not None:
            self.stdin = stdin
        else:
            self.stdin = sys.stdin
        if stdout is not None:
            self.stdout = stdout
        else:
            self.stdout = sys.stdout
            self.cmdqueue = []
            self.completekey = completekey
        self.CC = "pdfcslatex"
        self.allowedCC = ['pdfcslatex', 'pdflatex', 'cslatex', 'latex', 'tex']

    def noArgs(func):
        "decorator for functions which get no args"
        def wrapper(*args):
            if args[1] == "":
                func(*args)
            else:
                print "Function takes no arguments!"
        return wrapper

    def oneArg(func):
        "decorator for functions which get exactely one args"
        def wrapper(*args):
            if args[1] != "" and len(args[1].split('\n')) == 1:
                func(*args)
            else:
                print "Function takes exactely one argument!"
        return wrapper


    @noArgs
    def do_getCC(self, line):
        "Get compiler."
        print(self.CC)


    @oneArg
    def do_setCC(self, line):
        """setCC pdfcslatex|pdflatex|cslatex|latex|tex
        Set compiler for further use.
        """
        if line in self.allowedCC:
            self.CC = line
        else:
            print("%s not allowed as compiler" % line)


    def _yes_no(self, data):
        "Helper function for requesting Y/N from user"
        text = "%s do not exist. Do you want to create new one? [Y/n]: " % data
        sys.stdout.write(text)
        choice = raw_input().lower()
        if choice == "y" or choice == "":
            return True
        else:
            return False

    def _verify_name(self, data):
        """Helper function which realize simple filter.
        Following characters are excluded: \/|:.~!@#$%^&*()+,<>?`"""
        match = re.search(r'[^a-zA-Z0-9_]', data)
        if match:
            raise ShellError("Folowing charakters ' \/|:.~!@#$%^&*()+,<>?`\"' are disallowed!")

    
    def _skip_home(self):
        return str(os.getcwd()).replace(self.HOME, "")

    
    def _prompt(self, line):
        "Change the interactive prompt"
        self.prompt = line

    def _skip_hidden(self, name):
        "Skip doted files/dirs."
        match = re.match("^\.", name)
        if not match:
            return name

    def _print_list(self, list):
        "Format list of dirs/files"
        out = ""
        if len(list) == 0:
            print("No files or directories.")
        else:
            for item in list:
                if self._skip_hidden(item):
                    if os.path.isdir("./%s" % item):
                        out += "%s/ " % item
                    else:
                        out += "%s " % item
        return out

    @noArgs
    def do_whoami(self, line):
        """whoami 
        Get CWD, you have to run this command before you start compiling!"""
        print("You are in %s" % self._skip_home())

#TODO: nefunguje spravne
    def do_im(self, user):
        """im [user]
        Set CWD, if dir do not exist create new one."""
        try:
            self._verify_name(user)
        except ShellError as e:
            print("im: ", e.value)
            return False
        if len(user) > 0:
            path = "%s/%s" % (self.HOME, user)
            if os.path.isdir(path):
                os.chdir(path)
                prompt = "%s %s %s" % (self.PROMPT_PREFIX, self._skip_home(), self.PS1)
                self._prompt(prompt)
            else:
                if self._yes_no(user):
                    os.mkdir(path)
                    os.chdir(path)
                    prompt = "%s %s %s" % (self.PROMPT_PREFIX, self._skip_home(), self.PS1)
                    self._prompt(prompt)
        else:
            print("Entering root dir!")
            os.chdir(self.HOME)
            prompt = "%s %s" % (self.PROMPT_PREFIX, self.PS1)
            self._prompt(prompt)
            os.getcwd()

                
    def do_mkdir(self, path):
        """ mkdir [dir]
        Create new directory only if you are not in $HOME."""
        try:
            self._verify_name(path)
        except ShellError as e:
            print("mkdir: ", e.value)
            return False
        if os.getcwd() != self.HOME:
            os.mkdir(path)
        else:
            print("You can't be in root to run mkdir, run im [user] first.")

    @noArgs
    def do_ls(self, line):
        "Alternative fo unix ls command."
        print(self._print_list(os.listdir('.')))

    @noArgs    
    def do_lspdfs(self, line):
        "List only *.pdf"
        print(self._print_list(glob.glob('*.pdf')))

    @noArgs
    def do_lstex(self, line):
        "List only *.pdf"
        print(self._print_list(glob.glob('*.tex')))


#    def do_exit(self, line):
#        "Exit shell."
#        if len(line) == 0:
#            self.do_EOF(line)
#        else:
#            print "ls takes no arguments!"
#
#
#    def do_quit(self, line):
#        "Same as do_exit."
#        self.do_exit(line)

    
    @oneArg
    def do_compile(self, line):
        """compile texfile[.tex] 
        Compile tex source file. You can set your compiler using setCC."""
        if os.path.isfile(line):
            cmd = "%s %s" % (self.CC, line)
            args = shlex.split(cmd)
            p = subprocess.call(args)
        else:
            print("No such file %s" % line)
    

    def do_EOF(self, line):
        "Exit shell."
        return True


    def do_config(self, line):
        """Get/set current configuration
 config get current configuration if exist
 config [token=argument | token1=argument1,token2=argument2,...] set token to argument and write to config (create new one if not exist)"""
        SEPARATOR = ","
        MAIN_SEC = "main"
        RE_EXPR = "(\w+)=([a-zA-Z0-9'<>@]+)"
        config = ConfigParser.RawConfigParser()
        config.read(self.config)
        if len(line) > 0:
            print(line)
            if SEPARATOR in line:
                for item in line.split(SEPARATOR):
                    match = re.match(RE_EXPR, item.strip(' '))
                    if match:
                        # TODO: write conf
                        print match.groups()
                    else:
                        print("Config parameters (%s) are wrong. Make sure the separator is ','. \
Params should be in following format [A-Za-z0-9]=[A-Za-z0-9'<>@]" % item)
            else:
                    match = re.match(RE_EXPR, line.strip(' '))
                    if match:
                        # TODO: write conf
                        print match.groups()
                    else: 
                        print("Config parameters (%s) are wrong. Make sure the separator is ','. \
Params should be in following format [A-Za-z0-9]=[A-Za-z0-9'<>@]" % line)
            if not config.has_section(MAIN_SEC):
                config.add_section(MAIN_SEC)    
        else:
            if os.path.isfile(self.config):
                try:
#                    config = ConfigParser.RawConfigParser()
#                    config.read(self.config)
                    print("Configuration:")
                    for section in config.sections():
                        print(" '%s' section" % section)
                        items = config.items(section)
                        if len(items) > 0:
                            for item in items:
                                print("   %s = %s" % (item[0], item[1]))
                        else:
                            print("   This section is empty.")
                except ConfigParser.ParsingError as e:
                    print("Configuration file contains failures, please inspect.")
            else:
                print("No configuration file in current working directory. Nothing to print.")
                


    def postloop(self):
        "Logout message."
        print("Bye ...")

if __name__ == '__main__':
    TeXshell().cmdloop()

