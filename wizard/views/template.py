from openerp.addons.builder.models.fields import snake_case
from openerp import models, fields, api, _
from .base import FIELD_WIDGETS_ALL

__author__ = 'one'


class CalendarWizard(models.Model):
    _name = 'builder.wizard.views.calendar'
    _inherit = 'builder.wizard.views.abstract'

    field_ids = fields.One2many('builder.wizard.views.calendar.field', 'wizard_id', 'Items')


class CalendarField(models.Model):
    _name = 'builder.wizard.views.calendar.field'
    _inherit = 'builder.wizard.views.abstract.field'

    wizard_id = fields.Many2one('builder.wizard.views.calendar', string='Wizard', ondelete='cascade')
    