# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Soluciones Moebius (<http://www.solucionesmoebius.com>).
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

# noinspection PyStatementEffect
{
    'name': 'Module Builder',
    'version': '0.1',
    'category': 'Programming',
    'summary': 'Build your modules right inside Odoo',
    'description': """
This module aims to help in the development of new modules
=======================================================================================

""",
    'author': 'Soluciones Moebius',
    #"license": "AGPL-3",
    'website': 'http://www.solucionesmoebius.com/',
    'depends': ['web', 'base_mixins', 'web_diagram', 'generic_document_render_jinja', 'web_ace_editor'],
    'data': [
        # 'security/base_security.xml',
        # 'security/ir.model.access.csv',
        'data/templates.xml',
        'data/oe.css.classes.yml',
        'wizard/model_lookup_wizard_view.xml',
        'wizard/menu_lookup_wizard_view.xml',
        'wizard/action_lookup_wizard_view.xml',

        'views/views/base_view.xml',
        'views/views/calendar_view.xml',
        'views/views/form_view.xml',
        'views/views/gantt_view.xml',
        'views/views/graph_view.xml',
        'views/views/kanban_view.xml',
        'views/views/search_view.xml',
        'views/views/tree_view.xml',
        'views/views/selector_view.xml',

        'wizard/module_import_view.xml',
        'wizard/model_import_view.xml',
        'wizard/model_export_view.xml',
        'views/menu_view.xml',
        'views/module_view.xml',
        'views/model_view.xml',
        'views/action_view.xml',
        'views/menu.xml',
        'views/backend_assets.xml',
    ],
    'test': [
        'test/test_demo.yml',
    ],
    'qweb': [],
    # 'qweb': ['static/src/xml/templates.xml'],
    'installable': True,
    'application': True,
    'auto_install': False,
}