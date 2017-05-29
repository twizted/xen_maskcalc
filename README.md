XEN CPUID mask calculator
=========================

A script that uses raw `cpuid(1)` output to calculate the masks needed to use the servers with different CPUs for the 
same XEN cluster. This is needed if we intend to migrate VMs over CPUs with different instruction sets.
It generates configuration statements for the `xl` toolkit. To use simply clone this repo.

# Getting help

```bash
~$ ./xen_maskcalc.py -h
usage: xen_maskcalc.py [-h] [-v] [node_files [node_files ...]]

A utility that calculates a XEN CPUID difference mask

positional arguments:
  node_files     Filenames of XEN node CPUID outputs

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Get detailed mask derivation information
```

# Using it
We have to provide the raw `cpuid(1)` output as files, which are passed to the script as arguments, e.g.:

```bash
server1~$ cpuid -1r > node1
server2~$ cpuid -1r > node2
server3~$ cpuid -1r > node3

~$ ./xen_maskcalc.py node1 node2 node3
cpuid = [
    "0x00000001:ecx=x00xxxxxx0xxxxxxxxx00xxxxxxxxxxx",
    "0x00000007,0x00:ebx=xxxxxxxxxxxxxxxxxx00x0000x0x0x00"
]
```

With the `-v` or `--verbose` argument you get detailed mask derivation information, e.g.:

```bash
~$ ./xen_maskcalc.py -v node1 node2
cpuid = [
    "0x00000001:ecx=x00xxxxxx0xxxxxxxxx00xxxxxxxxxxx",
    "0x00000007,0x00:ebx=xxxxxxxxxxxxxxxxxx00x0000x0x0x00"
]

== Detailed mask derivation info ==

EAX1 ECX registers:
01111111111111101111101111111111
00011111101111101110001111111111
================================
x00xxxxxx0xxxxxxxxx00xxxxxxxxxxx

EAX1 EDX registers:
10111111111010111111101111111111
10111111111010111111101111111111
================================
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

EAX7,0 EBX registers:
00000000000000000011011110101011
00000000000000000000000000000000
================================
xxxxxxxxxxxxxxxxxx00x0000x0x0x00

EAX7,0 ECX registers:
00000000000000000000000000000000
00000000000000000000000000000000
================================
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

```
