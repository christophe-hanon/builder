import math
from openerp.tools import graph
from openerp import tools
from openerp.osv import osv

__author__ = 'one'


def process_order(self):
    """Finds actual-order of the nodes with respect to maximum number of nodes in a rank in component
    """

    if self.Is_Cyclic:
        max_level = max(map(lambda x: len(x), self.levels.values()))

        if max_level % 2:
            self.result[self.start]['y'] = (max_level + 1) / 2 + self.max_order + (self.max_order and 1)
        else:
            self.result[self.start]['y'] = max_level / 2 + self.max_order + (self.max_order and 1)

        self.graph_order()

    else:
        self.result[self.start]['y'] = 0
        self.tree_order(self.start, 0)
        min_order = math.fabs(min(map(lambda x: x['y'], self.result.values())))

        index = self.start_nodes.index(self.start)
        same = False

        roots = []
        if index > 0:
            for start in self.start_nodes[:index]:
                same = True
                for edge in self.tree_list[start][1:]:
                    if edge in self.tree_list[self.start]:
                        continue
                    else:
                        same = False
                        break
                if same:
                    roots.append(start)

        if roots:
            min_order += self.max_order
        else:
            min_order += self.max_order + 1

        for level in self.levels:
            for node in self.levels[level]:
                self.result[node]['y'] += min_order

        clean_tree = {r: v for r, v in self.tree_list.items() if v} if self.tree_list else {}

        if roots:
            roots.append(self.start)
            if clean_tree and self.start in self.tree_list and len(self.tree_list[self.start]):
                one_level_el = self.tree_list[self.start][0][1]
                base = self.result[one_level_el]['y']  # * 2 / (index + 2)
            else:
                base = 0

            no = len(roots)
            first_half = roots[:no / 2]

            if no % 2 == 0:
                last_half = roots[no / 2:]
            else:
                last_half = roots[no / 2 + 1:]

            factor = -math.floor(no / 2)
            for start in first_half:
                self.result[start]['y'] = base + factor
                factor += 1

            if no % 2:
                self.result[roots[no / 2]]['y'] = base + factor
            factor += 1

            for start in last_half:
                self.result[start]['y'] = base + factor
                factor += 1

        self.max_order = max(map(lambda x: x['y'], self.result.values()))


def process(self, starting_node):
    """Process the graph to find ranks and order of the nodes

        @param starting_node node from where to start the graph search
        """

    self.start_nodes = starting_node or []
    self.partial_order = {}
    self.links = []
    self.tree_list = {}

    if self.nodes:
        if self.start_nodes:
            # add dummy edges to the nodes which does not have any incoming edges
            tree = self.make_acyclic(None, self.start_nodes[0], 0, [])

            for node in self.no_ancester:
                for sec_node in self.transitions.get(node, []):
                    if sec_node in self.partial_order.keys():
                        self.transitions[self.start_nodes[0]].append(node)
                        break

            self.partial_order = {}
            tree = self.make_acyclic(None, self.start_nodes[0], 0, [])


        # if graph is disconnected or no start-node is given
        # than to find starting_node for each component of the node
        if len(self.nodes) > len(self.partial_order):
            self.find_starts()

        self.max_order = 0
        # for each component of the graph find ranks and order of the nodes
        for s in self.start_nodes:
            self.start = s
            self.rank()  # First step:Netwoek simplex algorithm
            self.order_in_rank()  #Second step: ordering nodes within ranks


def init_order(self, node, level):
    """Initialize orders the nodes in each rank with depth-first search
        """

    self._init_order(node, level, self.transitions)


def _init_order(self, node, level, transitions):
    if not self.result[node]['y']:
        self.result[node]['y'] = self.order[level]
        self.order[level] += 1

    node_trans = transitions.get(node, [])
    if node in transitions:
        del transitions[node]

    for sec_end in node_trans:
        if node != sec_end:
            self._init_order(sec_end, self.result[sec_end]['x'], transitions)


