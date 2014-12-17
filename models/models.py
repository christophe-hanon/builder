from openerp import models, fields, api
from openerp.models import check_object_name
from openerp.osv import fields as fields_old
from openerp import tools
from openerp import _

class IrModel(models.Model):
    _name = 'builder.ir.model'
    _description = "Models"
    _order = 'model'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', required=True, select=1, ondelete='cascade')

    name = fields.Char('Description', required=True)
    model = fields.Char('Model', required=True, select=1)
    info = fields.Text('Information')
    osv_memory = fields.Boolean('Transient',
                                help="This field specifies whether the model is transient or not (i.e. if records are automatically deleted from the database or not)")
    field_ids = fields.One2many('builder.ir.model.fields', 'model_id', 'Fields', required=True, copy=True)
    relation_field_ids = fields.One2many('builder.ir.model.fields', 'relation_model_id', 'Referenced By Fields')
    inherit_model = fields.Char('Inherit', compute='_compute_inherit_model')

    inherit_model_ids = fields.Many2many('builder.ir.model', 'builder_ir_model_inherit_model_rel', 'model_id', 'inherited_model_id', 'Inherit')

    #access_ids = fields.One2many('builder.ir.model.access', 'model_id', 'Access', copy=True)

    #view_ids = fields.One2many('builder.ir.ui.view', 'model_id', 'Views')

    to_ids = fields.One2many('builder.ir.model.fields',
                                            'model_id',
                                            'Forward Models', domain=[('ttype', 'in', ['many2one','one2many','many2many']), ('relation_model_id', '!=', False)])

    from_ids = fields.One2many('builder.ir.model.fields',
                                            'relation_model_id',
                                            'Backward Models', domain=[('ttype', 'in', ['many2one','one2many','many2many']), ('relation_model_id', '!=', False)])

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

    order_field_id = fields.Many2one('builder.ir.model.fields', 'Order Field')
    order_direction = fields.Selection([('asc', 'asc'), ('desc', 'desc')], 'Order Field', default='asc')

    # @api.constrains('model')
    # def check_model_name(self):
    #     if not check_object_name(self.name):
    #         raise Warning(_('The model name is not valid.'))

    @api.onchange('model')
    def on_model_change(self):
        if not self.name:
            self.name = self.model

    @api.one
    @api.depends('inherit_model_ids')
    def _compute_inherit_model(self):
        self.inherit_model = ','.join([m.model for m in self.inherit_model_ids])

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


    @api.multi
    def action_open_view_wizard(self):
        view_wizard_obj = self.env['builder.ir.model.view.config.wizard']
        wizard = view_wizard_obj.search([('model_id', '=', self.id)])

        return {
            'name': _('View Wizard'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'builder.ir.model.view.config.wizard',
            'views': [(False, 'form')],
            'res_id': wizard.id or False,
            'target': 'new',
            'context': {
                'default_model_id': self.id,
                'default_special_states_field_id': self.special_states_field_id.id,
                'default_module_id': self.module_id.id,
            },
        }

class ModelMethod(models.Model):
    _name = 'builder.ir.model.method'

    name = fields.Char(string='Name', required=True)

    sugar_is_onchange = fields.Boolean('On Change')
    sugar_on_change_triggers = fields.Many2many('builder.ir.model.fields', 'builder_ir_model_method_on_change_trigger_rel', 'model_method_id', 'field_id', string="Onchange Fields")

    sugar_is_depends = fields.Boolean('Depends')
    sugar_depends_triggers = fields.Many2many('builder.ir.model.fields', 'builder_ir_model_method_depends_trigger_rel', 'model_method_id', 'field_id', string="Depends Fields")

    sugar_is_model = fields.Boolean('Model')

    sugar_is_constraint = fields.Boolean('Constraint')
    sugar_constraint_triggers = fields.Many2many('builder.ir.model.fields', 'builder_ir_model_method_constraint_trigger_rel', 'model_method_id', 'field_id', string="Constraint Fields")


    code = fields.Text('Code', required=True)