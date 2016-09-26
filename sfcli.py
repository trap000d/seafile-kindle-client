#! /usr/bin/python

import requests
from urllib import urlencode,quote
import ConfigParser
import os

### Some global definitions
#cfg_file='/mnt/us/extensions/seafile/seafile.cfg'
cfg_file='seafile.cfg'

def sf_ping():
    r = requests.get(url + '/api2/ping/')
    return r.text;

def sf_authping():
    hdr = { 'Authorization' : 'Token ' + token }
    print hdr
    r = requests.get(url + '/api2/auth/ping/', headers = hdr)
    return r.text;

def sf_get_token():
    postdata = {'username' : user , 'password' : password}
    r = requests.post( url + '/api2/auth-token/', data=postdata)
    jToken = r.json()
    token=jToken['token']
    return token;

def sf_get_lib_id():
    hdr = { 'Authorization' : 'Token ' + token  , 'Accept' : 'application/json; indent=4'}
    r = requests.get(url + '/api2/repos/', headers = hdr)
    jList=r.json()
    for i in jList:
        #print i['name']
        #print i['id']
        if i['name'] == lib:
            return i['id'];
    return;

def sf_ls_lib():
    hdr = { 'Authorization' : 'Token ' + token  , 'Accept' : 'application/json; indent=4'}
    r = requests.get( url + '/api2/repos/' + libid + '/dir/?p=/', headers = hdr)
    return r.json();

# # Returns 3 lists: 1 with filenames to erase, 2 for hashes to download
def sf_get_modified():
    h_lcl={}
    h_srv={}
    h1=[]
    h2=[]
    ## Local files list in format <hash> <filename>
    with open(dir_local + '/.hash','a+') as f:
        for row in f:
            hash = row.split(' ', 1 )
            h_lcl[hash[0]]=hash[1]
            h1.append(hash[0])
    f.close()
    jl=sf_ls_lib()
    for i in jl:
        #print i
        if i['type'] == 'file':
            h_srv[i['id']]=i['name']
            h2.append(str(i['id']))
            #print 'found file hash',i['id'],i['name']

    f_lcl = set(h1)
    f_srv = set(h2)
    #print f_lcl
    #print f_srv
    to_erase    = f_lcl - f_srv
    to_download = f_srv - f_lcl
    ## We'll Remove these files
    #print to_erase
    f_rm=[]
    f_dl=[]
    for i in list(to_erase):
        if i in h_lcl.keys():
            f_rm.append(h_lcl[i])

    for i in list(to_download):
        if i in h_srv.keys():
            f_dl.append(h_srv[i])
    return f_rm , f_dl, h_srv;
# 
def sf_dl(dl_list):
    for fname in dl_list:
        print 'Downloading:', fname
        hdr = { 'Authorization' : 'Token ' + token  , 'Accept' : 'application/json; indent=4'}
        uurl = url + '/api2/repos/' + libid + '/file/?p=/' + fname #quote(fname.encode('utf-8'))
        r = requests.get(uurl, headers=hdr)
        dl_url = r.content
        if dl_url.startswith('"') and dl_url.endswith('"'):
            dl_url = dl_url[1:-1]
        rdl = requests.get(dl_url, stream=True)
        with open( dir_local + '/' + fname, 'wb' ) as f:
            for chunk in rdl.iter_content(chunk_size=1024): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
        #dl_url = r.text()
        #print dl_url
    return;
 
def sf_rm(rm_list):
    for fname in rm_list:
        print "Erasing:", fname
        os.remove(dir_local + '/' + fname.rstrip())
    return;
 
## Updates hash table
def sf_up(up_list):
    with open(dir_local + '/.hash','w') as h:
        for i in up_list:
            s=i + ' ' +  up_list[i] + '\n'
            h.write(s.encode("UTF-8"))
    return;

### --- Main start
config = ConfigParser.RawConfigParser()
config.read(cfg_file)

url=config.get('server','url')
lib=config.get('server','library')
user=config.get('server','user')
#password=config.get('server','password')
dir_local=config.get('kindle','local')

b=sf_ping()
print b

try:
    token=config.get('server','token')
except ConfigParser.NoOptionError:
    token=sf_get_token()
    #print token
    config.set('server','token',token)
    with open(cfg_file, 'wb') as configfile:
        config.write(configfile)
    #print('exception caught')

rc = sf_authping()
#print rc
# #print token
# 
libid=sf_get_lib_id()
# print libid
# 
rm,dl,up = sf_get_modified()
print 'to remove:', rm
print 'to download:',dl
print  'to up:', up   
sf_rm(rm)
sf_dl(dl)
sf_up(up)

