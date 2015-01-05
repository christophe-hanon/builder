from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class GanttWizard(models.Model):
    _name = 'builder.wizard.views.gantt'
    _inherit = 'builder.wizard.views.abstract'

    attr_create = fields.Boolean('Allow Create', default=True)
    attr_edit = fields.Boolean('Allow Edit', default=True)
    attr_delete = fields.Boolean('Allow Delete', default=True)
    attr_date_start_field_id = fields.Many2one('builder.ir.model.fields', 'Date Start Field', ondelete='set null', required=True)
    attr_date_stop_field_id = fields.Many2one('builder.ir.model.fields', 'Date Stop Field', ondelete='set null')
    attr_date_delay_field_id = fields.Many2one('builder.ir.model.fields', 'Date Delay Field', ondelete='set null')
    attr_progress_field_id = fields.Many2one('builder.ir.model.fields', 'Progress Field', ondelete='set null')
    attr_default_group_by_field_id = fields.Many2one('builder.ir.model.fields', 'Default Group By Field', ondelete='set null')


    field_ids = fields.One2many('builder.wizard.views.gantt.field', 'wizard_id', 'Items')

    _defaults = {
        'view_type': 'gantt'
    }

    @api.onchange('model_id')
    def _onchange_model_id(self):
        self.attr_string = self.model_id.name
        self.view_id = "view_{snake}_gantt".format(snake = snake_case(self.model_id.model))

    @api.onchange('view_custom_arch', 'attr_create', 'attr_edit', 'attr_delete', 'attr_date_start_field_id', 'attr_date_stop_field_id', 'attr_date_delay_field_id', 'attr_progress_field_id', 'attr_default_group_by_field_id', 'attr_string')
    def _onchange_generate_arch(self):
        self.view_arch = self._get_view_arch()

    @api.multi
    def _get_view_arch(self):
        if self.view_custom_arch:
            return self.view_arch
        else:
            template_obj = self.env['document.template']
            return template_obj.render_template('builder.view_arch_gantt.xml', {
                'this': self,
                'string': self.attr_string,
                'create': self.attr_create,
                'edit': self.attr_edit,
                'delete': self.attr_delete,
                'date_start': self.attr_date_start_field_id and self.attr_date_start_field_id.name or False,
                'date_stop': self.attr_date_stop_field_id and self.attr_date_stop_field_id.name or False,
                'date_delay': self.attr_date_delay_field_id and self.attr_date_delay_field_id.name or False,
                'progress': self.attr_progress_field_id and self.attr_progress_field_id.name or False,
                'default_group_by': self.attr_default_group_by_field_id and self.attr_default_group_by_field_id.name or False,
            })


class GanttField(models.Model):
    _name = 'builder.wizard.views.gantt.field'
    _inherit = 'builder.wizard.views.abstract.field'

    wizard_id = fields.Many2one('builder.wizard.views.gantt', string='Wizard', ondelete='cascade')
    