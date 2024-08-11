#
# !!! This file will be run in micropython device as a backend service. 
#

import os
import time
from micropython import const
import errno

# ------------------------------------
# crc16
# ------------------------------------

# table for calculating CRC
# this particular table was generated using pycrc v0.7.6, http://www.tty1.net/pycrc/
# using the configuration:
#  *    Width        = 16
#  *    Poly         = 0x1021
#  *    XorIn        = 0x0000
#  *    ReflectIn    = False
#  *    XorOut       = 0x0000
#  *    ReflectOut   = False
#  *    Algorithm    = table-driven
# by following command:
#   python pycrc.py --model xmodem --algorithm table-driven --generate c
CRC16_XMODEM_TABLE = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
        0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
        0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
        0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
        0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
        0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
        0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
        0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
        0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
        0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
        0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
        0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
        0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
        0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
        0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
        0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
        0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
        0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
        0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
        0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
        0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
        0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
        0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
        0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
        0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0,
        ]

def crc16xmodem(data, crc=0):
    """Calculate CRC-CCITT (XModem) variant of CRC16.
    `data`      - data for calculating CRC, must be bytes
    `crc`       - initial value
    Return calculated value of CRC
    """
    for byte in data:
        crc = ((crc<<8)&0xff00) ^ CRC16_XMODEM_TABLE[((crc>>8)&0xff)^byte]
    return crc & 0xffff

# ------------------------------------
# pathlib.py
# ------------------------------------

_SEP = const("/")

def _mode_if_exists(path):
    try:
        return os.stat(path)[0]
    except OSError as e:
        if e.errno == errno.ENOENT:
            return 0
        raise e


def _clean_segment(segment):
    segment = str(segment)
    if not segment:
        return "."
    segment = segment.rstrip(_SEP)
    if not segment:
        return _SEP
    while True:
        no_double = segment.replace(_SEP + _SEP, _SEP)
        if no_double == segment:
            break
        segment = no_double
    return segment


class Path:
    def __init__(self, *segments):
        segments_cleaned = []
        for segment in segments:
            segment = _clean_segment(segment)
            if segment[0] == _SEP:
                segments_cleaned = [segment]
            elif segment == ".":
                continue
            else:
                segments_cleaned.append(segment)

        self._path = _clean_segment(_SEP.join(segments_cleaned))

    def __truediv__(self, other):
        return Path(self._path, str(other))

    def __rtruediv__(self, other):
        return Path(other, self._path)

    def __repr__(self):
        return f'{type(self).__name__}("{self._path}")'

    def __str__(self):
        return self._path

    def __eq__(self, other):
        return self.absolute() == Path(other).absolute()

    def absolute(self):
        path = self._path
        cwd = os.getcwd()
        if not path or path == ".":
            return cwd
        if path[0] == _SEP:
            return path
        return _SEP + path if cwd == _SEP else cwd + _SEP + path

    def resolve(self):
        return self.absolute()

    def open(self, mode="r", encoding=None):
        return open(self._path, mode, encoding=encoding)

    def exists(self):
        return bool(_mode_if_exists(self._path))

    def mkdir(self, parents=False, exist_ok=False):
        try:
            os.mkdir(self._path)
            return
        except OSError as e:
            if e.errno == errno.EEXIST and exist_ok:
                return
            elif e.errno == errno.ENOENT and parents:
                pass  # handled below
            else:
                raise e

        segments = self._path.split(_SEP)
        progressive_path = ""
        if segments[0] == "":
            segments = segments[1:]
            progressive_path = _SEP
        for segment in segments:
            progressive_path += _SEP + segment
            try:
                os.mkdir(progressive_path)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise e

    def is_dir(self):
        return bool(_mode_if_exists(self._path) & 0x4000)

    def is_file(self):
        return bool(_mode_if_exists(self._path) & 0x8000)

    def _glob(self, path, pattern, recursive):
        # Currently only supports a single "*" pattern.
        n_wildcards = pattern.count("*")
        n_single_wildcards = pattern.count("?")

        if n_single_wildcards:
            raise NotImplementedError("? single wildcards not implemented.")

        if n_wildcards == 0:
            raise ValueError
        elif n_wildcards > 1:
            raise NotImplementedError("Multiple * wildcards not implemented.")

        prefix, suffix = pattern.split("*")

        for name, mode, *_ in os.ilistdir(path):
            full_path = path + _SEP + name
            if name.startswith(prefix) and name.endswith(suffix):
                yield full_path
            if recursive and mode & 0x4000:  # is_dir
                yield from self._glob(full_path, pattern, recursive=recursive)

    def glob(self, pattern):
        """Iterate over this subtree and yield all existing files (of any
        kind, including directories) matching the given relative pattern.

        Currently only supports a single "*" pattern.
        """
        return self._glob(self._path, pattern, recursive=False)

    def rglob(self, pattern):
        return self._glob(self._path, pattern, recursive=True)

    def stat(self):
        return os.stat(self._path)

    def read_bytes(self):
        with open(self._path, "rb") as f:
            return f.read()

    def read_text(self, encoding=None):
        with open(self._path, "r", encoding=encoding) as f:
            return f.read()

    def rename(self, target):
        os.rename(self._path, target)

    def rmdir(self):
        os.rmdir(self._path)

    def touch(self, exist_ok=True):
        if self.exists():
            if exist_ok:
                return  # TODO: should update timestamp
            else:
                # In lieue of FileExistsError
                raise OSError(errno.EEXIST)
        with open(self._path, "w"):
            pass

    def unlink(self, missing_ok=False):
        try:
            os.unlink(self._path)
        except OSError as e:
            if not (missing_ok and e.errno == errno.ENOENT):
                raise e

    def write_bytes(self, data):
        with open(self._path, "wb") as f:
            f.write(data)

    def write_text(self, data, encoding=None):
        with open(self._path, "w", encoding=encoding) as f:
            f.write(data)

    def with_suffix(self, suffix):
        index = -len(self.suffix) or None
        return Path(self._path[:index] + suffix)

    @property
    def stem(self):
        return self.name.rsplit(".", 1)[0]

    @property
    def parent(self):
        tokens = self._path.rsplit(_SEP, 1)
        if len(tokens) == 2:
            if not tokens[0]:
                tokens[0] = _SEP
            return Path(tokens[0])
        return Path(".")

    @property
    def name(self):
        return self._path.rsplit(_SEP, 1)[-1]

    @property
    def suffix(self):
        elems = self._path.rsplit(".", 1)
        return "" if len(elems) == 1 else "." + elems[1]

