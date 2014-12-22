from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class GraphWizard(models.Model):
    _name = 'builder.wizard.views.graph'
    _inherit = 'builder.wizard.views.abstract'

    attr_type = fields.Selection([('bar', 'Bar'), ('pie', 'Pie'), ('line', 'Line'), ('pivot', 'Pivot')], 'Type')
    attr_stacked = fields.Boolean('Stacked')
    attr_orientation = fields.Selection([('horizontal', 'Horizontal'), ('vertical', 'Vertical')], 'Orientation')
    field_ids = fields.One2many('builder.wizard.views.graph.field', 'wizard_id', 'Items')

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.attr_string = self.model_id.name
        self.view_id = "view_{snake}_graph".format(snake = snake_case(self.model_id.model))



class GraphField(models.Model):
    _name = 'builder.wizard.views.graph.field'
    _inherit = 'builder.wizard.views.abstract.field'

    wizard_id = fields.Many2one('builder.wizard.views.graph', string='Wizard', ondelete='cascade')
    operator = fields.Selection([('+', '+')], 'Operator')
    type = fields.Selection([('row', 'row'), ('col', 'col'), ('measure', 'measure')], 'Type')
    interval = fields.Selection([('month', 'month'), ('year', 'year'), ('day', 'day')], 'Interval')
