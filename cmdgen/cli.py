from jinja2 import Environment,FileSystemLoader,PackageLoader,StrictUndefined

import itertools
import os

__all__ = [
    'simplify_command_elements',
    'XMLGenerator',
    'CLICommand',
    'CLINode',
    'CLICommandParam',
    'CLIDelimiter',
    'CLIString',
    'CLIInt',
    'CLIEnum',
    'CLICustomType'
]

def safe_makefirs(path):
    try:
        os.makedirs(path)
        return True
    except OSError:
        return False

class XMLGenerator(object):
    def __init__(self,out_folder,**kwargs):
        self.out_folder = out_folder
        safe_makefirs(self.out_folder)
        
        self.module = kwargs.get('module','TODO_MODULE')
        self.prefix = kwargs.get('prefix','')
        self.feature = kwargs.get('feature','TODO_FEATURE')

        #loader = FileSystemLoader([os.path.join(os.path.dirname(__file__),'templates')])
        loader = PackageLoader(__package__)
        self.environment = Environment(undefined=StrictUndefined,
                                       loader=loader,
                                       trim_blocks=True,
                                       lstrip_blocks=True)
        
        template = lambda filename: self.environment.get_template(filename)

        self.command_template = template('command.xml')
        self.node_template = template('node.xml')
        self.param_template = template('command_param.xml')
        self.string_template = template('string_type.xml')
        self.int_template = template('int_type.xml')
        self.enum_template = template('enum_type.xml')
        self.custom_type_template = template('custom_type.xml')
        self.contexts_template = template('contexts.xml')
        self.callbacks_template = template('callbacks.xml')
        self.list_template = template('list.xll')
        self.enum_definitions_template = template('enum_definitions.xml')
        self.features_template = template('features.xml')
        self.delphiscript_module_template = template('module.pas')        

        self.templates = {
            CLINode: self.node_template,
            CLICommandParam: self.param_template,
            CLIString: self.string_template,
            CLIInt: self.int_template,
            CLIEnum: self.enum_template,
            CLICustomType: self.custom_type_template,
        }

    def path_of(self,filename):
        return os.path.join(self.out_folder,filename)
    
    @staticmethod
    def gather_commands(contexts):
        return [
            command
            for context in contexts
            for command in contexts[context]
        ]
        
    @staticmethod       
    def gather_enums(commands):
        return {
            element.type 
            for command in commands
            for element in command.elements + command.params
            if type(element) == CLICommandParam and type(element.type) == CLIEnum            
        }

    @staticmethod
    def filter_invalid_commands(commands):
        def filter_callback(command):
            valid,reason = command.valid
            if not valid:
                print 'No XML would be generated for invalid command[%s]' % (command,)
                print 'Reason: %s' % (reason,)
                return False
            return True
        return filter(filter_callback,commands)
        
    def generate(self,contexts):
        contexts = {
            context:self.filter_invalid_commands(contexts[context])
            for context in contexts
        }

        commands = self.gather_commands(contexts)
        enums = self.gather_enums(commands)
        
        for command in commands:
            self.command_template.stream(**{
                'module': self.module,
                'name': command.name,
                'level': command.level,
                'nodes': command.elements,
                'params': command.params,
                'template_for': self.template_for,
            }).dump(self.path_of(command.filename + '.xml'))

        self.contexts_template.stream(**{
            'contexts': contexts,
        }).dump(self.path_of('contexts.xml'))
        
        self.callbacks_template.stream(**{
            'commands': commands,
        }).dump(self.path_of('callbacks.xml'))

        self.list_template.stream(**{
            'prefix': self.prefix,
            'commands': commands
        }).dump(self.path_of('list.xll'))
        
        if enums:
            self.enum_definitions_template.stream(**{
                'module': self.module,
                'enums': enums
            }).dump(self.path_of('enums.xml'))
            
        self.features_template.stream(**{
            'feature': self.feature,
            'commands': commands,
        }).dump(self.path_of('features.xml'))

        self.delphiscript_module_template.stream(**{
            'module': self.module,
            'commands': commands,
            'enums': enums,
        }).dump(self.path_of('module.pas'))

    def template_for(self,element):
        if type(element) not in self.templates:
            print 'Element',element
        return self.templates[type(element)]

