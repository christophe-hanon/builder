from StringIO import StringIO
import base64
import zipfile
import os
from openerp.addons.web import http
from openerp.addons.web.controllers.main import content_disposition
import posixpath
from openerp.addons.web.http import request


class MainController(http.Controller):
    def write_template(self, template_obj, zfile, filename, template, data, **params):
        info = zipfile.ZipInfo(filename)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 2175008768
        zfile.writestr(info, template_obj.render_template(template, data, **params))


    @http.route('/builder/download/<model("builder.ir.module.module"):module>', type='http', auth="user")
    def download(self, module, **kwargs):

        templates = request.env['document.template']

        functions = {
            'filters': {
                'dot2dashed': lambda x: x.replace('.', '_'),
                'dot2name': lambda x: ''.join([s.capitalize() for s in x.split('.')]),
                'cleargroup': lambda x: x.replace('.', '_'),
            },
        }

        filename = "{name}.{ext}".format(name=module.name, ext="zip")
        zfileIO = StringIO()

        zfile = zipfile.ZipFile(zfileIO, 'w')

        has_models = len(module.model_ids)
        has_data = len(module.data_file_ids)
        has_website = len(module.website_theme_ids) \
                      or len(module.website_asset_ids) \
                      or len(module.website_menu_ids) \
                      or len(module.website_page_ids)

        module_data = []

        packages = ['models'] if has_models else []
        self.write_template(templates, zfile, module.name + '/__init__.py', 'builder.python.__init__.py',
                            {'packages': packages}, **functions)
        if has_models:
            module_data.append(module.name + '/views/menu.xml')

            self.write_template(templates, zfile, module.name + '/views/menu.xml', 'builder.menu.xml', {'module': module},
                                **functions)

            self.write_template(templates, zfile, module.name + '/models/__init__.py', 'builder.python.__init__.py', {},
                                **functions)
            self.write_template(templates, zfile, module.name + '/models/models.py', 'builder.models.py',
                                {'models': module.model_ids},
                                **functions)

        if module.icon_image:
            info = zipfile.ZipInfo(module.name + '/static/description/icon.png')
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 2175008768
            zfile.writestr(info, base64.decodestring(module.icon_image))

        if module.description_html:
            info = zipfile.ZipInfo(module.name + '/static/description/index.html')
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 2175008768
            zfile.writestr(info, module.description_html)


        #website stuff
        for data in module.data_file_ids:
            info = zipfile.ZipInfo(posixpath.join(module.name, data.path.strip('/')))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 2175008768
            zfile.writestr(info, base64.decodestring(data.content))

        for theme in module.website_theme_ids:
            if theme.image:
                info = zipfile.ZipInfo(module.name + '/static/themes/' + theme.asset_id.attr_id +'.png')
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 2175008768
                zfile.writestr(info, base64.decodestring(theme.image))

        if module.website_asset_ids:
            module_data.append('views/website_assets.xml')
            self.write_template(templates, zfile, module.name + '/views/website_assets.xml', 'builder.website_assets.xml',
                                {'module': module, 'assets': module.website_asset_ids},
                                **functions)
        if module.website_page_ids:
            module_data.append('views/website_pages.xml')
            self.write_template(templates, zfile, module.name + '/views/website_pages.xml', 'builder.website_pages.xml',
                                {'module': module, 'pages': module.website_page_ids, 'menus': module.website_menu_ids},
                                **functions)
        if module.website_theme_ids:
            module_data.append('views/website_themes.xml')
            self.write_template(templates, zfile, module.name + '/views/website_themes.xml', 'builder.website_themes.xml',
                                {'module': module, 'themes': module.website_theme_ids},
                                **functions)

        #end website stuff


        #this must be last to include all resources
        self.write_template(templates, zfile, module.name + '/__openerp__.py', 'builder.__openerp__.py',
                            {'module': module, 'data': module_data}, **functions)

        zfile.close()
        zfileIO.flush()

        return request.make_response(
            zfileIO.getvalue(),
            headers=[('Content-Type', 'plain/text' or 'application/octet-stream'),
                     ('Content-Disposition', content_disposition(filename))])


    @http.route('/builder/export/<string:format>/<model("builder.ir.module.module"):module>', type='http', auth="user")
    def export(self, module, format, **kwargs):
        return "exported"