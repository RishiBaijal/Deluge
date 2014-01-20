#
# common.py
#
# Copyright (C) 2007, 2008 Andrew Resch <andrewresch@gmail.com>
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
#   The Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor
#   Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#
#


"""Common functions for various parts of Deluge to use."""

import os
import sys
import time
import subprocess
import platform
import chardet
import logging
import pkg_resources
import gettext
import locale

try:
    import json
except ImportError:
    import simplejson as json

from deluge.error import *

log = logging.getLogger(__name__)

# Do a little hack here just in case the user has json-py installed since it
# has a different api
if not hasattr(json, "dumps"):
    json.dumps = json.write
    json.loads = json.read

    def dump(obj, fp, **kw):
        fp.write(json.dumps(obj))

    def load(fp, **kw):
        return json.loads(fp.read())

    json.dump = dump
    json.load = load

LT_TORRENT_STATE = {
    "Queued": 0,
    "Checking": 1,
    "Downloading Metadata": 2,
    "Downloading": 3,
    "Finished": 4,
    "Seeding": 5,
    "Allocating": 6,
    "Checking Resume Data": 7,
    0: "Queued",
    1: "Checking",
    2: "Downloading Metadata",
    3: "Downloading",
    4: "Finished",
    5: "Seeding",
    6: "Allocating",
    7: "Checking Resume Data"
}

TORRENT_STATE = [
    "Allocating",
    "Checking",
    "Downloading",
    "Seeding",
    "Paused",
    "Error",
    "Queued"
]

FILE_PRIORITY = {
    0: "Do Not Download",
    1: "Normal Priority",
    2: "High Priority",
    3: "High Priority",
    4: "High Priority",
    5: "High Priority",
    6: "High Priority",
    7: "Highest Priority",
    "Do Not Download": 0,
    "Normal Priority": 1,
    "High Priority": 5,
    "Highest Priority": 7
}


def get_version():
    """
    Returns the program version from the egg metadata

    :returns: the version of Deluge
    :rtype: string

    """
    return pkg_resources.require("Deluge")[0].version


def get_default_config_dir(filename=None):
    """
    :param filename: if None, only the config path is returned, if provided,
                     a path including the filename will be returned
    :type filename: string
    :returns: a file path to the config directory and optional filename
    :rtype: string

    """

    if windows_check():
        def save_config_path(resource):
            appDataPath = os.environ.get("APPDATA")
            if not appDataPath:
                import _winreg
                hkey = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                                       "Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders")
                appDataReg = _winreg.QueryValueEx(hkey, "AppData")
                appDataPath = appDataReg[0]
                _winreg.CloseKey(hkey)
            return os.path.join(appDataPath, resource)
    else:
        from xdg.BaseDirectory import save_config_path
    if not filename:
        filename = ''
    try:
        return os.path.join(save_config_path("deluge"), filename)
    except OSError, e:
        log.error("Unable to use default config directory, exiting... (%s)", e)
        sys.exit(1)


def get_default_download_dir():
    """
    :returns: the default download directory
    :rtype: string

    """
    if windows_check():
        return os.path.join(os.path.expanduser("~"), 'Downloads')
    else:
        from xdg.BaseDirectory import xdg_config_home
        userdir_file = os.path.join(xdg_config_home, 'user-dirs.dirs')
        try:
            for line in open(userdir_file, 'r'):
                if not line.startswith('#') and 'XDG_DOWNLOAD_DIR' in line:
                        download_dir = os.path.expandvars(line.partition("=")[2].rstrip().strip('"'))
                        if os.path.isdir(download_dir):
                            return download_dir
        except IOError:
            pass

        return os.environ.get("HOME")


def windows_check():
    """
    Checks if the current platform is Windows

    :returns: True or False
    :rtype: bool

    """
    return platform.system() in ('Windows', 'Microsoft')


def vista_check():
    """
    Checks if the current platform is Windows Vista

    :returns: True or False
    :rtype: bool

    """
    return platform.release() == "Vista"


