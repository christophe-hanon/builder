from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class KanbanWizard(models.Model):
    _name = 'builder.wizard.views.kanban'
    _inherit = 'builder.wizard.views.abstract'

    field_ids = fields.One2many('builder.wizard.views.kanban.field', 'wizard_id', 'Items')

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.attr_string = self.model_id.name
        self.view_id = "view_{snake}_kanban".format(snake = snake_case(self.model_id.model))



class CalendarField(models.Model):
    _name = 'builder.wizard.views.kanban.field'
    _inherit = 'builder.wizard.views.abstract.field'

    wizard_id = fields.Many2one('builder.wizard.views.kanban', string='Wizard', ondelete='cascade')
    invisible = fields.Boolean('Invisible')
    