def simplify_command_elements(elements):
    def join_nodes(key,val):
        if key == CLINode:
            return [reduce(lambda a,b:a+b,val)]
        return list(val)

    groups = [join_nodes(key,val) for key,val
              in itertools.groupby(elements,lambda x: x.__class__)
              if key != CLIDelimiter]
    elements = list(itertools.chain(*groups))
    
    #end_pairs = itertools.izip(elements[-2::-2],elements[-1::-2])
    
    #def pair_selector(a,b):
    #    return type(a)==CLINode and type(b)==CLICommandParam
    
    #key_param_pairs = itertools.takewhile(pair_selector,end_pairs)
    #print 'pairs',key_param_pairs
                      
    return elements

class CLIContext(object):
    def __init__(self,name,prompt=None):
        self.name = name
        self.prompt = prompt

    def __hash__(self):
        return hash(self.name)

    def __eq__(self,other):
        return self.name == other.name

    def __str__(self):
        return 'CLIContext(%s,%s)' % (self.name,self.prompt)
    __repr__ = __str__

class CLICommand(object):
    def __init__(self,elements,level=None):
        self.elements = simplify_command_elements(elements)
        self.name = '_'.join(i.name for i in self.elements if type(i) == CLINode)
        
        self.params = list(itertools.takewhile(lambda x: type(x) == CLICommandParam,self.elements[::-1]))[::-1]
        if len(self.params):
            self.elements = self.elements[:-len(self.params)]
        self.node_params = [e for e in self.elements if type(e) == CLICommandParam]

        if level is None:
            level = 15
        self.level = level

    @property
    def valid(self):
        if self.name == '':
            return False,'Not enough nodes'

        if type(self.elements[0]) != CLINode:
            return False,'First command element must be Node'

        all_nodes_mandatory = all(not e.optional for e 
                                  in self.elements 
                                  if type(e) == CLICommandParam)

        if not all_nodes_mandatory:
            return False,'Optional parameter must not be present among mandatory nodes'

        if len(self.params):
            access_groups = list(itertools.groupby(self.params,lambda x:x.optional))
            if len(access_groups) > 2:
                return False,'Parameters must be divided into maximum of two groups of [...Mandatory...] [...Optional...] and here we have %d' % (len(access_groups),)

            if len(access_groups) > 1 and access_groups[0][0]:
                return False,'First group of parameters must be Mandatory'
        
        param_names = set()
        for param in self.params + self.node_params:
            type_valid,error = param.type.valid
            if not type_valid:
                return False,'Parameter %s:' % (param.name,) + error

            if param.name in param_names:
                return False,'Parameter name[%s] is not unique among parameters of this command' % (param.name,)
            param_names.add(param.name)
            
            valid,error = param.valid
            if not valid:
                return False,error

        return True,None

    @property
    def filename(self):
        return self.name
        
    def __str__(self):
        return 'Command[%s]:(%s)(%s)' % (self.name,self.elements,self.params)
    __repr__ = __str__

class CLINode(object):
    def __init__(self,name):
        self.name = name

    def __str__(self):
        return 'Node(%s)' % (self.name,)
    __repr__  = __str__

    def __add__(self,other):
        return CLINode(self.name + other.name)


class CLICommandParam(object):
    restricted_names = [
        'string',
        'integer',
    ]

    def __init__(self,name,type,optional=False,positional=True):
        self.name = name
        self.key_name = name
        self.type = type
        self.optional = optional
        self.positional = positional

    @property
    def valid(self):
        return self.name not in self.restricted_names,'Parameter name cannot be one of the following reserved words: %s' % (self.restricted_names,)
        
    @property
    def access(self):
        return 'Optional' if self.optional else 'Mandatory'
        
    @property
    def status(self):
        return 'Positional' if self.positional else 'Key'
 
    def __str__(self):
        return 'Param%s%s(%s:%s)' % ('?' if self.optional else '',
                                   '' if self.positional else 'K',
                                   self.name,
                                   self.type)
    __repr__  = __str__