# ------------------------------------
# mpy_backend.py
# ------------------------------------

class _mpy_backend():
    def __init__(self):
        pass

    def _test(self):
        print('[test ok]')

    def _timestamp(self, secs: int) -> str:
        year, month, mday, hour, minute, second, weekday, yearday = time.gmtime(secs)
        # 2024-05-16 14:07:11
        return f'{year}-{month:0>2d}-{mday:0>2d} {hour:0>2d}:{minute:0>2d}:{second:0>2d}'

    def touch(self, path, mkdir=False):
        if mkdir: Path(Path(path).parent).mkdir(True, True)
        with open(path, 'w') as f:
            dummy = f.write('')

    def mkdir(self, path, parents=False):
        Path(path).mkdir(parents, True)

    def ls(self, root_path=os.getcwd(), verbose=False):
        names = None
        try:
            names = os.listdir(root_path)
        except:
            print('')
            return
        if not verbose:
            cursor = 0
            total_num = len(names)
            if total_num > 15:
                while cursor < total_num:
                    nums = min(4, total_num - cursor)
                    name_max_len = 0
                    for i in range(nums):
                        _len = len(names[cursor + i])
                        if name_max_len < _len:
                            name_max_len = _len
                    line = ''
                    for i in range(nums):
                        if i > 0: line += '    '
                        line += f"{names[cursor + i]:>{name_max_len}}"
                    print(line)
                    cursor += nums
            else:
                for fname in names:
                    print(fname)
        else:
            # os.stat = (32768, 0, 0, 0, 0, 0, 60794, 774971513, 774971513, 774971513)
            # os.stat()[0] tells the file type, regular or directory.
            # os.stat()[6] is the file size
            # os.stat()[7], os.stat()[8], os.stat()[9] are all the same and tell the modification time. 
            # For that value to be correct, the time has to be set.
            fdir = '' if root_path == '/' else root_path
            for fname in names:
                _stat = os.stat(fdir + '/' + fname)
                ftype = '-'
                fsize = '         -'
                if _stat[0] == 0x4000:
                    ftype = 'd'
                if _stat[0] == 0x8000:
                    fsize = f'{_stat[6]:>10}'
                print(f'{ftype}---------  {fsize}    {self._timestamp(_stat[7])}    {fname}')

    def _tree(self, path: str, depth: int, max_depth: int):
        T_FORK = '├──'
        T_END  = '└──'
        indent = ' ' + (' ' * (4 * depth))
        findex = 0
        totals = len(os.listdir(path))
        for group in os.ilistdir(path): # -> (name, type, inode[, size])
            fname = group[0]
            if findex == totals - 1:
                print(indent + T_END + ' ' + fname)
            else:
                print(indent + T_FORK + ' ' + fname)
            # cursive dir
            if group[1] == 0x4000:
                p = ('' if path == '/' else path) + '/' + fname
                if max_depth != None:
                    if depth + 1 < max_depth:
                        self._tree(p, depth + 1, max_depth)
                else:
                    self._tree(p, depth + 1, max_depth)
            findex += 1

    def tree(self, root_path=os.getcwd(), max_depth=None):
        print(f"'{root_path}'")
        self._tree(root_path, 0, max_depth)

_mpy = _mpy_backend()