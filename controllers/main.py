from StringIO import StringIO
import base64
import openerp
from openerp import SUPERUSER_ID
from openerp.addons.web import http
from openerp.addons.website.models.website import unslug
from openerp import _
from openerp.addons.web.http import request
from openerp.addons.web.controllers.main import content_disposition
import werkzeug.urls
import zipfile

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

        self.write_template(templates, zfile, module.name + '/__openerp__.py', 'builder.__openerp__.py', {'module': module}, **functions)
        self.write_template(templates, zfile, module.name + '/__init__.py', 'builder.python.__init__.py', {'packages': ['base']}, **functions)
        self.write_template(templates, zfile, module.name + '/views/menu.xml', 'builder.menu.xml', {'module': module}, **functions)

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

        zfile.close()
        zfileIO.flush()

        return request.make_response(
                    zfileIO.getvalue(),
                    headers=[('Content-Type', 'plain/text' or 'application/octet-stream'),
                             ('Content-Disposition', content_disposition(filename))])


    @http.route('/builder/export/<string:format>/<model("builder.ir.module.module"):module>', type='http', auth="user")
    def export(self, module, format, **kwargs):
        return "exported"