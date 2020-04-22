import rdflib
import pprint
from pyshacl import validate
class SHACL:
    def __init__(self):
        self.graph = rdflib.Graph()
    def printGraph(self, keuze,graph):
        if keuze == 1: 
            for stmt in graph:
                print("SHACL:" + str(stmt))
        else:
            for stmt in graph:
                pprint.pprint(stmt)
    def Validation(self, graph,data_graph):

        r = validate(data_graph, shacl_graph=graph, ont_graph=None, inference='rdfs', abort_on_error=False, meta_shacl=False, debug=False)
        conforms, results_graph, results_text = r
        self.printGraph(1,results_graph)
        print(results_text)