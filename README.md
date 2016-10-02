# seafile-kindle-client
Simple client for synchronization between Kindle and Seafile server. Currently looks more like a PoC and works only in one way (i.e. download only). 

### Installation

- Your kindle must be jailbroken
- Install python for kindle http://www.mobileread.com/forums/showthread.php?t=225030
- Copy the contents of KUAL/seafile directory into /mnt/us/extensions/seafile
- Copy seafile.cfg.example to seafile.cfg, set there proper server address, library name, your login and password (as well as path to local directory):
```
[server]
url = https://seafile.example.com
library = MyBooks
user = user@mail.server
password = Password
; SSL certificate verify options: True, False or path to self-signed crt file
cert = False

[kindle]
local = /mnt/us/documents/Seafile
; screen dimensions in chars: 68x60 for PW3/KV, 48x42 for PW2
width  = 68
height = 60
```
- KUAL -> Seafile Sync -> Synchronize files

At the first run script will obtain an authentication token at Seafile server and remove your login and password entries from configuration file (for security reasons).

### Known Issues/Bugs
- Only one way synchronization
- Just rudimentary checks of internet/WiFi availability/file operations

### To Do
- Daemon mode
- Various errors handlers: add more checks of WiFi state, server hostname
- Two-way synchronization
