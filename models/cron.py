import logging
from openerp.addons.base.ir.ir_cron import str2tuple
import threading
import time
import psycopg2
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz

import openerp
from openerp import SUPERUSER_ID, netsvc, api
from openerp.osv import fields, osv
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools.safe_eval import safe_eval as eval
from openerp.tools.translate import _
from openerp.modules import load_information_from_description_file

_logger = logging.getLogger(__name__)


class ir_cron(osv.osv):
    """ Model describing cron jobs (also called actions or tasks).
    """

    # TODO: perhaps in the future we could consider a flag on ir.cron jobs
    # that would cause database wake-up even if the database has not been
    # loaded yet or was already unloaded (e.g. 'force_db_wakeup' or something)
    # See also openerp.cron

    _name = "builder.ir.cron"
    _order = 'name'
    _columns = {
        'module_id': fields.many2one('builder.ir.module.module', 'Module', ondelete='cascade'),

        'name': fields.char('Name', required=True),
        'active': fields.boolean('Active'),
        'interval_number': fields.integer('Interval Number',help="Repeat every x."),
        'interval_type': fields.selection( [('minutes', 'Minutes'),
            ('hours', 'Hours'), ('work_days','Work Days'), ('days', 'Days'),('weeks', 'Weeks'), ('months', 'Months')], 'Interval Unit'),
        'numbercall': fields.integer('Number of Calls', help='How many times the method is called,\na negative number indicates no limit.'),
        'doall' : fields.boolean('Repeat Missed', help="Specify if missed occurrences should be executed when the server restarts."),
        'nextcall' : fields.datetime('Next Execution Date', help="Next planned execution date for this job."),
        'model_id': fields.many2one('builder.ir.model', 'Object', help="Model name on which the method to be called is located, e.g. 'res.partner'."),
        'model_method_id': fields.many2one('builder.ir.model.method', 'Method', help="Name of the method to be called when this job is processed."),
        'args': fields.text('Arguments', help="Arguments to be passed to the method, e.g. (uid,)."),
        'priority': fields.integer('Priority', help='The priority of the job, as an integer: 0 means higher priority, 10 means lower priority.')
    }

    _defaults = {
        'priority' : 5,
        'interval_number' : 1,
        'interval_type' : 'months',
        'numbercall' : 1,
        'active' : 1,
    }

    def _check_args(self, cr, uid, ids, context=None):
        try:
            for this in self.browse(cr, uid, ids, context):
                str2tuple(this.args)
        except Exception:
            return False
        return True

    _constraints = [
        (_check_args, 'Invalid arguments', ['args']),
    ]

    def toggle(self, cr, uid, ids, model, domain, context=None):
        active = bool(self.pool[model].search_count(cr, uid, domain, context=context))

        return self.try_write(cr, uid, ids, {'active': active}, context=context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: