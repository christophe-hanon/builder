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

import base64
import operator
import re
import threading

import openerp.modules
from openerp.osv import fields, osv
from openerp import api, tools
from openerp.tools.safe_eval import safe_eval as eval
from openerp.tools.translate import _

MENU_ITEM_SEPARATOR = "/"


class IrUiMenu(osv.osv):
    _name = 'builder.ir.ui.menu'

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}

        ids = super(IrUiMenu, self).search(cr, uid, args, offset=0,
            limit=None, order=order, context=context, count=False)

        if not ids:
            if count:
                return 0
            return []

        # menu filtering is done only on main menu tree, not other menu lists
        if context.get('ir.ui.menu.full_list'):
            result = ids
        else:
            result = self._filter_visible_menus(cr, uid, ids, context=context)

        if offset:
            result = result[long(offset):]
        if limit:
            result = result[:long(limit)]

        if count:
            return len(result)
        return result

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for id in ids:
            elmt = self.browse(cr, uid, id, context=context)
            res.append((id, self._get_one_full_name(elmt)))
        return res

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

    def read_image(self, path):
        if not path:
            return False
        path_info = path.split(',')
        icon_path = openerp.modules.get_module_resource(path_info[0],path_info[1])
        icon_image = False
        if icon_path:
            try:
                icon_file = tools.file_open(icon_path,'rb')
                icon_image = base64.encodestring(icon_file.read())
            finally:
                icon_file.close()
        return icon_image

    def _get_image_icon(self, cr, uid, ids, names, args, context=None):
        res = {}
        for menu in self.browse(cr, uid, ids, context=context):
            res[menu.id] = r = {}
            for fn in names:
                fn_src = fn[:-5]    # remove _data
                r[fn] = self.read_image(menu[fn_src])

        return res

    def get_user_roots(self, cr, uid, context=None):
        """ Return all root menu ids visible for the user.

        :return: the root menu ids
        :rtype: list(int)
        """
        menu_domain = [('parent_id', '=', False)]
        return self.search(cr, uid, menu_domain, context=context)

    @api.cr_uid_context
    @tools.ormcache_context(accepted_keys=('lang',))
    def load_menus_root(self, cr, uid, context=None):
        fields = ['name', 'sequence', 'parent_id', 'action']
        menu_root_ids = self.get_user_roots(cr, uid, context=context)
        menu_roots = self.read(cr, uid, menu_root_ids, fields, context=context) if menu_root_ids else []
        return {
            'id': False,
            'name': 'root',
            'parent_id': [-1, ''],
            'children': menu_roots,
            'all_menu_ids': menu_root_ids,
        }


    @api.cr_uid_context
    @tools.ormcache_context(accepted_keys=('lang',))
    def load_menus(self, cr, uid, context=None):
        """ Loads all menu items (all applications and their sub-menus).

        :return: the menu root
        :rtype: dict('children': menu_nodes)
        """
        fields = ['name', 'sequence', 'parent_id', 'action']
        menu_root_ids = self.get_user_roots(cr, uid, context=context)
        menu_roots = self.read(cr, uid, menu_root_ids, fields, context=context) if menu_root_ids else []
        menu_root = {
            'id': False,
            'name': 'root',
            'parent_id': [-1, ''],
            'children': menu_roots,
            'all_menu_ids': menu_root_ids,
        }
        if not menu_roots:
            return menu_root

        # menus are loaded fully unlike a regular tree view, cause there are a
        # limited number of items (752 when all 6.1 addons are installed)
        menu_ids = self.search(cr, uid, [('id', 'child_of', menu_root_ids)], 0, False, False, context=context)
        menu_items = self.read(cr, uid, menu_ids, fields, context=context)
        # adds roots at the end of the sequence, so that they will overwrite
        # equivalent menu items from full menu read when put into id:item
        # mapping, resulting in children being correctly set on the roots.
        menu_items.extend(menu_roots)
        menu_root['all_menu_ids'] = menu_ids  # includes menu_root_ids!

        # make a tree using parent_id
        menu_items_map = dict(
            (menu_item["id"], menu_item) for menu_item in menu_items)
        for menu_item in menu_items:
            if menu_item['parent_id']:
                parent = menu_item['parent_id'][0]
            else:
                parent = False
            if parent in menu_items_map:
                menu_items_map[parent].setdefault(
                    'children', []).append(menu_item)

        # sort by sequence a tree using parent_id
        for menu_item in menu_items:
            menu_item.setdefault('children', []).sort(
                key=operator.itemgetter('sequence'))

        return menu_root

    _columns = {
        'name': fields.char('Menu', required=True, translate=True),
        'sequence': fields.integer('Sequence'),
        'child_id': fields.one2many('ir.ui.menu', 'parent_id', 'Child IDs'),
        'parent_id': fields.many2one('ir.ui.menu', 'Parent Menu', select=True, ondelete="restrict"),
        'parent_left': fields.integer('Parent Left', select=True),
        'parent_right': fields.integer('Parent Right', select=True),
        'groups_id': fields.many2many('res.groups', 'ir_ui_menu_group_rel',
            'menu_id', 'gid', 'Groups', help="If you have groups, the visibility of this menu will be based on these groups. "\
                "If this field is empty, Odoo will compute visibility based on the related object's read access."),
        'complete_name': fields.function(_get_full_name,
            string='Full Path', type='char', size=128),
        'icon': fields.selection(tools.icons, 'Icon', size=64),
        'icon_pict': fields.function(_get_icon_pict, type='char', size=32),
        'web_icon': fields.char('Web Icon File'),
        'web_icon_hover': fields.char('Web Icon File (hover)'),
        'web_icon_data': fields.function(_get_image_icon, string='Web Icon Image', type='binary', readonly=True, store=True, multi='icon'),
        'web_icon_hover_data': fields.function(_get_image_icon, string='Web Icon Image (hover)', type='binary', readonly=True, store=True, multi='icon'),
        'needaction_enabled': fields.function(_get_needaction_enabled,
            type='boolean',
            store=True,
            string='Target model uses the need action mechanism',
            help='If the menu entry action is an act_window action, and if this action is related to a model that uses the need_action mechanism, this field is set to true. Otherwise, it is false.'),
        'action': fields.function(_action, fnct_inv=_action_inv,
            type='reference', string='Action', size=21,
            selection=[
                ('ir.actions.report.xml', 'ir.actions.report.xml'),
                ('ir.actions.act_window', 'ir.actions.act_window'),
                ('ir.actions.wizard', 'ir.actions.wizard'),
                ('ir.actions.act_url', 'ir.actions.act_url'),
                ('ir.actions.server', 'ir.actions.server'),
                ('ir.actions.client', 'ir.actions.client'),
            ]),
    }

    def _rec_message(self, cr, uid, ids, context=None):
        return _('Error ! You can not create recursive Menu.')

    _constraints = [
        (osv.osv._check_recursion, _rec_message, ['parent_id'])
    ]
    _defaults = {
        'icon': 'STOCK_OPEN',
        'icon_pict': ('stock', ('STOCK_OPEN', 'ICON_SIZE_MENU')),
        'sequence': 10,
    }
    _order = "sequence,id"
    _parent_store = True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
