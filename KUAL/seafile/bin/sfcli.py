#! /mnt/us/python/bin/python2.7
# -*- coding:utf-8 -*-

import requests
from requests.packages.urllib3.exceptions import SubjectAltNameWarning

import ConfigParser
import os
import shutil
from subprocess import call

### Some global definitions
cfg_dir='/mnt/us/extensions/seafile'

def spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor

def spinner_up(s):
    call(['eips', '1', str(max_y-1),' '])
    call(['eips', '1', str(max_y-1), s ] )
    return;

def safe_str(obj):
    """ return the byte string representation of obj """
    try:
        return str(obj)
    except UnicodeEncodeError:
        # obj is unicode
        return unicode(obj).encode('unicode_escape')

def safe_unicode(str):
    try:
        return str.decode('utf-8')
    except UnicodeEncodeError:
        return str

def cprint(s, ypos):
    call(['eips', '3 ', str(ypos+max_y-3), safe_str(s)[:max_x-4] ] )
    return;

def cclear(xpos, ypos, len):
    call(['eips', str(xpos), str(ypos+max_y-3), ' ' * len])
    return;

def cout(xpos, ypos, c):
    call(['eips', str(xpos), str(ypos+max_y-3), ' '])
    call(['eips', str(xpos+1), str(ypos+max_y-3),  c ])
    return;

def sf_ping():
    try:
        r = requests.get(url + '/api2/ping/', verify=ca_verify, timeout=10)
        r.raise_for_status()
        return r.text;
    except requests.exceptions.Timeout:
        cprint('Timeout',2)
        return;
    except requests.exceptions.HTTPError as e:
        cprint('HTTP error:' + str(e), 2);
        return;
    except requests.exceptions.RequestException as e:
        cprint('Connection problem: ' + str(e), 2)
    return;

def sf_authping():
    hdr = { 'Authorization' : 'Token ' + token }
    r = requests.get(url + '/api2/auth/ping/', headers = hdr, verify=ca_verify)
    return r.text;

def sf_get_token():
    postdata = {'username' : user , 'password' : password}
    r = requests.post( url + '/api2/auth-token/', data=postdata, verify=ca_verify)
    jToken = r.json()
    token=jToken['token']
    return token;

def sf_get_lib_id():
    hdr = { 'Authorization' : 'Token ' + token  , 'Accept' : 'application/json; indent=4'}
    r = requests.get(url + '/api2/repos/', headers = hdr, verify=ca_verify)
    jList=r.json()
    for i in jList:
        if i['name'] == lib:
            return i['id'];
    return;

def sf_ls_lib(dir_entry='/'):
    hdr = { 'Authorization' : 'Token ' + token  , 'Accept' : 'application/json; indent=4'}
    r = requests.get( url + '/api2/repos/' + libid + '/dir/?p=' + dir_entry, headers = hdr, verify=ca_verify)
    return r.json();

# Returns 5 lists: 0 - with directories to erase, 1 - with filenames to erase, 2 - for files to download 3 - for hashes to update 4 - local files to upload
def sf_get_modified(dir_entry='/'):
    h_lcl={}
    h_srv={}
    h1=[]
    h2=[]
    fl=[]
    d=os.path.normpath(dir_local + dir_entry)
    try:
        os.makedirs(d)
    except OSError:
        if not os.path.isdir(d):
            raise

    with open(d + '/.hash','a+') as f:
        for row in f:
            hash = row.split(' ', 1 )
            name = hash[1].rstrip()
            h_lcl[hash[0]]=name
            h1.append(hash[0])
            fl.append(safe_unicode(name))
    f.close()
    subdirs_local = [safe_unicode(name) for name in os.listdir(d) if os.path.isdir(os.path.join(d, name)) and not name.endswith('.sdr')]
    files_real    = [safe_unicode(name) for name in os.listdir(d) if os.path.isfile(os.path.join(d, name))]

    jl=sf_ls_lib(dir_entry)
    subdirs_srv=[]
    for i in jl:
        if i['type'] == 'file':
            h_srv[i['id']]=i['name']
            h2.append(str(i['id']))
        elif i['type'] == 'dir':
            p=dir_entry+i['name']
            subdirs_srv.append(i['name'])
            dr,rm,dl,up,ul=sf_get_modified(p+'/')
            sf_ul(p,ul)
            sf_dr(p,dr)
            sf_rm(p,rm)
            sf_dl(p,dl)
            sf_up(p,up)

    f_lcl = set(h1)
    f_srv = set(h2)
    f_hash = set(fl)
    f_real = set(files_real)

    d_lcl = set(subdirs_local)
    d_srv = set(subdirs_srv)

    dir_to_erase= d_lcl - d_srv
    d_rm = list(dir_to_erase)

    to_erase    = f_lcl - f_srv
    to_download = f_srv - f_lcl
    to_upload   = f_real - f_hash
    f_ul = list(to_upload)

    f_rm=[]
    f_dl=[]
    for i in list(to_erase):
        if i in h_lcl.keys():
            f_rm.append(h_lcl[i])

    for i in list(to_download):
        if i in h_srv.keys():
            f_dl.append(h_srv[i])
    return d_rm, f_rm , f_dl, h_srv, f_ul;

