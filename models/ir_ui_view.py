from openerp.osv import osv
from operator import itemgetter
from openerp import api
from openerp import models, fields, _

class View(models.Model):
    _name = 'builder.ir.ui.view'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='CASCADE')
    model_id = fields.Many2one('builder.ir.model', 'Model', ondelete='CASCADE')
    wizard_id = fields.Reference([
                                     ('builder.wizard.views.calendar', 'Calendar'),
                                     ('builder.wizard.views.form', 'Form'),
                                     ('builder.wizard.views.gantt', 'Gantt'),
                                     ('builder.wizard.views.graph', 'Graph'),
                                     ('builder.wizard.views.kanban', 'Kanban'),
                                     ('builder.wizard.views.search', 'Search'),
                                     ('builder.wizard.views.tree', 'Tree'),
    ], 'Wizard')

    name = fields.Char('View Name', required=True)
    xml_id = fields.Char('XML Id', required=True)
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

    inherit_id = fields.Many2one('builder.ir.ui.view', 'Inherited View', ondelete='cascade', select=True)
    inherit_children_ids = fields.One2many('builder.ir.ui.view','inherit_id', 'Inherit Views')
    field_parent = fields.Char('Child Field')
    # model_data_id = fields.Many2one('ir.model.data', "Model Data", compute='_get_model_data',   store={
    #                                          _name: (lambda s, c, u, i, ctx=None: i, None, 10),
    #                                          'ir.model.data': (_views_from_model_data, ['model', 'res_id'], 10),
    #                                      })
    # xml_id = fields.Char("External ID", compute=osv.osv.get_xml_id, help="ID of the view defined in xml file")
    # model_ids = fields.One2many('ir.model.data', 'res_id', domain=[('model','=','ir.ui.view')], auto_join=True)
    # groups_id = fields.Many2many('res.groups', 'builder_ir_ui_view_group_rel', 'view_id', 'group_id', string='Groups', help="If this field is empty, the view applies to all users. Otherwise, the view applies to the users of those groups only.")

    @api.one
    def unlink(self):
        if self.wizard_id:
            self.wizard_id.unlink()
        return super(View, self).unlink()

    @api.multi
    def action_open_view_wizard(self):
        if self.wizard_id:
            wizard_name, wizard_id = self.wizard_id._name, self.wizard_id.id

            return {
                'name': _('View Wizard'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': wizard_name,
                'views': [(False, 'form')],
                'res_id': wizard_id or False,
                'target': 'new',
                'context': {
                    'from_view': True,
                    'view_id': self.id,
                },
            }

