from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class TreeView(models.Model):
    _name = 'builder.views.tree'

    _inherit = ['ir.mixin.polymorphism.subclass', 'builder.views.abstract']

    _inherits = {
        'builder.ir.ui.view': 'view_id'
    }

    view_id = fields.Many2one('builder.ir.ui.view', string='View', required=True, ondelete='cascade')
    field_parent_id = fields.Many2one('builder.ir.model.fields', string='Field Parent', ondelete='set null')
    attr_create = fields.Boolean('Allow Create', default=True)
    attr_edit = fields.Boolean('Allow Edit', default=True)
    attr_delete = fields.Boolean('Allow Delete', default=True)
    field_ids = fields.One2many('builder.views.tree.field', 'view_id', 'Fields')
    attr_toolbar = fields.Boolean('Show Toolbar', default=False)
    attr_fonts = fields.Char('Fonts', help='Font definition. Ex: bold:message_unread==True')
    attr_colors = fields.Char('Colors', help='Color definition. Ex: "gray:probability == 100;red:date_deadline and (date_deadline &lt; current_date)"')

    _defaults = {
        'type': 'tree',
        'custom_arch': False,
        'subclass_model': lambda s, c, u, cxt=None: s._name,
        'inherit_view_xpath': '//tree'
    }

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.name = self.model_id.name
        self.xml_id = "view_{snake}_tree".format(snake = snake_case(self.model_id.model))
        self.model_inherit_type = self.model_id.inherit_type #shouldn`t be doing that
        self.model_name = self.model_id.model #shouldn`t be doing that

        if not len(self.field_ids):
            field_list = []
            for field in self.model_id.field_ids:
                if field.ttype not in ['binary', 'one2many', 'many2many']:
                    field_list.append({'field_id': field.id, 'field_ttype': field.ttype, 'model_id': self.model_id.id, 'special_states_field_id': self.model_id.special_states_field_id.id})

            self.field_ids = field_list

    @api.onchange('custom_arch', 'field_ids', 'name', 'attr_create', 'attr_edit', 'attr_delete', 'attr_fonts', 'attr_colors', 'attr_toolbar')
    def _onchange_generate_arch(self):
        if not self.custom_arch:
            self.arch = self._get_view_arch()

    @api.multi
    def _get_view_arch(self):
        if self.custom_arch:
            return self.arch
        else:
            template_obj = self.env['document.template']
            return template_obj.render_template('builder.view_arch_tree.xml.jinja2', {
                'this': self,
                'string': self.name,
                'create': self.attr_create,
                'fields': self.field_ids,
                'edit': self.attr_edit,
                'delete': self.attr_delete,
                'toolbar': self.attr_toolbar,
                'fonts': self.attr_fonts,
                'colors': self.attr_colors,
            })


class TreeField(models.Model):
    _name = 'builder.views.tree.field'
    _inherit = 'builder.views.abstract.field'

    view_id = fields.Many2one('builder.views.tree', string='View', ondelete='cascade')
    widget = fields.Selection(FIELD_WIDGETS_ALL, 'Widget')
    widget_options = fields.Char('Widget Options')

    nolabel = fields.Boolean('Hide Label')

    invisible = fields.Boolean('Invisible')
    readonly = fields.Boolean('Readonly')
    domain = fields.Char('Domain')

    @api.one
    @api.depends('field_id.ttype', 'view_id')
    def _compute_field_type(self):
        if self.field_id:
            self.field_ttype = self.field_id.ttype


