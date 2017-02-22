# cmdgen

Command generator written in python using ply library.
cmdgen provides a way to define a set of strings matching given expression with a syntax resembling many CLI command definitions. 
This project is similar in nature to generation of a strings matching given regular expression, though with a different syntax and stricter limitations intended to better match CLI concepts.

In addition to basical sequencing of nodes it supports mandatory and optional nodes, options, integer ranges, variables and nested comments.

Examples:

```
>>> from cmdgen import parse

>>> parse('ping {domain [a|b]|ipv6 addr|ipv4 addr}')
['ping domain', 'ping domain a', 'ping domain b', 'ping ipv6 addr', 'ping ipv4 addr']

>>> print '\n'.join(parse('$mode = {A|B}; $key_args = [mode1 $mode] [mode2 $mode]; cmd $key_args')))
cmd
cmd mode2 A
cmd mode2 B
cmd mode1 A
cmd mode1 A mode2 A
cmd mode1 A mode2 B
cmd mode1 B
cmd mode1 B mode2 A
cmd mode1 B mode2 B
```


