from openerp import models, fields, api, pooler

__author__ = 'deimos'


class Superclass(models.AbstractModel):
    _name = 'ir.mixin.polymorphism.superclass'

    subclass_id = fields.Integer('Subclass ID', compute='_compute_res_id')
    subclass_model = fields.Char("Subclass Model", required=True)

    _defaults = {
        'subclass_model': lambda s, c, u, cxt=None: s._name
    }

    @api.one
    def _compute_res_id(self):
        if self.subclass_model == self._model._name:
            self.subclass_id = self.id
        else:
            subclass_model = self.env[self.subclass_model]
            attr = subclass_model._inherits.get(self._model._name)
            if attr:
                self.subclass_id = subclass_model.search([
                    (attr, '=', self.id)
                ]).id
            else:
                self.subclass_id = self.id

    # def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
    #     record = self.browse(cr, uid, 2, context=context)
    #     if self._name == record.subclass_model:
    #         view = super(Superclass, self).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)
    #     else:
    #         view = self.pool.get(record.subclass_model).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)
    #     return view

    def get_formview_action(self, cr, uid, id, context=None):
        """
        @return <ir.actions.act_window>
        """
        record = self.browse(cr, uid, id, context=context)
        if self._name == record.subclass_model:
            view = super(Superclass, self).get_formview_action(cr, uid, id, context=context)
        else:
            view = self.pool.get(record.subclass_model).get_formview_action(cr, uid, record.subclass_id,
                                                                            context=context)
        return view

    @api.multi
    def action_edit(self):
        cr, uid, cxt = self.env.args
        data = self._model.get_formview_action(cr, uid, self.id, context=cxt)
        return data


class Subclass(models.AbstractModel):
    _name = 'ir.mixin.polymorphism.subclass'

    def get_formview_id(self, cr, uid, id, context=None):
        view = self.pool.get('ir.ui.view').search(cr, uid, [
            ('type', '=', 'form'),
            ('model', '=', self._name)
        ], context=context)
        return view[0] if len(view) else False

    def unlink(self, cr, uid, ids, context=None):
        records = self.browse(cr, uid, ids, context=context)
        parent_ids = {
            model: [rec[field].id for rec in records] for model, field in self._inherits.items()
        }

        res = super(Subclass, self).unlink(cr, uid, ids, context=context)
        if res:
            for model in parent_ids:
                self.pool.get(model).unlink(cr, uid, parent_ids.get(model, []), context=context)
        return res
