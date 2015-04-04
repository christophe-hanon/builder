from addons.builder.tools.render import JinjaRender

__author__ = 'one'

from . import models
from . import wizard
from . import controllers
from . import tests
from openerp.tools import graph
import logging
from .tools.graph import process_order, tree_order, process, init_order, _init_order

_logger = logging.getLogger(__name__)

graph.process_order = process_order
graph.tree_order = tree_order
graph.init_order = init_order
graph._init_order = _init_order
# graph.process = process

render = JinjaRender(['builder/data/templates/python'])