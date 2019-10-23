# jcAIDScan
[![MIT licensed](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/petrs/jcAIDScan/blob/master/LICENSE)

An automated scanner for JavaCard packages installed and supported by target card. Evaluates all packages from JavaCard API specification up to JC API 3.0.5. 

Works by attempting to install small applet referencing particular package and its version (e.g., is javacard.security v1.6 available on card?). If the installation fails, the package is not supported. Uses [GlobalPlatformPro](https://github.com/martinpaljak/GlobalPlatformPro) by Martin Paljak for applet installation.


## Usage

WARNING: Multiple incorrect authentication attempts to smartcard may brick your card. Make sure you known what you are doing. 

1. Make sure GlobalPlatformPro tool is able to list installed applets and upload new ones for the target card. Verify correct functionality for 'gp.exe -list', 'gp.exe -install test_211.cap' (example for Windows). Some cards (e.g., G&D 3.2, 4.x, 6.0 requires additional '-emv' flag). The current implementation detects operating system, so there is no need to changing commands calling gp in code.
2. If your card requires additional authentication parameters for GPPro, edit jcAIDScan.py and change GP_AUTH_FLAG variable to desired one  In most cases, preset "GP_AUTH_FLAG = ''" is fine. Change to "GP_AUTH_FLAG = '--emv'" for G&D 3.2, 4.x, 6.0 cards.
3. Run jcAIDScan.py and follow the instructions (the tool will first try to authenticate and list installed applets. Do NOT continue if this command fails!)
4. Investigate the resulting output (also stored in your_card_name_AIDSUPPORT_atr.csv file)
5. The results for (some) cards from [JCAlgTest](http://jcalgtest.org) database are already available [here](https://www.fi.muni.cz/~xsvenda/jcalgtest/table.html#package_support). Please consider to send the results for your card as well (petr@svenda.com)

## Example output for Athena IDprotect card

```csv
PACKAGE AID; MAJOR VERSION; MINOR VERSION; PACKAGE NAME; INTRODUCING JC API VERSION;
a0000000620001; 1; 0; java.lang; 2.1
a0000000620002; 1; 0; java.io; 2.2.0
a0000000620003; 1; 0; java.rmi; 2.2.0
a0000000620101; 1; 0; javacard.framework; 2.1
a0000000620101; 1; 1; javacard.framework; 2.2.0
a0000000620101; 1; 2; javacard.framework; 2.2.1
a0000000620101; 1; 3; javacard.framework; 2.2.2
a000000062010101; 1; 0; javacard.framework.service; 2.2.0
a0000000620102; 1; 0; javacard.security; 2.1
a0000000620102; 1; 1; javacard.security; 2.1.1
a0000000620102; 1; 2; javacard.security; 2.2.1
a0000000620102; 1; 3; javacard.security; 2.2.2
a0000000620201; 1; 0; javacardx.crypto; 2.1
a0000000620201; 1; 1; javacardx.crypto; 2.1.1
a0000000620201; 1; 2; javacardx.crypto; 2.2.1
a0000000620201; 1; 3; javacardx.crypto; 2.2.2
a0000000620209; 1; 0; javacardx.apdu; 2.2.2

FULL PACKAGE AID; IS SUPPORTED?; PACKAGE NAME WITH VERSION; 
000107A0000000620001; 	yes; 	java.lang v1.0 a0000000620001;
010107A0000000620001; 	no; 	java.lang v1.1 a0000000620001;
000107A0000000620002; 	yes; 	java.io v1.0 a0000000620002;
010107A0000000620002; 	no; 	java.io v1.1 a0000000620002;
000107A0000000620003; 	yes; 	java.rmi v1.0 a0000000620003;
010107A0000000620003; 	no; 	java.rmi v1.1 a0000000620003;
000107A0000000620101; 	yes; 	javacard.framework v1.0 a0000000620101;
010107A0000000620101; 	yes; 	javacard.framework v1.1 a0000000620101;
020107A0000000620101; 	yes; 	javacard.framework v1.2 a0000000620101;
030107A0000000620101; 	yes; 	javacard.framework v1.3 a0000000620101;
040107A0000000620101; 	no; 	javacard.framework v1.4 a0000000620101;
050107A0000000620101; 	no; 	javacard.framework v1.5 a0000000620101;
060107A0000000620101; 	no; 	javacard.framework v1.6 a0000000620101;
070107A0000000620101; 	no; 	javacard.framework v1.7 a0000000620101;
000108A000000062010101; 	yes; 	javacard.framework.service v1.0 a000000062010101;
010108A000000062010101; 	no; 	javacard.framework.service v1.1 a000000062010101;
000107A0000000620102; 	yes; 	javacard.security v1.0 a0000000620102;
010107A0000000620102; 	yes; 	javacard.security v1.1 a0000000620102;
020107A0000000620102; 	yes; 	javacard.security v1.2 a0000000620102;
030107A0000000620102; 	yes; 	javacard.security v1.3 a0000000620102;
040107A0000000620102; 	no; 	javacard.security v1.4 a0000000620102;
050107A0000000620102; 	no; 	javacard.security v1.5 a0000000620102;
060107A0000000620102; 	no; 	javacard.security v1.6 a0000000620102;
070107A0000000620102; 	no; 	javacard.security v1.7 a0000000620102;
000107A0000000620201; 	yes; 	javacardx.crypto v1.0 a0000000620201;
010107A0000000620201; 	yes; 	javacardx.crypto v1.1 a0000000620201;
020107A0000000620201; 	yes; 	javacardx.crypto v1.2 a0000000620201;
030107A0000000620201; 	yes; 	javacardx.crypto v1.3 a0000000620201;
040107A0000000620201; 	no; 	javacardx.crypto v1.4 a0000000620201;
050107A0000000620201; 	no; 	javacardx.crypto v1.5 a0000000620201;
060107A0000000620201; 	no; 	javacardx.crypto v1.6 a0000000620201;
070107A0000000620201; 	no; 	javacardx.crypto v1.7 a0000000620201;
000107A0000000620202; 	no; 	javacardx.biometry v1.0 a0000000620202;
010107A0000000620202; 	no; 	javacardx.biometry v1.1 a0000000620202;
020107A0000000620202; 	no; 	javacardx.biometry v1.2 a0000000620202;
030107A0000000620202; 	no; 	javacardx.biometry v1.3 a0000000620202;
040107A0000000620202; 	no; 	javacardx.biometry v1.4 a0000000620202;
000107A0000000620203; 	no; 	javacardx.external v1.0 a0000000620203;
010107A0000000620203; 	no; 	javacardx.external v1.1 a0000000620203;
000107A0000000620204; 	no; 	javacardx.biometry1toN v1.0 a0000000620204;
010107A0000000620204; 	no; 	javacardx.biometry1toN v1.1 a0000000620204;
000107A0000000620205; 	no; 	javacardx.security v1.0 a0000000620205;
010107A0000000620205; 	no; 	javacardx.security v1.1 a0000000620205;
000108A000000062020801; 	no; 	javacardx.framework.util v1.0 a000000062020801;
010108A000000062020801; 	no; 	javacardx.framework.util v1.1 a000000062020801;
020108A000000062020801; 	no; 	javacardx.framework.util v1.2 a000000062020801;
000109A00000006202080101; 	no; 	javacardx.framework.util.intx v1.0 a00000006202080101;
010109A00000006202080101; 	no; 	javacardx.framework.util.intx v1.1 a00000006202080101;
000108A000000062020802; 	no; 	javacardx.framework.math v1.0 a000000062020802;
010108A000000062020802; 	no; 	javacardx.framework.math v1.1 a000000062020802;
000108A000000062020803; 	no; 	javacardx.framework.tlv v1.0 a000000062020803;
010108A000000062020803; 	no; 	javacardx.framework.tlv v1.1 a000000062020803;
000108A000000062020804; 	no; 	javacardx.framework.string v1.0 a000000062020804;
010108A000000062020804; 	no; 	javacardx.framework.string v1.1 a000000062020804;
000107A0000000620209; 	yes; 	javacardx.apdu v1.0 a0000000620209;
010107A0000000620209; 	no; 	javacardx.apdu v1.1 a0000000620209;
000108A000000062020901; 	no; 	javacardx.apdu.util v1.0 a000000062020901;
010108A000000062020901; 	no; 	javacardx.apdu.util v1.1 a000000062020901;
```

## Results for various cards 
Visit [JCAlgTest](http://jcalgtest.org) for results from almost 30 cards.

## How to extend scanner with additional packages

Extend AID_NAME_MAP map with entry for target package AID and package name. E.g., javacard.framework from JC API 3.0.1 has package AID equal to A0000000620101 and with version 1.4. This information can be found in api_export_files\javacard\framework\javacard\framework.exp. Open the *.exp file in hex editor, find the last occurence of javacard/framework string, skip next four bytes and then you can see 04 01 07 A0000000620101 which are interpreted as 04 = minor version, 01 = major version, 07 = length of package AID and A0000000620101 is package AID itself. 
