from colorama import just_fix_windows_console
from termcolor import colored
from packaging import version
import configparser
import subprocess
import patoolib
import winsound
import easygui as eg
import psutil
import shutil
import glob
import sys
import os
import re


# Options File
Options_file = os.path.join(os.getcwd(), "Options.ini")
# [||||||||||]'s translations
translations = os.path.join(os.getcwd(), "lang")
# WeMod default path
# C:\Users\My UserName\AppData\local\WeMod\
WeModPath    = os.path.join(os.getenv("LOCALAPPDATA"), "WeMod\\")


#########################
# do you have WeMod?
#########################
def WeModDir(WeModPath):
    if os.path.exists(WeModPath):
        return True
    else:
        return False

#########################
# Values from options file :)
#########################
class GetOptions(object):
    def __init__(self, Options_file):
        self.config = configparser.ConfigParser()
        self.config.read(Options_file)

    # Value from Section
    def get_settings(self, section, setting):
        try:
            ret = self.config.get(section, setting)
        except configparser.NoOptionError:
            ret = None
        return ret

#########################
# Parse translation files
#########################
def tSectionHeader(file, header):
    yield '[{}]\n'.format(header)
    for line in file:
        yield line

#########################
# Translation file
#########################
def LangFile(locale):
    tFileList = {}
    try:
        tfile  = os.path.join(translations, "lang_" + locale + ".ini")
        file   = open(tfile, encoding='utf-8-sig')
        config = configparser.ConfigParser()
        config.read_file(tSectionHeader(file, 'tmp'), source=tfile)
        list = dict(config['tmp'])
        # Assign values to dictionary
        for var, val in list.items():
            tFileList[var] = re.sub("^\'|\'$", "", val)
    except Exception as e:
        # If you can't open for some reason :$
        print(colored("Error", "red"), f"when opening Language File: {e}")
        os.system('Pause')
        sys.exit(1)
    return tFileList

#########################
# Translations based off of locale
#########################
def GetLocale(force_lang=""):
    TranslatedFiles = {"de": LangFile("de"), 
                    "en": LangFile("en"), 
                    "fr": LangFile("fr"), 
                    "pt": LangFile("pt"), 
                    "ru": LangFile("ru"), 
                    "tr": LangFile("tr"), 
                    "zh-cn": LangFile("zh-cn") 
                    }
    try:
        # System Language and locale
        SysLang = subprocess.run(["powershell.exe", "powershell -NoProfile \"Get-UICulture|select -ExpandProperty DisplayName\""], stdout=subprocess.PIPE, check=True, text=True).stdout.strip()
        locale  = subprocess.run(["powershell.exe", "powershell -NoProfile \"Get-UICulture|select -ExpandProperty Name\""], stdout=subprocess.PIPE, check=True, text=True).stdout.strip()
        displaylocale = locale
        if locale.lower() == "zh-cn":
            locale = "zh-cn"
        locale = locale.split("-")[0]
    except subprocess.CalledProcessError:
        print(colored("Oopsies", "yellow"), "couldn't get system locale, defaulting to en :(")
        locale = "en"
    lang_file_list = TranslatedFiles.get(locale, LangFile("en"))
    # if forced_lang has supported translation
    if force_lang and force_lang in TranslatedFiles:
        lang_file_list = TranslatedFiles[force_lang]
    elif force_lang and force_lang != "en":
        print(colored("Oopsies", "yellow"), "there's an error with the value of FORCE_LANGUAGE_FILE in options file:", colored(force_lang, "yellow"), "defaulting to en :(")
        lang_file_list = LangFile("en")
    return lang_file_list, displaylocale, SysLang

#########################
#   Beep
#########################
def Beep(Beep="no"):
    # beep, beep
    if Beep == "yes":
        winsound.MessageBeep()
    # if no beep
    else:
        return

