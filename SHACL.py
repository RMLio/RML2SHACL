import rdflib
class SHACL:
    def __init__(self):
        self.graph = rdflib.Graph()
    def printGraph(self, keuze):
        if keuze == 1: 
            for stmt in self.graph:
                print(stmt)
        else:
            for stmt in self.graph:
                pprint.pprint(stmt)