#!/usr/bin/env python
import shutil
import os
import subprocess
from shutil import copyfile
from os import path
from platform import system
import time
import textwrap


# defaults
SCRIPT_VERSION = '0.1.4'
BASE_PATH = '.'  # base path where script looks for templates an store output files

FORCE_UNINSTALL = True  # if true, test applet will be always attempted to be removed. Set to False for faster testing
FORCE_NO_SAFETY_CHECK = False # if True, no user prompt for authentication verification is performed. Leave this as False

SYSTEM = system()  # detect system platform, will be used for running GlobalPlatformPro binary and also for determining success responses
GP_BASIC_COMMAND = ['gp.exe'] if SYSTEM == 'Windows' else ['java', '-jar', 'gp.jar']  # command which will start GlobalPlatformPro binary
GP_AUTH_FLAG = []  # most of the card requires no additional authentication flag
# GP_AUTH_FLAG = '--emv'  # use of EMV key diversification is used (e.g., G&D cards)

SUCCESS_RESPONSE_HEURISTICS = '9000\r\nSCardEndTransaction(' if SYSTEM == 'Windows' else '9000\nSCardEndTransaction('

AID_VERSION_MAP = {"000107A0000000620001": "JC 2.1",  # java.lang
                   "000107A0000000620002": "JC 2.2.0",  # java.io
                   "000107A0000000620003": "JC 2.2.0",  # java.rmi
                   # javacard.framework
                   "000107A0000000620101": "JC 2.1", "010107A0000000620101": "JC 2.2.0", "020107A0000000620101": "JC 2.2.1",
                   "030107A0000000620101": "JC 2.2.2", "040107A0000000620101": "JC 3.0.1", "050107A0000000620101": "JC 3.0.4",
                   "060107A0000000620101": "JC 3.0.5",
                   # javacard.framework.service
                   "000108A000000062010101": "JC 2.2.0",
                   # javacard.security
                   "000107A0000000620102": "JC 2.1", "010107A0000000620102": "JC 2.1.1", "020107A0000000620102": "JC 2.2.1",
                   "030107A0000000620102": "JC 2.2.2", "040107A0000000620102": "JC 3.0.1", "050107A0000000620102": "JC 3.0.4",
                   "060107A0000000620102": "JC 3.0.5",
                   # javacardx.crypto
                   "000107A0000000620201": "JC 2.1", "010107A0000000620201": "JC 2.1.1", "020107A0000000620201": "JC 2.2.1",
                   "030107A0000000620201": "JC 2.2.2", "040107A0000000620201": "JC 3.0.1", "050107A0000000620201": "JC 3.0.4",
                   "060107A0000000620201": "JC 3.0.5",
                   # javacardx.biometry (starting directly from version 1.2 - previous versions all from 2.2.2)
                   "000107A0000000620202": "JC 2.2.2", "010107A0000000620202": "JC 2.2.2", "020107A0000000620202": "JC 2.2.2",
                   "030107A0000000620202": "JC 3.0.5",
                   "000107A0000000620203": "JC 2.2.2",  # javacardx.external
                   "000107A0000000620204": "JC 3.0.5",  # javacardx.biometry1toN
                   "000107A0000000620205": "JC 3.0.5",  # javacardx.security
                   # javacardx.framework.util
                   "000108A000000062020801": "JC 2.2.2", "010108A000000062020801": "JC 3.0.5",
                   "000109A00000006202080101": "JC 2.2.2",  # javacardx.framework.util.intx
                   "000108A000000062020802": "JC 2.2.2",  # javacardx.framework.math
                   "000108A000000062020803": "JC 2.2.2",  # javacardx.framework.tlv
                   "000108A000000062020804": "JC 3.0.4",  # javacardx.framework.string
                   "000107A0000000620209": "JC 2.2.2",  # javacardx.apdu
                   "000108A000000062020901": "JC 3.0.5",  # javacardx.apdu.util
                   # org.globalplatform
                   "000106A00000015100": "GP 2.1.1", "010106A00000015100": "GP 2.2", "020106A00000015100": "GP 2.2",
                   "030106A00000015100": "GP 2.2", "040106A00000015100": "GP 2.2", "050106A00000015100": "GP 2.2.1",
                   "060106A00000015100": "GP 2.2.1",
                   # org.globalplatform.contactless
                   "000106A00000015102": "GP 2.2.1", "010106A00000015102": "GP 2.2.1", "020106A00000015102": "GP 2.2.1",
                   "030106A00000015102": "GP 2.3", "040106A00000015102": "GP 2.3", "050106A00000015102": "GP 2.3",
                   "060106A00000015102": "GP 2.3",
                   # org.globalplatform.securechannel
                   "000106A00000015103": "GP 2.2.1", "010106A00000015103": "GP 2.2.1", "020106A00000015103": "GP 2.2.1",
                   "030106A00000015103": "GP 2.3", "040106A00000015103": "GP 2.3",
                   # org.globalplatform.securechannel.provider
                   "000106A00000015104": "GP 2.2.1", "010106A00000015104": "GP 2.2.1", "020106A00000015104": "GP 2.2.1",
                   # org.globalplatform.privacy
                   "000106A00000015105": "GP 2.2.1", "010106A00000015105": "GP 2.2.1", "020106A00000015105": "GP 2.2.1",
                   # org.globalplatform.filesystem
                   "000106A00000015106": "GP 2.2.1", "010106A00000015106": "GP 2.2.1", "020106A00000015106": "GP 2.2.1",

                   # visa.openplatform
                   "000107A0000000030000": "OP 2.0",
                   }

