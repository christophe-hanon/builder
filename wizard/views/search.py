from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class SearchWizard(models.Model):
    _name = 'builder.wizard.views.search'
    _inherit = 'builder.wizard.views.abstract'

    field_ids = fields.One2many('builder.wizard.views.search.field', 'wizard_id', 'Search Items')
    ungrouped_field_ids = fields.One2many('builder.wizard.views.search.field', 'wizard_id', 'Search Items', compute='_compute_field_groups')
    grouped_field_ids = fields.One2many('builder.wizard.views.search.field', 'wizard_id', 'Search Items', compute='_compute_field_groups')
    group_ids = fields.One2many('builder.wizard.views.search.group', 'wizard_id', 'Search Groups')

    _defaults = {
        'view_type': 'search'
    }

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.attr_string = self.model_id.name
        self.view_id = "view_{snake}_search".format(snake = snake_case(self.model_id.model))

    @api.multi
    def find_field_by_name(self, name):
        field_obj = self.env['builder.ir.model.fields']
        return field_obj.search([('model_id', '=', self.id), ('name', '=', name)])

    @api.one
    @api.depends('field_ids', 'field_ids.group_id')
    def _compute_field_groups(self):
        field_obj = self.env['builder.wizard.views.search.field']
        self.ungrouped_field_ids = field_obj.search([('wizard_id', '=', self.id), ('group_id', '=', False)])
        self.grouped_field_ids = field_obj.search([('wizard_id', '=', self.id), ('group_id', '<>', False)])

    @api.onchange('view_custom_arch', 'attr_string', 'group_ids', 'field_ids' )
    def _onchange_generate_arch(self):
        self.view_arch = self._get_view_arch()

    @api.multi
    def _get_view_arch(self):
        if self.view_custom_arch:
            return self.view_arch
        else:
            groups = {}
            ungrouped = []
            for field in self.field_ids:
                if field.group_id.id:
                    if not field.group_id.id in groups:
                        groups[field.group_id.id] = {'group': field.group_id, 'fields': []}
                    groups[field.group_id.id]['fields'].append(field)
                else:
                    ungrouped.append(field)

            template_obj = self.env['document.template']
            return template_obj.render_template('builder.view_arch_search.xml', {
                'this': self,
                'string': self.attr_string,
                'fields': self.field_ids,
                'ungrouped_fields': ungrouped,
                # 'ungrouped_fields': [field for field in self.field_ids if not field.group_id],
                # 'groups': self.group_ids,
                'groups': groups,
            })



class SearchGroup(models.Model):
    _name = 'builder.wizard.views.search.group'

    _order = 'sequence, name'

    wizard_id = fields.Many2one('builder.wizard.views.search', string='Wizard', ondelete='cascade')
    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence')
    expand = fields.Boolean('Expand')
    field_ids = fields.One2many('builder.wizard.views.search.field', 'group_id', 'Items')


class SearchField(models.Model):
    _name = 'builder.wizard.views.search.field'
    _inherit = 'builder.wizard.views.abstract.field'

    _order = 'wizard_id, sequence, id'

    wizard_id = fields.Many2one('builder.wizard.views.search', string='Wizard', ondelete='cascade')
    type = fields.Selection([('field', 'Field'), ('filter', 'Filter'), ('separator', 'Separator')], string='Type', required=False, default='field')
    field_id = fields.Many2one('builder.ir.model.fields', string='Field', required=False, ondelete='cascade')
    group_field_id = fields.Many2one('builder.ir.model.fields', string='Group By', ondelete='set null')
    group_id = fields.Many2one('builder.wizard.views.search.group', string='Group', required=False, ondelete='set null')
    attr_name = fields.Char('Name')
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
