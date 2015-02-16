from openerp.addons.builder.models.fields import snake_case
from openerp.exceptions import ValidationError
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL
from collections import defaultdict

__author__ = 'one'


class FormView(models.Model):
    _name = 'builder.views.form'

    _inherit = ['ir.mixin.polymorphism.subclass', 'builder.views.abstract']

    _inherits = {
        'builder.ir.ui.view': 'view_id'
    }

    view_id = fields.Many2one('builder.ir.ui.view', string='View', required=True, ondelete='cascade')
    attr_create = fields.Boolean('Allow Create', default=True)
    attr_edit = fields.Boolean('Allow Edit', default=True)
    attr_delete = fields.Boolean('Allow Delete', default=True)
    states_clickable = fields.Boolean('States Clickable')
    show_status_bar = fields.Boolean('Show Status Bar')
    visible_states = fields.Char('Visible States')

    # buttonbar_button_ids = fields.One2many('builder.ir.model.view.config.view.buttonbar.buttons', 'view_id', 'Buttons')
    statusbar_button_ids = fields.One2many('builder.views.form.statusbar.button', 'view_id', 'Status Bar Buttons')
    field_ids = fields.One2many('builder.views.form.field', 'view_id', 'Items')


    @api.onchange('inherit_view_id')
    def onchange_inherit_view_id(self):
        self.inherit_view_ref = False
        if self.inherit_view_id:
            data = self.env['ir.model.data'].search([('model', '=', 'ir.ui.view'), ('res_id', '=', self.inherit_view_id.id)])
            self.inherit_view_ref = "{module}.{id}".format(module=data.module, id=data.name) if data else False

    @api.onchange('type')
    def onchange_type(self):
        self.inherit_view_ref = False
        self.inherit_view_id = False

    @api.onchange('inherit_view')
    def onchange_inherit_view(self):
        if self.inherit_view and self.model_id:
            views = self.env['ir.ui.view'].search([('type', '=', 'form'), ('model', '=', self.model_id.model)])
            if views:
                self.inherit_view_id = views[0].id

    @api.one
    @api.constrains('inherit_view_ref')
    def _check_view_ref(self):
        exists = self.env['ir.model.data'].xmlid_lookup(self.inherit_view_ref)
        if exists:
            view = self.env['ir.model.data'].get_object(*self.inherit_view_ref.split('.'))
            if not view.model == self.model_id.model:
                raise ValidationError("View Ref is not a valid view reference")

    _defaults = {
        'type': 'form',
        'custom_arch': False,
        'subclass_model': lambda s, c, u, cxt=None: s._name,
        'inherit_view_xpath': '//form'
    }

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.name = self.model_id.name
        self.xml_id = "view_{snake}_form".format(snake = snake_case(self.model_id.model))
        self.show_status_bar = True if self.model_id.special_states_field_id.id else False
        self.model_inherit_type = self.model_id.inherit_type #shouldn`t be doing that
        self.model_name = self.model_id.model #shouldn`t be doing that

        if not len(self.field_ids):
            field_list = []
            for field in self.model_id.field_ids:
                if field.name in ['state'] or field.is_inherited: continue
                field_list.append({'field_id': field.id, 'widget': DEFAULT_WIDGETS_BY_TYPE.get(field.ttype), 'field_ttype': field.ttype, 'model_id': self.model_id.id, 'special_states_field_id': self.model_id.special_states_field_id.id})

            self.field_ids = field_list

    @api.onchange('custom_arch', 'name', 'field_ids', 'attr_create', 'attr_edit', 'attr_delete', 'states_clickable', 'show_status_bar', 'visible_states',
                  'inherit_view', 'inherit_view_id', 'inherit_view_ref', 'inherit_view_type', 'inherit_view_field_id', 'inherit_view_xpath', 'inherit_view_position' )
    def _onchange_generate_arch(self):
        self.arch = self._get_view_arch()

    @api.multi
    def _get_view_arch(self):
        if self.custom_arch:
            return self.arch
        else:
            pages = defaultdict(list)
            flat = []
            for field in self.field_ids:
                if field.page:
                    pages[field.page].append(field)
                else:
                    flat.append(field)

            template_obj = self.env['document.template']
            return template_obj.render_template('builder.view_arch_form.xml', {
                'this': self,
                'string': self.name,
                'fields': self.field_ids,
                'flat_fields': flat,
                'pages': pages,
                'create': self.attr_create,
                'delete': self.attr_delete,
                'edit': self.attr_edit,
                'states_clickable': self.states_clickable,
                'show_status_bar': self.show_status_bar,
                'visible_states': self.visible_states.split(',') if self.visible_states else False,
            })


DEFAULT_WIDGETS_BY_TYPE = {
    'binary': 'image'
}


class StatusBarActionButton(models.Model):
    _name = 'builder.views.form.statusbar.button'

    _order = 'sequence, name'

    view_id = fields.Many2one('builder.views.form', string='View', ondelete='cascade')
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
    _name = 'builder.views.form.field'
    _inherit = 'builder.views.abstract.field'

    view_id = fields.Many2one('builder.views.form', string='View', ondelete='cascade')
    page = fields.Char('Page')

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
    @api.depends('field_id.ttype', 'view_id')
    def _compute_field_type(self):
        if self.field_id:
            self.field_ttype = self.field_id.ttype


