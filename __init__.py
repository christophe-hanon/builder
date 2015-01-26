__author__ = 'one'

from . import models
from . import wizard
from . import controllers
from . import tests
from openerp.tools import graph
import logging
from .tools.graph import process_order

_logger = logging.getLogger(__name__)


graph.process_order = process_order
