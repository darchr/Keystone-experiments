# Keystone Runs in gem5

This document explains how to setup all components to run Keystone on gem5.
Some of the instructions (relevant to building Keystone components) are a summarized form of the keystone setup instructions from the Keystone [documentation](http://docs.keystone-enclave.org/).


Pre-requisite libraries needed:

```sh
sudo apt update
sudo apt install autoconf automake autotools-dev bc \
bison build-essential curl expat libexpat1-dev libexpat-dev flex gawk gcc git \
gperf libgmp-dev libmpc-dev libmpfr-dev libtool texinfo tmux \
patchutils zlib1g-dev wget bzip2 patch vim-common lbzip2 python \
pkg-config libglib2.0-dev libpixman-1-dev libssl-dev screen \
device-tree-compiler expect makeself unzip cpio rsync cmake p7zip-full
```

Clone the main keystone repo:

```sh
git clone https://github.com/keystone-enclave/keystone.git
```

A quick way to do initial set-up is running `fast-setup.sh` script in `keystone` directory:

```sh
cd keystone
# Optionally to checkout the version we tested:
git checkout a1842a1ec959c4e40ffd55091795bb577894c545
./fast-setup.sh
```

This should build/install needed tool-chain as well:

Then to set all the environment variables:

```sh
source source.sh
```

Then to build all components:

```sh
mkdir build
cd build
cmake ..
make
```

This would build all the components needed to run Keystone.
The built disk image (build/buildroot.build/images/rootfs.ext2) will contain test binaries, eyrie runtime and a test runner application all combined into a single package.

Assuming that you are in the build/ directory, the created disk image can be found in `buildroot.build/images/rootfs.ext2`

Bootloader compiled with SM and the Linux kernel will be here:

`sm.build/platform/generic/firmware/fw_payload.elf`

One change that is still needed in the disk image is to remove a networking related init script:

```sh
 cd buildroot.build/images/;
mkdir mnt;
mount -o loop rootfs.ext2 mnt/;
rm ../etc/init.d/S40network ;
umount mnt/;
```

Linux would still boot on gem5 with this init script, but it makes the booting process very slow (as a networking device is nor supported yet for RISC-V and this script keeps scanning for it).



## To compile and run RV8 benchmarks

First building musl riscv toolchain:

```sh
git clone https://github.com/rv8-io/musl-riscv-toolchain.git
cd musl-riscv-toolchain
sh bootstrap.sh riscv64
```

You might need to apply this patch before building the toolchain:
`https://github.com/michaeljclark/musl-riscv-toolchain/pull/5`.

`RISCV_MUSL` env variable should be set to the path of the built toolchain:

To build the workloads:

```sh
git clone https://github.com/keystone-enclave/rv8-bench.git
cd rv8-bench
git checkout keystone
make
```

We will have to separately compile eyrie runtime, the one that is built by default as in above instructions will not work for unmodified rv8 benchmarks:

```sh
cd keystone/build/examples/tests/runtime/src/eyrie-test-eyrie;
/build.sh freemem untrusted_io_syscall env_setup linux_syscall;
```

Add the build runtime to the disk image.


## Using this with gem5

gem5 scripts are available in [configs-riscv-keystone](configs-riscv-keystone/).

The command to use:

```sh
build/RISCV/gem5.opt  configs-riscv-keystone/run_trusted.py [path to fw_payload.elf] [path to rootfs.ext2] [cpu type] [number of cores] [rv8 benchmark name]
```

Note that there are some kernel command line arguments passed in the above scripts that are needed to run keystone on gem5.

**Note:** You can also look at the instructions to compile/build each individual artifact in `launch_keystone_experiments.py` script in this repo.

# Keystone Runs in gem5 using gem5art


If you want to do run Keystone experiments using `gem5art` run:

```sh
GEM5ART_DB="[path to the mongodb database]" python3 launch_keystone_experiments.py
```

`GEM5ART_DB` by default will point to a mongodb database on local system.

For DArchr:

```sh
GEM5ART_DB="mongodb://glacier.cs.ucdavis.edu" python3 launch_keystone_experiments.py
```

## Citation

```
@inproceedings{akram21carrv,
  title={Enabling Design Space Exploration for RISC-V Secure Compute Environments},
  author={Akram, Ayaz and Akella, Venkatesh and Peisert, Sean and Lowe-Power, Jason},
  booktitle={Fifth Workshop on Computer Architecture Research with RISC-V (CARRV 2021)},
  pages={1--7},
  year={2021}
}
```