from openerp.osv import osv
from operator import itemgetter
from openerp import models, fields, _

class View(models.Model):
    _name = 'ir.ui.view'

    def _get_model_data(self, cr, uid, ids, fname, args, context=None):
        result = dict.fromkeys(ids, False)
        IMD = self.pool['ir.model.data']
        data_ids = IMD.search_read(cr, uid, [('res_id', 'in', ids), ('model', '=', 'ir.ui.view')], ['res_id'], context=context)
        result.update(map(itemgetter('res_id', 'id'), data_ids))
        return result

    def _views_from_model_data(self, cr, uid, ids, context=None):
        IMD = self.pool['ir.model.data']
        data_ids = IMD.search_read(cr, uid, [('id', 'in', ids), ('model', '=', 'ir.ui.view')], ['res_id'], context=context)
        return map(itemgetter('res_id'), data_ids)

    name = fields.Char('View Name', required=True)
    model = fields.Char('Object', select=True)
    priority = fields.Integer('Sequence', required=True)
    type = fields.Selection([
            ('tree','Tree'),
            ('form','Form'),
            ('graph', 'Graph'),
            ('calendar', 'Calendar'),
            ('diagram','Diagram'),
            ('gantt', 'Gantt'),
            ('kanban', 'Kanban'),
            ('search','Search'),
            ('qweb', 'QWeb')], string='View Type')

    arch = fields.Text('View Architecture', required=True)

    inherit_id = fields.Many2one('ir.ui.view', 'Inherited View', ondelete='cascade', select=True)
    inherit_children_ids = fields.One2many('ir.ui.view','inherit_id', 'Inherit Views')
    field_parent = fields.Char('Child Field')
    model_data_id = fields.Many2one('ir.model.data', "Model Data", compute='_get_model_data',   store={
                                             _name: (lambda s, c, u, i, ctx=None: i, None, 10),
                                             'ir.model.data': (_views_from_model_data, ['model', 'res_id'], 10),
                                         })
    # xml_id = fields.Char("External ID", compute=osv.osv.get_xml_id, help="ID of the view defined in xml file")
    # model_ids = fields.One2many('ir.model.data', 'res_id', domain=[('model','=','ir.ui.view')], auto_join=True)
    # groups_id = fields.Many2many('res.groups', 'builder_ir_ui_view_group_rel', 'view_id', 'group_id', string='Groups', help="If this field is empty, the view applies to all users. Otherwise, the view applies to the users of those groups only.")

