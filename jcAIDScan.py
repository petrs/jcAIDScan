import shutil
import os
import subprocess
from shutil import copyfile
import time

# TODO: save complete log to separate named file
# Format Import.cap: 04 00 len num_packages package1 package2 ... packageN
# packageFormat: package_major package_minor package_len AID

SCRIPT_VERSION = "0.1.0"
BASE_PATH = '.'


AID_VERSION_MAP = {"000107A0000000620001": "2.1",  # java.lang
                   "000107A0000000620002": "2.2.0",  # java.io
                   "000107A0000000620003": "2.2.0",  # java.rmi
                   # javacard.framework
                   "000107A0000000620101": "2.1", "010107A0000000620101": "2.2.0", "020107A0000000620101": "2.2.1",
                   "030107A0000000620101": "2.2.2", "040107A0000000620101": "3.0.1", "050107A0000000620101": "3.0.4",
                   "060107A0000000620101": "3.0.5",
                   # javacard.framework.service
                   "000108A000000062010101": "2.2.0",
                   # javacard.security
                   "000107A0000000620102": "2.1", "010107A0000000620102": "2.1.1", "020107A0000000620102": "2.2.1",
                   "030107A0000000620102": "2.2.2", "040107A0000000620102": "3.0.1", "050107A0000000620102": "3.0.4",
                   "060107A0000000620102": "3.0.5",
                   # javacardx.crypto
                   "000107A0000000620201": "2.1", "010107A0000000620201": "2.1.1", "020107A0000000620201": "2.2.1",
                   "030107A0000000620201": "2.2.2", "040107A0000000620201": "3.0.1", "050107A0000000620201": "3.0.4",
                   "060107A0000000620201": "3.0.5",
                   # javacardx.biometry (starting directly from version 1.2)
                   "020107A0000000620202": "2.2.2", "030107A0000000620202": "3.0.5",
                   "000107A0000000620203": "2.2.2",  # javacardx.external
                   "000107A0000000620204": "3.0.5",  # javacardx.biometry1toN
                   "000107A0000000620005": "3.0.5",  # javacardx.security
                   # javacardx.framework.util
                   "000108A000000062020801": "2.2.2", "010108A000000062020801": "3.0.5",
                   "000109A00000006202080101": "2.2.2",  # javacardx.framework.util.intx
                   "000108A000000062020802": "2.2.2",  # javacardx.framework.math
                   "000108A000000062020803": "2.2.2",  # javacardx.framework.tlv
                   "000108A000000062020804": "3.0.4",  # javacardx.framework.string
                   "000107A0000000620209": "2.2.2",  # javacardx.apdu
                   "000108A000000062020901": "3.0.5",  # javacardx.apdu.util
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
        return "{0} v{1}.{2} {3}".format(self.get_aid_hex(), self.major, self.minor, self.get_well_known_name())

    def get_length(self):
        return len(self.aid) + 1 + 1 + 1

    def serialize(self):
        aid_str = ''.join('{:02X}'.format(a) for a in self.aid)
        serialized = '{:02X}{:02X}{:02X}{}'.format(self.minor, self.major, len(self.aid), aid_str)
        return serialized

    def get_aid_hex(self):
        return bytes(self.aid).hex()  # will be in lowercase

    def get_well_known_name(self):
        hex_aid = bytes(self.aid).hex() # will be in lowercase

        if hex_aid == "A0000000620001".lower():
            return "java.lang"
        if hex_aid == "A0000000620002".lower():
            return "java.io"
        if hex_aid == "A0000000620003".lower():
            return "java.rmi"

        if hex_aid == "A0000000620101".lower():
            return "javacard.framework"
        if hex_aid == "A0000000620102".lower():
            return "javacard.security"
        if hex_aid == "A000000062010101".lower():
            return "javacard.framework.service"

        if hex_aid == "A0000000620201".lower():
            return "javacardx.crypto"
        if hex_aid == "A0000000620202".lower():
            return "javacardx.biometry"
        if hex_aid == "A0000000620203".lower():
            return "javacardx.external"
        if hex_aid == "A0000000620209".lower():
            return "javacardx.apdu"

        if hex_aid == "A000000062020801".lower():
            return "javacardx.framework.util"
        if hex_aid == "A00000006202080101".lower():
            return "javacardx.framework.util.intx"
        if hex_aid == "A000000062020802".lower():
            return "javacardx.framework.math"
        if hex_aid == "A000000062020803".lower():
            return "javacardx.framework.tlv"

        if hex_aid == "A00000015100".lower():
            return "org.globalplatform"

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
    min4 = 0x62
    max4 = 0x62
    min5 = 0
    max5 = 2
    min6 = 0
    max6 = 2
    package_template = ""
    package_template_bytes = []

    def __init__(self, min_major, max_major, min_minor, max_minor, min4, max4, min5, max5,
                 min6, max6, package_template):
        self.min_major = min_major
        self.max_major = max_major
        self.min_minor = min_minor
        self.max_minor = max_minor
        self.min4 = min4
        self.max4 = max4
        self.min5 = min5
        self.max5 = max5
        self.min6 = min6
        self.max6 = max6
        self.package_template = package_template
        self.package_template_bytes = bytearray(bytes.fromhex(package_template))

    def __init__(self, min_major, max_major, min_minor, max_minor, package_template):
        self.min_major = min_major
        self.max_major = max_major
        self.min_minor = min_minor
        self.max_minor = max_minor
        self.min4 = -1
        self.max4 = -1
        self.min5 = -1
        self.max5 = -1
        self.min6 = -1
        self.max6 = -1
        self.package_template = package_template
        self.package_template_bytes = bytearray(bytes.fromhex(package_template))

    def __repr__(self):
        return 'MAJOR=[{0}-{1}], MINOR=[{2}-{3}], 4TH=[{4}-{5}], 5TH=[{6}-{7}], 6TH=[{8}-{9}], TEMPLATE={10}'.format(
            self.min_major, self.max_major, self.min_minor, self.max_minor, self.min4, self.max4, self.min5, self.max5,
            self.min6, self.max6, self.package_template)

    @staticmethod
    def get_range(min_val, max_val, template_val):
        if min_val == -1:
            start = template_val
        else:
            start = min_val
        if max_val == -1:
            stop = template_val
        else:
            stop = max_val

        return start, stop

    def get_val4_range(self):
        return self.get_range(self.min4, self.max4, self.package_template_bytes[4])

    def get_val5_range(self):
        return self.get_range(self.min5, self.max5, self.package_template_bytes[5])

    def get_val6_range(self):
        return self.get_range(self.min6, self.max6, self.package_template_bytes[6])


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


javacard_framework = PackageAID(b'\xA0\x00\x00\x00\x62\x01\x01', 1, 3)
java_lang = PackageAID(b'\xA0\x00\x00\x00\x62\x00\x01', 1, 0)

package_template = b'\xA0\x00\x00\x00\x62\x01\x01'


def check(import_section, package, uninstall):
    print(import_section)
    f = open('{0}\\template\\test\\javacard\\Import.cap'.format(BASE_PATH), 'wb')
    f.write(bytes.fromhex(import_section))
    f.close()

    # create new
    shutil.make_archive('test.cap', 'zip', '{0}\\template\\'.format(BASE_PATH))

    package_hex = package.serialize()

    # remove zip appendix
    os.remove('test.cap')
    os.rename('test.cap.zip', 'test.cap')
    copyfile('test.cap', '{0}\\results\\test_{1}.cap'.format(BASE_PATH, package_hex))

    uninstall = True
    if uninstall:
        subprocess.run(['gp.exe', '--uninstall', 'test.cap'], stdout=subprocess.PIPE)

    # try to install
    result = subprocess.run(['gp.exe', '--install', 'test.cap', '--d'], stdout=subprocess.PIPE)

    result = result.stdout.decode("utf-8")
    # print(result)
    f = open('{0}\\results\\{1}.txt'.format(BASE_PATH, package_hex), 'w')
    f.write(result)
    f.close()

    if result.find('9000\r\nSCardEndTransaction()') != -1:
        return True
    else:
        return False


def format_import(packages_list):
    total_len = 0
    for package in packages_list:
        total_len += package.get_length()
    total_len += 1 # include count of number of packages
    import_section = '0400{:02x}{:02x}'.format(total_len, len(packages_list))
    for package in packages_list:
        import_section += package.serialize()

    return import_section


def test():
    javacard_framework = PackageAID(b'\xA0\x00\x00\x00\x62\x01\x01', 1, 3)
    javacard_security = PackageAID(b'\xA0\x00\x00\x00\x62\x01\x02', 1, 3)
    javacardx_crypto = PackageAID(b'\xA0\x00\x00\x00\x62\x02\x01', 1, 3)
    java_lang = PackageAID(b'\xA0\x00\x00\x00\x62\x00\x01', 1, 0)
    imported_packages = []

    imported_packages.append(java_lang)
    imported_packages.append(javacard_security)
    imported_packages.append(javacard_framework)
    imported_packages.append(javacardx_crypto)

    import_content = format_import(imported_packages)
    check(import_content, javacardx_crypto, True)

    supported = []
    run_scan(TestCfg(1, 1, 0, 0, "A0000000620001"), supported)
    save_scan(card_info, supported)




def test_aid(tested_package_aid, is_installed, supported_list):
    imported_packages = []
    imported_packages.append(javacard_framework)
    imported_packages.append(java_lang)
    imported_packages.append(tested_package_aid)

    import_content = format_import(imported_packages)

    if check(import_content, tested_package_aid, is_installed):
        print(" ###########\n  {0} IS SUPPORTED\n ###########\n".format(tested_package_aid.get_readable_string()))
        supported_list.append(tested_package_aid)
        is_installed = True
    else:
        print("   {0} v{1}.{2} is NOT supported ".format(tested_package_aid.get_aid_hex(), tested_package_aid.major,
                                                         tested_package_aid.minor))
        is_installed = False

    return is_installed


def print_supported(supported):
    print(" #################\n")
    if len(supported) > 0:
        for supported_aid in supported:
            print("{0} (since JC API {1})\n".format(supported_aid.get_readable_string(),
                                                    supported_aid.get_first_jcapi_version()))
    else:
        print("No items")
    print(" #################\n")


def run_scan(cfg, supported):
    print("################# BEGIN ###########################\n")
    print(cfg)
    print("###################################################\n")

    localtime = time.asctime(time.localtime(time.time()))
    print(localtime)

    template = bytearray(bytes.fromhex(cfg.package_template))
    is_installed = True
    # now check all possible values
    for major in range(cfg.min_major, cfg.max_major + 1):
        print("############################################\n")
        print("MAJOR = {0}".format(major))
        print_supported(supported)
        for minor in range(cfg.min_minor, cfg.max_minor + 1):
            print_supported(supported)
            print("############################################\n")
            print("MAJOR = {0}, MINOR = {1}".format(major, minor))
            # compute start and end of required range
            [start4, stop4] = cfg.get_val4_range()
            for val_4 in range(start4, stop4 + 1):
                print_supported(supported)
                print("############################################\n")
                print("MAJOR = {0}, MINOR = {1}, VAL4 = {2}".format(major, minor, val_4))
                # compute start and end of required range
                [start5, stop5] = cfg.get_val5_range()
                for val_5 in range(start5, stop5 + 1):
                    # compute start and end of required range
                    [start6, stop6] = cfg.get_val6_range()
                    for val_6 in range(start6, stop6 + 1):
                        new_package_aid = bytearray(bytes.fromhex(cfg.package_template))
                        new_package_aid[4] = val_4
                        new_package_aid[5] = val_5
                        new_package_aid[6] = val_6
                        new_package = PackageAID(new_package_aid, major, minor)

                        is_installed = test_aid(new_package, is_installed, supported)

    print_supported(supported)

    localtime = time.asctime(time.localtime(time.time()))
    print(localtime)

    print("################# END ###########################\n")
    print(cfg)
    print("#################################################\n")


def scan_JC_API_305(supported):
    MAX_MAJOR = 1
    #ADDITIONAL_MINOR = 1
    ADDITIONAL_MINOR = 1
    # maximal version (minor/major is always 1 higher than expected from given version of JC SDK)
    # If highest version is detected, additional inspection is necessary

    run_scan(TestCfg(1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR, "A0000000620001"), supported)
    run_scan(TestCfg(1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR, "A0000000620002"), supported)
    run_scan(TestCfg(1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR, "A0000000620003"), supported)

    run_scan(TestCfg(1, MAX_MAJOR, 0, 6 + ADDITIONAL_MINOR, "A0000000620101"), supported)
    run_scan(TestCfg(1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR, "A000000062010101"), supported)
    run_scan(TestCfg(1, MAX_MAJOR, 0, 6 + ADDITIONAL_MINOR, "A0000000620102"), supported)

    run_scan(TestCfg(1, MAX_MAJOR, 0, 6 + ADDITIONAL_MINOR, "A0000000620201"), supported)
    run_scan(TestCfg(1, MAX_MAJOR, 0, 3 + ADDITIONAL_MINOR, "A0000000620202"), supported)
    run_scan(TestCfg(1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR, "A0000000620203"), supported)
    run_scan(TestCfg(1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR, "A0000000620204"), supported)
    run_scan(TestCfg(1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR, "A0000000620205"), supported)

    run_scan(TestCfg(1, MAX_MAJOR, 0, 1 + ADDITIONAL_MINOR, "A000000062020801"), supported)
    run_scan(TestCfg(1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR, "A00000006202080101"), supported)
    run_scan(TestCfg(1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR, "A000000062020802"), supported)
    run_scan(TestCfg(1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR, "A000000062020803"), supported)
    run_scan(TestCfg(1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR, "A000000062020804"), supported)

    run_scan(TestCfg(1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR, "A0000000620209"), supported)
    run_scan(TestCfg(1, MAX_MAJOR, 0, 0 + ADDITIONAL_MINOR, "A000000062020901"), supported)

    print_supported(supported)


def get_card_info(card_name):
    if card_name == "":
        card_name = input("Please enter card name: ")

    result = subprocess.run(['gp.exe', '--i'], stdout=subprocess.PIPE)
    result_text = result.stdout.decode("utf-8")

    atr_before = "http://smartcard-atr.appspot.com/parse?ATR="
    pos = result_text.find(atr_before)
    end_pos = result_text.find("\n", pos)
    atr = result_text[pos + len(atr_before):end_pos]
    atr = atr.rstrip()

    cplc_before = "Card CPLC:"
    pos = result_text.find(cplc_before)
    cplc = result_text[pos + len(cplc_before):]
    cplc = cplc.rstrip()
    cplc = cplc.replace(":", ";")

    return CardInfo(card_name, atr, cplc, result_text)


def save_scan(card_info, supported):
    file_name = "{0}_AIDSUPPORT_{1}.csv".format(card_info.card_name, card_info.atr)
    f = open('{0}\\{1}'.format(BASE_PATH, file_name), 'w')

    f.write("jcAIDScan version; {0}\n".format(SCRIPT_VERSION))
    f.write("Card ATR; {0}\n".format(card_info.atr))
    f.write("Card name; {0}\n".format(card_info.card_name))
    f.write("CPLC;;\n{0}\n\n".format(card_info.cplc))

    f.write("PACKAGE AID; MAJOR VERSION; MINOR VERSION; PACKAGE NAME; INTRODUCING JC API VERSION;\n")
    for aid in supported:
        f.write("{0}; {1}; {2}; {3}; {4}\n".format(aid.get_aid_hex(), aid.major, aid.minor, aid.get_well_known_name(),
                                               aid.get_first_jcapi_version()))

    f.close()

def scan_subpackages(supported):
    # scan user-defined package
    supported = []
    #test1 = TestCfg(1, 1, 0, 1, 0x62, 0x62, 0, 1, 0, 1, PACKAGE_TEMPLATE)
    test1 = TestCfg(1, 2, 0, 10, 0x62, 0x62, 0, 10, 0, 20, PACKAGE_TEMPLATE)
    run_scan(test1, supported)
    print_supported(supported)

    # now check supported packages with appended 1 byte
    is_installed = True
    supported_01 = []

    new_package_aid = []
    for supported_aid in supported:
        for val in range(0, 10):
            new_package_aid[:] = supported_aid.aid
            new_package_aid.append(val)
            new_package = PackageAID(new_package_aid, supported_aid.major, supported_aid.minor)
            is_installed = test_aid(new_package, is_installed, supported_01)

    # print all results
    print_supported(supported)
    print_supported(supported_01)


def prepare_for_testing():
    # restore default import section
    imported_packages = []
    imported_packages.append(javacard_framework)
    imported_packages.append(java_lang)
    import_section = format_import(imported_packages)
    f = open('{0}\\template\\test\\javacard\\Import.cap'.format(BASE_PATH), 'wb')
    f.write(bytes.fromhex(import_section))
    f.close()


# if aid supported, try also aid + 01 and aid + 01 01
def main():
    # uninstall any previous installation
    subprocess.run(['gp.exe', '--uninstall', 'test.cap'], stdout=subprocess.PIPE)
    is_installed = False

    # restore template to good known state
    prepare_for_testing()

    # obtain card basic info
    card_info = get_card_info("")
    # scan standard JC API
    supported = []
    scan_JC_API_305(supported)
    # create file with results
    save_scan(card_info, supported)

    return

if __name__ == "__main__":
    #test()
    main()