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

    @api.multi
    def get_user_roots(self):
        """ Return all root menu ids visible for the user.

        :return: the root menu ids
        :rtype: list(int)
        """
        menu_domain = [('parent_id', '=', False)]
        return self.search(menu_domain)

    @api.multi
    def load_menus_root(self, context=None):
        menu_roots = self.get_user_roots()
        return {
            'id': False,
            'name': 'root',
            'parent_id': [-1, ''],
            'children': menu_roots,
            'all_menu_ids': [i.id for i in menu_roots],
        }

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='cascade')
    name = fields.Char('Menu', required=True, translate=True)
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name')
    sequence = fields.Integer('Sequence')
    child_ids = fields.One2many('builder.ir.ui.menu', 'parent_id', 'Child Ids')
    # group_ids = fields.Many2many('builder.res.groups', 'builder_ir_ui_menu_group_rel', 'menu_id', 'gid', 'Groups', help="If you have groups, the visibility of this menu will be based on these groups. "\
    #             "If this field is empty, Odoo will compute visibility based on the related object's read access.")
    parent_id = fields.Many2one('builder.ir.ui.menu', 'Parent Menu', select=True, ondelete='restrict')
    parent_ref = fields.Char('Parent Menu', select=True)
    parent_type = fields.Selection([('none', 'None'), ('id', 'Existing'), ('ref', 'Reference')], 'Parent Type')
    parent_left = fields.Integer('Parent Left', select=True)
    parent_right = fields.Integer('Parent Left', select=True)
    action = fields.Reference([
                                    ('ir.actions.report.xml', 'ir.actions.report.xml'),
                                    ('ir.actions.act_window', 'ir.actions.act_window'),
                                    ('ir.actions.wizard', 'ir.actions.wizard'),
                                    ('ir.actions.act_url', 'ir.actions.act_url'),
                                    ('ir.actions.server', 'ir.actions.server'),
                                    ('ir.actions.client', 'ir.actions.client'),
    ], 'Action')

    @api.one
    def _compute_complete_name(self):
        self.complete_name = 'Hola'

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
