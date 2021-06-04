#!/usr/bin/env python3

# This is a job launch script to run experiments
# using RISCV's Keystone TEE on gem5
# Other details of these experiments can also be
# found in the CARRV paper "Enabling Design Space Exploration
# for RISC-V Secure Compute Environments"

import os
import sys
from uuid import UUID
from itertools import starmap
from itertools import product

from gem5art.artifact.artifact import Artifact
from gem5art.run import gem5Run
from gem5art.tasks.tasks import run_job_pool


experiments_repo = Artifact.registerArtifact(
    command = 'https://github.com/darchr/Keystone-experiments.git',
    typ = 'git repo',
    name = 'Keystone-experiments',
    path =  './',
    cwd = '../',
    documentation = 'main experiments repo to run keystone experiments on gem5'
)

gem5_repo = Artifact.registerArtifact(
    command = 'git clone https://gem5.googlesource.com/public/gem5',
    typ = 'git repo',
    name = 'gem5',
    path =  'gem5/',
    cwd = './',
    documentation = 'cloned gem5 from googlesource and checked out develop version (as around June 1)'
)

gem5_binary = Artifact.registerArtifact(
    command = '''cd gem5;
    git checkout 62610709df76f4b544769cbbb;
    git apply ../0001-arch-riscv-add-pma-pmp-checks-during-page-table-walk.patch;
    git apply ../0002-arch-riscv-Update-the-way-a-valid-virtual-address-is.patch;
    scons build/RISCV/gem5.opt -j8
    ''',
    typ = 'gem5 binary',
    name = 'gem5',
    cwd = 'gem5/',
    path =  'gem5/build/RISCV/gem5.opt',
    inputs = [gem5_repo, experiments_repo],
    documentation = 'gem5 binary based on develop version (as around June 1) and applied two patches which are currently under review on gerrit'
)

m5_binary = Artifact.registerArtifact(
    command = 'scons -C util/m5 build/riscv/out/m5',
    typ = 'binary',
    name = 'm5',
    path =  'gem5/util/m5/build/riscv/out/m5',
    cwd = 'gem5/util/m5',
    inputs = [gem5_repo,],
    documentation = 'm5 utility'
)

keystone_repo = Artifact.registerArtifact(
    command = 'git clone https://github.com/keystone-enclave/keystone.git',
    typ = 'git repo',
    name = 'keystone',
    cwd = './',
    path = 'keystone/',
    inputs = [],
    documentation = 'Keystone enclave github repo'
)

eyrie_runtime = Artifact.registerArtifact(
    command = '''cd keystone;
    git checkout a1842a1ec959c4e40ffd55091795bb577894c545;
    ./fast-setup.sh;
    source source.sh;
    mkdir build;
    cd build;
    cmake ..;
    make -j64;
    cd keystone/build/examples/tests/runtime/src/eyrie-test-eyrie;
    ./build.sh paging;
    ''',
    typ = 'binary',
    name = 'eyrie runtime',
    path =  'keystone/build/examples/tests/runtime/src/eyrie-test-eyrie/eyrie-rt',
    cwd = './',
    inputs = [keystone_repo,],
    documentation = 'Eyrie runtime with paging enabled to run rv8 benchmarks'
)

keystone_driver = Artifact.registerArtifact(
    command = '''cd keystone;
    git checkout a1842a1ec959c4e40ffd55091795bb577894c545;
    ./fast-setup.sh;
    source source.sh;
    mkdir build;
    cd build;
    cmake ..;
    make -j64;
    ''',
    typ = 'binary',
    name = 'keystone driver',
    path =  'keystone/build/linux-keystone-driver.build/keystone-driver.ko',
    cwd = './',
    inputs = [keystone_repo,],
    documentation = 'Keystone linux driver'
)

test_runner = Artifact.registerArtifact(
    command = '''cd keystone;
    git checkout a1842a1ec959c4e40ffd55091795bb577894c545;
    ./fast-setup.sh;
    source source.sh;
    mkdir build;
    cd build;
    cmake ..;
    make -j64;
    ''',
    typ = 'binary',
    name = 'test runner',
    path =  'keystone/build/examples/tests/test-runner',
    cwd = './',
    inputs = [keystone_repo,],
    documentation = 'Test (untrusted) runner application'
)

musl_tool = Artifact.registerArtifact(
    command = '''git clone https://github.com/rv8-io/musl-riscv-toolchain.git;
    cd musl-riscv-toolchain;
    cp ../bootstrap_musl_riscv.sh bootstrap.sh;
    sh bootstrap.sh riscv64;
    ''',
    typ = 'git repo',
    name = 'test runner',
    path =  'musl-riscv-toolchain/',
    cwd = './',
    inputs = [experiments_repo,],
    documentation = 'musl riscv toolchain to compile rv8 benchmarks'
)

