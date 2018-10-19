import pdb
import cmdgen
import sys

sys.argv += ['-i', "l2tp_redirect_commands.txt"]

pdb.run('cmdgen.main()')