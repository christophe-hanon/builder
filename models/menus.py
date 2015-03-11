# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2010-2012 OpenERP SA (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, tools, _
from openerp.osv import osv
MENU_ITEM_SEPARATOR = "/"


class IrUiMenu(models.Model):
    _name = 'builder.ir.ui.menu'

    _rec_name = 'complete_name'

    @api.multi
    def get_user_roots(self):
        """ Return all root menu ids visible for the user.

        :return: the root menu ids
        :rtype: list(int)
        """
        menu_domain = [('parent_id', '=', False), ('parent_ref', '=', False)]
        return self.search(menu_domain)

    @api.multi
    def load_menus_root(self):
        menu_roots = self.get_user_roots()
        return {
            'id': False,
            'name': 'root',
            'parent_id': [-1, ''],
            'children': menu_roots,
            'all_menu_ids': [i.id for i in menu_roots],
        }

    def _get_full_name(self, cr, uid, ids, name=None, args=None, context=None):
        if context is None:
            context = {}
        res = {}
        for elmt in self.browse(cr, uid, ids, context=context):
            res[elmt.id] = self._get_one_full_name(elmt)
        return res

    def _get_one_full_name(self, elmt, level=6):
        if level<=0:
            return '...'
        if elmt.parent_id:
            parent_path = self._get_one_full_name(elmt.parent_id, level-1) + MENU_ITEM_SEPARATOR
        else:
            parent_path = ''
        return parent_path + elmt.name

    @api.onchange('parent_ref')
    def onchange_parent_ref(self):
        self.parent_menu_id = False
        if self.parent_ref:
            self.parent_menu_id = self.env['ir.model.data'].xmlid_to_res_id(self.parent_ref)

    @api.onchange('parent_menu_id')
    def onchange_parent_menu_id(self):
        if self.parent_menu_id:
            data = self.env['ir.model.data'].search([('model', '=', 'ir.ui.menu'), ('res_id', '=', self.parent_menu_id.id)])
            self.parent_ref = "{module}.{id}".format(module=data.module, id=data.name) if data.id else False

    @api.onchange('parent_type')
    def onchange_parent_type(self):
        self.parent_ref = False
        self.parent_menu_id = False
        self.parent_id = False

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='cascade')
    name = fields.Char('Menu', required=True, translate=True)
    xml_id = fields.Char('XML ID', required=True)
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name')
    sequence = fields.Integer('Sequence')
    child_ids = fields.One2many('builder.ir.ui.menu', 'parent_id', 'Child Ids')
    # group_ids = fields.Many2many('builder.res.groups', 'builder_ir_ui_menu_group_rel', 'menu_id', 'gid', 'Groups', help="If you have groups, the visibility of this menu will be based on these groups. "\
    #             "If this field is empty, Odoo will compute visibility based on the related object's read access.")
    parent_menu_id = fields.Many2one('ir.ui.menu', 'System Menu', ondelete='set null')
    parent_ref = fields.Char('System Menu Ref', select=True)
    parent_id = fields.Many2one('builder.ir.ui.menu', 'Parent Menu', select=True, ondelete='set null')
    parent_type = fields.Selection([('module', 'Module'), ('system', 'System')], 'Parent Type')
    parent_left = fields.Integer('Parent Left', select=True)
    parent_right = fields.Integer('Parent Left', select=True)
    action_type = fields.Selection([('module', 'Module'), ('system', 'System')], 'Action Type')
    action_system_ref = fields.Char('Action System Ref')
    action_system = fields.Reference([
                                    ('ir.actions.report.xml', 'ir.actions.report.xml'),
                                    ('ir.actions.act_window', 'ir.actions.act_window'),
                                    ('ir.actions.wizard', 'ir.actions.wizard'),
                                    ('ir.actions.act_url', 'ir.actions.act_url'),
                                    ('ir.actions.server', 'ir.actions.server'),
                                    ('ir.actions.client', 'ir.actions.client'),
    ], 'System Action')

    action_module = fields.Reference([
                                    ('builder.ir.actions.act_window', 'Window'),
                                    # ('builder.ir.actions.act_url', 'URL'),
    ], 'Module Action')

    group_ids = fields.Many2many('builder.res.groups', 'builder_ir_ui_menu_group_rel', 'menu_id', 'gid', string='Groups', help="If this field is empty, the menu applies to all users. Otherwise, the view applies to the users of those groups only.")


    @api.onchange('action_system')
    def onchange_action_system(self):
        if self.action_system:
            model, res_id = self.action_system._name, self.action_system.id
            data = self.env['ir.model.data'].search([('model', '=', model), ('res_id', '=', res_id)])
            self.action_system_ref = "{module}.{id}".format(module=data.module, id=data.name) if data.id else False

            self.name = self.action_system.name
            self.xml_id = "menu_{action}".format(action=self.action_system_ref.replace('.', '_'))

    @api.onchange('action_module')
    def onchange_action_module(self):
        if self.action_module:
            self.name = self.action_module.name
            self.xml_id = "menu_{action}".format(action=self.action_module.xml_id)

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        if not vals.get('parent_type', False):
            vals['parent_id'] = False
            vals['parent_menu_id'] = False
            vals['parent_ref'] = False

        return super(IrUiMenu, self).create(vals)

    @api.multi
    def write(self, vals):
        if not vals.get('parent_type', False):
            vals['parent_id'] = False
            vals['parent_menu_id'] = False
            vals['parent_ref'] = False

        return super(IrUiMenu, self).write(vals)



    @api.one
    def _compute_complete_name(self):
        self.complete_name = self._get_full_name_one()

    @api.multi
    def _get_full_name_one(self, level=6):
        if level<=0:
            return '...'
        parent_path = ''
        if self.parent_id:
            parent_path = self.parent_id._get_full_name_one(level-1) + MENU_ITEM_SEPARATOR
        elif self.parent_ref:
            parent_path = _('[INHERITED]') + MENU_ITEM_SEPARATOR
            if self.parent_menu_id:
                parent_path = '[{name}]'.format(name=self.parent_menu_id.complete_name) + MENU_ITEM_SEPARATOR
            else:
                parent_path = '[{ref}]'.format(ref=self.parent_ref) + MENU_ITEM_SEPARATOR

        return parent_path + self.name

    @api.one
    def name_get(self):
        return self.id, self._get_full_name_one()

    def _rec_message(self, cr, uid, ids, context=None):
        return _('Error ! You can not create recursive Menu.')

    _constraints = [
        (osv.osv._check_recursion, _rec_message, ['parent_id'])
    ]
    _defaults = {
        'sequence': 10,
    }
    _order = "sequence,id"
    _parent_store = True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
