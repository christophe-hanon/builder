from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class CalendarView(models.Model):
    _name = 'builder.views.calendar'
    _inherit = 'builder.views.abstract'

    field_ids = fields.One2many('builder.views.calendar.field', 'view_id', 'Items')


class CalendarField(models.Model):
    _name = 'builder.views.calendar.field'
    _inherit = 'builder.views.abstract.field'

    view_id = fields.Many2one('builder.views.calendar', string='View', ondelete='cascade')
    