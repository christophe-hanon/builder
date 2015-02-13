from openerp.addons.base.res.res_users import cset

__author__ = 'one'

# from openerp import models, api, fields, _
from openerp.osv import fields, osv
from openerp import SUPERUSER_ID
from openerp import tools, _, api


class Groups(osv.osv):
    _name = "builder.res.groups"
    _description = "Access Groups"
    _rec_name = 'full_name'
    _order = 'name'

    def _get_full_name(self, cr, uid, ids, field, arg, context=None):
        res = {}
        for g in self.browse(cr, uid, ids, context):
            if (g.category_type == 'system') and g.category_id:
                res[g.id] = '%s / %s' % (g.category_id.name, g.name)
            elif (g.category_type == 'system') and g.category_ref:
                res[g.id] = '%s / %s' % (g.category_ref, g.name)
            elif g.category_type == 'module':
                res[g.id] = "{module} / {group}".format(module=g.module_id.shortdesc, group=g.name)
            else:
                res[g.id] = g.name
        return res

    def _get_trans_implied(self, cr, uid, ids, field, arg, context=None):
        "computes the transitive closure of relation implied_ids"
        memo = {}           # use a memo for performance and cycle avoidance
        def computed_set(g):
            if g not in memo:
                memo[g] = cset(g.implied_ids)
                for h in g.implied_ids:
                    computed_set(h).subsetof(memo[g])
            return memo[g]

        res = {}
        for g in self.browse(cr, SUPERUSER_ID, ids, context):
            res[g.id] = map(int, computed_set(g))
        return res

    _columns = {
        'module_id': fields.many2one('builder.ir.module.module', 'Module', ondelete='cascade'),
        'xml_id': fields.char('XML ID', required=True),
        'name': fields.char('Name', required=True, translate=True),
        # 'users': fields.many2many('res.users', 'res_groups_users_rel', 'gid', 'uid', 'Users'),
        'model_access': fields.one2many('builder.ir.model.access', 'group_id', 'Access Controls', copy=True),
        # 'rule_groups': fields.many2many('ir.rule', 'builder_rule_group_rel', 'group_id', 'rule_group_id', 'Rules', domain=[('global', '=', False)]),
        'menu_access': fields.many2many('builder.ir.ui.menu', 'builder_ir_ui_menu_group_rel', 'gid', 'menu_id', 'Access Menu'),
        'view_access': fields.many2many('builder.ir.ui.view', 'builder_ir_ui_view_group_rel', 'group_id', 'view_id', 'Views'),
        'comment' : fields.text('Comment', size=250, translate=True),
        'category_type': fields.selection([('custom', 'Custom'), ('module', 'Module'), ('system', 'System')], 'Application Type'),
        'category_id': fields.many2one('ir.module.category', 'System Application', select=True, ondelete='set null'),
        'category_ref': fields.char('System Application Ref'),
        'full_name': fields.function(_get_full_name, type='char', string='Group Name'),
        'implied_ids': fields.many2many('builder.res.groups', 'builder_res_groups_implied_rel', 'gid', 'hid',
            string='Inherits', help='Users of this group automatically inherit those groups'),
        'trans_implied_ids': fields.function(_get_trans_implied, type='many2many', relation='builder.res.groups', string='Transitively inherits'),
    }

    _sql_constraints = [
        ('name_uniq', 'unique (module_id, category_type, category_id, category_ref, name)', 'The name of the group must be unique within an application!')
    ]

    def copy(self, cr, uid, id, default=None, context=None):
        group_name = self.read(cr, uid, [id], ['name'])[0]['name']
        default.update({'name': _('%s (copy)')%group_name})
        return super(Groups, self).copy(cr, uid, id, default, context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'name' in vals:
            if vals['name'].startswith('-'):
                raise osv.except_osv(_('Error'),
                        _('The name of the group can not start with "-"'))
        res = super(Groups, self).write(cr, uid, ids, vals, context=context)
        return res

    @api.onchange('category_ref')
    def onchange_category_ref(self):
        self.category_id = False
        if self.category_ref:
            self.category_id = self.env['ir.model.data'].xmlid_to_res_id(self.category_ref)

    @api.onchange('category_id')
    def onchange_category_id(self):
        if self.category_id:
            data = self.env['ir.model.data'].search([('model', '=', 'ir.module.category'), ('res_id', '=', self.category_id.id)])
            self.category_ref = "{module}.{id}".format(module=data.module, id=data.name) if data.id else False


class IrModelAccess(osv.osv):
    _name = 'builder.ir.model.access'

    _columns = {
        'module_id': fields.many2one('builder.ir.module.module', 'Module', ondelete='cascade'),
        'name': fields.char('Name', required=True, select=True),
        'model_id': fields.many2one('builder.ir.model', 'Object', required=True, domain=[('osv_memory','=', False)], select=True, ondelete='cascade'),
        'group_id': fields.many2one('builder.res.groups', 'Group', ondelete='cascade', select=True),
        'perm_read': fields.boolean('Read Access'),
        'perm_write': fields.boolean('Write Access'),
        'perm_create': fields.boolean('Create Access'),
        'perm_unlink': fields.boolean('Delete Access'),
    }