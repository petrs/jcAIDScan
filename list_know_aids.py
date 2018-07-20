import subprocess
import csv
import re

GP_BASIC_COMMAND = 'gp.exe'  # command which will start GlobalPlatformPro binary
GP_AUTH_FLAG = ''  # most of the card requires no additional authentication flag
# GP_AUTH_FLAG = '--emv'  # use of EMV key diversification is used (e.g., G&D cards)


def best_match(aid, aid_list):
    for aid_ctx in aid_list:
        if len(aid_ctx) > 0:
            if aid == aid_ctx[0]:
                return "{0}, {1}, Vendor: {2}/{3}".format(aid_ctx[3], aid_ctx[4], aid_ctx[1], aid_ctx[2])

    return "unknown AID"


def gp_list():
    # load list of well-known aids
    # taken from https://www.eftlab.co.uk/index.php/site-map/knowledge-base/211-emv-aid-rid-pix
    with open('well_known_aids.csv', 'r') as f:
        reader = csv.reader(f)
        aid_list = list(reader)

    # strip leading/trailing zeroes
    for aid_ctx in aid_list:
        if len(aid_ctx) > 4:
            aid_ctx[0] = aid_ctx[0].strip()
            aid_ctx[1] = aid_ctx[1].strip()
            aid_ctx[2] = aid_ctx[2].strip()
            aid_ctx[3] = aid_ctx[3].strip()
            aid_ctx[4] = aid_ctx[4].strip()

    # run gp and get list of applets
    result = subprocess.run([GP_BASIC_COMMAND, GP_AUTH_FLAG, '--list'], stdout=subprocess.PIPE)
    result_text = result.stdout.decode("utf-8")
    gp_lines = result_text.splitlines()

    # print gp result in augmented mode 'AID info:'
    for line in gp_lines:
        match = re.match(r'AID: (?P<aid>.*?) \(', line, re.I)
        if match:
            # AID in output detected
            print(line)
            # annotate (if known)
            print("AID info: {0}".format(best_match(match.group("aid"), aid_list)))
        else:
            # other lines from gp - just print
            print(line)


def main():
    gp_list()


if __name__ == "__main__":
    main()

