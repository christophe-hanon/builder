import StringIO
from base64 import decodestring
import json

__author__ = 'one'

from openerp import models, api, fields, _


class ModuleImport(models.TransientModel):
    _name = 'builder.ir.module.module.import.wizard'

    file = fields.Binary('File', required=True)

    @api.one
    def action_import(self):
        f = StringIO.StringIO()
        recordset = json.loads(decodestring(self.file))

        module = self.env['builder.ir.module.module']

        self.__build_module(module,recordset)

        return {'type': 'ir.actions.act_window_close'}

    def __build_module(self,module,recordset,inverse_field={}):
        relational_multi = {}
        relational = {}
        related_fields = {}

        for k,v in recordset.iteritems():
            if isinstance(v,dict):
                if v['relational_multi'] == 1:
                    relational_multi[k] = v
                else:
                    relational[k] = v
            else:
                related_fields[k] = v

        if len(inverse_field) > 0:
            k,v = inverse_field.items()[0]
            related_fields[k] = v

        record  = module.create(related_fields)

        for k,v in relational_multi.iteritems():
            comodel = self.env[v['comodel_name']]

            for rec_ in v['recordset']:
              self.__build_module(comodel,rec_,{module._fields[k].inverse_name:record.id})


        for k,v in relational.iteritems():
            comodel = self.env[v['comodel_name']]

            search_query =[(k_,"=",v_) for k_,v_ in v['recordset'].iteritems()]
            rec_ = comodel.search(search_query,limit = 1)
            record.write({k:rec_.id})