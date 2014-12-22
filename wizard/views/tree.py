from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class TreeWizard(models.Model):
    _name = 'builder.wizard.views.tree'
    _inherit = 'builder.wizard.views.abstract'

    attr_create = fields.Boolean('Allow Create', default=True)
    attr_edit = fields.Boolean('Allow Edit', default=True)
    attr_delete = fields.Boolean('Allow Delete', default=True)
    field_ids = fields.One2many('builder.wizard.views.tree.field', 'wizard_id', 'Fields')
    attr_toolbar = fields.Boolean('Show Toolbar', default=True)
    attr_fonts = fields.Char('Fonts', help='Font definition. Ex: bold:message_unread==True')
    attr_colors = fields.Char('Colors', help='Color definition. Ex: "gray:probability == 100;red:date_deadline and (date_deadline &lt; current_date)"')

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.attr_string = self.model_id.name
        self.view_id = "view_{snake}_tree".format(snake = snake_case(self.model_id.model))

        if not len(self.field_ids):
            field_list = []
            for field in self.model_id.field_ids:
                if field.ttype not in ['binary', 'one2many', 'many2many']:
                    field_list.append({'field_id': field.id, 'field_ttype': field.ttype, 'model_id': self.model_id.id, 'special_states_field_id': self.model_id.special_states_field_id.id})

            self.field_ids = field_list


class TreeField(models.Model):
    _name = 'builder.wizard.views.tree.field'
    _inherit = 'builder.wizard.views.abstract.field'

    wizard_id = fields.Many2one('builder.wizard.views.tree', string='Wizard', ondelete='cascade')
    widget = fields.Selection(FIELD_WIDGETS_ALL, 'Widget')
    widget_options = fields.Char('Widget Options')

    nolabel = fields.Boolean('Hide Label')

    invisible = fields.Boolean('Invisible')
    readonly = fields.Boolean('Readonly')
    domain = fields.Char('Domain')

    @api.one
    @api.depends('field_id.ttype', 'wizard_id')
    def _compute_field_type(self):
        if self.field_id:
            self.field_ttype = self.field_id.ttype