def osx_check():
    """
    Checks if the current platform is Mac OS X

    :returns: True or False
    :rtype: bool

    """
    return platform.system() == "Darwin"


def get_pixmap(fname):
    """
    Provides easy access to files in the deluge/ui/data/pixmaps folder within the Deluge egg

    :param fname: the filename to look for
    :type fname: string
    :returns: a path to a pixmap file included with Deluge
    :rtype: string

    """
    return resource_filename("deluge", os.path.join("ui", "data", "pixmaps", fname))


def resource_filename(module, path):
    # While developing, if there's a second deluge package, installed globally
    # and another in develop mode somewhere else, while pkg_resources.require("Deluge")
    # returns the proper deluge instance, pkg_resources.resource_filename does
    # not, it returns the first found on the python path, which is not good
    # enough.
    # This is a work-around that.
    return pkg_resources.require("Deluge>=%s" % get_version())[0].get_resource_filename(
        pkg_resources._manager, os.path.join(*(module.split('.')+[path]))
    )


def open_file(path):
    """
    Opens a file or folder using the system configured program

    :param path: the path to the file or folder to open
    :type path: string

    """
    if windows_check():
        os.startfile(path.decode("utf8"))
    elif osx_check():
        subprocess.Popen(["open", "%s" % path])
    else:
        subprocess.Popen(["xdg-open", "%s" % path])


def open_url_in_browser(url):
    """
    Opens a url in the desktop's default browser

    :param url: the url to open
    :type url: string

    """
    import webbrowser
    webbrowser.open(url)

## Formatting text functions

# For performance reasons these fsize units are translated outside the function
byte_txt = "Bytes"
kib_txt = "KiB"
mib_txt = "MiB"
gib_txt = "GiB"


def translate_size_units():
    global byte_txt, kib_txt, mib_txt, gib_txt
    byte_txt = _("Bytes")
    kib_txt = _("KiB")
    mib_txt = _("MiB")
    gib_txt = _("GiB")


def fsize(fsize_b, precision=1):
    """
    Formats the bytes value into a string with KiB, MiB or GiB units

    :param fsize_b: the filesize in bytes
    :type fsize_b: int
    :param precision: the filesize float precision
    :type precision: int
    :returns: formatted string in KiB, MiB or GiB units
    :rtype: string

    **Usage**

    >>> fsize(112245)
    '109.6 KiB'
    >>> fsize(112245, precision=0)
    '110 KiB'

    """
    # Bigger than 1 GiB
    if (fsize_b == 0):
        return "0"
    elif (fsize_b >= 1073741824):
        return "%.*f %s" % (precision, fsize_b / 1073741824.0, gib_txt)
    # Bigger than 1 MiB
    elif (fsize_b >= 1048576):
        return "%.*f %s" % (precision, fsize_b / 1048576.0, mib_txt)
    # Bigger than 1 KiB
    elif (fsize_b >= 1024):
        return "%.*f %s" % (precision, fsize_b / 1024.0, kib_txt)
    else:
        return "%d %s" % (fsize_b, byte_txt)


def fsize_short(fsize_b, precision=0):
    """
    Formats the bytes value into a string with K, M or G units

    :param fsize_b: the filesize in bytes
    :type fsize_b: int
    :param precision: the filesize float precision
    :type precision: int
    :returns: formatted string in K, M or G units
    :rtype: string

    **Usage**

    >>> fsize_short(112245)
    '110 K'
    >>> fsize_short(112245, precision=1)
    '109.6 K'

    """
    fsize_kb = fsize_b / 1024.0
    if fsize_kb < 1024:
        return "%.*f %s" % (precision, fsize_kb, _("K"))
    fsize_mb = fsize_kb / 1024.0
    if fsize_mb < 1024:
        return "%.*f %s" % (precision, fsize_mb, _("M"))
    fsize_gb = fsize_mb / 1024.0
    return "%.*f %s" % (precision, fsize_gb, _("G"))