def name_generator(base):
    i = 0
    while True:
        yield '%s%d' % (base,i)
        i += 1    
    
class CLIEnum(object):
    delphiscript_type = 'integer'
    delphiscript_default_value = "0"
    delphiscript_free_format = None
    delphiscript_tostring_format = '%s'

    names = name_generator('enum')

    def __init__(self,name,members):
        if name is None:
            name = self.names.next()
        self.name = name
        self.members = members

    @property
    def valid(self):
        return True,None

    def __hash__(self):
        return hash('|'.join(self.members))

    def __str__(self):
        return 'CLIEnum[%s]%s' % (self.name,self.members)
    __repr__ = __str__

class CLIString(object):
    delphiscript_type = 'string'
    delphiscript_default_value = "''"
    delphiscript_free_format = None
    delphiscript_tostring_format = '%s'
    
    def __init__(self,max_length):
        self.max_length = max_length

    @property
    def valid(self):
        return True,None

    def __str__(self):
        return 'CLIString[%s]' % (self.max_length,)
    __repr__ = __str__

class CLIInt(object):
    delphiscript_type = 'integer'
    delphiscript_default_value = "0"
    delphiscript_free_format = None
    delphiscript_tostring_format = '%s'

    def __init__(self,min,max):
        self.min = min
        self.max = max

    @property
    def valid(self):
        return True,None

    def __str__(self):
        return 'CLIint[%s-%s]' % (self.min,self.max)
    __repr__ = __str__

class CLICustomType(object):
    tostring = '%s.toString()'
    free = '%s.free'

    known_types = {
        'Integer':           ('integer',   "0",                 None, None),
        'SignedInteger':     ('integer',   "0",                 None, None),
        'String':            ('string',    "''",                None, None),
        'IpV6address':       ('TInetAddr', "TInetAddr.Create()",free, tostring),
        'IpAddress':         ('TInetAddr', "TInetAddr.Create()",free, tostring),
        'VlanTag':           ('TVlanList', "TVlanList.Create()",free, tostring),
        'VlanRangeAll':      ('TVlanList', "TVlanList.Create()",free, tostring),
        'VlanRangeAll2':     ('TVlanList', "TVlanList.Create()",free, tostring),
        'ciscoVlanRange':    ('TVlanList', "TVlanList.Create()",free, tostring),
        'ciscoPortList':     ('TPortSet',  "TPortSet.Create()", free, tostring),
        'ciscoPort':         ('TPortSet',  "TPortSet.Create()", free, tostring),
        'ciscoPortVlanlist': ('TPortSet',  "TPortSet.Create()", free, tostring),
    }

    def __init__(self,name):
        self.name = name
        
        source = self.known_types.get(self.name,self.known_types['Integer'])

        [self.delphiscript_type,
         self.delphiscript_default_value,
         self.delphiscript_free_format,
         self.delphiscript_tostring_format] = source

    @property
    def valid(self):
        present = self.name in self.known_types
        if not present:
            return False,'Unknown type: %s' % (self.name,)
        return True,None

    def __str__(self):
        return 'CLICustomType[%s]' % (self.name,)
    __repr__ = __str__

class CLIDelimiter(object):
    def __str__(self):
        return 'Delimiter'
    __repr__  = __str__  

    @staticmethod
    def join(iterable):
        i = iter(iterable)
        result = []
        try:
            for j in i.next():
                result.append(j)
            while True:
                n = i.next()
                result.append(CLIDelimiter())
                for j in n:
                    result.append(j)
        except StopIteration:
            return result