rv8_bench = Artifact.registerArtifact(
    command = '''https://github.com/keystone-enclave/rv8-bench.git;
    cd rv8-bench;
    git checkout keystone;
    export PATH=$PATH:/opt/riscv/musl-riscv-toolchain-8.2.0-1/bin/;
    make
    ''',
    typ = 'git repo',
    name = 'rv8 source',
    path =  'rv8-bench/',
    cwd = './',
    inputs = [experiments_repo, musl_tool],
    documentation = 'rv8 benchmarks'
)

disk_image = Artifact.registerArtifact(
    command = '''cd keystone;
    git checkout a1842a1ec959c4e40ffd55091795bb577894c545;
    ./fast-setup.sh;
    source source.sh;
    mkdir build;
    cd build;
    cmake ..;
    make -j64;
    cd buildroot.build/images/;
    mkdir mnt;
    mount -o loop rootfs.ext2 mnt/;
    cd mnt/root/;
    cp ../../../../examples/tests/runtime/src/eyrie-test-eyrie/eyrie-rt . ;
    cp -r ../../../../../../keystone-bench/rv8-bench/bin/riscv64/ . ;
    cp ../../../../../../runscript.sh . ;
    cp ../../../../examples/tests/test-runner . ;
    cp ../../../../../../inittab ../etc/inittab ;
    rm ../etc/init.d/S40network ;
    cp ../../../../../../gem5/util/m5/build/riscv/out/m5 /sbin/m5;
    cd ../../ ;
    umount mnt/;
    ''',
    typ = 'disk image',
    name = 'keystone-disk',
    cwd = './',
    path = 'keystone/build/buildroot.build/images/rootfs.ext2',
    inputs = [experiments_repo, keystone_repo, m5_binary, eyrie_runtime, rv8_bench,],
    documentation = 'Keystone disk image with RV8 benchamarks in addition to other needed components/changes to run the experiments'
)

linux_repo = Artifact.registerArtifact(
    command = '''cd keystone;
    git checkout a1842a1ec959c4e40ffd55091795bb577894c545;
    ./fast-setup.sh;
    ''',
    typ = 'git repo',
    name = 'linux source',
    path =  'keystone/linux',
    inputs = [keystone_repo,],
    cwd = './',
    documentation = 'Linux kernel source (v5.7)'
)

linux_binary = Artifact.registerArtifact(
    command = '''cd keystone;
    git checkout a1842a1ec959c4e40ffd55091795bb577894c545;
    ./fast-setup.sh;
    source source.sh;
    mkdir build;
    cd build;
    cmake ..;
    make -j64;
    ''',
    typ = 'binary',
    name = 'vmlinux',
    path =  'keystone/build/linux.build/vmlinux',
    inputs = [keystone_repo,linux_repo],
    cwd = './',
    documentation = 'linux kernel binary which will be embedded into opensbi'
)

firmware_binary = Artifact.registerArtifact(
    command = '''cd keystone;
    git checkout a1842a1ec959c4e40ffd55091795bb577894c545;
    ./fast-setup.sh;
    source source.sh;
    mkdir build;
    cd build;
    cmake ..;
    make -j64;
    ''',
    typ = 'binary',
    name = 'firmware',
    path =  'keystone/build/sm.build/platform/generic/firmware/fw_payload.elf',
    inputs = [linux_binary, keystone_repo],
    cwd = './',
    documentation = 'opensbi with keystone security monitor + linux kernel'
)

if __name__ == "__main__":
    num_cpus = ['1']
    cpu_types = ['timing','minor']
    benchmarks = ['aes.O3', 'bigint.O3', 'dhrystone.O3', 'miniz.O3', 'norx.O3', 'primes.O3', 'qsort.O3', 'sha512.O3']
    configs = ['untrusted', 'trusted']

    def createRun(config, cpu, num_cpu, bench):

        return gem5Run.createFSRun(
            'keystone experiments with gem5 for carrv',
            'gem5/build/RISCV/gem5.opt',
            'configs-riscv-keystone/run_{}.py'.format(config),
            'results/{}/{}/{}/{}'.format(config, bench, cpu, num_cpu),
            gem5_binary, gem5_repo, experiments_repo,
            'keystone/build/sm.build/platform/generic/firmware/fw_payload.elf',
            'keystone/build/buildroot.build/images/rootfs.ext2',
            firmware_binary, disk_image,
            cpu, num_cpu, bench,
            timeout = 20*60*60 #20 hours
            )

    # For the cross product of tests, create a run object.
    runs = starmap(createRun, product(configs, cpu_types, num_cpus, benchmarks))
    # Run all of these experiments in parallel
    run_job_pool(runs)