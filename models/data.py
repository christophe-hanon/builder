from __future__ import unicode_literals
import base64
import csv
from random import randrange
import re
import types
from jinja2 import Template
from openerp import models, fields, api, _

__author__ = 'deimos'


def utf_8_encoder(unicode_csv_data):
    if not unicode_csv_data:
        yield ''
    else:
        for line in unicode_csv_data.split('\n'):
            yield line.encode('utf-8')


class Lambda(models.Model):
    _name = b'builder.lambda'

    name = fields.Char(string='Name', required=True)
    code = fields.Text(string='Code', required=True)

    @api.one
    @api.constrains('code')
    def _check_code(self):
        try:
            l = eval(self.code)
            if not isinstance(l, types.LambdaType):
                raise ValueError(_("The python code must be a lambda."))
        except (SyntaxError, NameError, ):
            raise ValueError(_("The python code must be a lambda."))

    _sql_constraints = [
        ('name', 'unique(name)', 'The name must be unique.')
    ]


class ModelDataAttributeProcess(models.Model):
    _name = b'builder.model.data.change'

    sequence = fields.Integer('Sequence')
    name = fields.Char(string='Name', related='lambda_id.name')
    attribute_id = fields.Many2one(
        comodel_name=b'builder.model.data.attribute',
        string='Attribute',
        ondelete='cascade',
        required=True,
        domain=[],
    )

    lambda_id = fields.Many2one(
        comodel_name=b'builder.lambda',
        string='Lambda',
        ondelete='cascade',
        required=True,
        domain=[],
    )

    parameters = fields.Char('Parameters')


ATTRIBUTE_PATTERN = re.compile('[\w_]+')


class ModelDataAttribute(models.Model):
    _name = b'builder.model.data.attribute'

    name = fields.Char(string='Input Attribute', required=True)
    model_attr = fields.Char(string='Model Attribute')
    filters = fields.Char(string='Filters')
    xml_attr = fields.Char(string='XML Attribute')
    model_id = fields.Many2one(
        comodel_name=b'builder.model.data',
        string='File',
        ondelete='cascade',
        domain=[],
    )
    visible = fields.Boolean('Visible', default=True)
    xml_id = fields.Boolean('XML ID', default=False)

    change_ids = fields.One2many(
        comodel_name=b'builder.model.data.change',
        inverse_name='attribute_id',
        string='Filters',
    )

    @api.onchange('name')
    def onchange_name(self):
        self.model_attr = self.name

    @api.constrains('result_name')
    def _check_result_name(self):
        if not ATTRIBUTE_PATTERN.match(self.result_name):
            raise ValueError('Result Attribute must be a valid name.')

    def compute_value(self, row):
        value = row[self.name]
        for f in self.change_ids:
            plist = eval('[{params}]'.format(params=f.parameters or ''))
            value = eval('({code})(*params)'.format(code=f.filter_id.code), {}, {
                'params': [value] + plist,
                'row': row,
                'model': lambda x: self.env[x].sudo()
            })

        return value.decode('utf-8')


IMPORTER_PATTERN = re.compile('_import_(\w+)')


XML_TEMPLATE = Template(u"""<?xml version="1.0"?>
<openerp>
    <data>
        {% for object in data -%}
        <record model="{{ object.model }}" id="{{ object.id }}">
            {% for field in object.fields -%}
            {% if field.value -%}
            <field name="{{ field.name }}"{% if field.attribute %} {{ field.attribute }}="{{ field.value }}" /> {% else %}>{{ field.value }}</field>{% endif %}
            {% endif -%}
            {% endfor -%}
        </record>
        {% endfor %}
    </data>
</openerp>""")


class ModelData(models.Model):
    _name = b'builder.model.data'

    module_id = fields.Many2one(b'builder.ir.module.module', 'Module', ondelete='cascade', required=True)
    name = fields.Char(string='Name', required=True)
    model_id = fields.Many2one(b'builder.ir.model', 'Model', ondelete='set null')
    model = fields.Char(string='Model ID', required=True)
    input_file = fields.Binary('File', required=True)
    input_text = fields.Text('File Text', compute='_compute_input_text', store=True)
    importer = fields.Selection(selection='_get_importer_selection', string='Importer', required=True)

    key_id = fields.Many2one(
        comodel_name=b'builder.model.data.attribute',
        string='Key',
        compute='_compute_key_id'
    )

    attribute_ids = fields.One2many(
        comodel_name=b'builder.model.data.attribute',
        inverse_name='model_id',
        string='Attributes',
    )

    result_text = fields.Text('XML', compute='_compute_result', store=True)
    result_file = fields.Binary('Result', compute='_compute_result', store=True)

    @api.one
    @api.depends('attribute_ids.xml_id')
    def _compute_key_id(self):
        cr, uid, context = self.env.args
        attrs = self.resolve_2many_commands(cr, uid, 'attribute_ids', self.attribute_ids, context=context)
        keys = [value.id for key, value in attrs.items() if value.get('id') and value.get('xml_id')]
        if any(keys):
            self.key_id = keys[0]

    @api.one
    @api.depends('input_file')
    def _compute_input_text(self):
        self.input_text = base64.decodestring(self.input_file) if self.input_file else ''

    @api.one
    @api.depends('input_text', 'importer', 'model', 'attribute_ids.xml_id', 'key_id')
    def _compute_result(self):
        self.result_text = getattr(self, '_import_{type}'.format(type=self.importer))() if self.importer else ''
        self.result_file = base64.encodestring(self.result_text.encode('utf-8'))

    @api.model
    def _get_importer_selection(self):
        return [
            (attr.replace('_import_', ''), attr.replace('_import_', '').upper()) for attr in dir(self) if
            IMPORTER_PATTERN.match(attr) and isinstance(getattr(self, attr), types.MethodType)
        ]

    @api.onchange('model_id')
    def change_model(self):
        if self.model_id:
            self.model = self.model_id.model

    @api.onchange('input_text')
    def change_attributes(self):
        self.result_file = False
        if self.importer:
            self.attribute_ids = [
                {'name': attr} for attr in
                getattr(self, '_get_{type}_attributes'.format(type=self.importer))(self.input_text)
            ]

    @staticmethod
    def _get_csv_attributes(content):
        return csv.DictReader(utf_8_encoder(content)).fieldnames

    # @api.one  # this means that is used in a @api.one function, so self is a record
    def _import_csv(self):
        if not self.input_text:
            return ''
        data = csv.DictReader(utf_8_encoder(self.input_text))
        header = data.fieldnames  # this is needed to consume the headers

        d = [
            {
                'fields': [
                    {
                        'name': attr.model_attr or attr.name,
                        'attribute': attr.xml_attr,
                        'value': attr.compute_value(row)
                    }
                    for attr in self.attribute_ids if attr.visible
                ],
                'model': self.model,
                'id': self.compute_xml_id(row)
            }
            for row in data
        ]

        return XML_TEMPLATE.render(data=d)

    # @api.one
    def compute_xml_id(self, data):
        key = self.env[b'builder.model.data.attribute'].search([
            ('model_id', '=', self.id),
            ('xml_id', '=', True)
        ])
        return '{model}_{hash}'.format(model=self.model.replace('.', '_'), hash=(key.compute_value(data).replace(' ', '_') if key else randrange(100000000000, 999999999999)))


class Module(models.Model):
    _name = b'builder.ir.module.module'
    _inherit = [b'builder.ir.module.module']

    data_ids = fields.One2many(b'builder.model.data', b'module_id', 'Data')
