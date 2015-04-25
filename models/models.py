from openerp import models, fields, api
from openerp.models import check_object_name
from openerp.osv import fields as fields_old
from openerp import tools
from openerp import _


class IrModel(models.Model):
    _name = 'builder.ir.model'
    _description = "Models"
    _order = 'model'

    _rec_name = 'model'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', required=True, select=1, ondelete='cascade')

    name = fields.Char('Description', required=True)
    model = fields.Char('Model', required=True, select=1)
    info = fields.Text('Information')
    rec_name_field_id = fields.Many2one('builder.ir.model.fields', 'Record Name', domain=[('ttype', 'in', ['char', 'text', 'date', 'datetime', 'selection'])])
    osv_memory = fields.Boolean('Transient',
                                help="This field specifies whether the model is transient or not (i.e. if records are automatically deleted from the database or not)")
    field_ids = fields.One2many('builder.ir.model.fields', 'model_id', 'Fields', required=True, copy=True)
    relation_field_ids = fields.One2many('builder.ir.model.fields', 'relation_model_id', 'Referenced By Fields')
    # inherit_model = fields.Char('Inherit', compute='_compute_inherit_model')

    inherit_model_ids = fields.One2many('builder.ir.model.inherit', 'model_id', 'Inherit')
    inherits_model_ids = fields.One2many('builder.ir.model.inherits', 'model_id', 'Inherits')

    is_inherited = fields.Boolean('Inherited', compute='_compute_inherited', store=True)
    inherit_type = fields.Selection([('mixed', 'Mixed'), ('class', 'Class'), ('prototype', 'Prototype'), ('delegation', 'Delegation')], 'Inherit Type', compute='_compute_inherited', store=True)

    access_ids = fields.One2many('builder.ir.model.access', 'model_id', 'Access', copy=True)

    view_ids = fields.One2many('builder.ir.ui.view', 'model_id', 'Views')
    method_ids = fields.One2many('builder.ir.model.method', 'model_id', 'Models')

    to_ids = fields.One2many('builder.ir.model.fields', 'relation_model_id', 'Forward Models', domain=[('ttype', 'in', ['many2one','one2many','many2many']), ('relation_model_id', '!=', False)])
    from_ids = fields.One2many('builder.ir.model.fields', 'model_id', 'Backward Models', domain=[('ttype', 'in', ['many2one','one2many','many2many']), ('relation_model_id', '!=', False)])

    #extra fields

    special_states_field_id = fields.Many2one('builder.ir.model.fields', 'States Field', compute='_compute_special_fields', store=True)
    special_active_field_id = fields.Many2one('builder.ir.model.fields', 'Active Field', compute='_compute_special_fields', store=True)
    special_sequence_field_id = fields.Many2one('builder.ir.model.fields', 'Sequence Field', compute='_compute_special_fields', store=True)
    special_parent_id_field_id = fields.Many2one('builder.ir.model.fields', 'Parent Field', compute='_compute_special_fields', store=True)

    groups_date_field_ids = fields.One2many('builder.ir.model.fields', 'model_id', string='Date Fields', compute='_compute_field_groups')
    groups_numeric_field_ids = fields.One2many('builder.ir.model.fields','model_id', string='Numeric Fields', compute='_compute_field_groups')
    groups_boolean_field_ids = fields.One2many('builder.ir.model.fields','model_id', string='Boolean Fields', compute='_compute_field_groups')
    groups_relation_field_ids = fields.One2many('builder.ir.model.fields','model_id', string='Relation Fields', compute='_compute_field_groups')
    groups_o2m_field_ids = fields.One2many('builder.ir.model.fields', 'model_id', string='O2m Fields', compute='_compute_field_groups')
    groups_m2m_field_ids = fields.One2many('builder.ir.model.fields','model_id', string='M2m Fields', compute='_compute_field_groups')
    groups_m2o_field_ids = fields.One2many('builder.ir.model.fields', 'model_id', string='M2o Fields', compute='_compute_field_groups')
    groups_binary_field_ids = fields.One2many('builder.ir.model.fields', 'model_id', string='M2o Fields', compute='_compute_field_groups')
    groups_inherited_field_ids = fields.One2many('builder.ir.model.fields', 'model_id', string='Inherited Fields', compute='_compute_field_groups')

    order_field_id = fields.Many2one('builder.ir.model.fields', 'Order Field')
    order_direction = fields.Selection([('asc', 'asc'), ('desc', 'desc')], 'Order Field', default='asc')

    diagram_position_x = fields.Integer('X')
    diagram_position_y = fields.Integer('Y')

    # @api.constrains('model')
    # def check_model_name(self):
    #     if not check_object_name(self.name):
    #         raise Warning(_('The model name is not valid.'))

    @api.one
    @api.depends('inherit_model_ids', 'inherits_model_ids')
    def _compute_inherited(self):
        self.is_inherited = len(self.inherit_model_ids) > 0

        self.inherit_type = False
        if len(self.inherit_model_ids):
            if (len(self.inherit_model_ids) == 1) and ( self.inherit_model_ids[0].model_display == self.model ):
                self.inherit_type = 'class'
            else:
                self.inherit_type = 'prototype'
        else:
            if len(self.inherits_model_ids):
                self.inherit_type = 'delegation'

        if len(self.inherit_model_ids) and len(self.inherits_model_ids):
            self.inherit_type = 'mixed'

    @api.onchange('model')
    def on_model_change(self):
        if not self.name:
            self.name = self.model

    # @api.one
    # @api.depends('inherit_model_ids')
    # def _compute_inherit_model(self):
    #     self.inherit_model = ','.join([m.model for m in self.inherit_model_ids])

    @api.multi
    def find_field_by_name(self, name):
        field_obj = self.env['builder.ir.model.fields']
        return field_obj.search([('model_id', '=', self.id), ('name', '=', name)])

    @api.multi
    def find_field_by_type(self, types):
        field_obj = self.env['builder.ir.model.fields']
        return field_obj.search([('model_id', '=', self.id), ('ttype', 'in', types)])

    @api.one
    @api.depends('field_ids', 'field_ids.name')
    def _compute_special_fields(self):
        self.special_states_field_id = self.find_field_by_name('state')
        self.special_active_field_id = self.find_field_by_name('active')
        self.special_sequence_field_id = self.find_field_by_name('sequence')
        self.special_parent_id_field_id = self.find_field_by_name('parent')

    @api.one
    @api.depends('field_ids', 'field_ids.ttype')
    def _compute_field_groups(self):
        self.groups_date_field_ids = self.find_field_by_type(['date', 'datetime'])
        self.groups_numeric_field_ids = self.find_field_by_type(['integer', 'float'])
        self.groups_boolean_field_ids = self.find_field_by_type(['boolean'])
        self.groups_relation_field_ids = self.find_field_by_type(['one2many', 'many2many', 'many2one'])
        self.groups_o2m_field_ids = self.find_field_by_type(['one2many'])
        self.groups_m2m_field_ids = self.find_field_by_type(['many2many'])
        self.groups_m2o_field_ids = self.find_field_by_type(['many2one'])
        self.groups_binary_field_ids = self.find_field_by_type(['binary'])
        self.groups_inherited_field_ids = self.env['builder.ir.model.fields'].search([('model_id', '=', self.id), ('is_inherited', '=', True)])

    @api.multi
    def action_fields(self):
        ref = self.env.ref('builder.builder_ir_model_fields_form_view', False)
        return {
            'name': _('Fields'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': self.field_ids._name,
            'views': [(False, 'tree'), (ref.id if ref else False, 'form')],
            'domain': [('model_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.module_id.id,
                'default_model_id': self.id,
            },
        }

    @api.multi
    def action_methods(self):
        return {
            'name': _('Methods'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': self.method_ids._name,
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('model_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.module_id.id,
                'default_model_id': self.id,
            },
        }


class ModelMethod(models.Model):
    _name = 'builder.ir.model.method'

    model_id = fields.Many2one('builder.ir.model', 'Model', ondelete='cascade')
    module_id = fields.Many2one('builder.ir.module.module', string='Module', related='model_id.module_id', ondelete='cascade')

    reference = fields.Reference([
                                     ('builder.ir.model.fields', 'Field'),
    ], string='Reference')

    name = fields.Char(string='Name', required=True)
    arguments = fields.Char(string='Arguments', default='')

    prototype = fields.Char('Prototype', compute='_compute_prototype')

    sugar_is_onchange = fields.Boolean('On Change')
    sugar_on_change_triggers = fields.Many2many('builder.ir.model.fields', 'builder_ir_model_method_on_change_trigger_rel', 'model_method_id', 'field_id', string="Onchange Fields")

    sugar_is_depends = fields.Boolean('Depends')
    sugar_depends_triggers = fields.Many2many('builder.ir.model.fields', 'builder_ir_model_method_depends_trigger_rel', 'model_method_id', 'field_id', string="Depends Fields")

    sugar_is_model = fields.Boolean('Model')

    sugar_api_type = fields.Selection([('one', '@api.one'), ('multi', '@api.multi'), ('model', '@api.model')], 'Api Type', default='one')

    sugar_is_constraint = fields.Boolean('Constraint')
    sugar_constraint_triggers = fields.Many2many('builder.ir.model.fields', 'builder_ir_model_method_constraint_trigger_rel', 'model_method_id', 'field_id', string="Constraint Fields")

    code = fields.Text('Code', required=True)
    code_template = fields.Selection([
                                         ('onchange', 'On Change Attributes'),
                                         ('constraint', 'Constraint Method'),
                                         ('create', 'Create Method Rewrite'),
                                         ('write', 'Write Method Rewrite'),
                                         ('unlink', 'Unlink Method Rewrite'),
    ], 'Method Template', store=False, search=True)

    @api.one
    @api.depends('name', 'arguments')
    def _compute_prototype(self):
        self.prototype = "{name}({arguments})".format(name=self.name, arguments=self.arguments)

    @api.onchange('code_template')
    def _onchange_code_template(self):
        self.code = self.code_template


class InheritModelTemplate(models.AbstractModel):
    _name = 'builder.ir.model.inherit.template'
    _order = 'sequence, id'

    sequence = fields.Integer('Sequence')
    model_id = fields.Many2one('builder.ir.model', string='Model', ondelete='cascade')
    module_id = fields.Many2one('builder.ir.module.module', string='Module', related='model_id.module_id', ondelete='cascade')
    model_source = fields.Selection([('module', 'Module'), ('system', 'System')], 'Source', required=True)
    module_model_id = fields.Many2one('builder.ir.model', 'Model', ondelete='cascade')
    system_model_id = fields.Many2one('ir.model', 'Model', ondelete='set null')
    system_model_name = fields.Char('Model Name')
    model_display = fields.Char('Model', compute='_compute_model_display')

    @api.one
    @api.depends('model_source', 'module_model_id', 'system_model_id', 'system_model_name')
    def _compute_model_display(self):
        self.model_display = self.system_model_name if self.model_source == 'system' else self.module_model_id.name

    @api.onchange('model_source', 'module_model_id', 'system_model_id', 'system_model_name')
    def onchange_system_model_id(self):
        self.system_model_name = self.system_model_id.name if self.model_source == 'system' else False
        self.model_display = self.system_model_name if self.model_source == 'system' else self.module_model_id.name


class InheritModel(models.Model):
    _name = 'builder.ir.model.inherit'
    _inherit = 'builder.ir.model.inherit.template'


class InheritsModel(models.Model):
    _name = 'builder.ir.model.inherits'
    _inherit = 'builder.ir.model.inherit.template'

    field_name = fields.Char('Field')
    field_id = fields.Many2one('builder.ir.model.fields', 'Field')
    field_display = fields.Char('Field', compute='_compute_field_display')

    @api.one
    @api.depends('model_source', 'module_model_id', 'system_model_id', 'system_model_name')
    def _compute_field_display(self):
        self.field_display = self.field_name if self.model_source == 'system' else self.field_id.name