def fpcnt(dec, precision=2):
    """
    Formats a string to display a percentage with two decimal places

    :param dec: the ratio in the range [0.0, 1.0]
    :type dec: float
    :param precision: the percentage float precision
    :type precision: int
    :returns: a formatted string representing a percentage
    :rtype: string

    **Usage**

    >>> fpcnt(0.9311)
    '93.11%'
    >>> fpcnt(0.9311, precision=0)
    '93%'

    """
    pcnt = (dec * 100)
    if pcnt == 0 or pcnt == 100:
        precision = 0
    return '%.*f%%' % (precision, pcnt)


def fspeed(bps, precision=1):
    """
    Formats a string to display a transfer speed utilizing :func:`fsize`

    :param bps: bytes per second
    :type bps: int
    :returns: a formatted string representing transfer speed
    :rtype: string

    **Usage**

    >>> fspeed(43134)
    '42.1 KiB/s'

    """
    if bps == 0:
        return "0"
    fspeed_kb = bps / 1024.0
    if fspeed_kb < 1024:
        return "%.*f %s" % (precision, fspeed_kb, _("KiB/s"))
    fspeed_mb = fspeed_kb / 1024.0
    if fspeed_mb < 1024:
        return "%.*f %s" % (precision, fspeed_mb, _("MiB/s"))
    fspeed_gb = fspeed_mb / 1024.0
    return "%.*f %s" % (precision, fspeed_gb, _("GiB/s"))

def fspeed_short(precision=0):
    """
    Formats a string to display a transfer speed utilizing :func:`fsize`

    :param bps: bytes per second
    :type bps: int
    :returns: a formatted string representing transfer speed
    :rtype: string

    **Usage**

    >>> fspeed(43134)
    '42.1 K/s'

    """
    if bps == 0:
        return "0"
    fspeed_kb = bps / 1024.0
    if fspeed_kb < 1024:
        return "%.*f %s" % (precision, fspeed_kb, _("K/s"))
    fspeed_mb = fspeed_kb / 1024.0
    if fspeed_mb < 1024:
        return "%.*f %s" % (precision, fspeed_mb, _("M/s"))
    fspeed_gb = fspeed_mb / 1024.0
    return "%.*f %s" % (precision, fspeed_gb, _("G/s"))

def fpeer(num_peers, total_peers):
    """
    Formats a string to show 'num_peers' ('total_peers')

    :param num_peers: the number of connected peers
    :type num_peers: int
    :param total_peers: the total number of peers
    :type total_peers: int
    :returns: a formatted string: num_peers (total_peers), if total_peers < 0, then it will not be shown
    :rtype: string

    **Usage**

    >>> fpeer(10, 20)
    '10 (20)'
    >>> fpeer(10, -1)
    '10'

    """
    if total_peers > -1:
        return "%d (%d)" % (num_peers, total_peers)
    else:
        return "%d" % num_peers


def ftime(seconds):
    """
    Formats a string to show time in a human readable form

    :param seconds: the number of seconds
    :type seconds: int
    :returns: a formatted time string, will return '' if seconds == 0
    :rtype: string

    **Usage**

    >>> ftime(23011)
    '6h 23m'

    """
    if seconds == 0:
        return ""
    if seconds < 60:
        return '%ds' % (seconds)
    minutes = seconds / 60
    if minutes < 60:
        seconds = seconds % 60
        return '%dm %ds' % (minutes, seconds)
    hours = minutes / 60
    if hours < 24:
        minutes = minutes % 60
        return '%dh %dm' % (hours, minutes)
    days = hours / 24
    if days < 7:
        hours = hours % 24
        return '%dd %dh' % (days, hours)
    weeks = days / 7
    if weeks < 52:
        days = days % 7
        return '%dw %dd' % (weeks, days)
    years = weeks / 52
    weeks = weeks % 52
    return '%dy %dw' % (years, weeks)


def fdate(seconds):
    """
    Formats a date time string in the locale's date representation based on the systems timezone

    :param seconds: time in seconds since the Epoch
    :type seconds: float
    :returns: a string in the locale's datetime representation or "" if seconds < 0
    :rtype: string

    """
    if seconds < 0:
        return ""
    return time.strftime("%x %X", time.localtime(seconds))


