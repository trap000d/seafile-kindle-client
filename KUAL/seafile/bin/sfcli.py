#! /mnt/us/python/bin/python2.7
# -*- coding:utf-8 -*-

import threading
import time

import requests
from requests.packages.urllib3.exceptions import SubjectAltNameWarning
import requests.packages.urllib3
from requests.packages.urllib3.packages import six
import email.utils
import mimetypes

import ConfigParser
import os
import sys
import shutil
from subprocess import call, Popen, PIPE
from re import findall


def spinning_cursor():
    while True:
        for cursor in '+*':
            yield cursor


def spinner():
    s = spinning_cursor()
    while True:
        call(['eips', '1 ', str(1 + max_y - 3), s.next()])
        time.sleep(1)


def utf8_format_header_param(name, value):
    """
    Helper function to format and quote a single header parameter.

    Particularly useful for header parameters which might contain
    non-ASCII values, like file names. This follows RFC 2231, as
    suggested by RFC 2388 Section 4.4.
    Modified to encode utf-8 by default Standard function
    from `requests` should be monkeypatched as:
    `requests.packages.urllib3.fields.format_header_param = utf8_format_header_param`

    :param name:
        The name of the parameter, a string expected to be ASCII only.
    :param value:
        The value of the parameter, provided as a unicode string.
    """
    if not any(ch in value for ch in '"\\\r\n'):
        result = '%s="%s"' % (name, value)
        try:
            result.encode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
        else:
            return result
    if not six.PY3 and isinstance(value, six.text_type):  # Python 2:
        value = value.encode('utf-8')
    value = email.utils.encode_rfc2231(value, 'utf-8')
    value = '%s*=%s' % (name, value)
    return value


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
    call(['eips', '3 ', str(ypos + max_y - 3), safe_str(s)[:max_x - 4]])
    return


def cclear(xpos, ypos, len):
    call(['eips', str(xpos), str(ypos + max_y - 3), ' ' * len])
    return


def cstatus(s):
    cclear(3, 1, max_x - 3)
    cprint(s, 1)


def cout(xpos, ypos, c):
    call(['eips', str(xpos), str(ypos + max_y - 3), ' '])
    call(['eips', str(xpos + 1), str(ypos + max_y - 3), c])
    return


def sf_authping():
    r = requests.get(url + '/api2/auth/ping/', headers=hdr, verify=ca_verify)
    return r.text


def sf_get_token():
    postdata = {'username': user, 'password': password}
    r = requests.post(
        url + '/api2/auth-token/',
        data=postdata,
        verify=ca_verify)
    jToken = r.json()
    token = jToken['token']
    return token


def sf_get_lib_id():
    r = requests.get(url + '/api2/repos/', headers=hdr, verify=ca_verify)
    jList = r.json()
    for i in jList:
        if i['name'] == lib:
            return i['id']
    return


def sf_ls_lib(dir_entry='/'):
    r = requests.get(
        url +
        '/api2/repos/' +
        libid +
        '/dir/?p=' +
        dir_entry,
        headers=hdr,
        verify=ca_verify)
    return r.json()


def sf_get_modified(dir_entry='/'):
    """ Returns 4 lists a,b,c,d : a - directories to erase, b - filenames to erase, c - files to download d - hashes to update """
    h_lcl = {}
    h_srv = {}
    h1 = []
    h2 = []
    d = os.path.normpath(dir_local + dir_entry)
    try:
        os.makedirs(d)
    except OSError:
        if not os.path.isdir(d):
            raise

    with open(d + '/.hash', 'a+') as f:
        for row in f:
            hash = row.split(' ', 1)
            name = hash[1].rstrip()
            h_lcl[hash[0]] = name
            h1.append(hash[0])
    f.close()
    subdirs_local = [safe_unicode(name) for name in os.listdir(
        d) if os.path.isdir(os.path.join(d, name)) and not name.endswith('.sdr')]

    jl = sf_ls_lib(dir_entry)
    subdirs_srv = []
    for i in jl:
        if i['type'] == 'file':
            h_srv[i['id']] = i['name']
            h2.append(str(i['id']))
        elif i['type'] == 'dir':
            p = dir_entry + i['name']
            subdirs_srv.append(i['name'])
            dr, rm, dl, up = sf_get_modified(p + '/')
            sf_dr(p, dr)
            sf_rm(p, rm)
            sf_dl(p, dl)
            sf_up(p, up)

    f_lcl = set(h1)
    f_srv = set(h2)

    d_lcl = set(subdirs_local)
    d_srv = set(subdirs_srv)

    dir_to_erase = d_lcl - d_srv
    d_rm = list(dir_to_erase)

    to_erase = f_lcl - f_srv
    to_download = f_srv - f_lcl

    f_rm = []
    f_dl = []
    for i in list(to_erase):
        if i in h_lcl.keys():
            f_rm.append(h_lcl[i])

    for i in list(to_download):
        if i in h_srv.keys():
            f_dl.append(h_srv[i])
    return d_rm, f_rm, f_dl, h_srv


