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

    _defaults = {
        'view_type': 'graph'
    }

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.attr_string = self.model_id.name
        self.view_id = "view_{snake}_graph".format(snake = snake_case(self.model_id.model))

    @api.onchange('view_custom_arch', 'attr_type', 'attr_stacked', 'attr_orientation', 'attr_string', 'field_ids')
    def _onchange_generate_arch(self):
        self.view_arch = self._get_view_arch()

    @api.multi
    def _get_view_arch(self):
        if self.view_custom_arch:
            return self.view_arch
        else:
            template_obj = self.env['document.template']
            return template_obj.render_template('builder.view_arch_graph.xml', {
                'this': self,
                'string': self.attr_string,
                'type': self.attr_type,
                'orientation': self.attr_orientation,
                'stacked': self.attr_stacked,
                'fields': self.field_ids,
            })

class GraphField(models.Model):
    _name = 'builder.wizard.views.graph.field'
    _inherit = 'builder.wizard.views.abstract.field'

    wizard_id = fields.Many2one('builder.wizard.views.graph', string='Wizard', ondelete='cascade')
    operator = fields.Selection([('+', '+')], 'Operator')
    type = fields.Selection([('row', 'row'), ('col', 'col'), ('measure', 'measure')], 'Type')
    interval = fields.Selection([('month', 'month'), ('year', 'year'), ('day', 'day')], 'Interval')
