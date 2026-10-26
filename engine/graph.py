
class Node():
    linked_edges: set[Edge] = set()
    outgoing_edges: set[Edge] = set()
    incoming_edges: set[Edge] = set()
    
    def __init__(self) -> None:
        pass

    def remove_edge(self, edge: Edge):
        if self not in edge.endpoints:
            return
        if edge in self.linked_edges:
            self.linked_edges.remove(edge)
        if edge in self.outgoing_edges:
            self.outgoing_edges.remove(edge)
        if edge in self.incoming_edges:
            self.incoming_edges.remove(edge)

class Edge():
    def __init__(self, source: Node, dest: Node, weight: int|float|None=None, directed=False) -> None:
        self.endpoints : set[Node] = set([source, dest])
        self.source : Node = source
        self.destination : Node = dest
        self.weight : int|float|None = weight

class Graph():
    nodes: set[Node] = set()
    edges: set[Edge] = set()

    def __init__(self) -> None:
        pass

    def add_node(self, node: Node):
        self.nodes.add(node)

    def add_edge(self, source:Node, dest:Node, weight=None, directed=False) -> Edge:
        edge = Edge(source, dest, weight, directed)
        self.edges.add(edge)
        return edge

    def remove_node(self, node: Node):
        self.nodes.remove(node)
        for edge in node.linked_edges:
            self.edges.remove(edge)

    def remove_edge(self, edge: Edge):
        self.edges.remove(edge)
        edge.source.remove_edge(edge)
        edge.destination.remove_edge(edge)

    def adjacent(self, source: Node, dest: Node):
        for edge in source.outgoing_edges:
            if edge in dest.incoming_edges:
                return True
        return False

    def neighbours(self, node: Node) -> set[Node]:
        n: set[Node] = set()
        for edge in node.linked_edges:
            n.union(edge.endpoints)
        return n

    def endpoints(self, edge: Edge)->set[Node]:
        return edge.endpoints

# operations:
# 	CREATE         : → GRAPH
# 	ADD_NODE       : GRAPH x ELEMENT → GRAPH
# 	ADD_EDGE       : GRAPH x ELEMENT x ELEMENT → GRAPH
# 	REMOVE_NODE    : GRAPH x ELEMENT → GRAPH
# 	REMOVE_EDGE    : GRAPH x ELEMENT → GRAPH
# 	ADJACENT       : GRAPH x ELEMENT x ELEMENT → BOOLEAN
# 	NEIGHBOURS     : GRAPH x ELEMENT → SET
# 	NODES          : GRAPH → SET
# 	EDGES          : GRAPH → SET
# 	ENDPOINTS      : ELEMENT → ARRAY