import shutil
import os
import subprocess
from shutil import copyfile
import time

# TODO: insert additional ID instead of direct modification
# TODO: save complete log to separate named file
# Format Import.cap: 04 00 len num_packages package1 package2 ... packageN
# packageFormat: package_major package_minor package_len AID

# 04001f 03 030107A0000000620101 000107A0000000620001 000107A0000000620001

# modify Imports file
#import_template = b'\x04\x00\x15\x02\x03\x01\x07\xA0\x00\x00\x00\x62\x01\x01\x00\x01\x07\xA0\x00\x00\x00\x62\x00\x01' valid standard
import_template_len = 0x15
import_template_num_packages = 2

base_path = 'h:\\Documents\\Develop\\jcAIDScan'

import_template = b'\x04\x00\x1F\x03\x00\x01\x07\xA0\x00\x00\x00\x62\x00\x01\x03\x01\x07\xA0\x00\x00\x00\x62\x01\x01\x00\x01\x07\xA0\x00\x00\x00\x62\x00\x01'

PACKAGE_TEMPLATE = "A0000000620102"

MAX_MAJOR = 3
MAX_MINOR = 5

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


javacard_framework = PackageAID(b'\xA0\x00\x00\x00\x62\x01\x01', 1, 3)
java_lang = PackageAID(b'\xA0\x00\x00\x00\x62\x00\x01', 1, 0)

package_template = b'\xA0\x00\x00\x00\x62\x01\x01'

def check(import_section, package, uninstall):
    print(import_section)
    f = open('{0}\\template\\test\\javacard\\Import.cap'.format(base_path), 'wb')
    f.write(bytes.fromhex(import_section))
    f.close()

    # create new
    shutil.make_archive('test.cap', 'zip', '{0}\\template\\'.format(base_path))

    package_hex = package.serialize()

    # remove zip appendix
    os.remove('test.cap')
    os.rename('test.cap.zip', 'test.cap')
    copyfile('test.cap', '{0}\\results\\test_{1}.cap'.format(base_path, package_hex))

    uninstall = True
    if uninstall:
        subprocess.run(['gp.exe', '--uninstall', 'test.cap'], stdout=subprocess.PIPE)

    # try to install
    result = subprocess.run(['gp.exe', '--install', 'test.cap', '--d'], stdout=subprocess.PIPE)

    result = result.stdout.decode("utf-8")
    # print(result)
    f = open('{0}\\results\\{1}.txt'.format(base_path, package_hex), 'w')
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
            print("{0})\n".format(supported_aid.get_readable_string()))
    else:
        print("No items")
    print(" #################\n")


# if aid supported, try also aid + 01 and aid + 01
def main():
    # uninstall any previous installation
    subprocess.run(['gp.exe', '--uninstall', 'test.cap'], stdout=subprocess.PIPE)
    is_installed = False

    localtime = time.asctime(time.localtime(time.time()))
    print(localtime)

    supported = []
    # now check all possible values
    for major in range(1,MAX_MAJOR + 1):
        print("############################################\n")
        print("MAJOR = {0}".format(major))
        print_supported(supported)
        for minor in range(0,MAX_MINOR + 1):
            print_supported(supported)
            print("############################################\n")
            print("MAJOR = {0}, MINOR = {1}".format(major, minor))
            for val_5 in range(0, 10):
                for val_6 in range(0, 20):
                    new_package_aid = bytearray(package_template)
                    new_package_aid[5] = val_5
                    new_package_aid[6] = val_6
                    new_package = PackageAID(new_package_aid, major, minor)

                    is_installed = test_aid(new_package, is_installed, supported)

    print_supported(supported)

    # now check supported packages with appended 1 byte
    is_installed = True
    supported_01 = []
    for supported_aid in supported:
        for val in range(0, 10):
            new_package_aid[:] = supported_aid.aid
            new_package_aid.append(val)
            new_package = PackageAID(new_package_aid, supported_aid.major, supported_aid.minor);
            is_installed = test_aid(new_package, is_installed, supported_01)

    print_supported(supported)
    print_supported(supported_01)

if __name__ == "__main__":
    #test()
    main()