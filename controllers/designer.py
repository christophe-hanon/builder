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
    def index(self, model, res_id, **kw):
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

        if model == 'builder.ir.module.module':
            field_template = 'builder.page_designer_builder_ir_module_module_description_html'
            return_url = '/web#return_label=Website&model={model}&id={id}&view_type=form&action=builder.open_module_tree'.format(model=model, id=record.id)
        elif model == 'builder.website.page':
            field_template = 'builder.page_designer_builder_website_page_content'
            return_url = '/web#return_label=Website&model={model}&id={id}&view_type=form&action=builder.open_module_tree'.format(model=model, id=record.module_id.id)
        else:
            return request.redirect('/')

        values = {
            'record': record,
            'model': model,
            'res_id': res_id,
            'returnUrl': return_url,
            'field_template': field_template
        }

        return request.website.render("builder.page_designer", values)

    @http.route(['/builder/page/snippets'], type='json', auth="user", website=True)
    def snippets(self):
        return request.website._render('builder.page_designer_snippets')
