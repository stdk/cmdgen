# cmdgen

Command generator written in python using ply library.

cmdgen provides a way to define a set of strings matching given expression with a syntax resembling many CLI command definitions. 

This project is similar in nature to the generation of strings that match given regular expression, though with a different syntax and stricter limitations intended to better match CLI concepts.

In addition to basical sequencing of nodes it supports mandatory and optional elements, options, integer ranges, variables and nested comments.

### Usage

Import 
```python
>>> from cmdgen import parse_into_options
```

cmdgen recognizes input string as a list of nodes and generates all strings that may be derived from it.

Obviously, when format string does not include any variance, cmdgen output would be no different from input:
```python
>>> parse_into_options('node1 node2 node3')
['node1 node2 node3']
```

To specify that something is optional of our format, curved brackets are used:
```python
>>> parse_into_options('node1 {node2} node3')
['node1 node3', 'node1 node2 node3']
```

As the opposite of optional brackets we use mandatory squared brackets:
```python
>>> parse_into_options('node1 [node2] node3')
['node1 node2 node3']
```

As you can see, mandatory brackets make no difference to a single node - you may just skip them in that case.

But we do have a purpose for them: squared and curved brackets may contain a list of options, separated by '|':
```python
>>> parse_into_options('[node1|node2] {node3|node4}')
['node1', 'node1 node3', 'node1 node4', 'node2', 'node2 node3', 'node2 node4']
```

Optional brackets have an additional feature to them, which is widely used in Panasonic switches CLI.
In addition to their normal mode of operation it is possible to follow optional brackets with a
parentheses containing an integer to change their meaning from "nothing or one of the options" 
they become "at least (number) of options from the given list":
```python
>>> parse_into_options('{one|two|three}(2)')
['one two','one three','two three','one two three']
```

For integers, it is possible to avoid tedious specification of all possible options and use ranges:
```python
>>> parse_into_options('1~5')
['1', '2', '3', '4', '5']
```

Some options of CLI commands may be used more than once or be worth enough to define them separately.

We can handle it with variables:

```python
>>> parse_into_options('$mode = [a|b|1~3]; set mode $mode')
['set mode a', 'set mode b', 'set mode 1', 'set mode 2', 'set mode 3']
```

Whitespaces are part of the syntax too. They can be used to achieve some otherwise impossible things:
```python

```

All these features may be combined to define commands of varied complexity:
```python
>>> parse_into_options('ping [domain {a|b}|ipv6 addr|ipv4 addr]')
['ping domain', 'ping domain a', 'ping domain b', 'ping ipv6 addr', 'ping ipv4 addr']
```
```python
>>> print '\n'.join(parse_into_options('$mode = [A|B]; $key_args = {mode1 $mode} {mode2 $mode}; cmd $key_args')))
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
Finally, to make complex command definitions understandable for other people we may use comments.

Consider the following file test1:
```
$mode = [shallow|deep]; (* algorithm execution mode *)
$conf = [router|switch]; (* system configuration to use *)
$user = [alice|bob|carol]; (* predefined users *)
$key_args = {-v} -m $mode -c $conf -u $user;
setup $key_args
```

```python
>>> print '\n'.join(parse_into_options(open('test1').read()))
setup -m shallow -c router -u alice
setup -m shallow -c router -u bob
setup -m shallow -c router -u carol
setup -m shallow -c switch -u alice
setup -m shallow -c switch -u bob
setup -m shallow -c switch -u carol
setup -m deep -c router -u alice
setup -m deep -c router -u bob
setup -m deep -c router -u carol
setup -m deep -c switch -u alice
setup -m deep -c switch -u bob
setup -m deep -c switch -u carol
setup -v -m shallow -c router -u alice
setup -v -m shallow -c router -u bob
setup -v -m shallow -c router -u carol
setup -v -m shallow -c switch -u alice
setup -v -m shallow -c switch -u bob
setup -v -m shallow -c switch -u carol
setup -v -m deep -c router -u alice
setup -v -m deep -c router -u bob
setup -v -m deep -c router -u carol
setup -v -m deep -c switch -u alice
setup -v -m deep -c switch -u bob
setup -v -m deep -c switch -u carol
```

### Notes

There are many opinions which brackets represent mandatory or optional elements. cmdgen attempts to be compatible 
with most CLI concepts by using mode parameter of its parse_into_options function. mode parameter accepts
string 'old' or 'new'. All examples in this README are made using new mode which is default. Old mode 
differs from it by reversing literals for mandatory and optional brackets.

```python
>>> parse_into_options('Using [old] mode ',mode='old')
['Using mode', 'Using old mode']
>>> parse_into_options('Using {new} mode ',mode='new')
['Using mode', 'Using new mode']
```

### CLI generation