def sf_get_ul(dir_entry='/'):
    """
    :param dir_entry:
        Relative path to directory
    :return:
        list of files to upload
    """
    fl = []
    d = os.path.normpath(dir_local + dir_entry)

    try:
        os.makedirs(d)
    except OSError:
        if not os.path.isdir(d):
            raise

    with open(d + '/.hash', 'a+') as f:
        for row in f:
            hash = row.split(' ', 1)
            name = hash[1].rstrip()
            fl.append(safe_unicode(name))
    f.close()
    files_real = [safe_unicode(name) for name in os.listdir(
        d) if os.path.isfile(os.path.join(d, name)) and not name.startswith('.')]

    jl = sf_ls_lib(dir_entry)
    for i in jl:
        if i['type'] == 'dir':
            p = dir_entry + i['name']
            ul, rms = sf_get_ul(p + '/')
            sf_ul(p + '/', ul)
            sf_rm_srv(p + '/', rms)

    f_hash = set(fl)
    f_real = set(files_real)
    to_upload = f_real - f_hash
    to_remove_srv = f_hash - f_real
    f_ul = list(to_upload)
    f_rm_srv = list(to_remove_srv)
    return f_ul, f_rm_srv


def sf_dl(dir_entry, dl_list):
    if not dl_list:
        return
    cclear(2, 1, max_x - 3)
    for idx, fname in enumerate(dl_list):
        cstatus('Downloading file ' + str(idx + 1) +
                ' of ' + str(len(dl_list)))
        uurl = url + '/api2/repos/' + libid + '/file/?p=' + dir_entry + '/' + fname
        r = requests.get(uurl, headers=hdr, verify=ca_verify)
        dl_url = r.content
        if dl_url.startswith('"') and dl_url.endswith('"'):
            dl_url = dl_url[1:-1]
        rdl = requests.get(dl_url, stream=True, verify=ca_verify)
        d = dir_local + dir_entry
        try:
            os.makedirs(d)
        except OSError:
            if not os.path.isdir(d):
                raise
        with open(d + '/' + fname, 'wb') as f:
            idx = 0
            for chunk in rdl.iter_content(chunk_size=65536):
                if chunk:  # filter out keep-alive new chunks
                    cout(2, 2, str(idx * 64) + ' K')
                    idx = idx + 1
                    f.write(chunk)
            cclear(0, 2, max_x - 1)
    return


def sf_rm(dir_entry, rm_list):
    if not rm_list:
        return
    cclear(2, 1, max_x - 3)
    for idx, fname in enumerate(rm_list):
        cstatus('Removing ' + str(idx) + ' file of ' + str(len(rm_list)))
        f = safe_unicode(fname.rstrip())
        try:
            os.remove(dir_local + dir_entry + '/' + f)
        except OSError:
            pass
    return


def sf_dr(dir_entry, dir_list):
    """ remove directories from list """
    if not dir_list:
        return
    cclear(2, 1, max_x - 3)
    for idx, dirname in enumerate(dir_list):
        cstatus('Removing directory ' + str(idx) +
                ' of ' + str(len(dir_list)))
        try:
            shutil.rmtree(os.path.normpath(dir_local + dir_entry + dirname))
        except OSError:
            pass
    return


