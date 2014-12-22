from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class CalendarWizard(models.Model):
    _inherit = 'builder.wizard.views.abstract'
    _name = 'builder.wizard.views.calendar'

    attr_color_field_id = fields.Many2one('builder.ir.model.fields', 'Color Field', ondelete='set null')
    attr_color_ttype = fields.Char('Color Field Type', store=False)
    attr_date_start_field_id = fields.Many2one('builder.ir.model.fields', 'Date Start Field', ondelete='set null', required=True)
    attr_date_start_ttype = fields.Char('Start Date Field Type', store=False)
    attr_date_stop_field_id = fields.Many2one('builder.ir.model.fields', 'Date Stop Field', ondelete='set null')
    attr_day_length_field_id = fields.Many2one('builder.ir.model.fields', 'Day Length Field', ondelete='set null')
    attr_date_delay_field_id = fields.Many2one('builder.ir.model.fields', 'Date Delay Field', ondelete='set null')
    attr_all_day = fields.Boolean('All Day')
    attr_use_contacts = fields.Boolean('Use Contacts', help="If this field is set to true, we will use the calendar_friends model as filter and not the color field.")
    attr_color_is_attendee = fields.Boolean('Color is Attendee')
    field_ids = fields.One2many('builder.wizard.views.calendar.field', 'wizard_id', 'Items')

    @api.onchange('attr_date_start_field_id')
    def _compute_calendar_attr_date_start_ttype(self):
        self.attr_date_start_ttype = self.attr_date_start_field_id.ttype if self.attr_date_start_field_id else False

    @api.onchange('attr_color_field_id')
    def _compute_calendar_attr_color_ttype(self):
        self.attr_color_ttype = self.attr_color_field_id.ttype if self.attr_color_field_id else False

    @api.onchange('model_id')
    def _onchange_calendar_view(self):
        self.attr_string = self.model_id.name
        self.view_id = "view_{snake}_calendar".format(snake = snake_case(self.model_id.model))


class CalendarField(models.Model):
    _name = 'builder.wizard.views.calendar.field'
    _inherit = 'builder.wizard.views.abstract.field'

    invisible = fields.Boolean('Invisible')
