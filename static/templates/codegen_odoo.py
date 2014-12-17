# -*- coding: utf-8 -*-
import re

import sys, dia, os
import jinja2, zipfile, string, types

# dia.diagrams()[0].data

_py_header = """# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{% block content %}
{% endblock %}
"""

_py_openerp = """{% include 'header.py' ignore missing %}
# noinspection PyStatementEffect
{
        "name" : "{{module}}",
        "version" : "0.1",
        "author" : "Odoo",
        "website" : "http://www.odoo.com",
        "category" : "Unknown",
        "description": \"\"\"  \"\"\",
        "depends" : ['base'],
        "data" : [
                'security/ir.model.access.csv',
                'views/menu.xml',
                {% for pkg in packages -%}
                'views/{{pkg}}.xml',
                {%- endfor %}
        ],
        "demo" : [ ],
        "installable": True
}
"""

_py_models_init = """{% include 'header.py' ignore missing %}
{% for pack in packages -%}
from . import {{pack}}
{% endfor %}
"""

_py_package = """{% include 'header.py' ignore missing %}

from openerp import models, fields, api, tools, _
from openerp.osv import fields as fields_old
import openerp.addons.decimal_precision as dp

{% for model in models %}
class {{model.class_name}}({% if model.abstract %}models.AbstractModel{% else %}models.Model{% endif %}):
    _name = '{{model.class_id}}'
    {% if model.parents_class_list %}_inherit = {{model.parents_class_list}}{% endif %}
    {% if model.inherits %}_inherits = {{model.inherits_class_dict}}{% endif %}
    {% if model.comment %}_description = '{{model.comment}}'{% endif %}
    {% if model.handle_attribute %}_order = '{{model.handle_attribute.name}}' {% endif %}

    {% for field in model.attributes -%}
    {{field.name}} = {{field}}
    {% endfor -%}

    {%- for definition in model.clips.values() %}
    {{definition}}
    {% endfor -%}

    {%- for operation in model.operations %}
    {{ operation.sugar() }}
    def {{ operation.scope() }}{{ operation.name }}({{ operation.self() }}{{ operation.param_list() }}):
        \"\"\"
        {{ operation.comment }}
        {%- for param in operation.params %}
        @{{ param.name }}: <{{ param.type|default('Unknown') }}> {{ param.comment }}
        {% endfor -%}
        @return <{{ operation.type }}>
        \"\"\"
        raise NotImplementedError
    {% endfor -%}

{% endfor %}
"""

_csv_security = """"id","name","model_id:id","group_id:id","perm_read","perm_write","perm_create","perm_unlink"
{% if data.groups %}
{% for group in data.groups -%}
{% for model in data.class_map.values() -%}
"access_{{group|cleargroup}}_{{model|dot2dashed}}","{{model}}","model_{{model|dot2dashed}}","{{group}}",1,0,0,0
{%endfor %}
{%- endfor %}
{% else %}
{%- for model in data.class_map.values() -%}
"access_{{model|dot2dashed}}","{{model}}","model_{{model|dot2dashed}}","base.group_user",1,0,0,0
{% endfor %}
{% endif %}
"""

_xml_base = """<?xml version="1.0"?>
<openerp>
    <data>
        {% block content %}
        {% endblock %}
    </data>
</openerp>
"""

_xml_view_full = """
{%- extends 'base.xml' %}
{% import 'fields.xml' as field %}

{% block content %}

<menuitem name="{{package.name.capitalize()}}" id="{{module}}_{{package.name}}_menu_root" parent="{{module}}_menu_root"/>

{% for model in models %}
<!-- begin model: {{model.class_name}}({{model.class_id}}) -->
<record model="ir.ui.view" id="{{model.class_id|dot2dashed}}_tree_view">
    <field name="name">{{model.class_id}}.tree</field>
    <field name="model">{{model.class_id}}</field>
    <field name="arch" type="xml">
        {{ field.tree_tag(model) }}
    </field>
</record>

<record model="ir.ui.view" id="{{model.class_id|dot2dashed}}_form_view">
    <field name="name">{{model.class_id}}.form</field>
    <field name="model">{{model.class_id}}</field>
    <field name="arch" type="xml">
        {{ field.form_tag(model) }}
    </field>
</record>

<record model="ir.actions.act_window" id="act_{{model.class_id|dot2dashed}}">
    <field name="name">{{model.class_name}}</field>
    <field name="res_model">{{model.class_id}}</field>
    <field name="view_type">form</field>
    <field name="view_mode">tree,form</field>
    <field name="help" type="html">
        <p class="oe_view_nocontent_create">
            Click to create a new {{model.class_name}}.
        </p>
        <p>

        </p>
    </field>
</record>

<menuitem name="{{model.class_name}}" id="menu_{{model.class_id|dot2dashed}}" parent="{{module}}_{{package.name}}_menu_root" action="act_{{model.class_id|dot2dashed}}" />
<!-- end model: {{model.class_name}} -->
{% endfor %}

{% endblock %}
"""

_xml_fields = """
{% macro tree_tag(model, editable=False, extra='') -%}
        <tree string="{{model.class_name}}" {% if editable %}editable="{{editable}}"{% endif %} {{extra}} >
            {% for attr in model.view_tree_attributes -%}
            <field name="{{attr.name}}" />
            {% endfor -%}
        </tree>
{%- endmacro %}

{% macro form_field(model, field) -%}
    {% if field.type in ["Many2many", "One2many"] %}
    <field name="{{field.name}}" mode="tree" {% if field.options['widget'] %}widget="{{field.options['widget']}}"{% endif %}>
        {{ tree_tag(field.options.related_class, editable="bottom") }}
    </field>
    {% else -%}
    <field name="{{field.name}}" {% if field.options['widget'] %}widget="{{field.options['widget']}}"{% endif %}/>
    {%- endif %}
{%- endmacro %}



{% macro form_tag(model) -%}
    <form string="{{model.class_name}}" version="7.0">
        <sheet>
            <group col="4">
                {% for attr in model.view_form_attributes -%}
                    {% if attr.type not in ["Many2many", "One2many"] %}
                       {{ form_field(model, attr) }}
                    {% endif %}
                {% endfor -%}
            </group>

            {% for attr in model.view_form_attributes -%}
                {% if attr.type in ["Many2many", "One2many"] %}
                    {{ form_field(model, attr) }}
                {% endif %}
            {% endfor -%}
        </sheet>
    </form>
{% endmacro -%}

"""

_xml_view_menu = """
{%- extends 'base.xml' %}

{% block content %}
    <menuitem name="{{module.capitalize()}}" id="{{module}}_menu_root" />
{% endblock %}
"""

_method_get_set_image = """

    @api.multi
    def _get_image(self, name, args):
        return dict((p.id, tools.image_get_resized_images(p.{{image_field}})) for p in self)

    @api.one
    def _set_image(self, name, value, args):
        return self.write({'{{image_field}}': tools.image_resize_image_big(value)})

    @api.multi
    def _has_image(self, name, args):
        return dict((p.id, bool(p.{{image_field}})) for p in self)

    _columns = {
       'image_medium': fields_old.function(_get_image, fnct_inv=_set_image,
            string="Medium-sized image", type="binary", multi="_get_image",
            store={
                '{{model.class_id}}': (lambda self, cr, uid, ids, c={}: ids, ['{{image_field}}'], 10),
            },
            help="Medium-sized image. It is automatically "\\
                 "resized as a 128x128px image, with aspect ratio preserved. "\\
                 "Use this field in form views or some kanban views."),
        'image_small': fields_old.function(_get_image, fnct_inv=_set_image,
            string="Small-sized image", type="binary", multi="_get_image",
            store={
                '{{model.class_id}}': (lambda self, cr, uid, ids, c={}: ids, ['{{image_field}}'], 10),
            },
            help="Small-sized image. It is automatically "\\
                 "resized as a 64x64px image, with aspect ratio preserved. "\\
                 "Use this field anywhere a small image is required."),
        'has_image': fields_old.function(_has_image, type="boolean"),
    }
"""

_method_get_set_image_new = """
    @api.one
    def _get_image(self):
        self.image_medium = tools.image_resize_image_medium(self.{{image_field}})
        self.image_small = tools.image_resize_image_small(self.{{image_field}})

    @api.one
    def _set_image(self, name, value, args):
        self.{{image_field}} = tools.image_resize_image_big(value)
"""

_field_method_compute = """
    @api.one
    @api.depends({{depends}})
    def {{name}}(self):
        self.{{field}} = False
"""

_field_method_inverse = """
    @api.one
    def {{name}}(self):
        self.{{field}} = True
"""

_field_method_search = """
    def {{name}}(self, operator, value):
        if operator == 'like':
            operator = 'ilike'
        return [('name', operator, value)]
"""

templates = {
    'fields.xml': _xml_fields,
    'header.py': _py_header,
    'base.xml': _xml_base,
    'view.xml': _xml_view_full,
    'menu.xml': _xml_view_menu,
    '__openerp__.py': _py_openerp,
    '__init__.py': _py_models_init,
    'models/package.py': _py_package,
    'models/__init__.py': _py_models_init,
    'security/ir.model.access.csv': _csv_security,

    'methods/get_set_image': _method_get_set_image,
    'methods/field_method_inverse': _field_method_inverse,
    'methods/field_method_compute': _field_method_compute,
    'methods/field_method_search': _field_method_search,
}

env = jinja2.Environment(loader=jinja2.DictLoader(templates))

env.filters['dot2dashed'] = lambda x: x.replace('.', '_')
env.filters['dot2name'] = lambda x: ''.join([s.capitalize() for s in x.split('.')])
env.filters['cleargroup'] = lambda x: x.replace('.', '_')


class DiaPackage:
    def __init__(self, obj=None, name=None, context=None):
        self.obj = obj
        self.context = context
        self.depends = []
        self.name = name
        if obj:
            self.name = obj.properties['name'].value
        self.classes = []

    @classmethod
    def is_valid_for_object(cls, obj):
        return obj and obj.type.name == 'UML - LargePackage'

    def __add__(self, other):
        self.classes.append(other)

    def __iter__(self):
        return self.classes

    def __str__(self):
        return self.name