AID_NAME_MAP = {"A0000000620001": "java.lang",
                "A0000000620002": "java.io",
                "A0000000620003": "java.rmi",
                "A0000000620101": "javacard.framework",
                "A000000062010101": "javacard.framework.service",
                "A0000000620102": "javacard.security",
                "A0000000620201": "javacardx.crypto",
                "A0000000620202": "javacardx.biometry",
                "A0000000620203": "javacardx.external",
                "A0000000620204": "javacardx.biometry1toN",
                "A0000000620205": "javacardx.security",
                "A000000062020801": "javacardx.framework.util",
                "A00000006202080101":"javacardx.framework.util.intx",
                "A000000062020802":"javacardx.framework.math",
                "A000000062020803":"javacardx.framework.tlv",
                "A000000062020804":"javacardx.framework.string",
                "A0000000620209": "javacardx.apdu",
                "A000000062020901": "javacardx.apdu.util",
                "A00000015100": "org.globalplatform",
                "A00000015102": "org.globalplatform.contactless",
                "A00000015103": "org.globalplatform.securechannel",
                "A00000015104": "org.globalplatform.securechannel.provider",
                "A00000015105": "org.globalplatform.privacy",
                "A00000015106": "org.globalplatform.filesystem",
                "A0000000030000": "visa.openplatform"
                }


class PackageAID:
    aid = []
    major = 0
    minor = 0

    def __init__(self, aid, major, minor):
        self.aid = aid
        self.major = major
        self.minor = minor

    def get_readable_string(self):
        return "{0} v{1}.{2} {3}".format(self.get_well_known_name(), self.major, self.minor, self.get_aid_hex())

    def get_length(self):
        return len(self.aid) + 1 + 1 + 1

    def serialize(self):
        aid_str = ''.join('{:02X}'.format(a) for a in self.aid)
        # one package format: package_major package_minor package_len package_AID
        serialized = '{:02X}{:02X}{:02X}{}'.format(self.minor, self.major, len(self.aid), aid_str)
        return serialized

    def get_aid_hex(self):
        return bytes(self.aid).hex()  # will be in lowercase

    def get_well_known_name(self):
        hex_aid = bytes(self.aid).hex().upper()
        if hex_aid in AID_NAME_MAP:
            return AID_NAME_MAP[hex_aid]
        else:
            return "unknown"

    def get_first_jcapi_version(self):
        hex_aid = bytes(self.aid).hex().upper()
        aid_with_version = "{0:02X}{1:02X}{2:02X}{3}".format(self.minor, self.major, len(self.aid), hex_aid)
        if aid_with_version in AID_VERSION_MAP:
            version = AID_VERSION_MAP[aid_with_version]
        else:
            version = "unknown"

        return version


