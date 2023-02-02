#!/usr/bin/env sh
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

outfile="uboot_patched.img"
test -e "${outfile}" && rm "${outfile}"

# Download the u-boot image from Dorian
# NOTE: the _patched postfix refers to the fix that enables access to memory >
# 32 MB, not with regard to extlinux.conf changes
wget https://github.com/DorianRudolph/pinenotes/raw/main/static/uboot_patched.img

# checksum
# NOTE: This only checks that the u-boot blob from Dorian was not changed since
# the creation of this script. No guarantee is made regarding the actual
# contents of this binary blob!!!!
echo "42cb5a0d116a37ca8ccc39ee5bfc1e4fa6a047e0b088a0e8bc58d38290a4a78c  uboot_patched.img" | shasum -a 256 -c

# insert the modified environment
python3 pinenote-uboot-envtool.py insert uboot_patched.img uboot_env_modified_extlinux.env uboot_32mb_extlinux.img

