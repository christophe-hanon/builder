# -*- coding: utf-8 -*-

from urllib import urlencode

from openerp.addons.web import http
from openerp.addons.web.http import request
from openerp.tools.mail import html_sanitize


class WebsiteDesigner(http.Controller):

    @http.route('/builder/designer', type='http', auth="user", website=True)
    def designer(self, model, res_id, field, return_url=None, **kw):
        if not model or not model in request.registry or not res_id:
            return request.redirect('/')
        model_fields = request.registry[model]._fields

        if not field or not field in model_fields:
            return request.redirect('/')

        res_id = int(res_id)
        obj_ids = request.registry[model].exists(request.cr, request.uid, [res_id], context=request.context)
        if not obj_ids:
            return request.redirect('/')
        # try to find fields to display / edit -> as t-field is static, we have to limit
        cr, uid, context = request.cr, request.uid, request.context
        record = request.registry[model].browse(cr, uid, res_id, context=context)

        values = {
            'record': record,
            'templates': None,
            'model': model,
            'res_id': res_id,
            'field': field,
            'return_url': return_url,
        }

        return request.website.render("builder.designer", values)


    @http.route('/builder/page/designer', type='http', auth="user", website=True)
    def index(self, model, res_id, template_model=None, **kw):
        if not model or not model in request.registry or not res_id:
            return request.redirect('/')
        model_fields = request.registry[model]._fields
        res_id = int(res_id)
        obj_ids = request.registry[model].exists(request.cr, request.uid, [res_id], context=request.context)
        if not obj_ids:
            return request.redirect('/')
        # try to find fields to display / edit -> as t-field is static, we have to limit
        cr, uid, context = request.cr, request.uid, request.context
        record = request.registry[model].browse(cr, uid, res_id, context=context)

        values = {
            'record': record,
            'templates': None,
            'model': model,
            'res_id': res_id
        }

        return request.website.render("builder.page_designer", values)

    @http.route(['/builder/page/snippets'], type='json', auth="user", website=True)
    def snippets(self):
        return request.website._render('builder.page_designer_snippets')
