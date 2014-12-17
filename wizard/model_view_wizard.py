from openerp.addons.builder.models.fields import snake_case

__author__ = 'one'

from openerp import models, api, fields, _

FIELD_WIDGETS = [
    ('barchart', "FieldBarChart"),
    ('binary', "FieldBinaryFile"),
    ('boolean', "FieldBoolean"),
    ('char', "FieldChar"),
    ('char_domain', "FieldCharDomain"),
    ('date', "FieldDate"),
    ('datetime', "FieldDatetime"),
    ('email', "FieldEmail"),
    ('float', "FieldFloat"),
    ('float_time', "FieldFloat"),
    ('html', "FieldTextHtml"),
    ('image', "FieldBinaryImage"),
    ('integer', "FieldFloat"),
    ('kanban_state_selection', "KanbanSelection"),
    ('many2many', "FieldMany2Many"),
    ('many2many_binary', "FieldMany2ManyBinaryMultiFiles"),
    ('many2many_checkboxes', "FieldMany2ManyCheckBoxes"),
    ('many2many_kanban', "FieldMany2ManyKanban"),
    ('many2many_tags', "FieldMany2ManyTags"),
    ('many2one', "FieldMany2One"),
    ('many2onebutton', "Many2OneButton"),
    ('monetary', "FieldMonetary"),
    ('one2many', "FieldOne2Many"),
    ('one2many_list', "FieldOne2Many"),
    ('percentpie', "FieldPercentPie"),
    ('priority', "Priority"),
    ('progressbar', "FieldProgressBar"),
    ('radio', "FieldRadio"),
    ('reference', "FieldReference"),
    ('selection', "FieldSelection"),
    ('statinfo', "StatInfo"),
    ('statusbar', "FieldStatus"),
    ('text', "FieldText"),
    ('url', "FieldUrl"),
    ('x2many_counter', "X2ManyCounter"),
]


class ModelViewWizardFormPage(models.Model):
    _name = 'builder.ir.model.view.config.wizard.form.pages'

    _order = 'sequence, name'

    wizard_id = fields.Many2one('builder.ir.model.view.config.wizard', string='Wizard', ondelete='cascade')
    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence')
    field_ids = fields.One2many('builder.ir.model.view.config.wizard.form.fields', 'page_id', 'Fields')


class ModelViewWizardSearchGroup(models.Model):
    _name = 'builder.ir.model.view.config.wizard.search.group'

    _order = 'sequence, name'

    wizard_id = fields.Many2one('builder.ir.model.view.config.wizard', string='Wizard', ondelete='cascade')
    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence')
    expand = fields.Boolean('Expand')
    item_ids = fields.One2many('builder.ir.model.view.config.wizard.search.items', 'group_id', 'Items')


DEFAULT_WIDGETS_BY_TYPE = {
    'binary': 'image'
}


class StatusBarActionButton(models.Model):
    _name = 'builder.ir.model.view.config.wizard.form.statusbar.buttons'

    _order = 'sequence, name'

    wizard_id = fields.Many2one('builder.ir.model.view.config.wizard', string='Wizard', ondelete='cascade')
    model_id = fields.Many2one('builder.ir.model', string='Model')
    special_states_field_id = fields.Many2one('builder.ir.model.fields', related='model_id.special_states_field_id', string='States Field')
    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence')
    highlighted = fields.Boolean('Highlighted')
    type = fields.Selection([('state', 'State Change'), ('action', 'Defined Action'), ('object', 'Model Action'), ('relation', 'Relation')], 'Type')
    states = fields.Char('States')
    change_to_state = fields.Char('Change to State')
    method_name = fields.Char('Method Name')
    method_code = fields.Text('Method Code')
    action_ref = fields.Char('Action')

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'state' and self.change_to_state:
            self.method_name = "action_{state}".format(state=self.change_to_state)
        elif self.type == 'object' and self.name:
            self.method_name = "action_{name}".format(name=snake_case(self.name.replace(' ', '.')).lower())



