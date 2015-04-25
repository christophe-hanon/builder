__author__ = 'one'
from openerp import models, fields, api, _


class Workflow(models.Model):
    _name = 'builder.workflow'
    _order = "name"

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='cascade')
    name = fields.Char('Name', required=True)
    model_id = fields.Many2one('builder.ir.model', 'Model', ondelete='cascade')
    on_create = fields.Boolean('On Create', default=True)
    activities = fields.One2many('builder.workflow.activity', 'wkf_id', 'Activities')

    def copy(self, values):
        raise Warning(_("Duplicating workflows is not possible, please create a new workflow"))


class WorkflowActivity(models.Model):
    _name = 'builder.workflow.activity'
    _order = "name"

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='cascade', related='wkf_id.module_id', store=True)
    wkf_id = fields.Many2one('builder.workflow', 'Workflow', required=True, ondelete='cascade')
    name = fields.Char('Name', required=True)
    split_mode = fields.Selection([('XOR', 'Xor'), ('OR','Or'), ('AND','And')], 'Split Mode', size=3, default='XOR')
    join_mode = fields.Selection([('XOR', 'Xor'), ('AND', 'And')], 'Join Mode', size=3, required=True, default='XOR')
    kind = fields.Selection([('dummy', 'Dummy'), ('function', 'Function'), ('subflow', 'Subflow'), ('stopall', 'Stop All')], 'Kind', required=True, default='dummy')
    action = fields.Text('Python Action')
    action_id = fields.Many2one('ir.actions.server', 'Server Action', ondelete='set null')
    action_ref = fields.Char('Server Action Ref')
    flow_start = fields.Boolean('Flow Start')
    flow_stop = fields.Boolean('Flow Stop')
    subflow_type = fields.Selection([('module', 'Module'), ('system', 'System')], 'Subflow Type')
    system_subflow_id = fields.Many2one('workflow', 'Subflow')
    system_subflow_ref = fields.Char('Subflow Ref')
    module_subflow_id = fields.Many2one('builder.workflow', 'Subflow')
    signal_send = fields.Char('Signal (subflow.*)')
    out_transitions = fields.One2many('builder.workflow.transition', 'act_from', 'Outgoing Transitions')
    in_transitions = fields.One2many('builder.workflow.transition', 'act_to', 'Incoming Transitions')
    has_subflow = fields.Boolean('Has Subflow', compute='_compute_has_subflow')
    diagram_position_x = fields.Integer('X')
    diagram_position_y = fields.Integer('Y')

    @api.one
    @api.depends('subflow_type', 'system_subflow_id', 'module_subflow_id')
    def _compute_has_subflow(self):
        self.has_subflow = self.subflow_type and (fields.system_subflow_id != False or self.module_subflow_id != False)

    @api.onchange('system_subflow_ref')
    def onchange_system_subflow_ref(self):
        self.system_subflow_id = False
        if self.system_subflow_ref:
            self.system_subflow_id = self.env['ir.model.data'].xmlid_to_res_id(self.system_subflow_ref)

    @api.onchange('system_subflow_id')
    def onchange_system_subflow_id(self):
        if self.system_subflow_id:
            data = self.env['ir.model.data'].search([('model', '=', self._name), ('res_id', '=', self.system_subflow_id.id)])
            self.system_subflow_ref = "{module}.{id}".format(module=data.module, id=data.name) if data.id else False

    @api.onchange('subflow_type')
    def onchange_subflow_type(self):
        self.system_subflow_ref = False
        self.system_subflow_id = False
        self.module_subflow_id = False


class WorkflowTransition(models.Model):
    _name = 'builder.workflow.transition'
    _rec_name = 'signal'

    _order = 'sequence,id'

    module_id = fields.Many2one('builder.ir.module.module', 'Module', ondelete='cascade', related='wkf_id.module_id', store=True)
    sequence = fields.Integer('Sequence', default=10)
    signal = fields.Char('Signal (Button Name)',
                         help="When the operation of transition comes from a button pressed in the client form, "\
                              "signal tests the name of the pressed button. If signal is NULL, no button is necessary to validate this transition.")
    group_id = fields.Many2one('res.groups', 'Group Required', help="The group that a user must have to be authorized to validate this transition.")
    condition = fields.Char('Condition', required=True,
                            help="Expression to be satisfied if we want the transition done.", default='True')
    act_from = fields.Many2one('builder.workflow.activity', 'Source Activity', required=True, select=True, ondelete='cascade',
                                    help="Source activity. When this activity is over, the condition is tested to determine if we can start the ACT_TO activity.")
    act_to = fields.Many2one('builder.workflow.activity', 'Destination Activity', required=True, select=True, ondelete='cascade',
                                  help="The destination activity.")
    wkf_id = fields.Many2one('builder.workflow', related='act_from.wkf_id', string='Workflow', select=True)