def is_url(url):
    """
    A simple test to check if the URL is valid

    :param url: the url to test
    :type url: string
    :returns: True or False
    :rtype: bool

    **Usage**

    >>> is_url("http://deluge-torrent.org")
    True

    """
    return url.partition('://')[0] in ("http", "https", "ftp", "udp")


def is_magnet(uri):
    """
    A check to determine if a uri is a valid bittorrent magnet uri

    :param uri: the uri to check
    :type uri: string
    :returns: True or False
    :rtype: bool

    **Usage**

    >>> is_magnet("magnet:?xt=urn:btih:SU5225URMTUEQLDXQWRB2EQWN6KLTYKN")
    True

    """
    magnet_scheme = 'magnet:?'
    xt_param = 'xt=urn:btih:'
    if uri.startswith(magnet_scheme) and xt_param in uri:
        return True
    return False


def create_magnet_uri(infohash, name=None, trackers=[]):
    """
    Creates a magnet uri

    :param infohash: the info-hash of the torrent
    :type infohash: string
    :param name: the name of the torrent (optional)
    :type name: string
    :param trackers: the trackers to announce to (optional)
    :type trackers: list of strings

    :returns: a magnet uri string
    :rtype: string

    """
    from base64 import b32encode
    uri = "magnet:?xt=urn:btih:" + b32encode(infohash.decode("hex"))
    if name:
        uri = uri + "&dn=" + name
    if trackers:
        for t in trackers:
            uri = uri + "&tr=" + t

    return uri


def get_path_size(path):
    """
    Gets the size in bytes of 'path'

    :param path: the path to check for size
    :type path: string
    :returns: the size in bytes of the path or -1 if the path does not exist
    :rtype: int

    """
    if not os.path.exists(path):
        return -1

    if os.path.isfile(path):
        return os.path.getsize(path)

    dir_size = 0
    for (p, dirs, files) in os.walk(path):
        for file in files:
            filename = os.path.join(p, file)
            dir_size += os.path.getsize(filename)
    return dir_size


def free_space(path):
    """
    Gets the free space available at 'path'

    :param path: the path to check
    :type path: string
    :returns: the free space at path in bytes
    :rtype: int

    :raises InvalidPathError: if the path is not valid

    """
    if not os.path.exists(path):
        raise InvalidPathError("%s is not a valid path" % path)

    if windows_check():
        from win32file import GetDiskFreeSpaceEx
        return GetDiskFreeSpaceEx(path)[0]
    else:
        disk_data = os.statvfs(path.encode("utf8"))
        block_size = disk_data.f_frsize
        return disk_data.f_bavail * block_size


def is_ip(ip):
    """
    A simple test to see if 'ip' is valid

    :param ip: the ip to check
    :type ip: string
    :returns: True or False
    :rtype: bool

    ** Usage **

    >>> is_ip("127.0.0.1")
    True

    """
    import socket
    #first we test ipv4
    try:
        if windows_check():
            if socket.inet_aton("%s" % (ip)):
                return True
        else:
            if socket.inet_pton(socket.AF_INET, "%s" % (ip)):
                return True
    except socket.error:
        if not socket.has_ipv6:
            return False
    #now test ipv6
    try:
        if windows_check():
            log.warning("ipv6 check unavailable on windows")
            return True
        else:
            if socket.inet_pton(socket.AF_INET6, "%s" % (ip)):
                return True
    except socket.error:
        return False


def path_join(*parts):
    """
    An implementation of os.path.join that always uses / for the separator
    to ensure that the correct paths are produced when working with internal
    paths on Windows.
    """
    path = ''
    for part in parts:
        if not part:
            continue
        elif part[0] == '/':
            path = part
        elif not path:
            path = part
        else:
            path += '/' + part
    return path

XML_ESCAPES = (
    ('&', '&amp;'),
    ('<', '&lt;'),
    ('>', '&gt;'),
    ('"', '&quot;'),
    ("'", '&apos;')
)


