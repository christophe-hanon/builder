from openerp.tools import graph

__author__ = 'one'
from openerp import api

def simple_selection(model, value_field, label_field=None, domain=None):
    domain = domain or []
    label_field = label_field or value_field
    @api.model
    def _selection_function(self):
        return [(getattr(c, value_field), getattr(c, label_field)) for c in self.env[model].search(domain)]
    return _selection_function