class TestCfg:
    min_major = 1
    max_major = 1
    min_minor = 0
    max_minor = 1
    modified_ranges = []
    package_template = ""
    package_template_bytes = []

    def __init__(self, package_template, min_major, max_major, min_minor, max_minor, modified_range=None):
        self.min_major = min_major
        self.max_major = max_major
        self.min_minor = min_minor
        self.max_minor = max_minor
        self.modified_ranges = modified_range
        self.package_template = package_template
        self.package_template_bytes = bytearray(bytes.fromhex(package_template))

    def __repr__(self):
        modifiers_str = ""
        if self.modified_ranges:
            modifiers_str = ''.join('[{0}]=[{1:02X}-{2:02X}] '.format(a[0], a[1], a[2]) for a in self.modified_ranges)
        return 'MAJOR=[{0}-{1}], MINOR=[{2}-{3}], {4}, TEMPLATE={5}'.format(
            self.min_major, self.max_major, self.min_minor, self.max_minor, modifiers_str, self.package_template)

    @staticmethod
    def get_val_range(offset, modified_ranges, template_value):
        if modified_ranges:
            for range_modif in modified_ranges:
                if range_modif[0] == offset:
                    return range_modif[1], range_modif[2]

        # if no special range modifier found, then return byte from template
        return template_value, template_value


class CardInfo:
    card_name = ""
    atr = ""
    cplc = ""
    gp_i = ""

    def __init__(self, card_name, atr, cplc, gp_i):
        self.card_name = card_name
        self.atr = atr
        self.cplc = cplc
        self.gp_i = gp_i


javacard_framework = PackageAID(b'\xA0\x00\x00\x00\x62\x01\x01', 1, 0)
java_lang = PackageAID(b'\xA0\x00\x00\x00\x62\x00\x01', 1, 0)

package_template = b'\xA0\x00\x00\x00\x62\x01\x01'


