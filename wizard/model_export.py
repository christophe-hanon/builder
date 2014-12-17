__author__ = 'one'

from openerp import models, api, fields, _




class ModelImport(models.TransientModel):
    _name = 'builder.ir.model.export.wizard'

    @api.one
    def _get_export_types(self):
        available_formats = self.env['builder.ir.module.module'].get_available_export_formats()
        return [(r['type'], r['name']) for r in available_formats]

    export_type = fields.Selection(_get_export_types, 'Format', required=True)

    @api.one
    def action_export(self):
        module = self.env[self.env.context.get('active_model')].search([('id', '=', self.env.context.get('active_id'))])
        print "exported!!"
        return {'type': 'ir.actions.act_window_close'}
