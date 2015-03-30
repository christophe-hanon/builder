from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class GraphView(models.Model):
    _name = 'builder.views.graph'

    _inherit = ['ir.mixin.polymorphism.subclass', 'builder.views.abstract']

    _inherits = {
        'builder.ir.ui.view': 'view_id'
    }

    view_id = fields.Many2one('builder.ir.ui.view', string='View', required=True, ondelete='cascade')
    attr_type = fields.Selection([('bar', 'Bar'), ('pie', 'Pie'), ('line', 'Line'), ('pivot', 'Pivot')], 'Type')
    attr_stacked = fields.Boolean('Stacked')
    attr_orientation = fields.Selection([('horizontal', 'Horizontal'), ('vertical', 'Vertical')], 'Orientation')
    field_ids = fields.One2many('builder.views.graph.field', 'view_id', 'Items')

    _defaults = {
        'type': 'graph',
        'custom_arch': False,
        'subclass_model': lambda s, c, u, cxt=None: s._name,
        'inherit_view_xpath': '//graph'
    }

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.name = self.model_id.name
        self.xml_id = "view_{snake}_graph".format(snake = snake_case(self.model_id.model))
        self.model_inherit_type = self.model_id.inherit_type #shouldn`t be doing that
        self.model_name = self.model_id.model #shouldn`t be doing that

    @api.onchange('custom_arch', 'attr_type', 'attr_stacked', 'attr_orientation', 'name', 'field_ids')
    def _onchange_generate_arch(self):
        self.arch = self._get_view_arch()

    @api.multi
    def _get_view_arch(self):
        if self.custom_arch:
            return self.arch
        else:
            template_obj = self.env['document.template']
            return template_obj.render_template('builder.view_arch_graph.xml.jinja2', {
                'this': self,
                'string': self.name,
                'type': self.attr_type,
                'orientation': self.attr_orientation,
                'stacked': self.attr_stacked,
                'fields': self.field_ids,
            })

class GraphField(models.Model):
    _name = 'builder.views.graph.field'
    _inherit = 'builder.views.abstract.field'

    view_id = fields.Many2one('builder.views.graph', string='View', ondelete='cascade')
    operator = fields.Selection([('+', '+')], 'Operator')
    type = fields.Selection([('row', 'row'), ('col', 'col'), ('measure', 'measure')], 'Type')
    interval = fields.Selection([('month', 'month'), ('year', 'year'), ('day', 'day')], 'Interval')