class AbstractWizardViewField(models.AbstractModel):
    _name = 'builder.ir.model.view.config.wizard.abstract.fields'

    _rec_name = 'field_id'
    _order = 'wizard_id, sequence'

    wizard_id = fields.Many2one('builder.ir.model.view.config.wizard', string='Name', ondelete='cascade')
    sequence = fields.Integer('Sequence')
    field_id = fields.Many2one('builder.ir.model.fields', string='Field', required=True, ondelete='cascade')
    field_ttype = fields.Char(string='Field Type', compute='_compute_field_type')
    model_id = fields.Many2one('builder.ir.model', related='wizard_id.model_id', string='Model')
    special_states_field_id = fields.Many2one('builder.ir.model.fields', related='wizard_id.model_id.special_states_field_id', string='States Field')
    module_id = fields.Many2one('builder.ir.model', related='wizard_id.model_id.module_id', string='Module')


    @api.one
    @api.depends('field_id.ttype', 'wizard_id')
    def _compute_field_type(self):
        if self.field_id:
            self.field_ttype = self.field_id.ttype



class WizardViewFormField(models.Model):
    _name = 'builder.ir.model.view.config.wizard.form.fields'
    _inherit = ['builder.ir.model.view.config.wizard.abstract.fields']

    page_id = fields.Many2one('builder.ir.model.view.config.wizard.form.pages', string='Page', ondelete='set null')

    related_field_view_type = fields.Selection([('default', 'Default'), ('defined', 'Defined'), ('custom', 'Custom')], 'View Type', required=True, default='default')
    related_field_arch = fields.Text('Arch')
    related_field_form_id = fields.Char('Form View ID')
    related_field_tree_id = fields.Char('Tree View ID')
    domain = fields.Char('Domain')
    related_field_mode = fields.Selection([('tree', 'Tree'), ('form', 'Form')], 'Mode', default='tree')
    related_field_tree_editable = fields.Selection([('False', 'No Editable'), ('top', 'Top'), ('bottom', 'Bottom')], 'Tree Editable', default='bottom')

    widget = fields.Selection(FIELD_WIDGETS, 'Widget')
    widget_options = fields.Char('Widget Options')

    nolabel = fields.Boolean('Hide Label')

    required = fields.Boolean('Required')
    required_condition = fields.Char('Required Condition')

    invisible = fields.Boolean('Invisible')
    invisible_condition = fields.Char('Invisible Condition')

    readonly = fields.Boolean('Readonly')
    readonly_condition = fields.Char('Readonly Condition')

    states = fields.Char('States')

    @api.one
    @api.depends('field_id.ttype', 'wizard_id')
    def _compute_field_type(self):
        if self.field_id:
            self.field_ttype = self.field_id.ttype


class WizardSearchItem(models.Model):
    _name = 'builder.ir.model.view.config.wizard.search.items'
    _inherit = ['builder.ir.model.view.config.wizard.abstract.fields']

    type = fields.Selection([('field', 'Field'), ('filter', 'Filter'), ('separator', 'Separator')], string='Type', required=False, default='field')
    field_id = fields.Many2one('builder.ir.model.fields', string='Field', required=False, ondelete='cascade')
    group_field_id = fields.Many2one('builder.ir.model.fields', string='Group By', ondelete='set null')
    group_id = fields.Many2one('builder.ir.model.view.config.wizard.search.group', string='Group', required=False, ondelete='set null')
    attr_string = fields.Char('String')
    attr_filter_domain = fields.Char('Filter Domain')
    attr_domain = fields.Char('Domain')
    attr_operator = fields.Char('Operator')
    attr_help = fields.Char('Help')

    @api.one
    @api.depends('field_id.ttype', 'wizard_id')
    def _compute_field_type(self):
        if self.field_id:
            self.field_ttype = self.field_id.ttype


class WizardViewTreeField(models.Model):
    _name = 'builder.ir.model.view.config.wizard.tree.fields'
    _inherit = ['builder.ir.model.view.config.wizard.abstract.fields']

    widget = fields.Selection(FIELD_WIDGETS, 'Widget')
    widget_options = fields.Char('Widget Options')

    nolabel = fields.Boolean('Hide Label')

    invisible = fields.Boolean('Invisible')
    readonly = fields.Boolean('Readonly')
    domain = fields.Char('Domain')

    @api.one
    @api.depends('field_id.ttype', 'wizard_id')
    def _compute_field_type(self):
        if self.field_id:
            self.field_ttype = self.field_id.ttype


class WizardViewGraphField(models.Model):
    _name = 'builder.ir.model.view.config.wizard.graph.fields'
    _inherit = ['builder.ir.model.view.config.wizard.abstract.fields']

    operator = fields.Selection([('+', '+')], 'Operator')
    type = fields.Selection([('row', 'row'), ('col', 'col'), ('measure', 'measure')], 'Type')
    interval = fields.Selection([('month', 'month'), ('year', 'year'), ('day', 'day')], 'Interval')


class WizardViewCalendarField(models.Model):
    _name = 'builder.ir.model.view.config.wizard.calendar.fields'
    _inherit = ['builder.ir.model.view.config.wizard.abstract.fields']

    invisible = fields.Boolean('Invisible')


class ModelViewWizard(models.Model):
    _name = 'builder.ir.model.view.config.wizard'

    model_id = fields.Many2one('builder.ir.model', ondelete='cascade')
    special_states_field_id = fields.Many2one('builder.ir.model.fields', 'States Field', related='model_id.special_states_field_id')
    model_groups_date_field_ids = fields.One2many('builder.ir.model.fields', string='Has Date Fields', related='model_id.groups_date_field_ids')

    form_view = fields.Boolean('Form View', default=True)
    tree_view = fields.Boolean('Tree View', default=True)
    graph_view = fields.Boolean('Graph View', default=False)
    gantt_view = fields.Boolean('Gantt View', default=False)
    calendar_view = fields.Boolean('Calendar View', default=False)
    search_view = fields.Boolean('Search View', default=False)
    diagram_view = fields.Boolean('Diagram View', default=False)

    #form fields
    form_attr_string = fields.Char('Form String')
    form_view_arch = fields.Text('Arch')
    form_view_custom_arch = fields.Boolean('Customize')
    form_view_id = fields.Char('View ID')
    form_attr_create = fields.Boolean('Allow Create', default=True)
    form_attr_edit = fields.Boolean('Allow Edit', default=True)
    form_attr_delete = fields.Boolean('Allow Delete', default=True)
    form_page_ids = fields.One2many('builder.ir.model.view.config.wizard.form.pages', 'wizard_id', 'Pages')
    form_field_ids = fields.One2many('builder.ir.model.view.config.wizard.form.fields', 'wizard_id', 'Fields')
    form_states_clickable = fields.Boolean('States Clickable')
    form_show_status_bar = fields.Boolean('Show Status Bar')
    form_visible_states = fields.Char('Visible States')

    # form_buttonbar_button_ids = fields.One2many('builder.ir.model.view.config.wizard.buttonbar.buttons', 'wizard_id', 'Buttons')
    form_statusbar_button_ids = fields.One2many('builder.ir.model.view.config.wizard.form.statusbar.buttons', 'wizard_id', 'Status Bar Buttons')
    
    
    #tree fields
    tree_attr_string = fields.Char('Tree String')
    tree_view_arch = fields.Text('Arch')
    tree_view_custom_arch = fields.Boolean('Customize')
    tree_view_id = fields.Char('View ID')
    tree_attr_create = fields.Boolean('Allow Create', default=True)
    tree_attr_edit = fields.Boolean('Allow Edit', default=True)
    tree_attr_delete = fields.Boolean('Allow Delete', default=True)
    tree_attr_toolbar = fields.Boolean('Show Toolbar', default=True)
    tree_attr_fonts = fields.Char('Fonts', help='Font definition. Ex: bold:message_unread==True')
    tree_attr_colors = fields.Char('Colors', help='Color definition. Ex: "gray:probability == 100;red:date_deadline and (date_deadline &lt; current_date)"')
    tree_field_ids = fields.One2many('builder.ir.model.view.config.wizard.tree.fields', 'wizard_id', 'Fields')


    #graph fields
    graph_attr_string = fields.Char('Graph String')
    graph_view_arch = fields.Text('Arch')
    graph_view_custom_arch = fields.Boolean('Customize')
    graph_view_id = fields.Char('View ID')
    graph_attr_type = fields.Selection([('bar', 'Bar'), ('pie', 'Pie'), ('line', 'Line'), ('pivot', 'Pivot')], 'Type')
    graph_attr_stacked = fields.Boolean('Stacked')
    graph_attr_orientation = fields.Selection([('horizontal', 'Horizontal'), ('vertical', 'Vertical')], 'Orientation')
    graph_field_ids = fields.One2many('builder.ir.model.view.config.wizard.graph.fields', 'wizard_id', 'Fields')


    #graph fields
    search_attr_string = fields.Char('Graph String')
    search_view_arch = fields.Text('Arch')
    search_view_custom_arch = fields.Boolean('Customize')
    search_view_id = fields.Char('View ID')
    search_item_ids = fields.One2many('builder.ir.model.view.config.wizard.search.items', 'wizard_id', 'Search Items')


    #graph fields
    gantt_attr_string = fields.Char('Gantt String')
    gantt_view_arch = fields.Text('Arch')
    gantt_view_custom_arch = fields.Boolean('Customize')
    gantt_view_id = fields.Char('View ID')
    # gantt_item_ids = fields.One2many('builder.ir.model.view.config.wizard.search.items', 'wizard_id', 'Search Items')


    #calendar fields
    calendar_attr_string = fields.Char('Calendar String')
    calendar_view_arch = fields.Text('Arch')
    calendar_view_custom_arch = fields.Boolean('Customize')
    calendar_view_id = fields.Char('View ID')
    calendar_attr_color_field_id = fields.Many2one('builder.ir.model.fields', 'Color Field', ondelete='set null')
    calendar_attr_color_ttype = fields.Char('Color Field Type', store=False)
    calendar_attr_date_start_field_id = fields.Many2one('builder.ir.model.fields', 'Date Start Field', ondelete='set null')
    calendar_attr_date_start_ttype = fields.Char('Start Date Field Type', store=False)
    calendar_attr_date_stop_field_id = fields.Many2one('builder.ir.model.fields', 'Date Stop Field', ondelete='set null')
    calendar_attr_day_length_field_id = fields.Many2one('builder.ir.model.fields', 'Day Length Field', ondelete='set null')
    calendar_attr_date_delay_field_id = fields.Many2one('builder.ir.model.fields', 'Date Delay Field', ondelete='set null')
    calendar_attr_all_day = fields.Boolean('All Day')
    calendar_attr_use_contacts = fields.Boolean('Use Contacts', help="If this field is set to true, we will use the calendar_friends model as filter and not the color field.")
    calendar_attr_color_is_attendee = fields.Boolean('Color is Attendee')
    calendar_field_ids = fields.One2many('builder.ir.model.view.config.wizard.calendar.fields', 'wizard_id', 'Fields')

    _sql_constraints = [
        ('model_uniq', 'unique (model_id)', 'The model must be unique !'),
    ]

    @api.onchange('calendar_attr_date_start_field_id')
    def _compute_calendar_attr_date_start_ttype(self):
        self.calendar_attr_date_start_ttype = self.calendar_attr_date_start_field_id.ttype if self.calendar_attr_date_start_field_id else False

    @api.onchange('calendar_attr_color_field_id')
    def _compute_calendar_attr_color_ttype(self):
        self.calendar_attr_color_ttype = self.calendar_attr_color_field_id.ttype if self.calendar_attr_color_field_id else False

    @api.multi
    def action_generate(self):
        # self.unlink()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_save(self):
        # self.unlink()
        return {'type': 'ir.actions.act_window_close'}



    @api.onchange('form_view')
    def _onchange_form_view(self):
        self.form_attr_string = self.model_id.name
        self.form_view_id = "view_{snake}_form".format(snake = snake_case(self.model_id.model))
        self.form_show_status_bar = True if self.model_id.special_states_field_id.id else False

        if not len(self.form_field_ids):
            field_list = []
            for field in self.model_id.field_ids:
                if field.name in ['state']: continue
                field_list.append({'field_id': field.id, 'widget': DEFAULT_WIDGETS_BY_TYPE.get(field.ttype), 'field_ttype': field.ttype, 'model_id': self.model_id.id, 'special_states_field_id': self.model_id.special_states_field_id.id})

            self.form_field_ids = field_list


    @api.onchange('tree_view')
    def _onchange_tree_view(self):
        self.tree_attr_string = self.model_id.name
        self.tree_view_id = "view_{snake}_tree".format(snake = snake_case(self.model_id.model))


    @api.onchange('search_view')
    def _onchange_tree_view(self):
        self.search_attr_string = self.model_id.name
        self.search_view_id = "view_{snake}_search".format(snake = snake_case(self.model_id.model))


    @api.onchange('graph_view')
    def _onchange_graph_view(self):
        self.graph_attr_string = self.model_id.name
        self.graph_view_id = "view_{snake}_graph".format(snake = snake_case(self.model_id.model))

    @api.onchange('calendar_view')
    def _onchange_calendar_view(self):
        self.calendar_attr_string = self.model_id.name
        self.calendar_view_id = "view_{snake}_calendar".format(snake = snake_case(self.model_id.model))

    @api.onchange('gantt_view')
    def _onchange_gantt_view(self):
        self.gantt_attr_string = self.model_id.name
        self.gantt_view_id = "view_{snake}_gantt".format(snake = snake_case(self.model_id.model))





