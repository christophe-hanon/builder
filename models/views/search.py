from collections import defaultdict
from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class SearchView(models.Model):
    _name = 'builder.views.search'

    _inherit = ['ir.mixin.polymorphism.subclass', 'builder.views.abstract']

    _inherits = {
        'builder.ir.ui.view': 'view_id'
    }

    view_id = fields.Many2one('builder.ir.ui.view', string='View', required=True, ondelete='cascade')
    field_ids = fields.One2many('builder.views.search.field', 'view_id', 'Search Items')

    _defaults = {
        'type': 'search',
        'custom_arch': False,
        'subclass_model': lambda s, c, u, cxt=None: s._name,
    }

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.name = self.model_id.name
        self.xml_id = "view_{snake}_search".format(snake = snake_case(self.model_id.model))

    @api.multi
    def find_field_by_name(self, name):
        field_obj = self.env['builder.ir.model.fields']
        return field_obj.search([('model_id', '=', self.id), ('name', '=', name)])

    @api.onchange('custom_arch', 'name', 'field_ids' )
    def _onchange_generate_arch(self):
        self.arch = self._get_view_arch()

    @api.multi
    def _get_view_arch(self):
        if self.custom_arch:
            return self.arch
        else:
            groups = defaultdict(list)
            flat = []
            for field in self.field_ids:
                if field.group:
                    groups[field.group].append(field)
                else:
                    flat.append(field)

            template_obj = self.env['document.template']
            return template_obj.render_template('builder.view_arch_search.xml', {
                'this': self,
                'string': self.name,
                'fields': self.field_ids,
                'ungrouped_fields': flat,
                'groups': groups,
            })



class SearchField(models.Model):
    _name = 'builder.views.search.field'
    _inherit = 'builder.views.abstract.field'

    _order = 'view_id, sequence, id'

    view_id = fields.Many2one('builder.views.search', string='View', ondelete='cascade')
    type = fields.Selection([('field', 'Field'), ('filter', 'Filter'), ('separator', 'Separator')], string='Type', required=False, default='field')
    field_id = fields.Many2one('builder.ir.model.fields', string='Field', required=False, ondelete='cascade')
    group_field_id = fields.Many2one('builder.ir.model.fields', string='Group By', ondelete='set null')
    group = fields.Char('Group')
    attr_name = fields.Char('Name')
    attr_string = fields.Char('String')
    attr_filter_domain = fields.Char('Filter Domain')
    attr_domain = fields.Char('Domain')
    attr_operator = fields.Char('Operator')
    attr_help = fields.Char('Help')

    @api.one
    @api.depends('field_id.ttype', 'view_id')
    def _compute_field_type(self):
        if self.field_id:
            self.field_ttype = self.field_id.ttype
