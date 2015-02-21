from openerp.addons.builder.models.module import get_module_exporters

__author__ = 'one'

from openerp import models, api, fields, _


class ModelImport(models.TransientModel):
    _name = 'builder.ir.model.export.wizard'

    @api.model
    def _get_export_types(self):
        return get_module_exporters(self.env['builder.ir.module.module'])

    export_type = fields.Selection(_get_export_types, 'Format', required=True)

    @api.multi
    def action_export(self):
        module = self.env[self.env.context.get('active_model')].search([('id', '=', self.env.context.get('active_id'))])

        return {
            'type': 'ir.actions.act_url',
            'url': '/builder/export/{format}/{id}'.format(id=module.id, format=self.export_type),
            'target': 'self'
        }
