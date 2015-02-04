__author__ = 'one'

from openerp import models, api, fields, _


class ModelImport(models.TransientModel):
    _name = 'builder.website.asset.data.wizard'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='CASCADE')
    data_ids = fields.Many2many('builder.data.file', 'builder_website_asset_data_file_rel', 'wizard_id', 'data_id', 'Files')

    @api.one
    def action_import(self):
        asset = self.env[self.env.context.get('active_model')].search([('id', '=', self.env.context.get('active_id'))])
        asset_item_model = self.env['builder.website.asset.item']

        for data_file in self.data_ids:
            current_file = self.env['builder.website.asset.item'].search([('asset_id', '=', asset.id), ('file_id', '=', data_file.id)])

            if not current_file.id:
                new_item = asset_item_model.create({
                    'asset_id': asset.id,
                    'file_id': data_file.id,
                })

        return {'type': 'ir.actions.act_window_close'}