class DiaOperation:
    VISIBILITY_PUBLIC = 0
    VISIBILITY_PRIVATE = 1
    VISIBILITY_PROTECTED = 2
    VISIBILITY_IMPLEMENTATION = 3

    def __init__(self, klass, obj):
        self.klass = klass
        self.obj = obj
        self.params = []
        self.__process()

    def __process(self):
        self.name, self.type, self.comment, self.stereotype, self.visibility, self.inheritance_type, self.class_scope, self.query, params = self.obj

        self.params = []
        for par in params:
            self.params.append({
                'name': par[0],
                'type': par[1],
                'default': par[2],
                'comment': par[3],
                'visibility': par[4]
            })

    def param_list(self):
        return (', ' if self.params else '') + (', '.join(['{name}{default}'.format(name=param.get('name'), default='={value}'.format(value=param.get('default')) if param.get('default') else '') for param in self.params]))

    def sugar(self):
        if self.class_scope:
            return '@classmethod'
        if self.stereotype:
            return '@api.{type}'.format(type=self.stereotype)
        return ''

    def self(self):
        if self.class_scope:
            return 'cls'
        return 'self'

    def scope(self):
        if self.visibility == self.VISIBILITY_PUBLIC:
            return ''
        return '_'


class DiaUMLAssociation:

    DIRECTION_NONE = 0
    DIRECTION_A_TO_B = 1
    DIRECTION_B_TO_A = 2

    MULTIPLICITY_ONE = '1'
    MULTIPLICITY_MULTI = '*'

    ASSOCIATION_TYPE_NONE = 0
    ASSOCIATION_TYPE_ASSOCIATION = 1
    ASSOCIATION_TYPE_COMPOSITION = 2

    def __init__(self, obj, context=None):
        self.obj = obj
        self.context = context
        self.class_a = False
        self.class_b = False

    @classmethod
    def is_valid_for_object(cls, obj):
        return obj.type.name == 'UML - Association'

    #valid values ['name', 'direction', 'show_direction', 'assoc_type', 'help', 'role_a', 'multipicity_a', 'visibility_a', 'show_arrow_a', 'help', 'role_b', 'multipicity_b', 'visibility_b', 'show_arrow_b', 'obj_pos', 'obj_bb', 'meta', 'orth_points', 'orth_orient', 'orth_autoroute', 'text_colour', 'line_colour']
    def __getattr__(self, item):
        if item in self.obj.properties.keys():
            return self.obj.properties[item].value

    @property
    def multipicity_a(self):
        val = self.obj.properties['multipicity_a'].value
        if val:
            return val
        return 1

    @property
    def multipicity_b(self):
        val = self.obj.properties['multipicity_b'].value
        if val:
            return val
        return 1

    def get_classes_order(self, direction=None):
        dirmap = {self.DIRECTION_NONE: None, self.DIRECTION_A_TO_B: [self.class_a, self.class_b], self.DIRECTION_B_TO_A: [self.class_b, self.class_a]}
        return dirmap[direction and direction or self.direction]

    def get_class_info_by_order(self, direction=DIRECTION_A_TO_B):
        has_order = {self.DIRECTION_NONE: False, self.DIRECTION_A_TO_B: True, self.DIRECTION_B_TO_A: True}[direction and direction or self.direction]
        classes = {self.DIRECTION_NONE: None, self.DIRECTION_A_TO_B: [self.class_a, self.class_b], self.DIRECTION_B_TO_A: [self.class_b, self.class_a]}[direction and direction or self.direction]
        multiplicity = {self.DIRECTION_NONE: None, self.DIRECTION_A_TO_B: [self.multipicity_a, self.multipicity_b], self.DIRECTION_B_TO_A: [self.multipicity_b, self.multipicity_a]}[direction and direction or self.direction]
        visibility = {self.DIRECTION_NONE: None, self.DIRECTION_A_TO_B: [self.visibility_a, self.visibility_b], self.DIRECTION_B_TO_A: [self.visibility_b, self.visibility_a]}[direction and direction or self.direction]
        role = {self.DIRECTION_NONE: None, self.DIRECTION_A_TO_B: [self.role_a, self.role_b], self.DIRECTION_B_TO_A: [self.role_b, self.role_a]}[direction and direction or self.direction]
        return has_order and [
            {
                'class': classes[0],
                'multiplicity': multiplicity[0],
                'visibility': visibility[0],
                'role': role[0],
            }, {
                'class': classes[1],
                'multiplicity': multiplicity[1],
                'visibility': visibility[1],
                'role': role[1],
            }
        ] or False

    def process(self):
        if self.obj.handles[0].connected_to and self.obj.handles[0].connected_to.object and DiaClass.is_valid_for_object(self.obj.handles[0].connected_to.object):
            info_a = DiaClass.name2class(self.obj.handles[0].connected_to.object.properties['name'].value)
            self.class_a = self.context.models[info_a['class_id']]
        if self.obj.handles[1].connected_to and self.obj.handles[1].connected_to.object and DiaClass.is_valid_for_object(self.obj.handles[1].connected_to.object):
            info_b = DiaClass.name2class(self.obj.handles[1].connected_to.object.properties['name'].value)
            self.class_b = self.context.models[info_b['class_id']]

        info = self.get_class_info_by_order()

        if info:
            field0 = False

            if info[1]['multiplicity'] == self.MULTIPLICITY_ONE:
                field0 = DiaAttribute(info[0]['class'], process=False)
                field0.name = info[0]['role'] and info[0]['role'] or info[1]['class'].class_id.replace('.', '_') + '_id'
                field0.type = 'Many2one'
                field0.options['related_class'] = info[1]['class']
                field0.options['reverse_attribute'] = info[1]['role'] and info[1]['role'] or info[0]['class'].class_id.replace('.', '_') + '_ids'
                field0.visibility = info[0]['visibility']
                field0.params.append('"{model}"'.format(model=info[1]['class'].class_id))
                field0.params.append('{key}="{value}"'.format(key='string', value=info[1]['class'].class_name))
                field0.context.attributes.append(field0)

                if self.assoc_type in [self.ASSOCIATION_TYPE_ASSOCIATION, self.ASSOCIATION_TYPE_COMPOSITION]:
                    field0.params.append('required=True')

            elif info[1]['multiplicity'] == self.MULTIPLICITY_MULTI and (info[0]['multiplicity'] != self.MULTIPLICITY_MULTI or info[0]['class'] == info[1]['class']):
                field0 = DiaAttribute(info[0]['class'], process=False)
                field0.name = info[0]['role'] and info[0]['role'] or info[1]['class'].class_id.replace('.', '_') + '_ids'
                field0.type = 'One2many'
                field0.options['related_class'] = info[1]['class']
                field0.options['reverse_attribute'] = info[1]['role'] and info[1]['role'] or info[0]['class'].class_id.replace('.', '_') + '_id'
                field0.visibility = info[0]['visibility']
                field0.params.append('"{model}"'.format(model=info[1]['class'].class_id))
                link_field = info[1]['role'] and info[1]['role'] or info[1]['class'].class_id.replace('.', '_') + '_id'
                field0.params.append('"{field}"'.format(field=link_field))
                field0.params.append('{key}="{value}"'.format(key='string', value=info[1]['class'].class_name))
                field0.context.attributes.append(field0)
                

            if info[0]['multiplicity'] == self.MULTIPLICITY_ONE:
                field1 = DiaAttribute(info[1]['class'], process=False)
                field1.name = info[1]['role'] and info[1]['role'] or info[0]['class'].class_id.replace('.', '_') + '_id'
                field1.type = 'Many2one'
                field1.options['related_class'] = info[0]['class']
                field1.options['reverse_attribute'] = info[0]['role'] and info[0]['role'] or info[1]['class'].class_id.replace('.', '_') + '_ids'
                field1.visibility = info[1]['visibility']
                field1.params.append('"{model}"'.format(model=info[0]['class'].class_id))
                field1.params.append('{key}="{value}"'.format(key='string', value=info[0]['class'].class_name))
                field1.context.attributes.append(field1)

                if self.assoc_type in [self.ASSOCIATION_TYPE_COMPOSITION]:
                    field0.params.append('ondelete="cascade"')

            elif info[0]['multiplicity'] == self.MULTIPLICITY_MULTI and (info[1]['multiplicity'] != self.MULTIPLICITY_MULTI or info[0]['class'] == info[1]['class']):
                field0 = DiaAttribute(info[1]['class'], process=False)
                field0.name = info[1]['role'] and info[1]['role'] or info[0]['class'].class_id.replace('.', '_') + '_ids'
                field0.type = 'One2many'
                field0.options['related_class'] = info[0]['class']
                field0.options['reverse_attribute'] = info[0]['role'] and info[0]['role'] or info[1]['class'].class_id.replace('.', '_') + '_id'
                field0.visibility = info[1]['visibility']
                field0.params.append('"{model}"'.format(model=info[0]['class'].class_id))
                link_field = info[0]['role'] and info[0]['role'] or info[1]['class'].class_id.replace('.', '_') + '_id'
                field0.params.append('"{field}"'.format(field=link_field))
                field0.params.append('{key}="{value}"'.format(key='string', value=info[0]['class'].class_name))
                field0.context.attributes.append(field0)

            #many2many relation different classes
            if info[0]['multiplicity'] == self.MULTIPLICITY_MULTI and info[1]['multiplicity'] == self.MULTIPLICITY_MULTI and info[0]['class'] != info[1]['class']:
                field0 = DiaAttribute(info[0]['class'], process=False)
                field0.name = info[0]['role'] and info[0]['role'] or info[1]['class'].class_id.replace('.', '_') + '_ids'
                field0.type = 'Many2many'
                field0.options['related_class'] = info[1]['class']
                field0.visibility = info[0]['visibility']
                field0.params.append('"{model}"'.format(model=info[1]['class'].class_id))
                field0.params.append('"{class_a}_{class_b}_rel"'.format(class_a=info[0]['class'].class_id.replace('.', '_'), class_b=info[1]['class'].class_id.replace('.', '_')))

                link_a = (info[1]['role'] and info[1]['role'] or info[0]['class'].class_id.replace('.', '_') + '_ids').replace('_ids', '_id')
                link_b = (info[0]['role'] and info[0]['role'] or info[1]['class'].class_id.replace('.', '_') + '_ids').replace('_ids', '_id')

                field0.params.append('"{field}"'.format(field=link_a))
                field0.params.append('"{field}"'.format(field=link_b))
                field0.params.append('{key}="{value}"'.format(key='string', value=info[1]['class'].class_name))

                field0.context.attributes.append(field0)

                #inverse relation
                field1 = DiaAttribute(info[1]['class'], process=False)
                field1.name = info[1]['role'] and info[1]['role'] or info[0]['class'].class_id.replace('.', '_') + '_ids'
                field1.type = 'Many2many'
                field1.options['related_class'] = info[0]['class']
                field1.visibility = info[1]['visibility']
                field1.params.append('"{model}"'.format(model=info[0]['class'].class_id))
                field1.params.append('"{class_a}_{class_b}_rel"'.format(class_a=info[0]['class'].class_id.replace('.', '_'), class_b=info[1]['class'].class_id.replace('.', '_')))

                field1.params.append('"{field}"'.format(field=link_b))
                field1.params.append('"{field}"'.format(field=link_a))

                field1.params.append('{key}="{value}"'.format(key='string', value=info[0]['class'].name))

                field1.context.attributes.append(field1)


