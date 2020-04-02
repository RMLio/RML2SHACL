import rdflib
import pprint

class RML:
    def __init__(self):
        self.graph = rdflib.Graph()
        self.rmlNS = rdflib.Namespace('http://semweb.mmlab.be/ns/rml#')
        self.r2rmlNS = rdflib.Namespace('http://www.w3.org/ns/r2rml#')
        self.template = self.r2rmlNS.template
        self.reference = self.rmlNS.reference
        self.termType = self.r2rmlNS.termType
        self.sPOM = self.r2rmlNS.predicateObjectMap
        self.pPred = self.r2rmlNS.predicate
        self.pPredMap = self.r2rmlNS.predicateMap
        self.tM = self.r2rmlNS.TriplesMap
        self.sSM = self.r2rmlNS.subjectMap
        self.pclass = self.r2rmlNS['class']
        self.sOM  = self.r2rmlNS.objectMap
        self.IRI = self.r2rmlNS.IRI
        self.pLan  = self.r2rmlNS.language
        self.pCons  = self.r2rmlNS.constant
        self.graphs = []
    def printGraph(self, keuze):
        if keuze == 1: 
            for stmt in self.graph:
                print(stmt)
        else:
            for stmt in self.graph:
                pprint.pprint(stmt)
    def createGraph(self):
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0000-CSV\\mapping.ttl", format="turtle")
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0002a-CSV\\mapping.ttl", format="turtle")
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0004a-CSV\\mapping.ttl", format="turtle")
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0005a-CSV\\mapping.ttl", format="turtle")


        #to do: constants => works for object but not yet for subject and or predicateMap
        self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0006a-CSV\\mapping.ttl", format="turtle")


        #geeft fout => stringpattern is niet juist
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0011b-CSV\\mapping.ttl", format="turtle")
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0012a-CSV\\mapping.ttl", format="turtle")


        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0015a-CSV\\mapping.ttl", format="turtle") #geen rdfs
        #self.graph.parse("C:\\Users\\Birte\\Documents\\masterproefHelpFiles\\rml15withRDFS.ttl",format="turtle")

        #self.graph.parse("C:\\Users\\Birte\\Documents\\masterproefHelpFiles\\rmlex.ttl",format="turtle")
        for ns in self.graph.namespaces():
            print(ns)
        #self.printGraph(1)
    def removeBlankNodes(self):
        for s,p,o in self.graph:
            for s2,p2,o2 in self.graph:
                if o == s2:
                    self.graph.add((p,p2,o2))
                    self.graph.remove((s2,p2,o2))
                    self.graph.remove((s,p,o))
    def removeBlankNodesMultipleMaps(self):
        for sTM,pTM,oTM in self.graph.triples((None,None,self.r2rmlNS.TriplesMap)):
            graph = rdflib.Graph()
            graph.add((sTM,pTM,oTM))
            for s,p,o in self.graph:
                if s==sTM:
                    for s2,p2,o2 in self.graph.triples((o,None,None)): #searching for same Blank Node
                        if p2 == self.r2rmlNS.objectMap:        #same for when we have refernrece map stuff??? (future work)
                            for s3,p3,o3 in self.graph.triples((o2,None,None)):
                                graph.add((p2,p3,o3))
                        else:
                            graph.add((p,p2,o2))
            self.graphs.append(graph)
        for graph in self.graphs:
            print("Hallo")
            for stmt in graph:
                print(stmt)
        

#wat als we meerdere triplemaps hebben?? testen op eerste subject en daaruit naam triples map halen

