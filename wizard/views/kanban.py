from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class KanbanWizard(models.Model):
    _name = 'builder.wizard.views.kanban'
    _inherit = 'builder.wizard.views.abstract'

    attr_create = fields.Boolean('Allow Create', default=True)
    attr_edit = fields.Boolean('Allow Edit', default=True)
    attr_delete = fields.Boolean('Allow Delete', default=True)
    attr_default_group_by_field_id = fields.Many2one('builder.ir.model.fields', 'Default Group By Field', ondelete='set null')
    attr_template = fields.Text('Template')
    attr_quick_create = fields.Boolean('Quick Create', default=True)
    # attr_quick_create = fields.Selection([(1, 'Quick Create'), (2, 'No Quick Create')], 'Quick Create')
    field_ids = fields.Many2many('builder.ir.model.fields', 'builder_wizard_views_kanban_field_rel', 'wizard_id', 'field_id', 'Items')
    # field_ids = fields.One2many('builder.wizard.views.kanban.field', 'wizard_id', 'Items')


    _defaults = {
        'view_type': 'kanban'
    }

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.attr_string = self.model_id.name
        self.view_id = "view_{snake}_kanban".format(snake = snake_case(self.model_id.model))


    @api.onchange('view_custom_arch', 'field_ids', 'attr_string', 'attr_create', 'attr_edit', 'attr_delete', 'attr_template', 'attr_quick_create', 'attr_default_group_by_field_id')
    def _onchange_generate_arch(self):
        self.view_arch = self._get_view_arch()

    @api.multi
    def _get_view_arch(self):
        if self.view_custom_arch:
            return self.view_arch
        else:
            template_obj = self.env['document.template']
            return template_obj.render_template('builder.view_arch_kanban.xml', {
                'this': self,
                'string': self.attr_string,
                'create': self.attr_create,
                'fields': self.field_ids,
                'edit': self.attr_edit,
                'delete': self.attr_delete,
                'template': self.attr_template and self.attr_template or False,
                'quick_create': self.attr_quick_create,
                'default_group_by': self.attr_default_group_by_field_id and self.attr_default_group_by_field_id.name or False,
            })


class CalendarField(models.Model):
    _name = 'builder.wizard.views.kanban.field'
    _inherit = 'builder.wizard.views.abstract.field'

    wizard_id = fields.Many2one('builder.wizard.views.kanban', string='Wizard', ondelete='cascade')
    invisible = fields.Boolean('Invisible')
    