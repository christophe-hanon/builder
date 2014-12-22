from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class SearchWizard(models.Model):
    _name = 'builder.wizard.views.search'
    _inherit = 'builder.wizard.views.abstract'

    field_ids = fields.One2many('builder.wizard.views.search.field', 'wizard_id', 'Search Items')

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.attr_string = self.model_id.name
        self.view_id = "view_{snake}_search".format(snake = snake_case(self.model_id.model))



class SearchGroup(models.Model):
    _name = 'builder.wizard.views.search.group'

    _order = 'sequence, name'

    wizard_id = fields.Many2one('builder.wizard.views.search', string='Wizard', ondelete='cascade')
    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence')
    expand = fields.Boolean('Expand')
    item_ids = fields.One2many('builder.wizard.views.search.field', 'group_id', 'Items')


class SearchField(models.Model):
    _name = 'builder.wizard.views.search.field'
    _inherit = 'builder.wizard.views.abstract.field'

    wizard_id = fields.Many2one('builder.wizard.views.search', string='Wizard', ondelete='cascade')
    type = fields.Selection([('field', 'Field'), ('filter', 'Filter'), ('separator', 'Separator')], string='Type', required=False, default='field')
    field_id = fields.Many2one('builder.ir.model.fields', string='Field', required=False, ondelete='cascade')
    group_field_id = fields.Many2one('builder.ir.model.fields', string='Group By', ondelete='set null')
    group_id = fields.Many2one('builder.wizard.views.search.group', string='Group', required=False, ondelete='set null')
    attr_string = fields.Char('String')
    attr_filter_domain = fields.Char('Filter Domain')
    attr_domain = fields.Char('Domain')
    attr_operator = fields.Char('Operator')
    attr_help = fields.Char('Help')

    @api.one
    @api.depends('field_id.ttype', 'wizard_id')
    def _compute_field_type(self):
        if self.field_id:
            self.field_ttype = self.field_id.ttype