class DiaAttribute:
    VISIBILITY_PUBLIC = 0           #grid and form
    VISIBILITY_PRIVATE = 1          #none
    VISIBILITY_PROTECTED = 2        #form
    VISIBILITY_IMPLEMENTATON = 3    #grid

    tiny_fields_map = {
        'char': 'Char',
        'date': 'Date',
        'datetime': 'Datetime',
        'int': 'Integer',
        'bool': 'Boolean',
        'boolean': 'Boolean',
        'float': 'Float',
        'text': 'Text',
        'string': 'Char',
        'html': 'Html',
        'enum': 'Selection',
        'binary': 'Binary',

        'url': {'type': 'Char', 'options': {'widget': 'url'}},
        'image': {'type': 'Binary', 'options': {'image': True, 'widget': 'image'}},
        'domain': 'Char',
        'email': {'type': 'Char', 'options': {'widget': 'email'}},
        'handle': {'type': 'Integer', 'options': {'widget': 'handle'}},
        'radio': {'type': 'Selection', 'options': {'widget': 'radio'}},
        'progressbar': {'type': 'Float', 'options': {'widget': 'progressbar'}},
        'progress': {'type': 'Float', 'options': {'widget': 'progressbar'}},
        'monetary': {'type': 'Float', 'options': {'widget': 'money'}},
        'float_time': {'type': 'Float', 'options': {'widget': 'float_time'}},
        'priority': {'type': 'Selection', 'options': {'widget': 'priority'}},

        'one2many': 'One2many',
        'o2m': 'One2many',
        'many2one': 'Many2one',
        'm2o': 'Many2one',
        'many2many': 'Many2many',
        'm2m': 'Many2many',
    }

    default_type_widget_map = {
        'url': 'url',
        'image': 'image',
        'domain': 'char_domain',
        'email': 'email',
        'handle': 'handle',
        'radio': 'radio',
        'progressbar': 'progressbar',
        'progress': 'progressbar',
        'monetary': 'monetary',
        'float_time': 'float_time',
        'priority': 'priority',
    }

    all_types = ['Char', 'Date', 'Datetime', 'Integer', 'Boolean', 'Binary', 'Float', 'Text', 'Char', 'Html', 'Selection', 'One2many', 'Many2one', 'Many2many']
    simple_types = ['Char', 'Date', 'Datetime', 'Integer', 'Boolean', 'Float', 'Text', 'Char', 'Html', 'Binary']
    default_type = 'Char'

    #name, type, visibility, params, inheritance_type, comment, class_scope
    def __init__(self, klass, obj=None, process=True):
        self.no_clips = False
        self.context = klass
        self.obj = obj
        self.name = None
        self.raw_type = None
        self.type = self.default_type
        self.visibility = self.VISIBILITY_PUBLIC
        self.default = None
        self.help = False
        self.string = False
        self.params = []
        self.options = {}
        self.selection = []
        self.fnc_search = False
        self.fnc_compute = False
        self.fnc_inverse = False
        self.groups = []
        self.raw_field_type = self.default_type
        if self.obj:
            self.name = self.obj[0]
            self.raw_type = self.obj[1]
            self.type = self.default_type
            self.visibility = self.obj[4]
            self.default = len(self.obj[2]) and self.obj[2] or None
            #self.help = self.obj[3]

        if process:
            self.__process()

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name and self.context.class_id == other.context.class_id

    @property
    def has_default(self):
        return self.default is not None

    def __process(self):

        self.string = self.name.capitalize()

        type_match = re.match('(?P<type>[\w\d_]*)(\((?P<params>.*)\))?', self.raw_type)

        if type_match:
            if type_match.group('type') in self.all_types:
                self.type = type_match.group('type')
            else:
                if self.tiny_fields_map.has_key(type_match.group('type')):
                    self.raw_field_type = type_match.group('type')
                    if isinstance(self.tiny_fields_map[type_match.group('type')], str):
                        self.type = self.tiny_fields_map[type_match.group('type')]
                    else:
                        for attr, value in self.tiny_fields_map[type_match.group('type')].items():
                            if hasattr(self, attr):
                                setattr(self, attr, value)
                        # self.options.update(self.tiny_fields_map[type_match.group('type')]['options'])

        p = re.match('(?P<type>[\w\d_]*)(\((?P<params>.*)\))?([;]\s*(?P<options>.*))?', self.raw_type)

        opts = self.obj[3].strip()
        
        if opts:
            opts = [s.strip() for s in opts.split(';')]

            for opt in opts:
                if '=' in opt:
                    key, value = opt.split('=')
                    self.options[key] = value
                else:
                    self.options[opt] = True

        #selection attribute has options and simple types has label inside
        if self.type == 'Selection' and p.group('params'):
            param_list = p.group('params').split(',')
            for i, item in enumerate(param_list):
                if ':' in item:
                    v, s = item.split(':')
                    self.selection += [(v, s)]
                else:
                    self.selection += [(item, item.capitalize())]
        elif self.type == 'Many2one':
            param_list = p.group('params').split(',')
            self.params.append('"{model}"'.format(model=param_list[0]))
            if len(param_list) >= 2:
                self.string = param_list[1].strip('"')
        elif self.type == 'One2many':
            param_list = p.group('params').split(',')
            self.params.append('"{model}"'.format(model=param_list[0]))
            self.params.append('"{field}"'.format(field=param_list[1]))
            if len(param_list) >= 3:
                self.string = param_list[2].strip('"')
        elif self.type == 'Many2many':
            param_list = p.group('params').split(',')
            self.params.append('"{model}"'.format(model=param_list[0]))
            self.params.append('"{field}"'.format(field=param_list[1]))
            self.params.append('"{field}"'.format(field=param_list[2]))
            if len(param_list) >= 4:
                self.string = param_list[3].strip('"')
        elif self.type in self.simple_types:
            self.string = p.group('params')
            if not self.string:
                self.string = self.name.capitalize()


        if self.type == 'Selection':
            self.params = [str(self.selection), '"{value}"'.format(value=self.string)]
        elif self.type in self.simple_types and self.string:
            self.params = ['"{string}"'.format(string=self.string)]

        for k, v in self.options.items():
            if k in ['required', 'index', 'store', 'copyable', 'recursive', 'change_default', 'translate']:
                self.params.append("{option}={value}".format(option=k, value=True))
            elif k in ['groups', 'related']:
                if k == 'groups':
                    self.groups = v.split(',')
                self.params.append('{key}="{value}"'.format(key=k, value=v))
            elif k in ['domain']:
                self.params.append('{key}={value}'.format(key=k, value=v))
            elif k in ['compute', 'search', 'inverse']:
                if isinstance(v, type(True)):
                    v = '_{key}_{name}'.format(key=k, name=self.name)
                    self.options[k] = v
                if hasattr(self, 'fnc_' + k):
                    setattr(self, 'fnc_' + k, v)
                self.params.append('{key}="{value}"'.format(key=k, value=v))
            elif k in ['track', 'track_visibility']:
                if v == 'True' or v is True:
                    v = 'always'
                self.params.append('track_visibility="{value}"'.format(value=v))
            elif k in ['digits', 'digits_compute']:
                v = v.strip('"')
                self.params.append('digits_compute=dp.get_precision("{value}")'.format(value=v))

        if self.help:
            self.params.append('help="{help}"'.format(help=self.help))

        if self.type == 'Binary' and ('image' in self.options) and self.options['image']:
            #hide raw binary image
            self.visibility = self.VISIBILITY_PRIVATE

            #show medium image instead
            # image_medium = DiaAttribute(self.context, process=False)
            # image_medium.name = 'image_medium'
            # image_medium.type = 'Binary'
            # image_medium.string = self.string
            # image_medium.visibility = self.VISIBILITY_PROTECTED
            # image_medium.help = self.help
            # image_medium.options = self.options.copy()
            # image_medium.options['widget'] = 'image'
            # image_medium.params = self.params[::]
            # image_medium.fnc_compute = '_get_image'
            # image_medium.fnc_inverse = '_set_image'
            # image_medium.params.append('{key}="{value}"'.format(key='compute', value='_get_image'))
            # image_medium.params.append('{key}="{value}"'.format(key='inverse', value='_set_image'))
            # self.context.attributes.append(image_medium)
            #
            # image_small = DiaAttribute(self.context, process=False)
            # image_small.name = 'image_small'
            # image_small.type = 'Binary'
            # image_small.string = self.string
            # image_small.visibility = self.VISIBILITY_PRIVATE
            # image_small.help = self.help
            # image_small.options = self.options.copy()
            # image_small.params = self.params[::]
            # image_small.fnc_compute = '_get_image'
            # image_small.fnc_inverse = '_set_image'
            # image_small.params.append('{key}="{value}"'.format(key='compute', value='_get_image'))
            # image_small.params.append('{key}="{value}"'.format(key='inverse', value='_set_image'))
            #
            # self.context.attributes.append(image_small)

            self.context.clips['image_get_set'] = env.get_template('methods/get_set_image').render(image_field=self.name, model=self.context)

        if self.default:
            self.context.defaults[self.name] = self.default.isdigit() and self.default or ('"' + self.default + '"')
            self.params.append('default={value}'.format(value=self.default.isdigit() and self.default or ('"' + self.default + '"')))

        if not self.no_clips:
            if self.fnc_compute:
                self.context.clips[self.fnc_compute] = env.get_template('methods/field_method_compute').render(field=self.name, name=self.fnc_compute)

            if self.fnc_search:
                self.context.clips[self.fnc_search] = env.get_template('methods/field_method_search').render(field=self.name, name=self.fnc_search)

            if self.fnc_inverse:
                self.context.clips[self.fnc_inverse] = env.get_template('methods/field_method_inverse').render(field=self.name, name=self.fnc_inverse)

    def __str__(self):
        params = ''
        if self.params:
            params = ', '.join(self.params)
        return "fields.{type}({params})".format(type=self.type, params=params)


