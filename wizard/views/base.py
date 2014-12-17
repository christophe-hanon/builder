from openerp import models, api, fields, _

__author__ = 'one'

FIELD_WIDGETS_ALL = [
    ('barchart', "FieldBarChart"),
    ('binary', "FieldBinaryFile"),
    ('boolean', "FieldBoolean"),
    ('char', "FieldChar"),
    ('char_domain', "FieldCharDomain"),
    ('date', "FieldDate"),
    ('datetime', "FieldDatetime"),
    ('email', "FieldEmail"),
    ('float', "FieldFloat"),
    ('float_time', "FieldFloat"),
    ('html', "FieldTextHtml"),
    ('image', "FieldBinaryImage"),
    ('integer', "FieldFloat"),
    ('kanban_state_selection', "KanbanSelection"),
    ('many2many', "FieldMany2Many"),
    ('many2many_binary', "FieldMany2ManyBinaryMultiFiles"),
    ('many2many_checkboxes', "FieldMany2ManyCheckBoxes"),
    ('many2many_kanban', "FieldMany2ManyKanban"),
    ('many2many_tags', "FieldMany2ManyTags"),
    ('many2one', "FieldMany2One"),
    ('many2onebutton', "Many2OneButton"),
    ('monetary', "FieldMonetary"),
    ('one2many', "FieldOne2Many"),
    ('one2many_list', "FieldOne2Many"),
    ('percentpie', "FieldPercentPie"),
    ('priority', "Priority"),
    ('progressbar', "FieldProgressBar"),
    ('radio', "FieldRadio"),
    ('reference', "FieldReference"),
    ('selection', "FieldSelection"),
    ('statinfo', "StatInfo"),
    ('statusbar', "FieldStatus"),
    ('text', "FieldText"),
    ('url', "FieldUrl"),
    ('x2many_counter', "X2ManyCounter"),
]


class ModelViewWizard(models.AbstractModel):
    _name = 'builder.wizard.views.abstract'

    model_id = fields.Many2one('builder.ir.model', ondelete='cascade')
    special_states_field_id = fields.Many2one('builder.ir.model.fields', 'States Field', related='model_id.special_states_field_id')
    model_groups_date_field_ids = fields.One2many('builder.ir.model.fields', string='Has Date Fields', related='model_id.groups_date_field_ids')

    view_type = fields.Char('View Type', required=True)

    attr_string = fields.Char('String')
    view_arch = fields.Text('Arch')
    view_custom_arch = fields.Boolean('Customize')
    view_id = fields.Char('View ID')

    @api.multi
    def action_generate(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_save(self):
        return {'type': 'ir.actions.act_window_close'}



class AbstractWizardField(models.AbstractModel):
    _name = 'builder.wizard.views.abstract.field'

    _rec_name = 'field_id'
    _order = 'wizard_id, sequence'

    wizard_id = fields.Many2one('builder.wizard.views.abstract', string='Name', ondelete='cascade')
    sequence = fields.Integer('Sequence')
    field_id = fields.Many2one('builder.ir.model.fields', string='Field', required=True, ondelete='cascade')
    field_ttype = fields.Char(string='Field Type', compute='_compute_field_type')
    model_id = fields.Many2one('builder.ir.model', related='wizard_id.model_id', string='Model')
    special_states_field_id = fields.Many2one('builder.ir.model.fields', related='wizard_id.model_id.special_states_field_id', string='States Field')
    module_id = fields.Many2one('builder.ir.model', related='wizard_id.model_id.module_id', string='Module')


    @api.one
    @api.depends('field_id.ttype', 'wizard_id')
    def _compute_field_type(self):
        if self.field_id:
            self.field_ttype = self.field_id.ttype