#!/usr/bin/env python3
# Downloaded from
# https://gist.github.com/charasyn/206b2537534b6679b0961be64cf9c35f on
# 2023.Feb.3
# pinenote-uboot-envtool.py
# charasyn 2022
# based on https://github.com/DorianRudolph/pinenotes/blob/main/py/uboot_img.py
#
# This tool extracts and inserts the default environment from/to a PineNote
# Uboot image.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
from hashlib import sha256
import sys
from typing import List

LOG_ERROR = 0
LOG_WARNING = 1
LOG_VERBOSE = 2
LOG_DEBUG = 3
def set_loglevel(level):
    global loglevel
    loglevel = level
def pd(*args, **kwargs):
    if loglevel < LOG_DEBUG:
        return
    kwargs['file'] = sys.stderr
    print('[DBG]', *args, **kwargs)
def pv(*args, **kwargs):
    if loglevel < LOG_VERBOSE:
        return
    kwargs['file'] = sys.stderr
    print('[NFO]', *args, **kwargs)
def pw(*args, **kwargs):
    if loglevel < LOG_WARNING:
        return
    kwargs['file'] = sys.stderr
    print('[WRN]', *args, **kwargs)
def pe(*args, **kwargs):
    if loglevel < LOG_ERROR:
        return
    kwargs['file'] = sys.stderr
    print('[ERR]', *args, **kwargs)


loglevel = LOG_WARNING
preserve_comments = True

IMAGE_SZ = 0x200000

UBOOT_OFFSET = 0xE00
UBOOT_SZ = 0x128288

ENV_OFFSET = 0xC1730
ENV_SZ = 0xE29

def read_image_data(image_fp: str) -> bytes:
    with open(image_fp, 'rb') as f:
        data = f.read()
    # the uboot image contains the same data two times
    data_firstcopy = data[:IMAGE_SZ]
    assert data_firstcopy == data[IMAGE_SZ:]
    return data_firstcopy

def extract_uboot(img_data: bytes) -> bytes:
    return img_data[UBOOT_OFFSET:UBOOT_OFFSET+UBOOT_SZ]

def get_uboot_hash_offset(img_data: bytes) -> int:
    h = sha256(extract_uboot(img_data)).digest()
    hash_offset = img_data.find(h)
    pd(f'Uboot hash offset is {hash_offset:#08x}')
    assert hash_offset > 0
    return hash_offset

def extract(src_img, dst_env):
    img = read_image_data(src_img)
    uboot = extract_uboot(img)
    env = uboot[ENV_OFFSET:ENV_OFFSET+ENV_SZ]
    env_before_terminator, _, _ = env.partition(b'\0\0')
    env_lines = (str(entry, encoding='ascii') for entry in env_before_terminator.split(b'\0'))
    with open(dst_env, 'w') as f:
        f.writelines(f'{line}\n' for line in env_lines)

def insert(src_img, src_env, dst_img):
    with open(src_env) as f:
        env_lines_raw = f.readlines()
    if preserve_comments:
        env_lines = (line.rstrip('\n') for line in env_lines_raw)
    else:
        env_lines = (line.partition('#')[0].strip() for line in env_lines_raw)
    env_lines = [line for line in env_lines if line]
    for line in env_lines:
        assert line.isprintable(), f"Non-printable characters in line '{line}'"
        assert line.isascii(), f"Non-ascii characters in line '{line}'"
    env_data = b'\0'.join(bytes(line, encoding='ascii') for line in env_lines)
    env_data += b'\0'
    pv(f"Environment uses {len(env_data)} bytes of space out of {ENV_SZ} available")
    assert len(env_data) <= ENV_SZ, f"Environment exceeds maximum size"
    env_data_padded = env_data.ljust(ENV_SZ, b'\0')

    if not src_img:
        pv(f"Using destination image '{dst_img}' as Uboot source image")
        src_img = dst_img
    img = read_image_data(src_img)
    hash_offset = get_uboot_hash_offset(img)
    uboot = extract_uboot(img)
    uboot_patched = bytearray(uboot)
    uboot_patched[ENV_OFFSET:ENV_OFFSET+ENV_SZ] = env_data_padded

    uboot_patched_hash = sha256(uboot_patched).digest()

    img_patched = bytearray(img)
    img_patched[UBOOT_OFFSET:UBOOT_OFFSET+UBOOT_SZ] = uboot_patched
    img_patched[hash_offset:hash_offset+len(uboot_patched_hash)] = uboot_patched_hash

    with open(dst_img, 'wb') as f:
        f.write(img_patched)
        f.write(img_patched)

def usage():
    print('''
usage: pinenote-uboot-envtool.py <extract|insert> ...
  This program extracts and modifies the default environment in a PineNote
  Uboot image. It transforms the environment from a series of null-terminated
  lines into a plain-text file that can be easily modified and re-inserted.

extract: Extracts the default environment.
  pinenote-uboot-envtool.py extract <input image> <output environment>

insert: Inserts a new default environment.
  pinenote-uboot-envtool.py insert <input image> <input environment> <output image>

This program is provided with no guarantees or warranty. Use at your own risk!
''')

def main(argv: List[str]):
    while argv and argv[0][0] == '-':
        if argv[0] in ['-h', '--help']:
            argv.pop(0)
            usage()
            return
        elif argv[0] in ['-d', '--debug']:
            argv.pop(0)
            set_loglevel(LOG_DEBUG)
        elif argv[0] in ['-v', '--verbose']:
            argv.pop(0)
            set_loglevel(LOG_VERBOSE)
    # Expect verb
    if not argv:
        usage()
        pe(f'Arguments not provided')
        return

    verb = argv.pop(0)
    def check_argcount(argcount):
        if len(argv) != argcount:
            usage()
            pe(f'Wrong arguments provided for {verb}, expected {argcount} but got {len(argv)}')
            return False
        return True

    if verb == 'extract':
        if not check_argcount(2):
            return
        extract(*argv)
    elif verb == 'insert':
        if not check_argcount(3):
            return
        insert(*argv)
    else:
        usage()
        pe(f'Invalid argument verb {argv[0]}')
        return

if __name__ == '__main__':
    main(sys.argv[1:])
