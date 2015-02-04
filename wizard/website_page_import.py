__author__ = 'one'

from openerp import models, api, fields, _


class PageImport(models.TransientModel):
    _name = 'builder.website.page.import.wizard'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='CASCADE')
    page_ids = fields.Many2many('ir.ui.view', 'builder_website_page_import_wizard_rel', 'wizard_id', 'view_id', 'Pages', domain="[('type', '=', 'qweb'), ('page', '=', True)]")
    include_menu = fields.Boolean('Include Menu', default=True)

    @api.one
    def action_import(self):
        # asset = self.env[self.env.context.get('active_model')].search([('id', '=', self.env.context.get('active_id'))])
        page_item_model = self.env['builder.website.page']
        menu_item_model = self.env['builder.website.menu']

        for page in self.page_ids:
            data = self.env['ir.model.data'].search([('model', '=', 'ir.ui.view'), ('res_id', '=', page.id)])
            current_page = page_item_model.search([('module_id', '=', self.module_id.id), ('attr_id', '=', data.name)])

            if not current_page.id:
                new_item = page_item_model.create({
                    'module_id': self.module_id.id,
                    'attr_id': data.name,
                    'attr_name': page.name,
                    'content': page.arch,
                    'attr_page': True,
                    'wrap_layout': 'website.layout',
                    'attr_priority': page.priority,
                })

        return {'type': 'ir.actions.act_window_close'}