class AIDScanner:
    base_path = BASE_PATH
    force_uninstall = FORCE_UNINSTALL  # if true, test applet will be always attempted to be removed. Set to False for faster testing
    force_no_safety_check = FORCE_NO_SAFETY_CHECK  # if True, no user prompt for authentication verification is performed. Leave this as False
    gp_basic_command = GP_BASIC_COMMAND  # command which will start GlobalPlatformPro binary
    gp_auth_flag = GP_AUTH_FLAG  # most of the card requires no additional authentication flag, some requires '--emv'
    gp_uninstall_command = GP_BASIC_COMMAND + GP_AUTH_FLAG + ['--uninstall']  # command starting installation of applet
    gp_install_command = GP_BASIC_COMMAND + GP_AUTH_FLAG + ['--install']  # command starting uninstall of applet

    success_response_heuristics = SUCCESS_RESPONSE_HEURISTICS

    card_name = ""
    is_installed = True # if true, test applet is installed and will  be removed
    num_tests = 0 # number of executed tests (for performance measurements)

    def check_aid(self, import_section, package, uninstall):
        # save content of Import.cap into directory structure
        print(import_section)
        f = open(path.join(self.base_path, 'template', 'test', 'javacard', 'Import.cap'), 'wb')
        f.write(bytes.fromhex(import_section))
        f.close()

        # create new cap file by zip of directories
        shutil.make_archive('test.cap', 'zip', path.join(self.base_path, 'template'))

        package_hex = package.serialize()

        # remove zip suffix
        if os.path.exists('test.cap'):
            os.remove('test.cap')
        os.rename('test.cap.zip', 'test.cap')
        # store used cap file
        copyfile('test.cap', path.join(self.base_path, 'results', 'test_{0}.cap'.format(package_hex)))

        # (try to) uninstall previous applet if necessary/required
        if uninstall or self.force_uninstall:
            subprocess.run(self.gp_uninstall_command + ['test.cap'], stdout=subprocess.PIPE)

        # try to install test applet
        result = subprocess.run(self.gp_install_command + ['test.cap'] + ['--d'], stdout=subprocess.PIPE)

        # store gp result into log file
        result = result.stdout.decode("utf-8")
        f = open(path.join(self.base_path, 'results', '{0}.txt'.format(package_hex)), 'w')
        f.write(result)
        f.close()

        # heuristics to detect successful installation - log must contain error code 0x9000 followed by SCardEndTransaction
        # If installation fails, different error code is present
        if result.find(self.success_response_heuristics) != -1:
            return True
        else:
            return False

    def format_import(self, packages_list):
        total_len = 1 # include count of number of packages
        for package in packages_list:
            total_len += package.get_length()

        # format of Import.cap: 04 00 len num_packages package1 package2 ... packageN
        import_section = '0400{:02x}{:02x}'.format(total_len, len(packages_list))

        # serialize all packages
        for package in packages_list:
            import_section += package.serialize()

        return import_section

    def test_aid(self, tested_package_aid, supported_list, tested_list):
        imported_packages = []
        imported_packages.append(javacard_framework)
        #imported_packages.append(java_lang)  # do not import java_lang as default (some cards will then fail to load)
        imported_packages.append(tested_package_aid)

        import_content = self.format_import(imported_packages)

        if self.check_aid(import_content, tested_package_aid, self.is_installed):
            print(" ###########\n  {0} IS SUPPORTED\n ###########\n".format(tested_package_aid.get_readable_string()))
            supported_list.append(tested_package_aid)
            tested_list[tested_package_aid] = True
            self.is_installed = True
        else:
            print("   {0} v{1}.{2} is NOT supported ".format(tested_package_aid.get_aid_hex(), tested_package_aid.major,
                                                             tested_package_aid.minor))
            tested_list[tested_package_aid] = False
            self.is_installed = False

        return self.is_installed

    def print_supported(self, supported, supported_caps):
        print(" #################\n")
        if supported_caps:
            if len(supported_caps) > 0:
                for convertor_version in supported_caps:
                    if supported_caps[convertor_version]:
                        print("{0} convertor version supported\n".format(convertor_version))

        if len(supported) > 0:
            for supported_aid in supported:
                print("{0} (since API {1})\n".format(supported_aid.get_readable_string(),
                                                        supported_aid.get_first_jcapi_version()))
        else:
            print("No items")
        print(" #################\n")

    def run_scan_recursive(self, modified_ranges_list, package_aid, major, minor, supported, tested):
        # recursive stop
        if len(modified_ranges_list) == 0:
            return

        # make local copy of modifiers list except first item
        local_modified_ranges_list = []
        local_modified_ranges_list[:] = modified_ranges_list[1:]

        # process first range and call recursively for the rest
        current_range = modified_ranges_list[0]
        offset = current_range[0]
        # compute actual range based on provided values
        start = current_range[1]
        stop = current_range[2]

        local_package_aid = bytearray(len(package_aid))
        local_package_aid[:] = package_aid
        for value in range(start, stop + 1):
            local_package_aid[offset] = value

            # check if already applied all modifiers
            if len(local_modified_ranges_list) == 0:
                #  if yes, then check prepared AID
                new_package = PackageAID(local_package_aid, major, minor)
                # test current package
                self.test_aid(new_package, supported, tested)
                self.num_tests += 1
            else:
                # if no, run additional recursion
                self.run_scan_recursive(local_modified_ranges_list, local_package_aid, major, minor, supported, tested)

        # print supported after iterating whole range
        self.print_supported(supported, None)


    def run_scan(self, cfg, supported, tested):
        print("################# BEGIN ###########################\n")
        print(cfg)
        print("###################################################\n")

        localtime = time.asctime(time.localtime(time.time()))
        print(localtime)

        # start performance measurements
        elapsed = -time.perf_counter()
        self.num_tests = 0

        self.is_installed = True  # assume that test applet was installed to call uninstall

        # check all possible values from specified ranges
        new_package_aid = bytearray(bytes.fromhex(cfg.package_template))
        for major in range(cfg.min_major, cfg.max_major + 1):
            self.print_supported(supported, None)
            print("############################################\n")
            print("MAJOR = {0:02X}".format(major))
            for minor in range(cfg.min_minor, cfg.max_minor + 1):
                self.print_supported(supported, None)
                print("###########################:#################\n")
                print("MAJOR = {0:02X}, MINOR = {1:02X}".format(major, minor))

                # Now recursively iterate via specified ranges (if provided)
                if cfg.modified_ranges:
                    self.run_scan_recursive(cfg.modified_ranges, new_package_aid, major, minor, supported, tested)
                else:
                    # nor modification ranges, just test package with current combination of major and minor version
                    new_package = PackageAID(new_package_aid, major, minor)
                    # test current package
                    self.test_aid(new_package, supported, tested)
                    self.num_tests += 1

        # end performance measurements
        elapsed += time.perf_counter()

        self.print_supported(supported, None)

        print("Elapsed time: {0:0.2f}s\nTesting speed: {1:0.2f} AIDs / min\n".format(elapsed, self.num_tests / (elapsed / 60)))

        print("################# END ###########################\n")
        print(cfg)
        print("#################################################\n")

    def scan_jc_api_305(self, card_info, supported_caps, supported, tested):
        MAX_MAJOR = 1
        ADDITIONAL_MINOR = 1
        # minor is tested with ADDITIONAL_MINOR additional values higher than expected from the given version of JC SDK).
        # If highest version is detected, additional inspection is necessary - suspicious (some cards ignore minor version)

        # intermediate results are saved after every tested package to preserve info even in case of card error

        self.run_scan(TestCfg("A0000000620001", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)
        self.run_scan(TestCfg("A0000000620002", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)
        self.run_scan(TestCfg("A0000000620003", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)

        self.run_scan(TestCfg("A0000000620101", 1, MAX_MAJOR, 0, 6 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)
        self.run_scan(TestCfg("A000000062010101", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)
        self.run_scan(TestCfg("A0000000620102", 1, MAX_MAJOR, 0, 6 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)

        self.run_scan(TestCfg("A0000000620201", 1, MAX_MAJOR, 0, 6 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)
        self.run_scan(TestCfg("A0000000620202", 1, MAX_MAJOR, 0, 3 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)

        self.run_scan(TestCfg("A0000000620203", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)
        self.run_scan(TestCfg("A0000000620204", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)
        self.run_scan(TestCfg("A0000000620205", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)

        self.run_scan(TestCfg("A000000062020801", 1, MAX_MAJOR, 0, 1 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)
        self.run_scan(TestCfg("A00000006202080101", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)
        self.run_scan(TestCfg("A000000062020802", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)

        self.run_scan(TestCfg("A000000062020803", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)
        self.run_scan(TestCfg("A000000062020804", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)

        self.run_scan(TestCfg("A0000000620209", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)
        self.run_scan(TestCfg("A000000062020901", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)

        self.print_supported(supported, supported_caps)

    def scan_globalplatform_api(self, card_info, supported_caps, supported, tested):
        MAX_MAJOR = 1
        ADDITIONAL_MINOR = 1
        # minor is tested with ADDITIONAL_MINOR additional values higher than expected from the given version of JC SDK).
        # If highest version is detected, additional inspection is necessary - suspicious (some cards ignore minor version)

        # intermediate results are saved after every tested package to preserve info even in case of card error
        self.run_scan(TestCfg("A00000015100", 1, MAX_MAJOR, 0, 8 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)

        self.run_scan(TestCfg("A00000015102", 1, MAX_MAJOR, 0, 4 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)

        self.run_scan(TestCfg("A00000015103", 1, MAX_MAJOR, 0, 1 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)

        self.run_scan(TestCfg("A00000015104", 1, MAX_MAJOR, 0, 1 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)

        self.run_scan(TestCfg("A00000015105", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)

        self.run_scan(TestCfg("A00000015106", 1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)


        self.run_scan(TestCfg("A0000000030000", 1, MAX_MAJOR, 0, 1 + ADDITIONAL_MINOR), supported, tested)
        self.save_scan(card_info, supported_caps, supported, tested)

        self.print_supported(supported, supported_caps)

    def test_upload_cap(self, cap_name, cap_version, supported_caps):
        print(" Going to upload cap file '" + cap_name + "' (JC API " + cap_version + ") ... ")
        # try to install test applet
        subprocess.run(self.gp_uninstall_command + [cap_name], stdout=subprocess.PIPE)
        result = subprocess.run(self.gp_install_command + [cap_name] + ['--d'], stdout=subprocess.PIPE)
        result = result.stdout.decode("utf-8")
        # heuristics to detect successful installation - log must contain error code 0x9000 followed by SCardEndTransaction
        # If installation fails, different error code is present
        if result.find(self.success_response_heuristics) != -1:
            print("OK\n")
            supported_caps[cap_version] = True
        else:
            print("FAIL\n")
            supported_caps[cap_version] = False

    def test_upload_caps(self, supported_caps):
        print("################# END ###########################\n")
        self.test_upload_cap('test_211.cap', '2.1.1', supported_caps)
        self.test_upload_cap('test_220.cap', '2.2.0', supported_caps)
        self.test_upload_cap('test_221.cap', '2.2.1', supported_caps)
        self.test_upload_cap('test_222.cap', '2.2.2', supported_caps)
        self.test_upload_cap('test_301.cap', '3.0.1', supported_caps)
        self.test_upload_cap('test_304.cap', '3.0.4', supported_caps)
        self.test_upload_cap('test_305.cap', '3.0.5', supported_caps)

    def get_card_info(self, card_name):
        if card_name == "":
            card_name = input("Please enter card name: ")

        result = subprocess.run(self.gp_basic_command + self.gp_auth_flag + ['--i'], stdout=subprocess.PIPE)
        result_text = result.stdout.decode("utf-8")

        atr_before = "http://smartcard-atr.appspot.com/parse?ATR="
        pos = result_text.find(atr_before)
        end_pos = result_text.find("\n", pos)
        atr = result_text[pos + len(atr_before):end_pos]
        atr = atr.rstrip()

        cplc_before = "CPLC:"
        cplc_after = "ICPersonalizationEquipmentID="
        pos = result_text.find(cplc_before)
        if pos == -1:
            pos = 0

        pos_end = result_text.find(cplc_after)
        if pos_end == -1:
            pos_end = len(result_text)
        else:
            pos_end = pos_end + len(cplc_after) + 8 # +8 is because of equipment id, e.g., B11801EE

        cplc = result_text[pos + len(cplc_before):pos_end]

        cplc = cplc.rstrip()
        cplc = cplc.replace(":", ";")
        cplc = cplc.replace("      ", "")

        return CardInfo(card_name, atr, cplc, result_text)

    def save_scan(self, card_info, supported_cap_versions, supported, tested):
        card_name = card_info.card_name.replace(' ', '_')
        file_name = "{0}_AIDSUPPORT_{1}.csv".format(card_name, card_info.atr)
        f = open(path.join(self.base_path, file_name), 'w')

        f.write("jcAIDScan version; {0}\n".format(SCRIPT_VERSION))
        f.write("Card ATR; {0}\n".format(card_info.atr))
        f.write("Card name; {0}\n".format(card_info.card_name))
        f.write("CPLC;;\n{0}\n\n".format(card_info.cplc))

        f.write("PACKAGE AID; MAJOR VERSION; MINOR VERSION; PACKAGE NAME; INTRODUCING JC API VERSION;\n")
        for aid in supported:
            f.write("{0}; {1}; {2}; {3}; {4}\n".format(aid.get_aid_hex(), aid.major, aid.minor, aid.get_well_known_name(),
                                                   aid.get_first_jcapi_version()))

        if tested:
            f.write("\n")
            f.write("FULL PACKAGE AID; IS SUPPORTED?; PACKAGE NAME WITH VERSION; \n")
            for aid in tested:
                f.write("{0}; \t{1}; \t{2};\n".format(aid.serialize(), "yes" if tested[aid] else "no", aid.get_readable_string()))

        if supported_cap_versions:
            f.write("\n")
            f.write("JC CONVERTOR VERSION; CAP SUCCESSFULLY UPLOADED?;;\n")
            for version in supported_cap_versions:
                f.write("{0}; {1};\n".format(version, "yes" if supported_cap_versions[version] else "no"))

        f.close()

    def prepare_for_testing(self):
        # restore default import section
        imported_packages = []
        imported_packages.append(javacard_framework)
        imported_packages.append(java_lang)
        import_section = self.format_import(imported_packages)
        f = open(path.join(self.base_path, 'template', 'test', 'javacard', 'Import.cap'), 'wb')
        f.write(bytes.fromhex(import_section))
        f.close()

        # uninstall any previous installation of applet
        result = subprocess.run(self.gp_uninstall_command + ['test.cap'], stdout=subprocess.PIPE)
        result_text = result.stdout.decode("utf-8")
        self.is_installed = False

    def verify_gp_authentication(self):
        # Try to list applets on card then prompt user for confirmation
        info = "IMPORTANT: Supported package scanning will execute large number of OpenPlatform SCP " \
                            "authentications. If your GlobalPlatformPro tool is not setup properly and fails to " \
                            "authenticate, your card may be permanently blocked. This script will now execute one " \
                            "authentication to list installed applets. Check if everything is correct. If you will see " \
                            "any authentication error, do NOT continue. Also, do not remove your card from reader during "\
                            "the whole scanning process."
        print(textwrap.fill(info, 80))

        input("\nPress enter to continue...")
        print("Going to list applets, please wait...")

        result = subprocess.run(self.gp_basic_command + self.gp_auth_flag + ['--list'] + ['--d'], stdout=subprocess.PIPE)
        result_text = result.stdout.decode("utf-8")
        print(result_text)

        auth_result = input("Were applets listed with no error? (yes/no): ")
        if auth_result == "yes":
            return True
        else:
            return False

    def print_info(self):
        print("jcAIDScan v{0} tool for scanning supported JavaCard packages.\nCheck https://github.com/petrs/jcAIDScan/ "
              "for the newest version and documentation.\n2018, Petr Svenda\n".format(SCRIPT_VERSION))

        info = "WARNING: this is a research tool and expects that you understand what you are doing. Your card may be " \
               "permanently blocked in case of incorrect use."

        print(textwrap.fill(info, 80))

    def scan_jc_api_305_complete(self):
        # verify gp tool configuration + user prompt
        if not self.force_no_safety_check:
            if not self.verify_gp_authentication():
                return

        # restore template to good known state, uninstall applet etc.
        self.prepare_for_testing()

        # obtain card basic info
        card_info = self.get_card_info(self.card_name)

        # create folder for results, if doesn't exist
        if not os.path.exists('./results/'):
            os.mkdir('./results/', 0o755)

        # try to upload cap files converted with different version of JC convertor
        supported_caps = {}
        supported = []
        tested = {}
        self.scan_globalplatform_api(card_info, supported_caps, supported, tested)
        self.test_upload_caps(supported_caps)

        # scan standard JC API
        #supported = []
        #tested = {}
        elapsed = -time.perf_counter()
        self.scan_jc_api_305(card_info, supported_caps, supported, tested)
        elapsed += time.perf_counter()
        print("Complete test elapsed time: {0:0.2f}s\n".format(elapsed))
        # create file with results
        self.save_scan(card_info, supported_caps, supported, tested)


def main():
    app = AIDScanner()
    app.scan_jc_api_305_complete()


if __name__ == "__main__":
    main()
