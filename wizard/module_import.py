import StringIO
from base64 import decodestring
import json
from openerp.addons.builder.tools.formats.json import JsonImport
from openerp.addons.builder.models.module import get_module_importers

__author__ = 'one'

from openerp import models, api, fields, _


class ModuleImport(models.TransientModel):
    _name = 'builder.ir.module.module.import.wizard'

    @api.model
    def _get_import_types(self):
        return get_module_importers(self.env['builder.ir.module.module'])

    import_type = fields.Selection(_get_import_types, 'Format', required=True)
    file = fields.Binary('File', required=True)


    @api.one
    def action_import(self):
        """
        :type self: ModuleImport
        """
        obj = self.env['builder.ir.module.module']

        getattr(obj, '_import_{type}'.format(type=self.import_type))(self)

        return {'type': 'ir.actions.act_window_close'}