def sf_up(dir_entry, up_list):
    """ Update hash table """
    if not up_list:
        return
    cclear(2, 1, max_x - 3)
    cstatus('Updating hashes')
    with open(dir_local + dir_entry + '/.hash', 'w') as h:
        for i in up_list:
            s = i + ' ' + up_list[i] + '\n'
            h.write(s.encode("UTF-8"))
    return


def sf_ul(dir_entry, ul_list):
    """ Upload file """
    if not ul_list:
        return
    cclear(2, 1, max_x - 3)
    for idx, lfile in enumerate(ul_list):
        cstatus('Uploading ' + str(idx) + ' new file of ' + str(len(ul_list)))
        uurl = url + '/api2/repos/' + libid + '/upload-link/?p=' + dir_entry
        r = requests.get(uurl, headers=hdr, verify=ca_verify)
        upload_link = r.json()
        response = requests.post(
            upload_link, data={'filename': lfile, 'parent_dir': dir_entry},
            files={'file': open(dir_local + dir_entry + '/' + lfile, 'rb')},
            headers=hdr,
            verify=ca_verify
        )
        cstatus('Updating hashes')
        with open(dir_local + dir_entry + '/.hash', 'a') as h:
            s = response.text + ' ' + lfile + '\n'
            h.write(s.encode('utf-8'))
    return


def sf_rm_srv(dir_entry, rm_list):
    """Remove file(s) from rm_list at the server side
       DELETE https://cloud.seafile.com/api2/repos/{repo-id}/file/?p=/foo
    """
    if not rm_list:
        return
    cclear(2, 1, max_x - 3)
    for idx, f in enumerate(rm_list):
        cstatus('Removing file ' + str(idx) + ' of ' +
                str(len(rm_list)) + ' on server...')
        uurl = url + '/api2/repos/' + libid + '/file/?p=' + dir_entry + f
        r = requests.delete(uurl, headers=hdr, verify=ca_verify)
        if r.status_code == 200 or r.status_code == 400:  # Removed successfully or doesn't exist on server
            with open(os.path.normpath(dir_local + dir_entry) + '/.hash', 'r+') as h:
                data = h.readlines()
                h.seek(0)
                h.truncate()
                for line in data:
                    if not f in safe_unicode(line):
                        h.write(line)
    return


def sf_get_push():
    d = os.path.normpath(dir_local + dir_push)
    upfiles = []
    for r, s, files in os.walk(d):
        s[:] = [x for x in s if not x.endswith('.sdr')]
        for f in files:
            if not f.startswith('.'):
                upfiles.append(os.path.join(r, f))
    return upfiles


def sf_push():
    """ Push directory to the server """
    files = sf_get_push()
    if not files:
        return
    hashlist = []
    cclear(2, 1, max_x - 3)
    for idx, f in enumerate(files):
        fn = os.path.basename(f)
        fb = safe_unicode(fn)
        cstatus('Updating file ' + str(idx) + ' of ' + str(len(files)))
        dir_entry = os.path.relpath(os.path.dirname(f), dir_local)
        uurl = url + '/api2/repos/' + libid + '/update-link/?p=/' + dir_entry
        r = requests.get(uurl, headers=hdr, verify=ca_verify)
        update_link = r.json()
        response = requests.post(
            update_link,
            data={
                'filename': fb,
                'target_file': '/' + dir_entry + '/' + fb},
            files={
                'file': (
                    fb,
                    open(
                        f,
                        'rb').read())},
            headers=hdr,
            verify=ca_verify)
        if response.status_code == 441:  # File not exists
            sf_ul('/' + dir_entry, [fb])
            return
        if response.status_code == 200:
            inhash = False
            with open(os.path.normpath(dir_local + dir_push) + '/.hash', 'r+') as h:
                data = h.readlines()
                h.seek(0)
                h.truncate()
                for row in data:
                    line = row.split(' ', 1)
                    if line[0] != '\n':
                        name = line[1].rstrip()
                        if fn == name:
                            inhash = True
                            line[0] = response.text
                            hashlist.append(
                                line[0] + ' ' + name.decode('utf-8'))
                if not inhash:
                    hashlist.append(response.text + ' ' + fn.decode('utf-8'))
                h.writelines(('\n'.join(hashlist) + '\n').encode('utf-8'))
    return