#########################
# First run?
#########################
def FirstRun(WMPath, latest_ver):
    backup_T = os.path.join(os.getcwd(), "app.asar.original")
    Asar_dir = os.path.join(WMPath, "app-" + latest_ver, "resources")
    # if backupfile in wemod dir
    if os.path.isfile(os.path.join(Asar_dir, "app.asar.original")):
        os.remove(os.path.join(Asar_dir, "app.asar"))
        os.rename(os.path.join(Asar_dir, "app.asar.original"), os.path.join(Asar_dir, "app.asar"))
    # if backupfile in current dir
    elif os.path.isfile(backup_T):
        os.remove(os.path.join(Asar_dir, "app.asar"))
        shutil.move(backup_T, os.path.join(Asar_dir, "app.asar"))

#########################
#   Clean Up and pack
#########################
def Cleanup(WMPath, latest_ver):
    print(colored("Cleaning", "yellow"), "up files :)")
    tmpdir   = os.path.join(os.getcwd(), "tmp")
    Asar_dir = os.path.join(WMPath, "app-" + latest_ver, "resources", "app.asar")
    unpacked = os.path.join(tmpdir, "asar_unpacked")
    try:
        files = os.listdir(unpacked)
        for f in files:
            if f.endswith(".js"):
                shutil.move(os.path.join(unpacked, f), os.path.join(tmpdir, f))
        subprocess.run("7z.exe a -y app.asar \"*.js\"", cwd=tmpdir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        shutil.move(os.path.join(tmpdir, "app.asar"), Asar_dir)
        shutil.rmtree(tmpdir)        
        print(colored("Cleaned", "green"), "up files :)")
    except Exception as e:
        print(colored("Error", "red"), f"in cleaning up {e}")

#########################
#   Gui
#########################
class gui:
    def __init__(self, list, WMPath, beep, locale, SysLang, Skip_beep_Q):
        self.list       = list
        self.WMPath     = WMPath
        self.beep       = beep
        self.locale     = locale
        self.SysLang    = SysLang
        self.beep_Q     = Skip_beep_Q

    # Gui initial question
    def init_QuestionsCheck(self):
        # is WeMod Running?
        is_running = "WeMod.exe" in (i.name() for i in psutil.process_iter())
        if is_running:
            Beep(Beep=self.beep)
            eg.msgbox(self.list['lang07'])
            # Kill WeMod
            title   = "Kill WeMod"
            msg     = "Kill WeMod process?"
            choices = ["Yes", "No"]
            if eg.buttonbox(msg, title, choices=choices) == "Yes":
                os.system("taskkill /F /im WeMod.exe")
            else:
                print(colored(self.list['lang08'], "yellow"))
                os.system('Pause')
                sys.exit(1)

        # is WeMod installed?
        installed = WeModDir(self.WMPath)
        if not installed:
            Beep(Beep=self.beep)
            eg.msgbox(f"WeMod {self.list['lang04']}\n {self.list['lang09']} {self.WMPath}")
            self.WMPath = eg.diropenbox("Select WeMod Folder")

        # Enable beep?
        if self.beep_Q == "yes":
            return self.WMPath, self.beep
        else:
            title   = self.list['lang10']
            msg     = self.list['lang11']
            choices = ["Yes", "No"]
            Beep(Beep=self.beep)
            if eg.buttonbox(msg, title, choices=choices) == "Yes":
                self.beep = "yes"
            else:
                self.beep = "no"
            return self.WMPath, self.beep

    # Options
    def MainMenu(self, versions, ProMode, Updates, DeveloperTools, latest_ver, [||||||||||]_ver):
        title     = "WeModPatcher"
        about_msg = "WeModPatcher by [||||||||||]\n" \
                    "Based off of [||||||||||] [||||||||||] [||||||||||] :)\n" \
                    f"\n{self.list['lang_translated']} {self.list['translatedby']}" \
                    f"\n{self.list['lang10']}: {self.beep}" \
                    f"\n{self.list['lang02']}\n" \
                    f"{self.list['lang_system']}: {self.SysLang}" \
                    f"\nlocale: {self.locale}" \
                    f"\n{self.list['lang13']}: | {versions} |" \
                    f"\n{self.list['lang14']}: | {latest_ver} |\n" \
                    f"\nCONFIG:" \
                    f"\n{self.list['lang15']}: {ProMode} {[||||||||||]_ver}" \
                    f"\n{self.list['lang23']}: {Updates}" \
                    f"\n{self.list['lang27']}: {DeveloperTools}"
        choices  = ["Select Option to configure",
                    f"{'='*25}",
                    # WeMod Pro
                    f"1. {self.list['lang15']}",
                    # Automatic Updates
                    f"2. {self.list['lang23']}",
                    # Developer Tools
                    f"3. {self.list['lang27']}",
                    # Restore From Back Up 
                    f"4. {self.list['lang55']}",
                    f"{'='*25}",
                    # Patch WeMod
                    f"{self.list['lang32']}"]
        Beep(Beep=self.beep)
        choice   = eg.choicebox(about_msg, title, choices)
        return choice

    # Pro Method
    def Pro_options(self):
        title   = self.list['lang15']
        msg     = self.list['lang18']
        choices = [f"1. {self.list['lang19']}",
                   f"2. {self.list['lang20']}"]
        Beep(Beep=self.beep)
        choice = eg.choicebox(msg, title, choices)
        if choice is None:
            return
        elif choice.startswith("1."):
            Mode    = "[||||||||||]"
            [||||||||||]_ver = ""
        elif choice.startswith("2."):
            Mode    = "[||||||||||]"
            msg     = "Version?"
            title   = Mode
            choices = ["1.0.4", "1.0.5"]
            Beep(Beep=self.beep)
            [||||||||||]_ver = eg.buttonbox(msg, title, choices=choices)
        return Mode, [||||||||||]_ver

    # Enable Pro?
    def Enable_Pro(self):
        title   = self.list['lang15']
        msg     = self.list['lang16']
        choices = ["Yes", "No"]
        Beep(Beep=self.beep)
        reply = eg.buttonbox(msg, title, choices=choices)
        if reply is None:
            return
        elif reply == "Yes":
            Mode, [||||||||||]_ver = self.Pro_options()
        else:
            return
        return Mode, [||||||||||]_ver

    # Enable Automatic Updates?
    def Updates(self):
        title   = self.list['lang23']
        msg     = self.list['lang24']
        choices = [f"1. {self.list['lang25']}",
                   f"2. {self.list['lang26']}"]
        Beep(Beep=self.beep)
        reply = eg.choicebox(msg, title, choices)
        if reply is None:
            return False
        elif reply.startswith("2."):
            return True
        else:
            return False

    # Enable Developer Tools?
    def Developer_Tools(self):
        title   = self.list['lang27']
        msg     = self.list['lang28']
        choices = [f"1. {self.list['lang29']}",
                   f"2. {self.list['lang30']}"]
        Beep(Beep=self.beep)
        reply = eg.choicebox(msg, title, choices)
        if reply is None:
            return False
        elif reply.startswith("1."):
            return True
        else:
            return False

    # Restore to original file
    def Restore_Backup(self, latest_ver):
        backup_T = os.path.join(self.WMPath, "app-" + latest_ver, "resources", "app.asar.original")
        backup_B = os.path.splitext(backup_T)[0] + ".bak"
        current  = os.path.splitext(backup_T)[0]
        try:
            # if they've used [||||||||||]'s tool beforehand
            if os.path.isfile(backup_B):
                if os.path.isfile(current):
                    os.remove(current)
                shutil.move(backup_B, current)
            # if they've used mine :)
            elif os.path.isfile(backup_T):
                if os.path.isfile(current):
                    os.remove(current)
                shutil.move(backup_T, current)
            else:
                # if somehow there's no backup in WeMod directory
                if not os.path.isfile(current):
                    backup_from_cwd = os.path.join(os.getcwd(), "app.asar.original")
                    shutil.copyfile(backup_from_cwd, current)
        except Exception as e:
            print(colored("Error", "red"), f"in restoring from backup: {e}")
            os.system('Pause')
            sys.exit(1)
        print(colored("Restored", "green"), "from backup :)")

#########################
#   WeMod Patch Routine
#########################
class Patching():
    def __init__(self, list, beep, ProMode, Updates, DeveloperTools, WMPath, latest_ver, splash, [||||||||||]_ver):
        self.list        = list
        self.beep        = beep
        self.ProMode     = ProMode
        self.Updates     = Updates
        self.DevTools    = DeveloperTools
        self.WMPath      = WMPath
        self.lver        = latest_ver
        self.splash      = splash
        self.[||||||||||]_ver     = [||||||||||]_ver
        self.tmpdir      = os.path.join(os.getcwd(), "tmp")
        self.AsarPath    = os.path.join(self.WMPath, "app-" + self.lver, "resources")
        self.rartools    = os.path.join(os.getcwd(), "WeModPatcherTools.rar")
        self.unpackeddir = os.path.join(self.tmpdir, "asar_unpacked")
        self.index_file  = os.path.join(self.unpackeddir, "index.js")
        self.app_files   = os.path.join(self.unpackeddir, "app-*.bundle.js")

    # Unpack files to tmp, make backups
    def unpack_files(self):
        print(colored("Unpacking", "yellow"), "files :)")
        try:
            # Make tmp dir
            if not os.path.exists(self.tmpdir):
                os.mkdir(self.tmpdir)
            elif os.path.exists(self.tmpdir):
                shutil.rmtree(self.tmpdir)
                os.mkdir(self.tmpdir)
            # Unpack rartools
            patoolib.extract_archive(self.rartools, outdir=self.tmpdir)
            # copy app.asar
            shutil.copyfile(os.path.join(self.AsarPath, "app.asar"), os.path.join(self.tmpdir, "app.asar"))
            # Mark Original file
            os.rename(os.path.join(self.AsarPath, "app.asar"), os.path.join(self.AsarPath, "app.asar.original"))
            # copy backup to current directory
            shutil.copyfile(os.path.join(self.AsarPath, "app.asar.original"), os.path.join(os.getcwd(), "app.asar.original"))
            # unpack app.asar to asar_unpacked
            subprocess.run("7z.exe e -y app.asar \"app-*bundle.js\" \"index.js\" -oasar_unpacked", cwd=self.tmpdir, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(colored("Error", "red"), f"in unpacking files: {e}")
            # Rename backup back to original case of failure :(
            os.rename(os.path.join(self.AsarPath, "app.asar.original"), os.path.join(self.AsarPath, "app.asar"))
            os.system('Pause')
            sys.exit(1)
        print(colored("Unpacked", "green"), f"files to {os.path.basename(self.tmpdir)} and app.asar to {os.path.join(os.path.basename(self.tmpdir), os.path.basename(self.unpackeddir))}")

    # Splash Screen
    def Splash(self):
        splashdir = os.path.join(self.tmpdir, "Splash.hta")
        try:
            if self.splash == "no":
                with open(splashdir, "r") as f:
                    buffer = f.read()
                    replace = re.sub("LANG_WELCOME", self.list['lang01'], buffer)
                with open(splashdir, "w") as f:
                    f.write(replace)
                subprocess.run(["mshta.exe", splashdir])
        except Exception as e:
            print(colored("Error", "red"), f"opening splash screen: {e}")
            os.system('Pause')
            sys.exit(1)

    # [||||||||||] Patch
    def [||||||||||](self):
        print(colored("Patching", "yellow"), "Files with [||||||||||]'s patch")
        gift_sender   = [||||||||||]
        original_func = [||||||||||]
        self.[||||||||||]_ver  = self.[||||||||||]_ver.replace(".", "")
        [||||||||||]_file      = os.path.join(self.tmpdir, "PRO_[||||||||||]_" + self.[||||||||||]_ver)
        files         = glob.glob(self.app_files)
        try:
            # [||||||||||] files
            with open([||||||||||]_file, "r", encoding="ascii") as f:
                buffer    = f.read()
                pattern   = "Gift_Sender" if self.[||||||||||]_ver == "105" else "-NewLine"
                replace   = re.sub(pattern, gift_sender if self.[||||||||||]_ver == "105" else "\n", buffer)
                [||||||||||]_patch = replace
            with open([||||||||||]_file, "w", encoding="ascii") as f:
                f.write(replace)
            # Asar files
            for file in files:
                with open(file, "r", encoding="utf-8-sig") as f:
                    lines = f.readlines()
                with open(file, "w", encoding="utf-8-sig") as f:
                    for line in lines:
                        if original_func in line:
                            f.write(line.replace(original_func, [||||||||||]_patch))
                        else:
                            f.write(line)
        except Exception as e:
            print(colored("Error", "red"), f"in [||||||||||] Patch method: {e}")
            os.system('Pause')
            sys.exit(1)
        print(colored("Patched!", "green"))
        # Enable Devtools?
        if self.DevTools == True:
            self.Dev_Tools()
        # Disable updates?
        elif self.Updates == True:
            self.dUpdates()

    # [||||||||||] Patch
    def [||||||||||](self):
        files         = glob.glob(self.app_files)
        original_func = [||||||||||]
        patched_func = [||||||||||]
        for file in files:
            with open(file, "r", encoding="utf-8-sig") as f:
                buffer = f.read()
                # Match each string
                for i, search in enumerate(original_func):
                    for match in re.finditer(search, buffer):
                        sIndex, eIndex = match.span()
                        # Sed out last } add patch string
                        replace = re.sub("\}$", "", match.group(0)) + patched_func[i]
                        # add patch to file content
                        buffer = buffer[:sIndex] + replace + buffer[eIndex:]
                with open(file, "w", encoding="utf-8-sig") as f:
                    f.write(buffer)
        if self.DevTools == True:
            self.Dev_Tools()
        elif self.Updates == True:
            self.dUpdates()

    # Disable Updates
    def dUpdates(self):
        print(colored("Patching", "yellow"), "updates with [||||||||||]'s patch")
        original_func = [||||||||||]
        patched_func =  [||||||||||]
        try:
            with open(self.index_file, "r", encoding="ascii") as f:
                buffer  = f.read()
                pattern = original_func[1] if version.parse("8.5.0") >= version.parse(self.lver) else original_func[0]
                replace = re.sub(pattern, patched_func, buffer)
            with open(self.index_file, "w", encoding="ascii") as f:
                f.write(replace)
        except Exception as e:
            print(colored("Error", "red"), f"in disabling updates: {e}")
            os.system('Pause')
            sys.exit(1)
        print(colored("Patched!", "green"))

    # Enable Developer Tools
    def Dev_Tools(self):
        print(colored("Enabling", "yellow"), "Developer Tools")
        original_func = [||||||||||]
        patched_func  = [||||||||||]
        try:
            with open(self.index_file, "r", encoding="ascii") as f:
                buffer = f.read()
                replace = re.sub(original_func, patched_func, buffer)
            with open(self.index_file, "w", encoding="ascii") as f:
                f.write(replace)
                print(colored("Enabled", "green"), "Developer Tools")
        except Exception as e:
            print(colored("Error", "red"), f"in enabling DevTools: {e}")
            os.system('Pause')
            sys.exit(1)

    # Patch WeMod?
    def Patch(self):
        if self.ProMode == None:
            eg.msgbox("No ProMode Set!")
            return False
        title = self.list['lang32']
        msg   = "Continue with these settings?\n" \
            f"\n{self.list['lang15']}: {self.ProMode} {self.[||||||||||]_ver}" \
            f"\n{self.list['lang23']}: {self.Updates}" \
            f"\n{self.list['lang27']}: {self.DevTools}"
        choices = ["Yes", "No"]
        Beep(Beep=self.beep)
        reply = eg.buttonbox(msg, title, choices=choices)
        if reply == "No":
            return False
        elif self.ProMode == "[||||||||||]":
            self.unpack_files()
            self.Splash()
            self.[||||||||||]()
            return True
        elif self.ProMode == "[||||||||||]":
            self.unpack_files()
            self.Splash()
            self.[||||||||||]()
            return True
        else:
            return False

#########################
#   Display :)
#########################
def Display(list, WMPath, beep, locale, SysLang, splash, Skip_beep_Q):
    # Default values
    [||||||||||]_ver        = ""
    ProMode        = None
    Updates        = False
    DeveloperTools = True

    # init
    Gui = gui(list, 
              WMPath, 
              beep, 
              locale, 
              SysLang, 
              Skip_beep_Q
              )

    print(colored("\033[FGUI Loaded!\n", "green"))
    print(colored("Info:", "yellow"))

    # Initial questions and checks
    WMPath, beep = Gui.init_QuestionsCheck()
    Gui.WMPath = WMPath
    print(f"Enabled Beep: {beep}")

    # WeMod Versions
    versions = []
    WM_ver   = os.listdir(WMPath)
    for ver in WM_ver:
        if ver.startswith("app-"):
            ver = re.sub("^app-", "", ver)
            versions.append(ver)
    latest_ver = versions[len(versions) - 1]
    versions = " | ".join(versions)

    # First run check
    FirstRun(WMPath, latest_ver)

    # Patching
    patch = Patching(list, 
                     beep, 
                     ProMode, 
                     Updates, 
                     DeveloperTools, 
                     WMPath, 
                     latest_ver, 
                     splash, 
                     [||||||||||]_ver
                     )

    # Until patch do config
    while True:
        choice = Gui.MainMenu(versions,
                              ProMode, 
                              Updates, 
                              DeveloperTools, 
                              latest_ver,
                              [||||||||||]_ver
                              )
        if choice is None:
            print(colored(list['lang50'], "yellow"))
            sys.exit(1)
        elif choice.startswith("1."):
            ProMode, [||||||||||]_ver = Gui.Enable_Pro()
            patch.ProMode    = ProMode
            patch.[||||||||||]_ver    = [||||||||||]_ver
            print(f"Enabled Pro Method: {ProMode} {[||||||||||]_ver}")
        elif choice.startswith("2."):
            Updates       = Gui.Updates()
            patch.Updates = Updates
            print(f"Enable Automatic Updates: {Updates}")
        elif choice.startswith("3."):
            DeveloperTools = Gui.Developer_Tools()
            patch.DevTools = DeveloperTools
            print(f"Enable Developer Tools: {DeveloperTools}")
        elif choice.startswith("4."):
            print(colored("\nRestoring", "yellow"), "WeMod from Backup...")
            Gui.Restore_Backup(latest_ver)
        elif choice == list['lang32']:
            print(colored("\nPatching WeMod :D", "yellow"))
            Has_Patched = patch.Patch()
            if Has_Patched == True:
                break
    return WMPath, latest_ver

#########################
#   Main
#########################
def main():
    # Colors! :D
    just_fix_windows_console()
    print(colored("Hiya! made by [||||||||||]!", "magenta"))
    print(colored("Based off of [||||||||||]'s [||||||||||] [||||||||||]!\n", "cyan"))
    print("All Debugging and other info will be here!")
    print(colored("Loading GUI", "yellow"))

    os.rename(os.path.join(os.getcwd(), "WeModTools"), os.path.join(os.getcwd(), "WeModTools.rar"))

    # Values from Options File
    options       = GetOptions(Options_file)
    lang          = options.get_settings("LANGUAGE", "FORCE_LANGUAGE_FILE").replace("'", "").lower()
    splash        = options.get_settings("SPLASH BANNER", "SKIP_BANNER").replace("'", "").lower()
    beep          = options.get_settings("BEEP", "ENABLE_BEEP").replace("'", "").lower()
    Skip_beep_Q   = options.get_settings("BEEP", "SKIP_BEEP_QUESTION").replace("'", "").lower()
    # No support for now :(
    #speech        = options.get_settings("SPEECH", "SKIP_SPEECH_QUEST")
    #speech_enable = options.get_settings("SPEECH", "ENABLE_SPEECH")
    #shortcut      = options.get_settings("SHORTCUT", "CREATE_SHORTCUT")

    # Translations
    list, Displaylocale, SysLang = GetLocale(force_lang=lang)

    # Gui Routine :)
    WMPath, latest_ver = Display(list, WeModPath, beep, Displaylocale, SysLang, splash, Skip_beep_Q)

    # Clean up and pack
    Cleanup(WMPath, latest_ver)

    print(colored(list['lang50'], "magenta"))
    sys.exit(1)

if __name__ == '__main__':
    main()
