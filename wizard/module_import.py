__author__ = 'one'

from openerp import models, api, fields, _


class ModuleImport(models.TransientModel):
    _name = 'builder.ir.module.module.import.wizard'

    file = fields.Binary('File', required=True)

    @api.one
    def action_import(self):

        return {'type': 'ir.actions.act_window_close'}