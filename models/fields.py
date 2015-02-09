import logging
from openerp.fields import Selection
import types
from openerp.addons.base.ir.ir_model import _get_fields_type as _base_field_types
from openerp.exceptions import except_orm
from openerp.osv import fields  as fields_old

__author__ = 'one'

from openerp import models, api, fields, _


_logger = logging.getLogger(__name__)

# class EnvSelection(Selection):
# def get_values(self, env):
#         """ return a list of the possible values """
#         selection = self.selection
#         if isinstance(selection, basestring):
#             selection = getattr(env[self.model_name], selection)(context=env.context)
#         elif callable(selection):
#             selection = selection(env[self.model_name], context=env.context)
#         return [value for value, _ in selection]


def snake_case(name, prefix=None, suffix=None):
    return (prefix or '') + (name or '').replace('.', '_') + (suffix or '')


def model_name(name, prefix=None, suffix=None):
    return (prefix or '') + ' '.join([p.capitalize() for p in (name or '').split('.')]) + (suffix or '')


relational_field_types = ['one2many', 'many2one', 'many2many']
relational_field_reverse_types = {'one2many': 'many2one', 'many2one': 'one2many', 'many2many': 'many2many'}
relational_field_reverse_funct = lambda x: '2'.join(x.split('2')[::-1])


