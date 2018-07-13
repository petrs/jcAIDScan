import shutil
import os
import subprocess
from shutil import copyfile

# TODO: insert additional ID instead of direct modification
# TODO: save complete log to separate named file
# Format Import.cap: 04 00 len num_packages package1 package2 ... packageN
# packageFormat: package_major package_minor package_len AID


# modify Imports file
#import_template = b'\x04\x00\x15\x02\x03\x01\x07\xA0\x00\x00\x00\x62\x01\x01\x00\x01\x07\xA0\x00\x00\x00\x62\x00\x01' valid standard
import_template_len = 0x15
import_template_num_packages = 2

base_path = 'h:\\Documents\\Develop\\jcAIDScan'

import_template = b'\x04\x00\x1F\x03\x00\x01\x07\xA0\x00\x00\x00\x62\x00\x01\x03\x01\x07\xA0\x00\x00\x00\x62\x01\x01\x00\x01\x07\xA0\x00\x00\x00\x62\x00\x01'

PACKAGE_TEMPLATE = "A0000000620001"


class PackageAID:
    aid = []
    major = 0
    minor = 0

    def __init__(self, aid, major, minor):
        self.aid = aid
        self.major = major
        self.minor = minor

    def get_length(self):
        return len(self.aid) + 1 + 1 + 1

    def serialize(self):
        aid_str = ''.join('{:02X}'.format(a) for a in self.aid)
        serialized = '{:02X}{:02X}{:02X}{}'.format(self.minor, self.major, len(self.aid), aid_str)
        #return b'{0}{1}{2}{3}'.format(minor, major, len(aid), aid)
        return serialized

javacard_framework = PackageAID(b'\x07\xA0\x00\x00\x00\x62\x01\x01', 1, 3)
java_lang = PackageAID(b'\x07\xA0\x00\x00\x00\x62\x00\x01', 1, 0)

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

    import_section = '0400{:02x}{:02x}'.format(total_len, len(packages_list))
    for package in packages_list:
        import_section += package.serialize()

    return import_section


def main():
    # uninstall any previous installation
    subprocess.run(['gp.exe', '--uninstall', 'test.cap'], stdout=subprocess.PIPE)
    is_installed = False

    supported = []
    # now check all possible values
    for val in range(0, 256):
        new_package_aid = bytearray(package_template)
        new_package_aid[6] = val
        new_package = PackageAID(new_package_aid, 1, 0);

        imported_packages = []
        imported_packages.append(javacard_framework)
        imported_packages.append(java_lang)
        imported_packages.append(new_package)

        import_content = format_import(imported_packages)

        if check(import_content, new_package, is_installed):
            print(" ###########\n  supported {0}\n ###########\n", val)
            supported.append(bytes(new_aid).hex())
            is_installed = True
        else:
            print("   NOT supported" + val)
            is_installed = False

    print(supported)

if __name__ == "__main__":
    main()