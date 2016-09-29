# seafile-kindle-client
Simple client for synchronization between Kindle and Seafile server. Currently looks more like a PoC and works only in one way (i.e. download only). 

### Installation

- Your kindle must be jailbroken
- Install python for kindle http://www.mobileread.com/forums/showthread.php?t=225030
- Copy the contents of KUAL/seafile directory into /mnt/us/extensions/seafile
- Create directory directory for local files (see config file -> /mnt/us/documents/Seafile)
- Copy seafile.cfg.example to seafile.cfg, set there proper server address, library name, your login and password (as well as path to local directory):
```
[server]
url = https://seafile.example.com
library = MyBooks
user = user@mail.server
password = Password

[kindle]
local = /mnt/us/documents/Seafile
```
- KUAL -> Seafile Sync -> Synchronize files

At the first run script will obtain an authentication token at Seafile server and remove your login and password entries from configuration file (for security reasons).

### Known Issues/Bugs
- Status message position is hardcoded, assuming you've got PW3/KPV (magic number 57)
- Non-latin characters are not shown through eips
- No any checks of internet/WiFi availability
- SSL certificates are ignored (verify=False) just to make it work with self-signed SSL certs

### To Do
- Daemon mode
- Various errors handlers: check WiFi state, server hostname
- Two-way synchronization
- Import self-signed ca or add config option for verify='path/to/self/signed/ca.crt'
