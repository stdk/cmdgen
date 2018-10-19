unit {{module}};

const
    c_{{module}}_debug = true;
{% if enums|length %}    
{% for enum in enums %}
{% for member in enum.members %}
    c_{{module}}_{{enum.name}}_{{member}} = {{loop.index}};
{% endfor %}
{% endfor %}

{% endif %}
{% for command in commands %}
function {{command.name}}: boolean;
var
{% for param in command.node_params + command.params %}
    {{param.name}}: {{param.type.delphiscript_type}};
    {% if param.optional %}
    {{param.name}}_present: boolean;
    {% endif %}
{% endfor %}
    param_type: integer;
    type_index: integer;
    ok: boolean;
begin
    if c_{{module}}_debug then writeln('{{command.name}} function');
    
    result := true;
    {% for param in command.node_params + command.params %}
    {% if param.type.delphiscript_default_value %}
    {{param.name}} := {{param.type.delphiscript_default_value}};
    {% endif %}
    {% endfor %}

    {% for param in command.node_params + command.params %}    
    param_type := cli.getParamValue('{{param.name}}', {{ param.name }}, type_index);
    if ( param_type <> paramTypeID_none_E ) then 
    begin
        {% if param.optional %}
        {{param.name}}_present := true;
        {% endif %}
        if c_{{module}}_debug then
        {% if param.optional %}
            writeln(format('param[{{param.name}}] present: [%s]',{{ param.type.delphiscript_tostring_format % (param.name,) }}));
        {% else %}
            writeln(format('{{param.name}}[%s]',{{ param.type.delphiscript_tostring_format % (param.name,) }}));
        {% endif %}
    end
    else
    begin
        {% if param.optional %}
        if c_{{module}}_debug then 
            writeln('param[{{param.name}}] is not present');
        {{param.name}}_present := false;
        {% else %}
        writeln('{{command.name}}: reading parameter {{param.name}} failed.');
        result := false;
        {% for param in command.node_params + command.params %}
        {% if param.type.delphiscript_free_format %}
        {{ param.type.delphiscript_free_format % (param.name,) }};
        {% endif %}
        {% endfor %}
        exit;
        {% endif %}
    end;
    {% endfor %}
    
    { logic goes here }
    
    {% for param in command.node_params + command.params %}
    {% if param.type.delphiscript_free_format %}
    {{ param.type.delphiscript_free_format % (param.name,) }};
    {% endif %}
    {% endfor %}
end;

{% endfor %}
end.