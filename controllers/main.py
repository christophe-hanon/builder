from StringIO import StringIO
import base64
import json
import zipfile
import os
from openerp.addons.web import http
from openerp.addons.web.controllers.main import content_disposition
import posixpath
from openerp.addons.web.http import request
from controllers.export import ExportJson


class MainController(http.Controller):
    def write_template(self, template_obj, zfile, filename, template, data, **params):
        info = zipfile.ZipInfo(filename)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 2175008768
        zfile.writestr(info, template_obj.render_template(template, data, **params))


    @http.route('/builder/download/<model("builder.ir.module.module"):module>', type='http', auth="user")
    def download(self, module, **kwargs):

        filename = "{name}.{ext}".format(name=module.name, ext="zip")

        zfileIO = module.get_zipped_module()

        return request.make_response(
            zfileIO.getvalue(),
            headers=[('Content-Type', 'plain/text' or 'application/octet-stream'),
                     ('Content-Disposition', content_disposition(filename))])


    @http.route('/builder/export/<string:format>/<model("builder.ir.module.module"):module>', type='http', auth="user")
    def export(self, module, format, **kwargs):
        dct_module = ExportJson(request.env).build_json(module)

        json_module = json.dumps(dct_module)

        filename = "{name}.{ext}".format(name=module.name, ext="json")

        fileIO = StringIO()

        fileIO.write(json_module)

        fileIO.flush()

        return request.make_response(
                    fileIO.getvalue(),
                    headers=[('Content-Type', 'plain/text' or 'application/octet-stream'),
                             ('Content-Disposition', content_disposition(filename))])