unit {{module}}

{% if enums|length %}
const
{% for enum in enums %}
{% for member in enum.members %}
    c_{{enum.name}}_{{member}} = {{loop.index}};
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
    ok: boolean;
begin
    result := true;
    
    writeln('{{command.name}} function');

    {% for param in command.node_params + command.params %}
    {% if param.type.delphiscript_default_value %}
    {{param.name}} := {{param.type.delphiscript_default_value}};
    {% endif %}
    {% endfor %}
        
    {% for param in command.node_params + command.params %}
    {% if param.optional %}
    param_type := cli.getParamTypeAndValue('{{param.name}}', {{ param.name }});
    if ( param_type <> paramTypeID_none_E ) then 
    begin
        writeln(format('param[{{param.name}}] present: [%s]',{{ param.type.delphiscript_tostring_format % (param.name,) }}));
        {{param.name}}_present := true;
    end
    else
    begin
        writeln('param[{{param.name}}] is not present');
        {{param.name}}_present := false;
    end;
    {% else %}
    ok := cli.getParamValue('{{param.name}}',{{param.name}});
    if ok then writeln(format('{{param.name}}[%s]',{{ param.type.delphiscript_tostring_format % (param.name,) }}))
    else writeln('reading {{param.name}} failed');
    {% endif %}    
    
    {% endfor %}
    {% for param in command.node_params + command.params %}
    {% if param.type.delphiscript_free_format %}
    {{ param.type.delphiscript_free_format % (param.name,) }};
    {% endif %}
    {% endfor %}
end;

{% endfor %}

end.