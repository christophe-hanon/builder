__author__ = 'one'

# from openerp import models, api, fields, _
from openerp.osv import fields, osv
from openerp import SUPERUSER_ID
from openerp import tools, _, api

class actions(osv.osv):
    _name = 'builder.ir.actions.actions'
    _table = 'builder_ir_actions'
    _order = 'name'
    _columns = {
        'module_id': fields.many2one('builder.ir.module.module', 'Module', ondelete='cascade'),
        'xml_id': fields.char('XML ID', required=True),
        'name': fields.char('Name', required=True),
        'type': fields.char('Action Type', required=True),
        'usage': fields.char('Action Usage'),

        'help': fields.text('Action description',
            help='Optional help text for the users with a description of the target view, such as its usage and purpose.',
            translate=True),
    }
    _defaults = {
        'usage': lambda *a: False,
    }


class ir_actions_act_url(osv.osv):
    _name = 'builder.ir.actions.act_url'
    _table = 'builder_ir_act_url'
    _inherit = 'builder.ir.actions.actions'
    _sequence = 'builder_ir_actions_id_seq'
    _order = 'name'
    _columns = {
        'name': fields.char('Action Name', translate=True),
        'type': fields.char('Action Type', required=True),
        'url': fields.text('Action URL',required=True),
        'target': fields.selection((
            ('new', 'New Window'),
            ('self', 'This Window')),
            'Action Target', required=True
        )
    }
    _defaults = {
        'type': 'builder.ir.actions.act_url',
        'target': 'new'
    }