def sf_dl(dir_entry, dl_list):
    cclear(0,2,40)
    for fname in dl_list:
        cprint ('Downloading:',2)
        hdr = { 'Authorization' : 'Token ' + token  , 'Accept' : 'application/json; indent=4'}
        uurl = url + '/api2/repos/' + libid + '/file/?p=' + dir_entry + '/' + fname
        r = requests.get(uurl, headers=hdr, verify=ca_verify)
        dl_url = r.content
        if dl_url.startswith('"') and dl_url.endswith('"'):
            dl_url = dl_url[1:-1]
        rdl = requests.get(dl_url, stream=True, verify=ca_verify)
        cclear(15,2,10)
        d = dir_local + dir_entry
        try:
            os.makedirs(d)
        except OSError:
            if not os.path.isdir(d):
                raise
        with open( d + '/' + fname, 'wb' ) as f:
            idx=0
            for chunk in rdl.iter_content(chunk_size=65536):
                if chunk: # filter out keep-alive new chunks
                    idx = idx+1
                    cout(15 + idx%20, 2,'>')
                    f.write(chunk)
        cclear(15,2,40)
        cout(15,2,'OK')
    return;

def sf_rm(dir_entry, rm_list):
    for fname in rm_list:
        cprint ('Removing:'+ fname, 2)
        try:
            os.remove(dir_local + dir_entry + '/' + fname.rstrip())
        except OSError:
            pass
    return;

## remove directories from list
def sf_dr(dir_entry, dir_list):
    for dirname in dir_list:
        cprint('Removing:' + dirname, 2)
        try:
            shutil.rmtree(os.path.normpath(dir_local + dir_entry + dirname)) 
        except OSError:
            pass
    return;

## Update hash table
def sf_up(dir_entry, up_list):
    cprint ('Updating hashes...', 2)
    with open(dir_local + dir_entry + '/.hash','w') as h:
        for i in up_list:
            s=i + ' ' +  up_list[i] + '\n'
            h.write(s.encode("UTF-8"))
    cout(20,2,'OK')
    return;

# Upload file
def sf_ul(dir_entry, file):
    cprint('[NOT implemented] Uploading: ',2)
    hdr = { 'Authorization' : 'Token ' + token  , 'Accept' : 'application/json; indent=4'}
    uurl = url + '/api2/repos/' + libid + '/upload-link/'
    #print 'Upload URL: ',uurl
    r = requests.get(uurl, headers=hdr, verify=ca_verify)
    upload_link = r.json()
    ## TODO: make a proper post request
    ##print j
    ##response = requests.post(
    ##    upload_link, data={'filename': 'git.jpg', 'parent_dir': '/'},
    ##    files={'file': open('/Users/xiez/Pictures/git.jpg', 'rb')},
    ##    headers={'Authorization': 'Token {token}'. format(token=token)}
    ##)
    cout(20,2,'OK')
    return;

### --- Main start
requests.packages.urllib3.disable_warnings(SubjectAltNameWarning)
config = ConfigParser.RawConfigParser()
cfg_file = cfg_dir + '/seafile.cfg'
config.read( cfg_file )

url       = config.get('server', 'url')
lib       = config.get('server', 'library')
user      = config.get('server', 'user')
password  = config.get('server', 'password')
cert      = config.get('server', 'cert')
dir_local = config.get('kindle', 'local')
max_x     = int(config.get('kindle', 'width'))
max_y     = int(config.get('kindle', 'height'))

if cert == 'False':
    ca_verify = False
elif cert == 'True':
    ca_verify = True
else:
    ca_verify = cert

cprint ('Connecting to server... ', 1 )
if sf_ping() == '':
    cprint('E Server not available', 1)
    quit()

try:
    token=config.get('server','token')
except ConfigParser.NoOptionError:
    token=sf_get_token()
    config.set('server','token',token)
    config.set('server','user','')
    config.set('server','password','')
    with open(cfg_file, 'wb') as configfile:
        config.write(configfile)

rc = sf_authping()
cprint ('Got ' + rc + ' from server', 1 )

libid=sf_get_lib_id()

dr,rm,dl,up,ul = sf_get_modified()

sf_ul('/',ul)
sf_dr('/',dr)
sf_rm('/',rm)
sf_dl('/',dl)
sf_up('/',up)

cclear (0,2,max_x-1)
cclear (0,1,max_x-1)
cprint ('Done', 1)
