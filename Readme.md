# Patching Dorian's u-boot image for extlinux.conf detection

This repository contains a simple bash/python script that patches the patched
uboot image from DoarianRudolph (https://github.com/DorianRudolph/pinenotes),
producing an u-boot image for the PineNote that

* allows memory access to regions larger than 32 mb (patch by DorianRudolph)
* patches the u-boot environment to look for extlinux.conf files in all
  partitions (the first one it finds it used for booting) by modifying the
  bootcmd command:

      *bootcmd=run distro_bootcmd;

  This second step is accomplished by using the u-boot env patching script from
  https://gist.github.com/charasyn/206b2537534b6679b0961be64cf9c35f (user:
  @charasyn)

# Patching u-boot:

Either clone, inspect, and then run

	./patch_it.sh

or trigger the github action to generate the patched image.

# Verification of generated image

Naturally there can be no full validation of the generated image as we are
using a random binary blob from the internet as input...

However, on my computer the following sha256 hash was computed for the
generated uboot image:

	2070cbe763812950602814d7097cc46a0a734f137722c6cc2bb94586ebbdd25a  uboot_32mb_extlinux.img