class ir_actions_act_window(osv.osv):
    _name = 'builder.ir.actions.act_window'
    _table = 'builder_ir_act_window'
    _inherit = 'builder.ir.actions.actions'
    _sequence = 'builder_ir_actions_id_seq'

    # @api.constrains('res_model','src_model')
    def _check_model(self, cr, uid, ids, context=None):
        for action in self.browse(cr, uid, ids, context):
            if action.res_model not in self.pool:
                return False
            if action.src_model and action.src_model not in self.pool:
                return False
        return True

    def _views_get_fnc(self, cr, uid, ids, name, arg, context=None):
        """Returns an ordered list of the specific view modes that should be
           enabled when displaying the result of this action, along with the
           ID of the specific view to use for each mode, if any were required.

           This function hides the logic of determining the precedence between
           the view_modes string, the view_ids o2m, and the view_id m2o that can
           be set on the action.

           :rtype: dict in the form { action_id: list of pairs (tuples) }
           :return: { action_id: [(view_id, view_mode), ...], ... }, where view_mode
                    is one of the possible values for ir.ui.view.type and view_id
                    is the ID of a specific view to use for this mode, or False for
                    the default one.
        """
        res = {}
        for act in self.browse(cr, uid, ids):
            res[act.id] = [(view.view_id.id, view.view_mode) for view in act.view_ids]
            view_ids_modes = [view.view_mode for view in act.view_ids]
            modes = act.view_mode.split(',')
            missing_modes = [mode for mode in modes if mode not in view_ids_modes]
            if missing_modes:
                if act.view_id and act.view_id.type in missing_modes:
                    # reorder missing modes to put view_id first if present
                    missing_modes.remove(act.view_id.type)
                    res[act.id].append((act.view_id.id, act.view_id.type))
                res[act.id].extend([(False, mode) for mode in missing_modes])
        return res

    def _search_view(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for act in self.browse(cr, uid, ids, context=context):
            field_get = self.pool[act.res_model].fields_view_get(cr, uid,
                act.search_view_id and act.search_view_id.id or False,
                'search', context=context)
            res[act.id] = str(field_get)
        return res

    _columns = {
        'name': fields.char('Action Name', translate=True),
        'view_id': fields.many2one('builder.ir.ui.view', 'View Ref.', ondelete='set null'),
        'domain': fields.char('Domain Value',
            help="Optional domain filtering of the destination data, as a Python expression"),
        'context': fields.char('Context Value', required=True,
            help="Context dictionary as Python expression, empty by default (Default: {})"),
        'res_id': fields.integer('Record ID', help="Database ID of record to open in form view, when ``view_mode`` is set to 'form' only"),
        'model_id': fields.many2one('builder.ir.model', 'Destination Model', required=True, ondelete='cascade', help="Model name of the object to open in the view window"),
        'src_model': fields.char('Source Model', help="Optional model name of the objects on which this action should be visible"),
        'target': fields.selection([('current','Current Window'),('new','New Window'),('inline','Inline Edit'),('inlineview','Inline View')], 'Target Window'),
        'view_mode': fields.char('View Mode', required=True,
            help="Comma-separated list of allowed view modes, such as 'form', 'tree', 'calendar', etc. (Default: tree,form)"),
        'view_type': fields.selection((('tree','Tree'),('form','Form')), string='View Type', required=True,
            help="View type: Tree type to use for the tree view, set to 'tree' for a hierarchical tree view, or 'form' for a regular list view"),
        'usage': fields.char('Action Usage',
            help="Used to filter menu and home actions from the user form."),
        'view_ids': fields.one2many('ir.actions.act_window.view', 'act_window_id', 'Views'),
        'views': fields.function(_views_get_fnc, type='binary', string='Views',
               help="This function field computes the ordered list of views that should be enabled " \
                    "when displaying the result of an action, federating view mode, views and " \
                    "reference view. The result is returned as an ordered list of pairs (view_id,view_mode)."),
        'limit': fields.integer('Limit', help='Default limit for the list view'),
        'auto_refresh': fields.integer('Auto-Refresh', help='Add an auto-refresh on the view'),
        # 'groups_id': fields.many2many('res.groups', 'ir_act_window_group_rel', 'act_id', 'gid', 'Groups'),
        'groups_id': fields.many2many('builder.res.groups', 'builder_ir_act_window_group_rel',
            'act_id', 'gid', 'Groups'),
        'search_view_id': fields.many2one('builder.ir.ui.view', 'Search View Ref.'),
        'filter': fields.boolean('Filter'),
        'auto_search':fields.boolean('Auto Search'),
        # 'search_view' : fields.function(_search_view, type='text', string='Search View'),
        'multi': fields.boolean('Restrict to lists', help="If checked and the action is bound to a model, it will only appear in the More menu on list views"),
        'show_help': fields.boolean('Display Help'),
        'help': fields.html('Help'),
    }

    _defaults = {
        'type': 'builder.ir.actions.act_window',
        'view_type': 'form',
        'view_mode': 'tree,form',
        'context': '{}',
        'limit': 80,
        'target': 'current',
        'auto_refresh': 0,
        'auto_search':True,
        'multi': False,
        'help': """
          <p class="oe_view_nocontent_create">
            Click to create a new model.
          </p><p>
            This is an example of help content.
          </p>
        """
    }

    @api.onchange('model_id')
    def onchange_model_id(self):
        if not self.name and self.model_id:
            self.xml_id = "act_{model}".format(model =self.model_id.model.replace('.', '_'))
            self.name = self.model_id.name

        if self.model_id:
            available_view_types = list(set([view.type for view in self.model_id.view_ids]) - {'search'})
            self.view_mode = ','.join(available_view_types)



    def for_xml_id(self, cr, uid, module, xml_id, context=None):
        """ Returns the act_window object created for the provided xml_id

        :param module: the module the act_window originates in
        :param xml_id: the namespace-less id of the action (the @id
                       attribute from the XML file)
        :return: A read() view of the ir.actions.act_window
        """
        dataobj = self.pool.get('ir.model.data')
        data_id = dataobj._get_id (cr, SUPERUSER_ID, module, xml_id)
        res_id = dataobj.browse(cr, uid, data_id, context).res_id
        return self.read(cr, uid, [res_id], [], context)[0]