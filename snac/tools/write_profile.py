"""
Write a progenitor file into SNEC profiles.

Prerequisites:
PROGS: tool for handling supernova progenitor files.
See https://github.com/AstroBarker/progs.git

Current PROGS setup only supports Sukhbold 2016 progenitors. 
Extension to other progenitor files is simple, but feel free to reach out.

TODO: make smarter output paths. currently writes files to current working directory.

***** No mass cut is applied. *****

"""

import progs 
import numpy as np

# load in progenitor data for a given model 
model = "25.0"
progenitor = progs.prog.Prog(model, 's16', verbose=False)

# write SNEC hydro profile. Modify filename convention as desired.
# column setup: cell index   mass   radius   temperature   density   velocity   Ye   Omega
# first line contains the number of lines
fn = "s" + model + "_a1.25_exploding_hydro.snec"
num_lines = len(progenitor.table)
with open(fn, "w") as f:
    f.write( str(num_lines-1) + '\n')

    for i in range(1,num_lines):
        f.write( str(i) + " " + str(progenitor.table['mass'][i]) + " " + str(progenitor.table['radius'][i]) \
            + " " + str(progenitor.table['temperature'][i]) + " " + str(progenitor.table['density'][i]) \
            + " " + str(progenitor.table['velocity'][i]) + " " + str(progenitor.table['ye'][i]) \
            + " " + str(progenitor.table['ang_velocity'][i]) + '\n')

# write SNEC comps profile
# first line: num_lines, num_isotopes
# second line: mass number of all isotopes (only num_isotopes of them!!)
# charge numbers of all isotopes
# cell mass   cell radius   (Mass fraction of isotope i) for i=1,nisotopes
fn = "s" + model + "_a1.25_exploding_comps.snec"
with open(fn, "w") as f:
    f.write( str(num_lines-1) + " " + str(len(progenitor.network)) + '\n')
    f.write(' '.join([str(i) for i in progenitor.network['A']]) + '\n')
    f.write(' '.join([str(i) for i in progenitor.network['Z']]) + '\n')

    for i in range(1,num_lines):
        f.write( str(i) + " " + str(progenitor.table['mass'][i]) + " " + str(progenitor.table['radius'][i]) + " "\
           + ' '.join([str(j).replace('\n','') for j in progenitor\
                .table[progenitor.network['isotope']].iloc[[i]].values.tolist()])\
                .replace(']','').replace('[','').replace(',','') + '\n')