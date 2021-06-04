#!/bin/sh

# Copyright (c) 2020 The Regents of the University of California.
# SPDX-License-Identifier: BSD 3-Clause

/sbin/m5 readfile > script.sh
if [ -s script.sh ]; then
    # if the file is not empty, execute it
    chmod +x script.sh
    ./script.sh
    /sbin/m5 exit
fi
# otherwise, drop to the terminal
