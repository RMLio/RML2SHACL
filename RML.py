import rdflib
import pprint

class RML:
    def __init__(self):
        self.graph = rdflib.Graph()
    def printGraph(self, keuze):
        if keuze == 1: 
            for stmt in self.graph:
                print(stmt)
        else:
            for stmt in self.graph:
                pprint.pprint(stmt)
    def createGraph(self):
        self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0000-CSV\\mapping.ttl", format="turtle")
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0002a-CSV\\mapping.ttl", format="turtle")
    def removeBlankNodes(self):
        for s,p,o in self.graph:
            for s2,p2,o2 in self.graph:
                if o == s2:
                    self.graph.add((p,p2,o2))
                    self.graph.remove((s2,p2,o2))
                    self.graph.remove((s,p,o))

#wat als we meerdere triplemaps hebben?? testen op eerste subject en daaruit naam triples map halen



#print(rdflib.util.guess_format("RML.ttl"))

#g = rdflib.Graph()
#g.parse("RML.ttl", format="turtle")
#g.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0000-CSV\\mapping.ttl", format="turtle")


#from rdflib import Namespace


