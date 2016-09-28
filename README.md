# seafile-kindle-client
Simple client for synchronization between Kindle and Seafile server. Currently looks more like a PoC and works only in one way (i.e. download only). 

### Installation
KUAL extension is to be written. Until that
- Your kindle must be jailbroken
- Install python for kindle http://www.mobileread.com/forums/showthread.php?t=225030
- Create directory /mnt/us/extensions/seafile/bin
- Copy seafile.cfg.example to seafile.cfg and change server address, library name and your login and password (as well as path to local directory):
```
[server]
url = https://seafile.example.com
library = MyBooks
user = user@mail.server
password = Password

[kindle]
local = /mnt/us/documents/Seafile
```
- Then copy it to /mnt/us/extensions/seafile
- Copy sfcli.py to /mnt/us/extensions/seafile/bin

At the first run script will obtain an authentication token at Seafile server and remove your login and password entries from configuration file (for security reasons).

### To Do
- KUAL support
- Daemon mode
- Various errors handles
- Two-way synchronization
