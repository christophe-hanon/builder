from openerp.fields import _RelationalMulti

__author__ = 'charlie'

class ExportJson:

    env = None

    def __init__(self,enviroment):
        self.env = enviroment

    def __get_column_values(self,module, inverse_field=[]):

        auto_field = ['id','_log_access','create_date','create_uid','write_date','write_uid']

        columns = [column for column in module._columns
                   if not column in auto_field and not column in inverse_field]

        object = module.read([column for column in columns])[0]

        object = { k:v for k,v in object.iteritems() if v }

        object.pop('id')

        return object


    def __get_link_column(self,module,record):

        return [column for column in record.keys()
                        if module._fields[column].relational and
                           not module._fields[column].compute and record.get(column)]


    def build_json(self,module,inverse_field=[]):

        record = self.__get_column_values(module,inverse_field)

        link_columns = self.__get_link_column(module,record)

        for column in link_columns:
            comodel_name = module._fields[column].comodel_name

            values = record.pop(column)

            relational_multi = issubclass(module._fields[column].__class__,_RelationalMulti)

            record[column] = {'comodel_name': comodel_name,
                              'relational_multi': 1 if relational_multi else 0}

            if relational_multi:
                record[column]['recordset'] = []
                for value in values:
                    recordset = self.env[comodel_name].search([['id', '=', value]])
                    record[column]['recordset'].append(self.build_json(recordset,[module._fields[column].inverse_name]))
            else:

                recordset = self.env[comodel_name].search([['id',"=",values[0]]])

                rec_ = self.__get_column_values(recordset)

                for k in self.__get_link_column(recordset,rec_):
                    rec_.pop(k)

                record[column]['recordset'] = rec_

        return record