def xml_decode(string):
    """
    Unescape a string that was previously encoded for use within xml.

    :param string: The string to escape
    :type string: string
    :returns: The unescaped version of the string.
    :rtype: string
    """
    for char, escape in XML_ESCAPES:
        string = string.replace(escape, char)
    return string


def xml_encode(string):
    """
    Escape a string for use within an xml element or attribute.

    :param string: The string to escape
    :type string: string
    :returns: An escaped version of the string.
    :rtype: string
    """
    for char, escape in XML_ESCAPES:
        string = string.replace(char, escape)
    return string


def decode_string(s, encoding="utf8"):
    """
    Decodes a string and return unicode. If it cannot decode using
    `:param:encoding` then it will try latin1, and if that fails,
    try to detect the string encoding. If that fails, decode with
    ignore.

    :param s: string to decode
    :type s: string
    :keyword encoding: the encoding to use in the decoding
    :type encoding: string
    :returns: s converted to unicode
    :rtype: unicode

    """
    if not s:
        return u''
    elif isinstance(s, unicode):
        return s

    encodings = [lambda: ("utf8", 'strict'),
                 lambda: ("iso-8859-1", 'strict'),
                 lambda: (chardet.detect(s)["encoding"], 'strict'),
                 lambda: (encoding, 'ignore')]

    if not encoding is "utf8":
        encodings.insert(0, lambda: (encoding, 'strict'))

    for l in encodings:
        try:
            return s.decode(*l())
        except UnicodeDecodeError:
            pass
    return u''


def utf8_encoded(s, encoding="utf8"):
    """
    Returns a utf8 encoded string of s

    :param s: (unicode) string to (re-)encode
    :type s: basestring
    :keyword encoding: the encoding to use in the decoding
    :type encoding: string
    :returns: a utf8 encoded string of s
    :rtype: str

    """
    if isinstance(s, str):
        s = decode_string(s, encoding).encode("utf8")
    elif isinstance(s, unicode):
        s = s.encode("utf8")
    return s


class VersionSplit(object):
    """
    Used for comparing version numbers.

    :param ver: the version
    :type ver: string

    """
    def __init__(self, ver):
        import re
        VERSION_RE = re.compile(r'''
        ^
        (?P<version>\d+\.\d+)          # minimum 'N.N'
        (?P<extraversion>(?:\.\d+)*)   # any number of extra '.N' segments
        (?:
            (?P<prerel>[abc]|rc)       # 'a'=alpha, 'b'=beta, 'c'=release candidate
                                       # 'rc'= alias for release candidate
            (?P<prerelversion>\d+(?:\.\d+)*)
        )?
        (?P<postdev>(\.post(?P<post>\d+))?(\.dev(?P<dev>\d+))?)?
        $''', re.VERBOSE)

        # Check for PEP 386 compliant version
        match = re.search(VERSION_RE, ver)
        if match:
            group = [(x if x is not None else '') for x in match.group(1, 2, 3, 4, 8)]
            vs = [''.join(group[0:2]), ''.join(group[2:4]), group[4].lstrip('.')]
        else:
            ver = ver.lower()
            vs = ver.replace("_", "-").split("-")

        self.version = [int(x) for x in vs[0].split(".")]
        self.suffix = None
        self.dev = False
        if len(vs) > 1:
            if vs[1].startswith(("rc", "a", "b", "c")):
                self.suffix = vs[1]
            if vs[-1].startswith('dev'):
                self.dev = vs[-1]

    def __cmp__(self, ver):
        """
        The comparison method.

        :param ver: the version to compare with
        :type ver: VersionSplit

        """
        # PEP 386 versions with .devN precede release version
        if (bool(self.dev) != bool(ver.dev)):
            if self.dev != 'dev':
                self.dev = not self.dev
            if ver.dev != 'dev':
                ver.dev = not ver.dev

        # If there is no suffix we use z because we want final
        # to appear after alpha, beta, and rc alphabetically.
        v1 = [self.version, self.suffix or 'z', self.dev]
        v2 = [ver.version, ver.suffix or 'z', ver.dev]
        return cmp(v1, v2)


