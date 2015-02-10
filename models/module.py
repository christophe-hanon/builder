from base64 import decodestring
from collections import defaultdict
import re
from string import Template
from types import MethodType
import os
import mimetypes
from StringIO import StringIO
import zipfile
import base64
import posixpath
from openerp import models, fields, api
from openerp import _
from openerp.addons.builder.tools import simple_selection


__author__ = 'one'

MODULE_EXPORTER_RE = re.compile('_export_\w[\w_]+')
def get_module_exporters(model):
    return [
        (attr.replace('_export_', ''), attr.replace('_export_', '').capitalize()) for attr in dir(model)
        if MODULE_EXPORTER_RE.match(attr) and isinstance(getattr(model, attr), MethodType)
    ]

MODULE_IMPORTER_RE = re.compile('_import_\w[\w_]+')
def get_module_importers(model):
    return [
        (attr.replace('_import_', ''), attr.replace('_import_', '').capitalize()) for attr in dir(model)
        if MODULE_IMPORTER_RE.match(attr) and isinstance(getattr(model, attr), MethodType)
    ]


class Module(models.Model):
    _name = 'builder.ir.module.module'

    @api.model
    def _get_categories(self):
        return [(c.name, c.name) for c in self.env['ir.module.category'].search([])]

    name = fields.Char("Technical Name", required=True, select=True)
    category_id = fields.Selection(simple_selection('ir.module.category', 'name') , 'Category')
    shortdesc = fields.Char('Module Name', translate=True, required=True)
    summary = fields.Char('Summary', translate=True)
    description = fields.Text("Description", translate=True)
    description_html = fields.Html(string='Description HTML', sanitize=False)
    author = fields.Char("Author", required=True)
    maintainer = fields.Char('Maintainer')
    contributors = fields.Text('Contributors')
    website = fields.Char("Website")

    installed_version = fields.Char('Installed Version', default='0.1')
    latest_version = fields.Char('Latest Version')
    published_version = fields.Char('Published Version')
    mirror = fields.Text('CodeMirror')

    url = fields.Char('URL')
    sequence = fields.Integer('Sequence')
    # dependencies_id = fields.One2many('programming.module.dependency', 'module_id', 'Dependencies')
    auto_install = fields.Boolean('Automatic Installation',
                                   help='An auto-installable module is automatically installed by the '
                                        'system when all its dependencies are satisfied. '
                                        'If the module has no dependency, it is always installed.')
    license = fields.Selection([
        ('GPL-2', 'GPL Version 2'),
        ('GPL-2 or any later version', 'GPL-2 or later version'),
        ('GPL-3', 'GPL Version 3'),
        ('GPL-3 or any later version', 'GPL-3 or later version'),
        ('AGPL-3', 'Affero GPL-3'),
        ('Other OSI approved licence', 'Other OSI Approved Licence'),
        ('Other proprietary', 'Other Proprietary')
    ], string='License', default='AGPL-3')

    application = fields.Boolean('Application')
    icon = fields.Char('Icon URL')
    image = fields.Binary(string='Icon')
    icon_image = fields.Binary(string='Icon')

    menus_by_module = fields.Text(string='Menus')
    reports_by_module = fields.Text(string='Reports')
    views_by_module = fields.Text(string='Views')
    demo = fields.Boolean('Has Demo Data')

    models_count = fields.Integer("Models Count", compute='_compute_models_count', store=False)

    dependency_ids = fields.One2many(
        comodel_name='builder.ir.module.dependency',
        inverse_name='module_id',
        string='Dependencies',
    )

    model_ids = fields.One2many('builder.ir.model', 'module_id', 'Models')
    view_ids = fields.One2many('builder.ir.ui.view', 'module_id', 'Views')
    menu_ids = fields.One2many('builder.ir.ui.menu', 'module_id', 'Menus')
    action_ids = fields.One2many('builder.ir.actions.actions', 'module_id', 'Actions')
    action_window_ids = fields.One2many('builder.ir.actions.act_window', 'module_id', 'Window Actions')
    action_url_ids = fields.One2many('builder.ir.actions.act_url', 'module_id', 'URL Actions')

    data_file_ids = fields.One2many('builder.data.file', 'module_id', 'Data Files')
    snippet_bookmarklet_url = fields.Char('Link', compute='_compute_snippet_bookmarklet_url')

    @api.one
    @api.depends('name')
    def _compute_snippet_bookmarklet_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        link = """
javascript:(function(){
    function script(url, callback){
        var new_script = document.createElement('script');
        new_script.src = url + '?__stamp=' + Math.random();
        new_script.onload = new_script.onreadystatechange = callback;
        document.getElementsByTagName('head')[0].appendChild(new_script);
        new_script.type='text/javascript';
    };
    window.odooUrl = '$base_url';
    window.newSnippetUrl = '$base_url/builder/$module/snippet/add';
    script('$base_url/builder/static/src/js/snippet_loader.js');
})();
        """
        self.snippet_bookmarklet_url = Template(link).substitute(base_url=base_url, module=self.name, db=self.env.cr.dbname)

    @api.one
    def dependencies_as_list(self):
        return [str(dep.name) for dep in self.dependency_ids]

    @api.one
    def add_dependency(self, names):
        if not names:
            return

        dependency_obj = self.env['builder.ir.module.dependency']
        if not isinstance(names, list):
            names = [names]

        for name in names:
            if not dependency_obj.search([('module_id', '=', self.id), ('dependency_module_name', '=', name)]).id:
                dependency_obj.create({
                    'module_id': self.id,
                    'type': 'manual',
                    'dependency_module_name': name
                })

    @api.one
    @api.depends('model_ids')
    def _compute_models_count(self):
        self.models_count = len(self.model_ids)


    def get_available_import_formats(self, cr, uid, context=None):
        return [
            {
                'type': 'raw',
                'action': 'import_base_form',
                'name': _('Import Module')
            },
            {
                'type': 'dia',
                'action': 'import_base_form',
                'name': _('Import from Dia')
            }
        ]

    def get_available_export_formats(self, cr, uid, context=None):
        return [
            {
                'name': _('Export Module'),
                'type': 'raw'
            },
            {
                'name': _('Export to Dia'),
                'type': 'dia'
            }
        ]

    @api.multi
    def button_download(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/builder/download/{id}'.format(id=self.id),
            'target': 'self'
        }

    @api.multi
    def action_models(self):

        tree_view = self.env.ref('builder.builder_ir_model_tree_view', False)
        form_view = self.env.ref('builder.builder_ir_model_form_view', False)

        return {
            'name': _('Models'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form,diagram',
            'res_model': 'builder.ir.model',
            'views': [(tree_view and tree_view.id or False, 'tree'), (form_view and form_view.id or False, 'form')],
            'view_id': tree_view and tree_view.id,
            'domain': [('module_id', '=', self.id)],
            # 'target': 'current',
            'context': {
                'default_module_id': self.id
            },
        }

    @api.multi
    def action_diagram(self):

        diagram_view = self.env.ref('builder.view_builder_model_diagram', False)

        return {
            'name': _('UML Diagram'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'diagram',
            'res_model': 'builder.ir.module.module',
            'views': [(diagram_view and diagram_view.id or False, 'diagram'),],
            'view_id': diagram_view and diagram_view.id,
            'res_id': self.id,
            'target': 'new',
            # 'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}},
            'context': {
                'default_module_id': self.id,
                'diagram_view': True
            },
        }

    def action_edit_description_html(self, cr, uid, ids, context=None):
        if not len(ids) == 1:
            raise ValueError('One and only one ID allowed for this action')
        url = '/builder/page/designer?model={model}&res_id={id}&enable_editor=1'.format (id = ids[0], model=self._name)
        return {
            'name': _('Edit Template'),
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
        }

    @api.multi
    def get_zipped_module(self):

        def write_template(template_obj, zf, fname, template, d, **params):
            i = zipfile.ZipInfo(fname)
            i.compress_type = zipfile.ZIP_DEFLATED
            i.external_attr = 2175008768
            zf.writestr(i, template_obj.render_template(template, d, **params))


        templates = self.env['document.template']

        functions = {
            'filters': {
                'dot2dashed': lambda x: x.replace('.', '_'),
                'dot2name': lambda x: ''.join([s.capitalize() for s in x.split('.')]),
                'cleargroup': lambda x: x.replace('.', '_'),
            },
        }

        zfileIO = StringIO()

        zfile = zipfile.ZipFile(zfileIO, 'w')

        has_models = len(self.model_ids)
        has_data = len(self.data_file_ids)
        has_website = len(self.website_theme_ids) \
                      or len(self.website_asset_ids) \
                      or len(self.website_menu_ids) \
                      or len(self.website_page_ids)

        module_data = []

        if has_models:
            module_data.append('views/views.xml')
            module_data.append('views/menu.xml')
            module_data.append('views/actions.xml')

            write_template(templates, zfile, self.name + '/__init__.py', 'builder.python.__init__.py', {}, **functions)
            write_template(templates, zfile, self.name + '/views/menu.xml', 'builder.menu.xml', {'module': self}, **functions)
            write_template(templates, zfile, self.name + '/views/actions.xml', 'builder.actions.xml', {'module': self}, **functions)
            write_template(templates, zfile, self.name + '/views/views.xml', 'builder.view.xml', {'models': self.view_ids}, **functions)
            write_template(templates, zfile, self.name + '/models/__init__.py', 'builder.python.__init__.py', {'packages': ['models']},**functions)
            write_template(templates, zfile, self.name + '/models/models.py', 'builder.models.py', {'models': self.model_ids}, **functions)

        if self.icon_image:
            info = zipfile.ZipInfo(self.name + '/static/description/icon.png')
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 2175008768
            zfile.writestr(info, base64.decodestring(self.icon_image))

        if self.description_html:
            info = zipfile.ZipInfo(self.name + '/static/description/index.html')
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 2175008768
            zfile.writestr(info, self.description_html)


        #website stuff
        for data in self.data_file_ids:
            info = zipfile.ZipInfo(posixpath.join(self.name, data.path.strip('/')))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 2175008768
            zfile.writestr(info, base64.decodestring(data.content))

        for theme in self.website_theme_ids:
            if theme.image:
                info = zipfile.ZipInfo(self.name + '/static/themes/' + theme.asset_id.attr_id +'.png')
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 2175008768
                zfile.writestr(info, base64.decodestring(theme.image))

        if self.website_asset_ids:
            module_data.append('views/website_assets.xml')
            write_template(templates, zfile, self.name + '/views/website_assets.xml', 'builder.website_assets.xml',
                                {'module': self, 'assets': self.website_asset_ids},
                                **functions)
        if self.website_page_ids:
            module_data.append('views/website_pages.xml')
            write_template(templates, zfile, self.name + '/views/website_pages.xml', 'builder.website_pages.xml',
                                {'module': self, 'pages': self.website_page_ids, 'menus': self.website_menu_ids},
                                **functions)
        if self.website_theme_ids:
            module_data.append('views/website_themes.xml')
            write_template(templates, zfile, self.name + '/views/website_themes.xml', 'builder.website_themes.xml',
                                {'module': self, 'themes': self.website_theme_ids},
                                **functions)

        if self.website_snippet_ids:
            snippet_type = defaultdict(list)
            for snippet in self.website_snippet_ids:
                snippet_type[snippet.is_custom_category].append(snippet)

            module_data.append('views/website_snippets.xml')
            write_template(templates, zfile, self.name + '/views/website_snippets.xml', 'builder.website_snippets.xml',
                                {'module': self, 'snippet_type': snippet_type},
                                **functions)

        #end website stuff


        #this must be last to include all resources
        write_template(templates, zfile, self.name + '/__openerp__.py', 'builder.__openerp__.py',
                            {'module': self, 'data': module_data}, **functions)

        zfile.close()
        zfileIO.flush()
        return zfileIO


class DataFile(models.Model):
    _name = 'builder.data.file'

    _rec_name = 'path'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='cascade')
    path = fields.Char(string='Path', required=True)
    filename = fields.Char('Filename')
    content_type = fields.Char('Content Type', compute='_compute_stats', store=True)
    extension = fields.Char('Extension', compute='_compute_stats', store=True)
    size = fields.Integer('Size', compute='_compute_stats', store=True)
    content = fields.Binary('Content')

    @api.one
    @api.depends('content', 'filename')
    def _compute_stats(self):
        self.size = False
        self.filename = False
        self.extension = False
        self.content_type = False
        if self.content:
            self.size = len(decodestring(self.content))

        self.filename = os.path.basename(self.path)
        self.extension = os.path.splitext(self.path)[1]
        self.content_type = mimetypes.guess_type(self.filename)[0] if mimetypes.guess_type(self.filename) else False