class IrFields(models.Model):
    _name = 'builder.ir.model.fields'
    _order = 'model_id, position asc'
    _description = 'Fields'
    _rec_name = 'name'

    def _get_fields_type_selection(self):
        context = {}
        # Avoid too many nested `if`s below, as RedHat's Python 2.6
        # break on it. See bug 939653.
        return sorted([(k, k) for k, v in fields_old.__dict__.iteritems()
                       if type(v) == types.TypeType and \
                       issubclass(v, fields_old._column) and \
                       v != fields_old._column and \
                       not v._deprecated and \
                       # not issubclass(v, fields_old.function)])
                       not issubclass(v, fields_old.function) and \
                       (not context.get('from_diagram', False) or (
                       context.get('from_diagram', False) and (k in ['one2many', 'many2one', 'many2many'])))

        ]
        )

    model_id = fields.Many2one('builder.ir.model', 'Model', select=1, ondelete='cascade')

    name = fields.Char('Name', required=True, select=1)
    position = fields.Integer('Position')
    complete_name = fields.Char('Complete Name', select=1)

    relation = fields.Char('Object Relation',
                           help="For relationship fields, the technical name of the target model")

    relation_model_id = fields.Many2one('builder.ir.model', 'Model', ondelete='set null')

    relation_many2many_comodel_name = fields.Char('Comodel Name')
    relation_many2many_relation = fields.Char('Relation Name')
    relation_many2many_column1 = fields.Char('Column1')
    relation_many2many_column2 = fields.Char('Column2')

    relation_create_inverse_relation = fields.Boolean('Create Inverse Relation',
                                                      help="Generates an inverse relation in the target model.")
    reverse_relation_name = fields.Char('Reverse Relation Name')
    reverse_relation_field_description = fields.Char('Reverse Relation Description')

    relation_field = fields.Char('Relation Field',
                                 help="For one2many fields, the field on the target model that implement the opposite many2one relationship")

    field_description = fields.Char('Field Label', required=True)
    ttype = fields.Selection(_get_fields_type_selection, 'Field Type', required=True)
    relation_ttype = fields.Selection([('many2one', 'many2one'), ('one2many', 'one2many'), ('many2many', 'many2many')],
                                      'Field Type')
    selection = fields.Char('Selection Options', help="List of options for a selection field, "
                                                      "specified as a Python expression defining a list of (key, label) pairs. "
                                                      "For example: [('blue','Blue'),('yellow','Yellow')]")
    required = fields.Boolean('Required')
    readonly = fields.Boolean('Readonly')
    select_level = fields.Selection(
        [('0', 'Not Searchable'), ('1', 'Always Searchable'), ('2', 'Advanced Search (deprecated)')], 'Searchable',
        required=True, default='0')
    translate = fields.Boolean('Translatable',
                               help="Whether values for this field can be translated (enables the translation mechanism for that field)")
    size = fields.Integer('Size')
    on_delete = fields.Selection([('cascade', 'Cascade'), ('set null', 'Set NULL'), ('restrict', 'Restrict')],
                                 'On Delete', default='set null', help='On delete property for many2one fields')
    domain = fields.Char('Domain', default='[]',
                         help="The optional domain to restrict possible values for relationship fields, "
                              "specified as a Python expression defining a list of triplets. "
                              "For example: [('color','=','red')]")
    #groups = fields.Many2many('programming.res.groups', 'ir_model_fields_group_rel', 'field_id', 'group_id', 'Groups')
    selectable = fields.Boolean('Selectable', default=1)

    compute = fields.Boolean('Compute')
    compute_method_name = fields.Char('Compute Method Name')
    compute_method = fields.Text('Compute Method')

    inverse = fields.Boolean('Inverse')
    inverse_method_name = fields.Char('Inverse Method Name')
    inverse_method = fields.Text('Inverse Method')

    is_inherited = fields.Boolean('Inherited')

    @api.onchange('compute', 'inverse')
    def _compute_method_names(self):
        self.compute_method_name = "_compute_{field}".format(field=self.name)
        self.inverse_method_name = "_inverse_{field}".format(field=self.name)


    @api.onchange('relation_ttype')
    def _onchange_relation_ttype(self):
        self.ttype = self.relation_ttype

    @api.constrains('ttype')
    def constraint_ttype_relational(self):
        if self.env.context.get('from_diagram') and self.ttype not in relational_field_types:
            raise ValueError(
                _("You must select one of the relational field types when creating a relation in the diagram view."))

        return True

    @api.onchange('ttype')
    def constraint_ttype_relational(self):
        if self.env.context.get('from_diagram') and self.ttype not in relational_field_types:
            self.ttype = 'many2one'


    @api.onchange('relation_model_id')
    def onchange_relation_model_id(self):
        if self.relation_model_id:
            self.relation = self.relation_model_id.model
        else:
            self.relation = False

    def __str__(self):
        return self.name

    @api.model
    def _get_default_name(self):
        if self.env.context.get('from_diagram'):
            return self.relation_model_id.model.replace('.', '_') + '_id' if self.relation_model_id else False
        return False

    @api.onchange('relation_field')
    def onchange_relation_field(self):
        if self.ttype == 'one2many' and self.reverse_relation_name != self.relation_field:
            self.reverse_relation_name = self.relation_field

    @api.onchange('reverse_relation_name')
    def onchange_reverse_relation_name(self):
        if self.ttype == 'one2many' and self.reverse_relation_name != self.relation_field:
            self.relation_field = self.reverse_relation_name

    @api.onchange('relation_model_id', 'ttype', 'model_id')
    def _get_default_field_values(self):
        if self.ttype in relational_field_types and self.relation_model_id:
            if self.model_id != self.relation_model_id:

                self.field_description = model_name(
                    self.relation_model_id.name)  # if self.model_id.id != self.relation_model_id.id else _('Parent')
                self.name = snake_case(self.relation_model_id.model,
                                       suffix='_id' if self.ttype.endswith('2one') else '_ids')

                self.relation_field = snake_case(self.model_id.model,
                                                 suffix='_ids' if self.ttype.endswith('2one') else '_id')

                if self.ttype != 'many2many':
                    self.reverse_relation_name = self.relation_field
                    self.reverse_relation_field_description = model_name(self.model_id.name)
                else:
                    self.reverse_relation_name = snake_case(self.model_id.model, suffix='_ids')
                    self.reverse_relation_field_description = model_name(self.model_id.name)
                    self.relation_many2many_column1 = snake_case(self.model_id.model, suffix='_id')
                    self.relation_many2many_column2 = snake_case(self.relation_model_id.model, suffix='_id')
                    self.relation_many2many_relation = "{module}_{model1}_{model2}_rel".format(
                        module=self.model_id.module_id.name, model1=snake_case(self.model_id.model),
                        model2=snake_case(self.relation_model_id.model))
            else:
                self.field_description = _('Parent') if self.ttype.endswith('2one') else _('Children')
                self.name = 'parent_id' if self.ttype.endswith('2one') else 'child_ids'

                self.relation_field = 'parent_id'

                if self.ttype != 'many2many':
                    self.reverse_relation_name = 'child_ids' if self.ttype.endswith('2one') else 'parent_id'
                    self.reverse_relation_field_description = _('Parent') if not self.ttype.endswith('2one') else _(
                        'Children')
                else:
                    self.reverse_relation_name = 'child_ids' if self.ttype.endswith('2one') else 'child2_ids'
                    self.reverse_relation_field_description = _('Children') if self.ttype.endswith('2one') else _(
                        'Children2')
                    self.relation_many2many_column1 = snake_case(self.model_id.model, suffix='_id')
                    self.relation_many2many_column2 = snake_case(self.relation_model_id.model, suffix='_id')
                    self.relation_many2many_relation = "{module}_{model1}_{model2}_rel".format(
                        module=self.model_id.module_id.name, model1=snake_case(self.model_id.model),
                        model2=snake_case(self.relation_model_id.model))

    @api.model
    def _get_default_ttype(self):
        if self.env.context.get('from_diagram'):
            return 'many2one'
        return False

    _defaults = {
        'ttype': _get_default_ttype,
        'name': _get_default_name,
    }


    def _check_selection(self, cr, uid, selection, context=None):
        try:
            selection_list = eval(selection)
        except Exception:
            _logger.warning('Invalid selection list definition for fields.selection', exc_info=True)
            raise except_orm(_('Error'),
                             _("The Selection Options expression is not a valid Pythonic expression."
                               "Please provide an expression in the [('key','Label'), ...] format."))

        check = True
        if not (isinstance(selection_list, list) and selection_list):
            check = False
        else:
            for item in selection_list:
                if not (isinstance(item, (tuple, list)) and len(item) == 2):
                    check = False
                    break

        if not check:
            raise except_orm(_('Error'),
                             _("The Selection Options expression is must be in the [('key','Label'), ...] format!"))
        return True

    def _size_gt_zero_msg(self, cr, user, ids, context=None):
        return _('Size of the field can never be less than 0 !')

    _sql_constraints = [
        ('size_gt_zero', 'CHECK (size>=0)', _size_gt_zero_msg ),
    ]

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        model = super(IrFields, self).create(vals)
        field_obj = self.env['builder.ir.model.fields']

        if model.ttype in relational_field_types and model.relation_create_inverse_relation:

            reverse_field = field_obj.search(
                [('model_id', '=', model.relation_model_id.id), ('name', '=', model.reverse_relation_name)])

            if not reverse_field.id:
                ttype = relational_field_reverse_funct(model.ttype)
                attrs = {
                    'model_id': model.relation_model_id.id,
                    'relation_model_id': model.model_id.id,
                    'name': model.reverse_relation_name,
                    'ttype': ttype,
                    'field_description': model.reverse_relation_field_description,
                }
                if ttype == 'one2many':
                    attrs['relation_field'] = model.name
                reverse_field = field_obj.create(attrs)

        return model

    @api.multi
    def write(self, vals):
        saved = super(IrFields, self).write(vals)
        field_obj = self.env['builder.ir.model.fields']

        model = field_obj.search([('id', '=', self.id)])

        if model.ttype in relational_field_types and model.relation_create_inverse_relation:

            reverse_field = field_obj.search(
                [('model_id', '=', model.relation_model_id.id), ('name', '=', model.reverse_relation_name)])

            if not reverse_field.id:
                ttype = relational_field_reverse_funct(model.ttype)
                attrs = {
                    'model_id': model.relation_model_id.id,
                    'relation_model_id': model.model_id.id,
                    'name': model.reverse_relation_name,
                    'ttype': ttype,
                    'field_description': model.reverse_relation_field_description,
                }
                if ttype == 'one2many':
                    attrs['relation_field'] = model.name
                reverse_field = field_obj.create(attrs)

        return saved




