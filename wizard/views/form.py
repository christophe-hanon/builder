from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class FormWizard(models.Model):
    _name = 'builder.wizard.views.form'
    _inherit = 'builder.wizard.views.abstract'

    attr_create = fields.Boolean('Allow Create', default=True)
    attr_edit = fields.Boolean('Allow Edit', default=True)
    attr_delete = fields.Boolean('Allow Delete', default=True)
    page_ids = fields.One2many('builder.wizard.views.form.page', 'wizard_id', 'Pages')
    field_ids = fields.One2many('builder.wizard.views.form.field', 'wizard_id', 'Fields')
    states_clickable = fields.Boolean('States Clickable')
    show_status_bar = fields.Boolean('Show Status Bar')
    visible_states = fields.Char('Visible States')

    # buttonbar_button_ids = fields.One2many('builder.ir.model.view.config.wizard.buttonbar.buttons', 'wizard_id', 'Buttons')
    statusbar_button_ids = fields.One2many('builder.wizard.views.form.statusbar.button', 'wizard_id', 'Status Bar Buttons')


    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.attr_string = self.model_id.name
        self.view_id = "view_{snake}_form".format(snake = snake_case(self.model_id.model))
        self.show_status_bar = True if self.model_id.special_states_field_id.id else False

        if not len(self.field_ids):
            field_list = []
            for field in self.model_id.field_ids:
                if field.name in ['state']: continue
                field_list.append({'field_id': field.id, 'widget': DEFAULT_WIDGETS_BY_TYPE.get(field.ttype), 'field_ttype': field.ttype, 'model_id': self.model_id.id, 'special_states_field_id': self.model_id.special_states_field_id.id})

            self.field_ids = field_list


class FormPage(models.Model):
    _name = 'builder.wizard.views.form.page'

    _order = 'sequence, name'

    wizard_id = fields.Many2one('builder.wizard.views.form', string='Wizard', ondelete='cascade')
    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence')
    field_ids = fields.One2many('builder.wizard.views.form.field', 'page_id', 'Fields')


DEFAULT_WIDGETS_BY_TYPE = {
    'binary': 'image'
}


class StatusBarActionButton(models.Model):
    _name = 'builder.wizard.views.form.statusbar.button'

    _order = 'sequence, name'

    wizard_id = fields.Many2one('builder.wizard.views.form', string='Wizard', ondelete='cascade')
    model_id = fields.Many2one('builder.ir.model', string='Model')
    special_states_field_id = fields.Many2one('builder.ir.model.fields', related='model_id.special_states_field_id', string='States Field')
    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence')
    highlighted = fields.Boolean('Highlighted')
    type = fields.Selection([('state', 'State Change'), ('action', 'Defined Action'), ('object', 'Model Action'), ('relation', 'Relation')], 'Type')
    states = fields.Char('States')
    change_to_state = fields.Char('Change to State')
    method_name = fields.Char('Method Name')
    method_code = fields.Text('Method Code')
    action_ref = fields.Char('Action')

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'state' and self.change_to_state:
            self.method_name = "action_{state}".format(state=self.change_to_state)
        elif self.type == 'object' and self.name:
            self.method_name = "action_{name}".format(name=snake_case(self.name.replace(' ', '.')).lower())




class FormField(models.Model):
    _name = 'builder.wizard.views.form.field'
    _inherit = 'builder.wizard.views.abstract.field'

    wizard_id = fields.Many2one('builder.wizard.views.form', string='Wizard', ondelete='cascade')
    page_id = fields.Many2one('builder.wizard.views.form.page', string='Page', ondelete='set null')

    related_field_view_type = fields.Selection([('default', 'Default'), ('defined', 'Defined'), ('custom', 'Custom')], 'View Type', required=True, default='default')
    related_field_arch = fields.Text('Arch')
    related_field_form_id = fields.Char('Form View ID')
    related_field_tree_id = fields.Char('Tree View ID')
    domain = fields.Char('Domain')
    related_field_mode = fields.Selection([('tree', 'Tree'), ('form', 'Form')], 'Mode', default='tree')
    related_field_tree_editable = fields.Selection([('False', 'No Editable'), ('top', 'Top'), ('bottom', 'Bottom')], 'Tree Editable', default='bottom')

    widget = fields.Selection(FIELD_WIDGETS_ALL, 'Widget')
    widget_options = fields.Char('Widget Options')

    nolabel = fields.Boolean('Hide Label')

    required = fields.Boolean('Required')
    required_condition = fields.Char('Required Condition')

    invisible = fields.Boolean('Invisible')
    invisible_condition = fields.Char('Invisible Condition')

    readonly = fields.Boolean('Readonly')
    readonly_condition = fields.Char('Readonly Condition')

    states = fields.Char('States')

    @api.one
    @api.depends('field_id.ttype', 'wizard_id')
    def _compute_field_type(self):
        if self.field_id:
            self.field_ttype = self.field_id.ttype


