from jcAIDScan import AIDScanner
from jcAIDScan import TestCfg

if __name__ == "__main__":
    # scan particular range of packages
    app = AIDScanner()
    app.force_no_safety_check = True
    app.force_uninstall = False
    app.card_name = "test"
    supported = []
    tested = {}
    cfg = TestCfg("A0000000000000", 1, 1, 0, 0, 0, 0xff, 0x00, 0x02, 0x00, 0x02)
    app.run_scan(cfg, supported, tested)

