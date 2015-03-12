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


class ModuleImportLocal(models.TransientModel):
    _name = 'builder.ir.module.module.import.local.wizard'

    module_id = fields.Many2one('ir.module.module', 'System Module', required=True)


    @api.one
    def action_import(self):
        """
        :type self: ModuleImport
        """
        obj = self.env['builder.ir.module.module']

        attrs = {
            'name': self.module_id.name,
            'shortdesc': self.module_id.shortdesc,
            'category_id': self.module_id.category_id.name_get()[0][1],
            'summary': self.module_id.summary,
            'description': self.module_id.description,
            'author': self.module_id.author,
            'maintainer': self.module_id.maintainer,
            'contributors': self.module_id.contributors,
            'website': self.module_id.website,
            'installed_version': self.module_id.installed_version,
            'latest_version': self.module_id.latest_version,
            'url': self.module_id.url,
            'auto_install': self.module_id.auto_install,
            'application': self.module_id.application,
            'image': self.module_id.icon_image,
            'icon_image': self.module_id.icon_image,
        }

        module = obj.create(attrs)

        for dep in self.module_id.dependencies_id:
            module.dependency_ids.create({'dependency_module_name': dep.name, 'dependency_module_id': self.module_id.id, 'type': 'module', 'module_id': module.id})

        model_data_obj = self.env['ir.model.data']
        imd_ids = model_data_obj.search([
                ('module', '=', self.module_id.name),
                ('model', '=', 'ir.ui.view')
        ])
        views = []
        model_names = []
        view_obj = self.env['ir.ui.view']
        for imd_res in imd_ids:
            view = view_obj.search([('id', '=', imd_res.res_id)])
            views.append(view)
            if view.model:
                model_names.append(view.model)

        sys_model_obj = self.env['ir.model']

        sys_models = sys_model_obj.search([('model', 'in', model_names)])

        model_map = {}
        for model in sys_models:
            new_model = module.model_ids.create({
                    'module_id': module.id,
                    'name': model.name,
                    'model': model.model,
                    'osv_memory': model.osv_memory,
                })
            model_map[model.model] = new_model

        self._create_model_fields(module, sys_models, model_map, False)

        for view in views:
            view_attrs = {
                'module_id': module.id,
                'model_id': model_map[view.model].id if view.model in model_map else False,
                'type': view.type,
                'priority': view.priority,
                'name': view.name,
                'xml_id': view.xml_id,
                'arch': view.arch,
                'custom_arch': True,
            }

            if view.type in ['calendar', 'search', 'tree', 'form', 'graph', 'kanban', 'gantt']:
                view_attrs['custom_arch'] = True

                mview = self.env['builder.views.' + view.type].create(view_attrs)
                mview.write({'arch': view.arch})
            else:
                module.view_ids.create(view_attrs)

        return {'type': 'ir.actions.act_window_close'}


    @api.one
    def _create_model_fields(self, module, model_items, model_map, relations_only=True):

        _review_models = []

        for model in model_items:
            module_model = self.env['builder.ir.model'].search([('module_id', '=', module.id), ('model', '=', model.model)])

            for field in model.field_id:
                if not self.env['builder.ir.model.fields'].search([('model_id', '=', module_model.id), ('name', '=', field.name)]):
                    values = {
                        'model_id': model_map[model.model].id,
                        'name': field.name,
                        'field_description': field.field_description,
                        'ttype': field.ttype,
                        'selection': field.selection,
                        'required': field.required,
                        'readonly': field.readonly,
                        'select_level': field.select_level,
                        'translate': field.translate,
                        'size': field.size,
                        'on_delete': field.on_delete,
                        'domain': field.domain,
                        'selectable': field.selectable,
                        'is_inherited': False
                    }

                    if field.ttype in ['one2many', 'many2many', 'many2one']:
                        if  field.relation in model_map:
                            values.update({
                                'relation': field.relation,
                                'relation_model_id': model_map[field.relation].id,
                                'relation_field': field.relation_field
                            })

                            _review_models.append(model)
                        else:
                            continue

                    if not relations_only or (relations_only and field.ttype in ['one2many', 'many2many', 'many2one']):
                        new_field = model_map[model.model].field_ids.create(values)

        if len(_review_models):
            self._create_model_fields(module, _review_models, model_map, relations_only)