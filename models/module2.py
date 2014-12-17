from openerp import models, fields, api
from openerp.api import Environment
from openerp.osv import fields as fields_old
from openerp import tools
from openerp.osv import expression
from openerp import _

__author__ = 'deimos'

def compute_reference_field(reference_field, computed_field, model=None):
    @api.one
    @api.depends(reference_field)
    def _compute_ref(self):
        field = self._columns[reference_field]
        _model = field['relation'] if field else model
        data = self.env['ir.model.data'].search([('model', '=', _model), ('res_id', '=', getattr(self, reference_field).id)])
        setattr(self, computed_field, "{module}.{id}".format(module=data.module, id=data.name) if data.id else False)
    return _compute_ref


class Module(models.Model):
    _name = 'builder.ir.module.module'

    @api.model
    def _get_categories(self):
        return [(c.name, c.name) for c in self.env['ir.module.category'].search([])]

    @api.one
    @api.depends('category_id')
    def _compute_category_ref(self):
        data = self.env['ir.model.data'].search([('model', '=', 'ir.module.category'), ('res_id', '=', self.category_id.id)])
        self.category_ref = "{module}.{id}".format(module=data.module, id=data.name) if data.id else False

    name = fields.Char("Technical Name", required=True, select=True)
    category_id = fields.Many2one('ir.module.category', 'Category', compute='_compute_category_id', readonly=False)
    # category_id = fields.Selection(simple_selection('ir.module.category', 'name') , 'Category')
    category_ref = fields.Char('Category Ref')
    shortdesc = fields.Char('Module Name', translate=True)
    summary = fields.Char('Summary', translate=True)
    description = fields.Text("Description", translate=True)
    description_html = fields.Html(string='Description HTML')
    author = fields.Char("Author")
    maintainer = fields.Char('Maintainer')
    contributors = fields.Text('Contributors')
    website = fields.Char("Website")

    installed_version = fields.Char('Installed Version')
    latest_version = fields.Char('Latest Version')
    published_version = fields.Char('Published Version')

    url = fields.Char('URL')
    sequence = fields.Integer('Sequence')
    # dependencies_id = fields.One2many('programming.module.dependency', 'module_id', 'Dependencies')
    auto_install = fields.Boolean('Automatic Installation',
                                   help='An auto-installable module is automatically installed by the '
                                        'system when all its dependencies are satisfied. '
                                        'If the module has no dependency, it is always installed.')
    license = fields.Selection([
        ('GPL-2', 'GPL Version 2'),
        ('GPL-2 or any later version', 'GPL-2 or later version'),
        ('GPL-3', 'GPL Version 3'),
        ('GPL-3 or any later version', 'GPL-3 or later version'),
        ('AGPL-3', 'Affero GPL-3'),
        ('Other OSI approved licence', 'Other OSI Approved Licence'),
        ('Other proprietary', 'Other Proprietary')
    ], string='License', default='AGPL-3')

    application = fields.Boolean('Application')
    icon = fields.Char('Icon URL')
    image = fields.Binary(string='Icon')
    icon_image = fields.Binary(string='Icon')

    menus_by_module = fields.Text(string='Menus')
    reports_by_module = fields.Text(string='Reports')
    views_by_module = fields.Text(string='Views')
    demo = fields.Boolean('Has Demo Data')

    dependency_ids = fields.One2many(
        comodel_name='builder.ir.module.dependency',
        inverse_name='module_id',
        string='Dependencies',
    )

    @api.one
    @api.depends('category_ref')
    def _compute_category_id(self):
        self.category_id = False
        if self.category_ref:
            self.category_id = self.env['ir.model.data'].xmlid_to_res_id(self.category_ref)

    @api.onchange('category_id')
    def onchange_category(self):
        if self.category_id:
            data = self.env['ir.model.data'].search([('model', '=', 'ir.module.category'), ('res_id', '=', self.category_id.id)])
            self.category_ref = "{module}.{id}".format(module=data.module, id=data.name) if data.id else False


    def get_available_import_formats(self, cr, uid, context=None):
        return [
            {
                'type': 'raw',
                'action': 'import_base_form',
                'name': _('Import Module')
            },
            {
                'type': 'dia',
                'action': 'import_base_form',
                'name': _('Import from Dia')
            }
        ]

    def get_available_export_formats(self, cr, uid, context=None):
        return [
            {
                'name': _('Export Module'),
                'type': 'raw'
            },
            {
                'name': _('Export to Dia'),
                'type': 'dia'
            }
        ]

    @api.multi
    def button_download(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/builder/download/{id}'.format(id=self.id),
            'target': 'self'
        }