class MethodTemplate:
    def __init__(self, name, template=None, params=None, content=None, context=None, decorators=None):
        self.name = name
        self.decorators = decorators and decorators or []
        self.template = template
        self.params = params and params or {}
        self.content = content
        self.context = context

    def render(self):
        if self.content:
            return jinja2.Template(self.content).render(**self.params)
        elif self.template:
            return env.get_template(self.template).render(**self.params)


class DiaClass:
    class_re = re.compile('(?P<name>.*)\((?P<id>.*)\)')

    @classmethod
    def is_valid_for_object(cls, obj):
        return obj and obj.type.name == 'UML - Class'

    def __init__(self, obj, context=None):
        self.TAG_SEARCH = 'search'
        self.TAG_GROUP = 'group'
        self.TAG_MEASURE = 'measure'
        self.TAG_ROW = 'row'
        self.TAG_TIME_START = 'start'
        self.TAG_TIME_END = 'end'
        self.TAG_TIME_DURATION = 'duration'

        self.obj = obj
        self.class_name = None
        self.class_id = None
        self.context = context
        self.comment = None
        self.clips = {}

        self.groups = []

        self.package = False

        self.parents = []
        self.inherits = {}
        self.mixin_classes = {}

        self.dependencies = []

        self.template = self.obj.properties['template'].value
        self.stereotype = self.obj.properties['stereotype'].value
        self.abstract = self.obj.properties['abstract'].value

        self.operations = []
        self.attributes = []

        self.defaults = {}

        self.__process()

    def __str__(self):
        return "<DiaClass name={name} id={id} at {uid}>".format(name=self.name, id=self.class_id, uid=id(self))

    def __repr__(self):
        return str(self)

    @property
    def has_date_columns(self):
        return len(self.attributes_by_type(['Date', 'Datetime'])) > 1

    def attributes_by_type(self, attrtype):
        if isinstance(attrtype, list) or isinstance(attrtype, tuple):
            return [c for c in self.attributes if c.type in attrtype]
        return [c for c in self.attributes if c.type in [attrtype]]

    @property
    def parent_names(self):
        return [p.class_id for p in self.parents]

    @property
    def searchable_fields(self):
        return [a for a in self.attributes if self.TAG_SEARCH in a.tags]

    @property
    def show_search_view(self):
        return len(self.attributes_by_tag([self.TAG_SEARCH, self.TAG_GROUP])) > 0

    def attributes_by_tag(self, tags):
        if isinstance(tags, list) or isinstance(tags, tuple):
            return [c for c in self.attributes if set(c.tags) & set(tags) ]
        return [c for c in self.attributes if tags in c.tags]

    @property
    def handle_attribute(self):
        attrs = [c for c in self.attributes if ('widget' in c.options) and (c.options['widget']=='handle')]
        return attrs[0] if attrs else False

    @classmethod
    def name2class(cls, name):
        uncapitalize = name[0].lower() + name[1:]
        m = cls.class_re.match(name)
        mixed_case = sum([c in string.ascii_uppercase and 1 or 0 for c in uncapitalize]) > 0

        if m:
            class_name = m.group('name')
            class_id = m.group('id')
        elif mixed_case:
            new_name = ''.join([c in string.ascii_uppercase and ' ' + c or c for c in name]).strip()
            parts = new_name.split()
            class_name = name
            class_id = '.'.join([s.lower() for s in parts])
        else:
            parts = name.split('.')
            class_name = ''.join([s.capitalize() for s in parts])
            class_id = name.lower()

        return {
            'class_name': class_name,
            'class_id': class_id,
            'name': name
        }

    def __process(self):
        class_info = self.name2class(self.obj.properties['name'].value)

        self.name = class_info['name']
        self.class_name = class_info['class_name']
        self.class_id = class_info['class_id']

        if DiaPackage.is_valid_for_object(self.obj.parent):
            self.package = self.context.packages[DiaPackage(self.obj.parent, context=self.context).name]
        else:
            self.package = self.context.default_package

        self.package.classes.append(self)

        #process attributes and methods
        for attr in self.obj.properties["attributes"].value:
            self.attributes.append(DiaAttribute(self, attr))

        for method in self.obj.properties["operations"].value:
            self.operations.append(DiaOperation(self, method))

        for k,v in self.obj.properties["templates"].value:
            self.inherits[k] = v

        for a in self.attributes:
            for g in a.groups:
                self.groups.append(g)

    @property
    def inherits_class_dict(self):
        return str(self.inherits)

    @property
    def parents_class_list(self):
        if self.stereotype or self.parents:
            if self.stereotype:
                parent_list = self.stereotype.split(',') + [p.class_id for p in self.parents]
            else:
                parent_list = [p.class_id for p in self.parents]
            
            return repr(parent_list[0]) if len(parent_list) else repr(parent_list)

    @property
    def view_tree_attributes(self):
        return [a for a in self.attributes if a.visibility in [DiaAttribute.VISIBILITY_PUBLIC, DiaAttribute.VISIBILITY_IMPLEMENTATON]]

    @property
    def view_form_attributes(self):
        return [a for a in self.attributes if a.visibility in [DiaAttribute.VISIBILITY_PUBLIC, DiaAttribute.VISIBILITY_PROTECTED]]


