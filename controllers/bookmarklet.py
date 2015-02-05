import werkzeug
from openerp.http import request
from openerp import http

__author__ = 'deimos'


class BookmarkController(http.Controller):

    # @http.route('/builder/<string():module>/snippet', type='http', auth='user', website=True, methods=['GET'])
    # def snippet_form(self, module, **kwargs):
    #
    #
    #     return request.website.render("builder.snippet.index", {
    #         'me': request.env.user,
    #         'users': users
    #     })

    @http.route('/builder/<string:module>/snippet/add', type='http', auth='user', website=True, methods=['GET'])
    def snippet_form(self, module, **kwargs):
        module = request.env['builder.ir.module.module'].search([
            ('name', '=', module)
        ])

        if not module:
            return request.not_found()

        return request.website.render("builder.snippet_form")

    @http.route('/builder/<string:module>/snippet/save', type='http', auth='user', website=True, methods=['POST'])
    def snippet_save(self, module, **kwargs):
        project = request.env['builder.ir.module.module'].search([
            ('name', '=', module)
        ])

        if not project:
            return request.not_found()

        request.env['builder.website.snippet'].create({
            'module_id': project.id,
            'category': 'custom',  # this must be set by the default!
            'name': request.httprequest.form.get('name'),
            'xpath': request.httprequest.form.get('xpath'),
            'source_url': request.httprequest.form.get('url'),
            'content': request.httprequest.form.get('html'),
        })

        return request.redirect('/builder/{module}/snippet/add'.format(module=module))
