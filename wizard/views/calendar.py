from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class CalendarWizard(models.Model):
    _inherit = 'builder.wizard.views.abstract'
    _name = 'builder.wizard.views.calendar'

    attr_date_start_field_id = fields.Many2one('builder.ir.model.fields', 'Date Start Field', ondelete='set null', required=True)
    attr_date_start_ttype = fields.Char('Start Date Field Type')
    attr_date_stop_field_id = fields.Many2one('builder.ir.model.fields', 'Date Stop Field', ondelete='set null')
    attr_day_length_field_id = fields.Many2one('builder.ir.model.fields', 'Day Length Field', ondelete='set null')
    attr_date_delay_field_id = fields.Many2one('builder.ir.model.fields', 'Date Delay Field', ondelete='set null')
    attr_all_day = fields.Boolean('All Day')
    attr_use_contacts = fields.Boolean('Use Contacts', help="If this field is set to true, we will use the calendar_friends model as filter and not the color field.")
    attr_color_field_id = fields.Many2one('builder.ir.model.fields', 'Color Field', ondelete='set null')
    attr_color_ttype = fields.Char('Color Field Type')
    attr_color_is_attendee = fields.Boolean('Color is Attendee')
    attr_event_open_popup = fields.Char('Event Open Popup', help="If this field is set ot true, we don't open the event in form view, but in a popup with the view_id passed by this parameter")
    attr_avatar_filter = fields.Char('Avatar Filter')
    attr_avatar_model = fields.Char('Avatar Model')
    attr_avatar_title = fields.Char('Avatar Title')
    attr_quick_add = fields.Selection([(False, 'No Quick Create'), (True, 'Quick Create')], 'Quick Create')
    attr_display = fields.Char('Display Format', help='The display format which will be used to display the event where fields are between "[" and "]"')


    field_ids = fields.One2many('builder.wizard.views.calendar.field', 'wizard_id', 'Items')

    _defaults = {
        'view_type': 'calendar'
    }

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

    @api.onchange('view_custom_arch', 'attr_string', 'field_ids', 'attr_date_start_field_id', 'attr_date_stop_field_id', 'attr_date_delay_field_id', 'attr_day_length_field_id', 'attr_color_field_id', 'attr_all_day', 'attr_use_contacts', 'attr_event_open_popup', 'attr_avatar_filter', 'attr_avatar_model', 'attr_avatar_title', 'attr_display', 'attr_quick_add')
    def _onchange_generate_arch(self):
        self.view_arch = self._get_view_arch()

    @api.multi
    def _get_view_arch(self):
        if self.view_custom_arch:
            return self.view_arch
        else:
            template_obj = self.env['document.template']
            return template_obj.render_template('builder.view_arch_calendar.xml', {
                'this': self,
                'string': self.attr_string,
                'date_start': self.attr_date_start_field_id and self.attr_date_start_field_id.name or False,
                'date_stop': self.attr_date_stop_field_id and self.attr_date_stop_field_id.name or False,
                'date_delay': self.attr_date_delay_field_id and self.attr_date_delay_field_id.name or False,
                'day_length': self.attr_day_length_field_id and self.attr_day_length_field_id.name or False,
                'color': self.attr_color_field_id and self.attr_color_field_id.name or False,
                'color_is_attendee': self.attr_color_is_attendee,
                'all_day': self.attr_all_day,
                'use_contacts': self.attr_use_contacts,
                'event_open_popup': self.attr_event_open_popup,
                'avatar_filter': self.attr_avatar_filter,
                'avatar_model': self.attr_avatar_model,
                'avatar_title': self.attr_avatar_title,
                'quick_add': self.attr_quick_add,
                'display': self.attr_display,
                'fields': self.field_ids,
            })


class CalendarField(models.Model):
    _name = 'builder.wizard.views.calendar.field'
    _inherit = 'builder.wizard.views.abstract.field'

    invisible = fields.Boolean('Invisible')
    wizard_id = fields.Many2one('builder.wizard.views.calendar', string='Wizard', ondelete='cascade')