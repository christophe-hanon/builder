from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class GanttWizard(models.Model):
    _name = 'builder.wizard.views.gantt'
    _inherit = 'builder.wizard.views.abstract'

    field_ids = fields.One2many('builder.wizard.views.gantt.field', 'wizard_id', 'Items')

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.attr_string = self.model_id.name
        self.view_id = "view_{snake}_gantt".format(snake = snake_case(self.model_id.model))



class GanttField(models.Model):
    _name = 'builder.wizard.views.gantt.field'
    _inherit = 'builder.wizard.views.abstract.field'

    wizard_id = fields.Many2one('builder.wizard.views.gantt', string='Wizard', ondelete='cascade')
    