def tree_order(self, node, last=0):
    mid_pos = self.result[node]['y']
    l = list(set(self.transitions.get(node, [])) - {node})
    l.reverse()
    no = len(l)

    rest = no % 2
    first_half = l[no / 2 + rest:]
    last_half = l[:no / 2]

    for i, child in enumerate(first_half):
        self.result[child]['y'] = mid_pos - (i + 1 - (0 if rest else 0.5))

        if self.transitions.get(child, False):
            if last:
                self.result[child]['y'] = last + len(self.transitions[child]) / 2 + 1
            last = self.tree_order(child, last)

    if rest:
        mid_node = l[no / 2]
        self.result[mid_node]['y'] = mid_pos

        if self.transitions.get(mid_node, False):
            if last:
                self.result[mid_node]['y'] = last + len(self.transitions[mid_node]) / 2 + 1
            if node != mid_node:
                last = self.tree_order(mid_node)
        else:
            if last:
                self.result[mid_node]['y'] = last + 1
        self.result[node]['y'] = self.result[mid_node]['y']
        mid_pos = self.result[node]['y']

    i = 1
    last_child = None
    for child in last_half:
        self.result[child]['y'] = mid_pos + (i - (0 if rest else 0.5))
        last_child = child
        i += 1
        if self.transitions.get(child, False):
            if last:
                self.result[child]['y'] = last + len(self.transitions[child]) / 2 + 1
            if node != child:
                last = self.tree_order(child, last)

    if last_child:
        last = self.result[last_child]['y']

    return last


class view(osv.osv):
    _inherit = 'ir.ui.view'

    def graph_get(self, cr, uid, id, model, node_obj, conn_obj, src_node, des_node, label, scale, context=None):
        nodes = []
        nodes_name = []
        transitions = []
        start = []
        tres = {}
        labels = {}
        no_ancester = []
        blank_nodes = []

        _Model_Obj = self.pool[model]
        _Node_Obj = self.pool[node_obj]
        _Arrow_Obj = self.pool[conn_obj]

        for model_key, model_value in _Model_Obj._columns.items():
            if model_value._type == 'one2many':
                if model_value._obj == node_obj:
                    _Node_Field = model_key
                    _Model_Field = model_value._fields_id
                flag = False
                for node_key, node_value in _Node_Obj._columns.items():
                    if node_value._type == 'one2many':
                        if node_value._obj == conn_obj:
                            if src_node in _Arrow_Obj._columns and flag:
                                _Source_Field = node_key
                            if des_node in _Arrow_Obj._columns and not flag:
                                _Destination_Field = node_key
                                flag = True

        # _Destination_Field = 'from_ids'
        # _Source_Field = 'to_ids'
        datas = _Model_Obj.read(cr, uid, id, [], context)
        for a in _Node_Obj.read(cr, uid, datas[_Node_Field], []):
            if a[_Source_Field] or a[_Destination_Field]:
                nodes_name.append((a['id'], a['name']))
                nodes.append(a['id'])
            else:
                blank_nodes.append({'id': a['id'], 'name': a['name']})

            if a.has_key('flow_start') and a['flow_start']:
                start.append(a['id'])
            else:
                if not a[_Source_Field]:
                    no_ancester.append(a['id'])
            for t in _Arrow_Obj.read(cr, uid, a[_Destination_Field], []):
                if des_node not in t or not t[des_node] or len(t[des_node]) == 0:
                    continue

                transitions.append((a['id'], t[des_node][0]))
                tres[str(t['id'])] = (a['id'], t[des_node][0])
                label_string = ""
                if label:
                    for lbl in eval(label):
                        if t.has_key(tools.ustr(lbl)) and tools.ustr(t[lbl]) == 'False':
                            label_string += ' '
                        else:
                            label_string = label_string + " " + tools.ustr(t[lbl])
                labels[str(t['id'])] = (a['id'], label_string)
        g = graph(nodes, transitions, no_ancester)
        g.process(start)
        g.scale(*scale)
        result = g.result_get()
        results = {}
        for node in nodes_name:
            results[str(node[0])] = result[node[0]]
            results[str(node[0])]['name'] = node[1]
        return {'nodes': results,
                'transitions': tres,
                'label': labels,
                'blank_nodes': blank_nodes,
                'node_parent_field': _Model_Field, }