def screen_size():
    cmd = Popen('eips 99 99 " "', shell=True, stdout=PIPE)
    # eips: pixel_in_range> (1600, 2400) pixel not in range (0..1072, 0..1448)
    for line in cmd.stdout:
        l = findall(r'\d+', line)
        x = 1 + int(l[3]) / (int(l[0]) / 100)
        y = int(l[5]) / (int(l[1]) / 100)
        return x, y


def is_connected():
    try:
        _ = requests.get(url + '/api2/ping/', verify=ca_verify, timeout=10)
        return True
    except requests.ConnectionError:
        pass
    return False


def sf_connect():
    cstatus('Connecting to Seafile server')
    for i in xrange(1, 20):
        if is_connected():
            return 0
        time.sleep(1)
    return 1


def wifi(enable=1):
    """ returns 0, 1 or error codes """
    status = 0
    cmd = Popen(
        'lipc-set-prop com.lab126.cmd wirelessEnable ' +
        str(enable),
        shell=True)
    if enable == 1:
        cstatus('Activating wireless')
        for i in xrange(1, 20):
            """ 20 seconds timeout for starting wireless
            """
            status = wifi_status()
            if status == 1:
                return status
            time.sleep(1)
    return status


def wifi_status():
    cmd = Popen(
        'lipc-get-prop com.lab126.cmd wirelessEnable',
        shell=True,
        stdout=PIPE)
    for line in cmd.stdout:
        l = int(line)
        if l in (0, 1):
            return l
    return 4


def quit_with(msg):
    if wifi_old == 0:
        wifi(0)
    cstatus(msg)
    quit()
    return

# --- Main start

if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings(SubjectAltNameWarning)

    # Some hardcoded path
    cfg_dir = '/mnt/us/extensions/seafile'

    config = ConfigParser.RawConfigParser()
    cfg_file = cfg_dir + '/seafile.cfg'
    config.read(cfg_file)

    url = config.get('server', 'url')
    lib = config.get('server', 'library')
    user = config.get('server', 'user')
    password = config.get('server', 'password')
    cert = config.get('server', 'cert')
    dir_local = config.get('kindle', 'local')
    dir_push = config.get('kindle', 'upload')

    max_x, max_y = screen_size()

    if cert == 'False':
        ca_verify = False
    elif cert == 'True':
        ca_verify = True
    else:
        ca_verify = cert

    t = threading.Thread(target=spinner)
    t.setDaemon(True)
    t.start()

    wifi_old = wifi_status()
    if wifi_old == 0:
        w = wifi(1)
        if w != 1:
            quit_with('Error: Can not activate wireless connection')

    rc = sf_connect()
    if rc:
        quit_with('Error: Connection timeout')

    try:
        token = config.get('server', 'token')
    except ConfigParser.NoOptionError:
        token = sf_get_token()
        config.set('server', 'token', token)
        config.set('server', 'user', '')
        config.set('server', 'password', '')
        with open(cfg_file, 'wb') as configfile:
            config.write(configfile)

    hdr = {'Authorization': 'Token ' + token}
    rc = sf_authping()
    cstatus('Got ' + rc + ' from server')
    libid = sf_get_lib_id()
    if not libid:
        quit_with('Error: Library doesn not exist on the server')

    requests.packages.urllib3.fields.format_header_param = utf8_format_header_param

    if len(sys.argv) > 1:
        if sys.argv[1] == 'push':
            push = True
            sf_push()
            cclear(0, 2, max_x - 1)
            quit_with('Done')

    ul, rms = sf_get_ul()
    sf_ul('/', ul)
    sf_rm_srv('/', rms)

    dr, rm, dl, up = sf_get_modified()
    sf_dr('/', dr)
    sf_rm('/', rm)
    sf_dl('/', dl)
    sf_up('/', up)

    cclear(0, 2, max_x - 1)
    quit_with('Done')
