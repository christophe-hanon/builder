from openerp import models, fields, api
from openerp.osv import fields as fields_old
from openerp import tools
from openerp.osv import expression
from openerp import _

__author__ = 'deimos'


class res_groups(models.Model):
    _name = "res.groups"
    _description = "Access Groups"
    _rec_name = 'full_name'
    _order = 'name'


    def _get_full_name(self, cr, uid, ids, field, arg, context=None):
        res = {}
        for g in self.browse(cr, uid, ids, context):
            if g.category_id:
                res[g.id] = '%s / %s' % (g.category_id.name, g.name)
            else:
                res[g.id] = g.name
        return res

    def _search_group(self, cr, uid, obj, name, args, context=None):
        operand = args[0][2]
        operator = args[0][1]
        lst = True
        if isinstance(operand, bool):
            domains = [[('name', operator, operand)], [('category_id.name', operator, operand)]]
            if operator in expression.NEGATIVE_TERM_OPERATORS == (not operand):
                return expression.AND(domains)
            else:
                return expression.OR(domains)
        if isinstance(operand, basestring):
            lst = False
            operand = [operand]
        where = []
        for group in operand:
            values = filter(bool, group.split('/'))
            group_name = values.pop().strip()
            category_name = values and '/'.join(values).strip() or group_name
            group_domain = [('name', operator, lst and [group_name] or group_name)]
            category_domain = [('category_id.name', operator, lst and [category_name] or category_name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS and not values:
                category_domain = expression.OR([category_domain, [('category_id', '=', False)]])
            if (operator in expression.NEGATIVE_TERM_OPERATORS) == (not values):
                sub_where = expression.AND([group_domain, category_domain])
            else:
                sub_where = expression.OR([group_domain, category_domain])
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                where = expression.AND([where, sub_where])
            else:
                where = expression.OR([where, sub_where])
        return where


    name = fields.Char('Name', required=True, translate=True)
    users = fields.Many2many('res.users', 'res_groups_users_rel', 'gid', 'uid', 'Users')
    model_access = fields.One2many('ir.model.access', 'group_id', 'Access Controls')
    rule_groups = fields.Many2many('ir.rule', 'rule_group_rel', 'group_id', 'rule_group_id', 'Rules', domain=[('global', '=', False)])
    menu_access = fields.Many2many('ir.ui.menu', 'ir_ui_menu_group_rel', 'gid', 'menu_id', 'Access Menu')
    view_access = fields.Many2many('ir.ui.view', 'ir_ui_view_group_rel', 'group_id', 'view_id', 'Views')
    comment = fields.Text('Comment', size=250, translate=True)
    category_id = fields.Many2one('programming.module.dependency', 'Application', select=True)
    full_name = fields.Char(string='Group Name', compute='_get_full_name', fnct_search=_search_group)


class ir_model_access(models.Model):
    _name = 'builder.ir.model.access'

    name = fields.Char('Name', required=True, select=True)
    active = fields.Boolean('Active', help='If you uncheck the active field, it will disable the ACL without deleting it (if you delete a native ACL, it will be re-created when you reload the module.')
    model_id = fields.Many2one('builder.ir.model', 'Object', required=True, domain=[('osv_memory','=', False)], select=True, ondelete='cascade')
    group_id = fields.Many2one('builder.res.groups', 'Group', ondelete='cascade', select=True)
    perm_read = fields.Boolean('Read Access')
    perm_write = fields.Boolean('Write Access')
    perm_create = fields.Boolean('Create Access')
    perm_unlink = fields.Boolean('Delete Access')


class ModelDependency(models.Model):
    _name = 'programming.module.dependency'
    name = fields.Char('Name', compute='_compute_name')
    # the module that depends on it
    module_id = fields.Many2one('programming.module', 'Module', ondelete='cascade')

    # the module corresponding to the dependency, and its status
    installed_id = fields.Many2one('ir.module.module', 'Dependency', store=False)
    programming_id = fields.Many2one('programming.module', 'Dependency', store=False)

    @api.one
    @api.depends('installed_id', 'programming_id')
    def _compute_name(self):
        self.name = self.installed_id.name or self.programming_id.name
