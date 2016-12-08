# seafile-kindle-client
Simple client for synchronization between Kindle and Seafile server. Upload works only for particular direectory. 

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
upload = /MyKindle_1
```
Run it via KUAL menu:
- KUAL -> Seafile Sync -> Synchronize
or
- KUAL -> Seafile Sync -> Push to server

At the first run script will obtain an authentication token at Seafile server and remove your login and password entries from configuration file (for security reasons).

### Known Issues/Bugs/Limitations
- Synchronization (download) works pretty well for 100-200 files in 3 sub-dir levels with overall size 1 Gb. For testing a bigger volumes I'll have to re-solder Kindle storage chip and hack firmware.
- One'n'half-way synchronization (only newly created local files are uploaded to server). As ID of file is generated on the server, there is no reliable way to determine if file is changed locally by it's ID. File timestamp doesn't look good too as kindle clock might reset after cold restart. 
- There is an option for uploading of the particular directory contents (useful e.g. for notes synchronization). As all files in that directory have to be uploaded to the server you should be careful: it could take much time.
- Directory for uploads must exist on the server. You have to create it there (e.g. via web interface or with desktop seafile client) and perform synchronization (download) at least once before upload.
- Upload directory must be a sub-folder in directory tree, e.g. /mnt/us/documents/Seafile/MyKindle_1. In config it should be defined as relative path to the base directory  
- File ID is a hash of file therefore all exact copies of particular file will have the same ID (though different names). Because the client idea is based on ID comparison, then if you make a copy of existing file at the server, client will download only the first file.
- Just rudimentary checks of internet/WiFi availability/file operations
- Hidden files/folders are not synchronized as well as bookmarks/statistics (*.sdr). It's because client has keeping actual state in hidden files ".hash", also some FUSE FS garbage often present as .fuse_hiddenXXXXXX.


### To Do
- Daemon mode
- Various errors handlers: add more checks of WiFi state, server hostname
- Two-way synchronization.
- Option for *.sdr directories synchronization (who need it?)