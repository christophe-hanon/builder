__author__ = 'one'

from . import models
from . import wizard
from . import controllers
from . import tests
from openerp.tools import graph
import logging
from .tools.graph import process_order, tree_order, process

_logger = logging.getLogger(__name__)

graph.process_order = process_order
graph.tree_order = tree_order
# graph.process = process
