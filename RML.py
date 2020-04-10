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
        self.oM  = self.r2rmlNS.objectMap
        self.IRI = self.r2rmlNS.IRI
        self.pLan  = self.r2rmlNS.language
        self.pCons  = self.r2rmlNS.constant
        self.obj = self.r2rmlNS.object
        self.graphs = []
        self.refgraphs = []
    def printGraph(self, keuze):
        if keuze == 1: 
            for stmt in self.graph:
                print(stmt)
        else:
            for stmt in self.graph:
                pprint.pprint(stmt)
    def createGraph(self):
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0000-CSV\\mapping.ttl", format="turtle")
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0002a-CSV\\mapping.ttl", format="turtle") #with rr:class
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0004a-CSV\\mapping.ttl", format="turtle")
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0005a-CSV\\mapping.ttl", format="turtle")


        #to do: constants => works for object but not yet for subject and or predicateMap
        self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0006a-CSV\\mapping.ttl", format="turtle")


        # #troubles readin this RML file in => template object bad escape
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0010c-CSV\\mapping.ttl", format="turtle")

        #works template
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0011b-CSV\\mapping.ttl", format="turtle")
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0012a-CSV\\mapping.ttl", format="turtle")

        #lang test
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0015a-CSV\\mapping.ttl", format="turtle") #geen rdfs
        #self.graph.parse("C:\\Users\\Birte\\Documents\\masterproefHelpFiles\\rml15withRDFS.ttl",format="turtle")

        #self.graph.parse("C:\\Users\\Birte\\Documents\\masterproefHelpFiles\\rmlex.ttl",format="turtle")

        #parentriplemap test
        #self.graph.parse("C:\\Users\\Birte\\Documents\\GitHub\\rml-test-cases\\test-cases\\RMLTC0008b-CSV\\mapping.ttl", format="turtle") #geen rdf
        #self.graph.parse("C:\\Users\\Birte\\Documents\\masterproefHelpFiles\\rml8bwithRDFS.ttl",format="turtle") 
        '''for ns in self.graph.namespaces():
            print(ns)'''
        #self.printGraph(1)

    def removeBlankNodesMultipleMaps(self):
        #loop over all the Triple Maps in the RML input file
        for sTM,pTM,oTM in self.graph.triples((None,None,self.r2rmlNS.TriplesMap)):
            graphHelp = {}
            graphsPOM = []
            graphTripleMap = rdflib.Graph()
            graphsubjectMap = rdflib.Graph()
            graphlogicalSource = rdflib.Graph()
            graphTripleMap.add((sTM,pTM,oTM)) #add triplesmap header
            graphHelp["TM"] = graphTripleMap
            tel=0
            #inside one Triple Map we doe loops over:
            for s,p,o in self.graph.triples((sTM,None,None)):
                #if s==sTM:
                    #the triples belonging to the Logical Source
                    if p == self.rmlNS.logicalSource:
                        for s2,p2,o2 in self.graph.triples((o,None,None)): #searching for same Blank Node
                            graphlogicalSource.add((p,p2,o2)) #add logical source info
                        graphHelp["LS"] = graphlogicalSource
                    #the triples belonging to the Subject Map
                    if p == self.sSM:
                        for s2,p2,o2 in self.graph.triples((o,None,None)): #searching for same Blank Node
                            graphsubjectMap.add((p,p2,o2)) #add subject Map  info
                        graphHelp["SM"] = graphsubjectMap
                    #the multiple triples that are PredicateObject Maps
                    if p == self.sPOM:
                        graphPredicatObjectMap = rdflib.Graph()
                        #searching for one PredicatObjectMap
                        for s2,p2,o2 in self.graph.triples((o,None,None)): #searching for same Blank Node
                            if p2 == self.r2rmlNS.predicateMap:
                                for s3,p3,o3 in self.graph.triples((o2,self.pCons,None)):
                                    #we make the "rr:predicateMap rr:constant o" triple to sthe shurtcut "rr:PredicateObjectMap rr:predicate o2" 
                                   graphPredicatObjectMap.add((p,self.pPred,o3))       #add the predicateobjectMap with the constant transformed into rr:predicate instead of constant
                            else:
                                graphPredicatObjectMap.add((p,p2,o2))       #add the predicateobjectMap
                        #searching for which objectMap belongs to this PredicateObjectMap 
                        for s2,p2,o2 in graphPredicatObjectMap.triples((p,self.oM,None)):
                            for s3,p3,o3 in self.graph.triples((o2,None,None)):
                                graphPredicatObjectMap.add((p2,p3,o3))      #add the objectMap beloning to the predicateobjectMap added in previous loop
                            graphPredicatObjectMap.remove((s2,p2,o2)) #remove something with a blanknode in that we added too much
                        # if we don't have an rr:ObjectMap but an rr:object (as part of rr:predicateMap as an predicate) we will write this as rr:ObjectMap rr:constant (object that belonged to the rr:object)
                        for s2,p2,o2 in graphPredicatObjectMap.triples((p,self.obj,None)):
                            #graphPredicatObjectMap.add((s2,p2,o2))      #add the object beloning to the predicateobjectMap added in previous loop'''
                            graphPredicatObjectMap.add((self.oM,self.pCons,o2))
                            graphPredicatObjectMap.remove((s2,p2,o2)) #remove the "rr:predicateMap rr:object o2" triple from the graph because it gets added in loop for objectMap
                        #loop to find any possible RefObjectMaps
                        for sROM,pROM,oROM in self.graph.triples((None,None,self.r2rmlNS.RefObjectMap)):
                            #if we find one we see if it belongs to the ObjectMap we are working with now
                            for s3,p3,o3 in self.graph.triples((p,self.oM,sROM)):
                                #if this is the fact we search inside the RefObjectMap (sROM) for the value of rr:parentTriplesMap
                                for s4, p4,o4 in self.graph.triples((sROM,self.r2rmlNS.parentTriplesMap,None)):
                                    graphPredicatObjectMap.add((self.oM,self.r2rmlNS.parentTriplesMap,o4)) #add the parentTriplesMap to the ObjectMap

                        graphHelp["POM"+str(tel)] = graphPredicatObjectMap
                        tel = tel +1
            self.graphs.append(graphHelp)
        '''for sROM,pROM,oROM in self.graph.triples((None,None,self.r2rmlNS.RefObjectMap)):
            graphHelp = {}
            graph = rdflib.Graph()
            graph.add((sROM,pROM,oROM))
            for s,p,o in self.graph.triples((sROM,None,None)):
                    graph.add((s,p,o))
            graphHelp['ROM'] = graph
            for g in graphHelp['ROM']:
                print(g)
            self.refgraphs.append(graphHelp)'''


        #print(self.graphs)
        for graphHelp in self.graphs:
            '''for g in graphHelp["TM"]:
                print("TM graph: " + str(g))
            for g in graphHelp["LS"]:
                print(g)
            for g in graphHelp["SM"]:
                print(g)
            lengte = len(graphHelp)-3
            for i in range(lengte):
                print("new POM" + str(i))
                for g in graphHelp["POM"+str(i)]:
                    print(g)'''
            for n,g in graphHelp.items():
                 for stm in g:
                    print(n,stm)
            '''for g in graphHelp.values():
               for stm in g:
                    print(stm)'''
            
            
    def main(self):
        self.createGraph()
        self.removeBlankNodesMultipleMaps()

Rml = RML()
Rml.main()