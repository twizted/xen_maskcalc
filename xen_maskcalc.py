#!/usr/bin/env python

#  Xen Mask Calculator - Calculate CPU masking information based on cpuid(1)
#  Copyright (C) 2017 Armando Vega
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import sys
import os


EAX1_MATCH = '0x00000001 0x00:'
EAX7_MATCH = '0x00000007 0x00:'
EXP_LINELN = 76


def get_register_mask(regs):
    """ Take a list of register values and return the calculated mask """
    reg_n = len(regs)
    mask = ''
    for idx in range(32):
        counter = 0
        for reg in regs:
            counter += 1 if (reg & (1 << idx) > 0) else 0
        # if we have all 1s or all 0s we don't mask the bit
        if counter == reg_n or counter == 0:
            mask = mask + 'x'
        else:
            mask = mask + '0'
    # we calculated the mask in reverse, so we reverse it again
    return mask[::-1]


def print_xl_masking_config(nodes):
    """ Take a dictionary of nodes containing their registers and print out CPUID masking configuration for xl """
    nomasking = 'x' * 32
    eax1_ecx_regs = []
    eax1_edx_regs = []
    eax7_ebx_regs = []
    eax7_ecx_regs = []
    for node in nodes:
        eax1_ecx_regs.append(nodes[node]['eax1_ecx'])
        eax1_edx_regs.append(nodes[node]['eax1_edx'])
        eax7_ebx_regs.append(nodes[node]['eax7_ebx'])
        eax7_ecx_regs.append(nodes[node]['eax7_ecx'])
    # Get masks for the EAX1 and EAX7 registers
    eax1_ecx_mask = get_register_mask(eax1_ecx_regs)
    eax1_edx_mask = get_register_mask(eax1_edx_regs)
    eax7_ebx_mask = get_register_mask(eax7_ebx_regs)
    eax7_ecx_mask = get_register_mask(eax7_ecx_regs)
    # Build the xl CPUID config
    cpuid_config = 'cpuid = [\n    "0x00000001:ecx=' + eax1_ecx_mask
    if eax1_edx_mask != nomasking:
        cpuid_config += ',edx=' + eax1_edx_mask
    cpuid_config += '",\n'
    cpuid_config += '    "0x00000007,0x00:ebx=' + eax7_ebx_mask
    if eax7_ecx_mask != nomasking:
        cpuid_config += ',ecx=' + eax7_ecx_mask
    cpuid_config += '"\n'
    cpuid_config += ']'
    print(cpuid_config)


def print_verbose_masking_info(nodes):
    """ Take a dictionary of nodes containing their registers and print out verbose mask derivation information """
    eax1_ecx_regs = []
    eax1_edx_regs = []
    eax7_ebx_regs = []
    eax7_ecx_regs = []
    for node in nodes:
        eax1_ecx_regs.append(nodes[node]['eax1_ecx'])
        eax1_edx_regs.append(nodes[node]['eax1_edx'])
        eax7_ebx_regs.append(nodes[node]['eax7_ebx'])
        eax7_ecx_regs.append(nodes[node]['eax7_ecx'])

    print("")
    print('== Detailed mask derivation info ==')
    print("")

    print('EAX1 ECX registers:')
    for reg in eax1_ecx_regs:
        print('{0:032b}'.format(reg))
    print('================================')
    print(get_register_mask(eax1_ecx_regs))

    print("")
    print('EAX1 EDX registers:')
    for reg in eax1_edx_regs:
        print('{0:032b}'.format(reg))
    print('================================')
    print(get_register_mask(eax1_edx_regs))

    print("")
    print('EAX7,0 EBX registers:')
    for reg in eax7_ebx_regs:
        print('{0:032b}'.format(reg))
    print('================================')
    print(get_register_mask(eax7_ebx_regs))

    print("")
    print('EAX7,0 ECX registers:')
    for reg in eax7_ecx_regs:
        print('{0:032b}'.format(reg))
    print('================================')
    print(get_register_mask(eax7_ecx_regs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A utility that calculates a XEN CPUID difference mask')
    parser.add_argument('node_files', nargs='*', help='Filenames of XEN node CPUID outputs')
    parser.add_argument('-v', '--verbose', action='store_true', help='Get detailed mask derivation information')
    args = parser.parse_args()
    if len(args.node_files) < 2:
        print('Need at least 2 files to do the comparison!')
        parser.print_help()
        sys.exit(1)
    
    nodes = dict()
    for node in args.node_files:
        if os.path.isfile(node):
            try:
                f = open(node)
            except IOError as e:
                print("I/O error({0}): {1}".format(e.errno, e.strerror))
                sys.exit(1)
            else:
                lines = [line.strip() for line in f]
                eax1 = ''
                eax7 = ''
                # try to match the lines containing interesting registers
                # EAX1 - Processor Info and Feature Bits
                # EAX7 - Extended features
                for line in lines:
                    if line.startswith(EAX1_MATCH):
                        eax1 = line
                    elif line.startswith(EAX7_MATCH):
                        eax7 = line
                # if we get garbled data we should probably just give up
                if len(eax1) < EXP_LINELN or len(eax7) < EXP_LINELN:
                    print('ERROR: invalid data format in file : ' + node)
                    sys.exit(1)

                # check if we can actually parse the strings into integers
                try:
                    eax1_ecx = int(eax1.split()[4].split('=')[1], 0)
                    eax1_edx = int(eax1.split()[5].split('=')[1], 0)
                    eax7_ebx = int(eax7.split()[3].split('=')[1], 0)
                    eax7_ecx = int(eax7.split()[4].split('=')[1], 0)
                except ValueError:
                    print('ERROR: invalid data format in file: ' + node)
                    sys.exit(1)

                nodes[node] = dict()
                nodes[node]['eax1_ecx'] = eax1_ecx
                nodes[node]['eax1_edx'] = eax1_edx
                nodes[node]['eax7_ebx'] = eax7_ebx
                nodes[node]['eax7_ecx'] = eax7_ecx
                f.close()
        else:
            print('File not found: ' + node)
            sys.exit(1)

    print_xl_masking_config(nodes)
    if args.verbose:
        print_verbose_masking_info(nodes)