# Common AUTH stuff
AUTH_LEVEL_NONE = 0
AUTH_LEVEL_READONLY = 1
AUTH_LEVEL_NORMAL = 5
AUTH_LEVEL_ADMIN = 10
AUTH_LEVEL_DEFAULT = AUTH_LEVEL_NORMAL


def create_auth_file():
    import stat
    import configmanager
    auth_file = configmanager.get_config_dir("auth")
    # Check for auth file and create if necessary
    if not os.path.exists(auth_file):
        fd = open(auth_file, "w")
        fd.flush()
        os.fsync(fd.fileno())
        fd.close()
        # Change the permissions on the file so only this user can read/write it
        os.chmod(auth_file, stat.S_IREAD | stat.S_IWRITE)


def create_localclient_account(append=False):
    import configmanager
    import random
    auth_file = configmanager.get_config_dir("auth")
    if not os.path.exists(auth_file):
        create_auth_file()

    try:
        from hashlib import sha1 as sha_hash
    except ImportError:
        from sha import new as sha_hash
    fd = open(auth_file, "a" if append else "w")
    fd.write(":".join([
        "localclient",
        sha_hash(str(random.random())).hexdigest(),
        str(AUTH_LEVEL_ADMIN)
    ]) + '\n')
    fd.flush()
    os.fsync(fd.fileno())
    fd.close()


def get_translations_path():
    """Get the absolute path to the directory containing translation files"""
    return resource_filename("deluge", "i18n")


def set_env_variable(name, value):
    '''
    :param name: environment variable name
    :param value: environment variable value

    This function ensures that changes to an environment variable are applied
    to each copy of the environment variables used by a process. Starting from
    Python 2.4, os.environ changes only apply to the copy Python keeps (os.environ)
    and are no longer automatically applied to the other copies for the process.

    On Microsoft Windows, each process has multiple copies of the environment
    variables, one managed by the OS and one managed by the C library. We also
    need to take care of the fact that the C library used by Python is not
    necessarily the same as the C library used by pygtk and friends. This because
    the latest releases of pygtk and friends are built with mingw32 and are thus
    linked against msvcrt.dll. The official gtk+ binaries have always been built
    in this way.

    Basen on _putenv in TransUtils.py from sourceforge project gramps
    http://sourceforge.net/p/gramps/code/HEAD/tree/branches/maintenance/gramps32/src/TransUtils.py
    '''
    # Update Python's copy of the environment variables
    os.environ[name] = value

    if windows_check():
        from ctypes import windll
        from ctypes import cdll
        from ctypes.util import find_msvcrt

        # Update the copy maintained by Windows (so SysInternals Process Explorer sees it)
        try:
            result = windll.kernel32.SetEnvironmentVariableW(name, value)
            if result == 0:
                raise Warning
        except Exception:
            log.warning('Failed to set Env Var \'%s\' (\'kernel32.SetEnvironmentVariableW\')' % name)
        else:
            log.debug('Set Env Var \'%s\' to \'%s\' (\'kernel32.SetEnvironmentVariableW\')' % (name, value))

        # Update the copy maintained by msvcrt (used by gtk+ runtime)
        try:
            result = cdll.msvcrt._putenv('%s=%s' % (name, value))
            if result != 0:
                raise Warning
        except Exception:
            log.warning('Failed to set Env Var \'%s\' (\'msvcrt._putenv\')' % name)
        else:
            log.debug('Set Env Var \'%s\' to \'%s\' (\'msvcrt._putenv\')' % (name, value))

        # Update the copy maintained by whatever c runtime is used by Python
        try:
            msvcrt = find_msvcrt()
            msvcrtname = str(msvcrt).split('.')[0] if '.' in msvcrt else str(msvcrt)
            result = cdll.LoadLibrary(msvcrt)._putenv('%s=%s' % (name, value))
            if result != 0:
                raise Warning
        except Exception:
            log.warning('Failed to set Env Var \'%s\' (\'%s._putenv\')' % (name, msvcrtname))
        else:
            log.debug('Set Env Var \'%s\' to \'%s\' (\'%s._putenv\')' % (name, value, msvcrtname))


