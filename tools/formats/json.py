from StringIO import StringIO
import simplejson
import zipfile
import zlib
import openerp
from openerp.fields import _RelationalMulti

__author__ = 'charlie'


class JsonExport:
    env = None

    def __init__(self, enviroment):
        self.env = enviroment

    def __get_column_values(self, module, inverse_field=[]):

        auto_field = ['id', '_log_access', 'create_date', 'create_uid', 'write_date', 'write_uid']

        columns = [column for column in module._columns
                   if not column in auto_field and not column in inverse_field]

        object = module.read([column for column in columns])[0]

        object = {k: v for k, v in object.iteritems() if v}

        object.pop('id')

        return object


    def __get_link_column(self, module, record):

        return [column for column in record.keys()
                if module._fields[column].relational and
                not module._fields[column].compute and record.get(column)]


    def build_json(self, model, inverse_field=[]):

        record = self.__get_column_values(model, inverse_field)

        link_columns = self.__get_link_column(model, record)

        for column in link_columns:
            comodel_name = model._fields[column].comodel_name

            values = record.pop(column)

            relational_multi = issubclass(model._fields[column].__class__, _RelationalMulti)

            record[column] = {'comodel_name': comodel_name,
                              'relational_multi': 1 if relational_multi else 0}

            if relational_multi:
                record[column]['recordset'] = []
                record_inverse_field = [model._fields[column].inverse_name] if hasattr(model._fields[column], 'inverse_name') else []
                for value in values:
                    recordset = self.env[comodel_name].search([['id', '=', value]])
                    record[column]['recordset'].append(
                        self.build_json(recordset, record_inverse_field))
            else:

                recordset = self.env[comodel_name].search([['id', "=", values[0]]])

                rec_ = self.__get_column_values(recordset)

                for k in self.__get_link_column(recordset, rec_):
                    rec_.pop(k)

                record[column]['recordset'] = rec_

        return record

    def export(self, module):
        zfileIO = StringIO()

        data = self.build_json(module)

        json_module = {
            'version': '1.0',
            'odoo_version': '8.0',
            'data': data
        }

        raw = zlib.compress(simplejson.dumps(json_module), zlib.Z_BEST_COMPRESSION)

        zfileIO.write(raw)
        zfileIO.flush()
        return zfileIO


class JsonImport:
    env = None

    def __init__(self, enviroment):
        self.env = enviroment

    def build(self, model_obj, file_data):
        json_dump = simplejson.loads(zlib.decompress(file_data))
        return self.build_model(model_obj, json_dump['data'])

    def build_model(self, model_obj, data, inverse_field={}):
        relational_multi = {}
        relational = {}
        related_fields = {}

        for k,v in data.iteritems():
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

        record = model_obj.create(related_fields)

        for k,v in relational_multi.iteritems():
            comodel = self.env[v['comodel_name']]

            for rec_ in v['recordset']:
              self.build_model(comodel,rec_,{record._fields[k].inverse_name:record.id})


        for k,v in relational.iteritems():
            comodel = self.env[v['comodel_name']]

            search_query =[(k_,"=",v_) for k_,v_ in v['recordset'].iteritems()]
            rec_ = comodel.search(search_query,limit = 1)
            record.write({k:rec_.id})

        return record