import math

__author__ = 'one'


def process_order(self):
    """Finds actual-order of the nodes with respect to maximum number of nodes in a rank in component
    """

    if self.Is_Cyclic:
        max_level = max(map(lambda x: len(x), self.levels.values()))

        if max_level%2:
            self.result[self.start]['y'] = (max_level+1)/2 + self.max_order + (self.max_order and 1)
        else:
            self.result[self.start]['y'] = max_level /2 + self.max_order + (self.max_order and 1)

        self.graph_order()

    else:
        self.result[self.start]['y'] = 0
        self.tree_order(self.start, 0)
        min_order = math.fabs(min(map(lambda x: x['y'], self.result.values())))

        index = self.start_nodes.index(self.start)
        same = False

        roots  = []
        if index>0:
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

        clean_tree = { r: v for r,v  in self.tree_list.items() if v} if self.tree_list else {}

        if roots:
            roots.append(self.start)
            if clean_tree:
                one_level_el = self.tree_list[self.start][0][1]
                base = self.result[one_level_el]['y']# * 2 / (index + 2)
            else:
                base = 0

            no = len(roots)
            first_half = roots[:no/2]

            if no%2==0:
                last_half = roots[no/2:]
            else:
                last_half = roots[no/2+1:]

            factor = -math.floor(no/2)
            for start in first_half:
                self.result[start]['y'] = base + factor
                factor += 1

            if no%2:
                self.result[roots[no/2]]['y'] = base + factor
            factor +=1

            for start in last_half:
                self.result[start]['y'] = base + factor
                factor += 1

        self.max_order = max(map(lambda x: x['y'], self.result.values()))