def set_language(lang):
    """
    Set the language to use.

    gettext and GtkBuilder will load the translations from the specified
    language.

    :param lang: the language, e.g. "en", "de" or "en_GB"
    :type lang: str
    """
    lang = str(lang)
    # Necessary to set these environment variables for GtkBuilder
    set_env_variable('LANGUAGE', lang)  # Windows/Linux
    set_env_variable('LANG', lang)  # For OSX

    translations_path = get_translations_path()
    ro = gettext.translation("deluge", localedir=translations_path, languages=[lang])
    ro.install()


# Initialize gettext
def setup_translations(setup_gettext=True, setup_pygtk=False):
    translations_path = get_translations_path()
    domain = "deluge"
    log.info("Setting up translations from %s", translations_path)

    if setup_pygtk:
        try:
            log.info("Setting up GTK translations from %s", translations_path)

            if windows_check():
                import ctypes
                libintl = ctypes.cdll.intl
                libintl.bindtextdomain(domain, translations_path.encode(sys.getfilesystemencoding()))
                libintl.textdomain(domain)
                libintl.bind_textdomain_codeset(domain, "UTF-8")
                libintl.gettext.restype = ctypes.c_char_p

            # Use glade for plugins that still uses it
            import gtk
            import gtk.glade
            gtk.glade.bindtextdomain(domain, translations_path)
            gtk.glade.textdomain(domain)
        except Exception, e:
            log.error("Unable to initialize glade translation!")
            log.exception(e)
    if setup_gettext:
        try:
            if hasattr(locale, "bindtextdomain"):
                locale.bindtextdomain(domain, translations_path)
            if hasattr(locale, "textdomain"):
                locale.textdomain(domain)

            gettext.bindtextdomain(domain, translations_path)
            gettext.bind_textdomain_codeset(domain, 'UTF-8')
            gettext.textdomain(domain)
            gettext.install(domain, translations_path, unicode=True)
        except Exception, e:
            log.error("Unable to initialize gettext/locale!")
            log.exception(e)
            import __builtin__
            __builtin__.__dict__["_"] = lambda x: x

        translate_size_units()


def unicode_argv():
    """ Gets sys.argv as list of unicode objects on any platform."""
    if windows_check():
        # Versions 2.x of Python don't support Unicode in sys.argv on
        # Windows, with the underlying Windows API instead replacing multi-byte
        # characters with '?'.
        from ctypes import POINTER, byref, cdll, c_int, windll
        from ctypes.wintypes import LPCWSTR, LPWSTR

        GetCommandLineW = cdll.kernel32.GetCommandLineW
        GetCommandLineW.argtypes = []
        GetCommandLineW.restype = LPCWSTR

        CommandLineToArgvW = windll.shell32.CommandLineToArgvW
        CommandLineToArgvW.argtypes = [LPCWSTR, POINTER(c_int)]
        CommandLineToArgvW.restype = POINTER(LPWSTR)

        cmd = GetCommandLineW()
        argc = c_int(0)
        argv = CommandLineToArgvW(cmd, byref(argc))
        if argc.value > 0:
            # Remove Python executable and commands if present
            start = argc.value - len(sys.argv)
            return [argv[i] for i in
                    xrange(start, argc.value)]
    else:
        # On other platforms, we have to find the likely encoding of the args and decode
        # First check if sys.stdout or stdin have encoding set
        encoding = getattr(sys.stdout, "encoding") or getattr(sys.stdin, "encoding")
        # If that fails, check what the locale is set to
        encoding = encoding or locale.getpreferredencoding()
        # As a last resort, just default to utf-8
        encoding = encoding or "utf-8"

        return [arg.decode(encoding) for arg in sys.argv]