class ObjRenderer:
    "Implements the Object Renderer Interface and transforms diagram into its internal representation"

    def __init__(self):
        # an empty dictionary of classes
        self.models = {}
        self.model_ids = []  # store class ids to maintain order
        self.class_map = {}  # store class names and class ids mappings
        self.arrows = []
        self.filename = ""
        self.groups = []
        self.default_package = None
        self.packages = {}

    def begin_render(self, data, filename):
        self.filename = filename
        self.default_package = DiaPackage(name=os.path.basename(filename).split('.')[-2])
        self.packages[self.default_package.name] = self.default_package

        for layer in data.layers:
            # for the moment ignore layer info. But we could use this to spread accross different files
            for o in layer.objects:
                # other UML objects which may be interesting
                # UML - Note, UML - LargePackage, UML - SmallPackage, UML - Dependency, ...
                if DiaPackage.is_valid_for_object(o):
                    package = DiaPackage(o, context=self)
                    if package.name not in self.packages.keys():
                        self.packages[package.name] = package

            for o in layer.objects:
                if DiaClass.is_valid_for_object(o):
                    klass = DiaClass(o, context=self)
                    self.models[klass.class_id] = klass
                    self.model_ids.append(klass.class_id)
                    self.class_map[klass.class_name] = klass.class_id
                    self.groups.extend(klass.groups)

            for o in layer.objects:
                if DiaUMLAssociation.is_valid_for_object(o):
                    asociation = DiaUMLAssociation(o, context=self)
                    asociation.process()


        self.groups = list(set(self.groups))

        edges = {}
        for layer in data.layers:
            for o in layer.objects:
                for c in o.connections:
                    for n in c.connected:
                        if not n.type.name in ("UML - Generalization", "UML - Realizes"):
                            continue
                        if str(n) in edges:
                            continue
                        edges[str(n)] = None
                        if not (n.handles[0].connected_to and n.handles[1].connected_to):
                            continue
                        par = n.handles[0].connected_to.object
                        chi = n.handles[1].connected_to.object
                        if not par.type.name == "UML - Class" and chi.type.name == "UML - Class":
                            continue

                        from_info = DiaClass.name2class(par.properties["name"].value)
                        to_info = DiaClass.name2class(par.properties["name"].value)
                        
                        if n.type.name == "UML - Realizes":
                            self.models[to_info['class_id']].parents.append(self.models[from_info['class_id']])
                        else:
                            inherited_class = self.models[from_info['class_id']]
                            field = n.properties['name'].value
                            if not field:
                                field = inherited_class.class_id.replace('.', '_') + '_id'
                            self.models[to_info['class_id']].inherits[field] = inherited_class.class_id

    def end_render(self):
        # without this we would accumulate info from every pass
        self.attributes = []
        self.operations = {}

        self.models = {}
        self.model_ids = []  # store class ids to maintain order
        self.class_map = {}  # store class names and class ids mappings
        self.arrows = []
        self.filename = ""
        self.groups = []
        self.default_package = None
        self.packages = {}

    def fill_rect(self, *args, **kargs):pass
    def draw_line(self, *args, **kargs):pass
    def draw_string(self, *args, **kargs):pass
    def fill_polygon(self, *args, **kargs):pass


class OdooRenderer(ObjRenderer):
    def __init__(self):
        ObjRenderer.__init__(self)

    def data_get(self):
        return {
            'file': self.filename,
            'module': os.path.basename(self.filename).split('.')[-2]
        }

    def end_render(self):
        module = self.data_get()['module']
        xip = zipfile.ZipFile(self.filename, 'w')

        zip_files = {
            '__init__.py': env.get_template('__init__.py').render(module=module, packages=['models']),
            '__openerp__.py': env.get_template('__openerp__.py').render(module=module, data=self, packages=self.packages.keys()),
            'models/__init__.py': env.get_template('models/__init__.py').render(module=module, data=self, packages=self.packages.keys()),
            'views/menu.xml': env.get_template('menu.xml').render(module=module, data=self, packages=self.packages.keys()),
            'security/ir.model.access.csv': env.get_template('security/ir.model.access.csv').render(module=module, data=self),
        }

        for name, package in self.packages.items():
            zip_files['models/{package}.py'.format(package=package.name)] = env.get_template('models/package.py').render(module=module, data=self, package=package, models=package.classes)
            zip_files['views/{package}.xml'.format(package=package.name)] = env.get_template('view.xml').render(module=module, data=self, package=package, models=package.classes)

        for name, datastr in zip_files.items():
            info = zipfile.ZipInfo(module + '/' + name)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 2175008768
            xip.writestr(info, datastr)
        xip.close()
        ObjRenderer.end_render(self)


# dia-python keeps a reference to the renderer class and uses it on demand
dia.register_export("PyDia Code Generation (Odoo v8)", "zip", OdooRenderer())

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
