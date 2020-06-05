import rdflib
import pprint

from FilesGitHub import *

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
        self.datatype = self.r2rmlNS.datatype
        self.graphs = []
        self.refgraphs = []
    def printGraph(self, keuze):
        if keuze == 1: 
            for stmt in self.graph:
                print(stmt)
        else:
            for stmt in self.graph:
                pprint.pprint(stmt)
    def createGraph(self,number, letter,typeInputFile):
        fileReadObj = FilesGitHub()
        filename = fileReadObj.getFile(number,letter,typeInputFile,fileReadObj.Mappingfile)
        self.graph.parse(filename,format=rdflib.util.guess_format(filename)) 
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
                    #the triples belonging to the Logical Source
                    if p == self.rmlNS.logicalSource:
                        for s2,p2,o2 in self.graph.triples((o,None,None)): 
                        #searching for same Blank Node
                            graphlogicalSource.add((p,p2,o2)) #add logical source info
                        graphHelp["LS"] = graphlogicalSource
                    #the triples belonging to the Subject Map
                    if p == self.sSM:
                        for s2,p2,o2 in self.graph.triples((o,None,None)): 
                        #searching for same Blank Node
                            graphsubjectMap.add((p,p2,o2))
                         #add subject Map  info
                        graphHelp["SM"] = graphsubjectMap
                    #the multiple triples that are PredicateObject Maps
                    if p == self.sPOM:
                        graphPredicatObjectMap = rdflib.Graph()
                        #searching for one PredicatObjectMap
                        for s2,p2,o2 in self.graph.triples((o,None,None)): #searching for same Blank Node
                            if p2 == self.r2rmlNS.predicateMap:
                                for s3,p3,o3 in self.graph.triples((o2,self.pCons,None)):
#we make the "rr:predicateMap rr:constant o" triple to sthe shurtcut "rr:PredicateObjectMap rr:predicate o2" 
                                   graphPredicatObjectMap.add((p,self.pPred,o3))      
 #add the predicateobjectMap with the constant transformed into rr:predicate instead of constant
                            else:
                                graphPredicatObjectMap.add((p,p2,o2))       
                            #add the predicateobjectMap
#searching for which objectMap belongs to this PredicateObjectMap 
                        for s2,p2,o2 in graphPredicatObjectMap.triples((p,self.oM,None)):
                            for s3,p3,o3 in self.graph.triples((o2,None,None)):
                                graphPredicatObjectMap.add((p2,p3,o3))     
#add the objectMap beloning to the predicateobjectMap added in previous loop
                            graphPredicatObjectMap.remove((s2,p2,o2)) 
#remove something with a blanknode in that we added too much
# if we don't have an rr:ObjectMap but an rr:object (as part of rr:predicateMap as an predicate) 
# we will write this as rr:ObjectMap rr:constant (object that belonged to the rr:object)
                        for s2,p2,o2 in graphPredicatObjectMap.triples((p,self.obj,None)):
 #graphPredicatObjectMap.add((s2,p2,o2))      
 # #add the object beloning to the predicateobjectMap added in previous loop
                            graphPredicatObjectMap.add((self.oM,self.pCons,o2))
                            graphPredicatObjectMap.remove((s2,p2,o2))
 #remove the "rr:predicateMap rr:object o2" triple from the graph because it gets added in loop for objectMap
                        #loop to find any possible RefObjectMaps
                        for sROM,pROM,oROM in self.graph.triples((None,None,self.r2rmlNS.RefObjectMap)):
#if we find one we see if it belongs to the ObjectMap we are working with now
                            for s3,p3,o3 in self.graph.triples((p,self.oM,sROM)):
#if this is the fact we search inside the RefObjectMap (sROM) for the value of rr:parentTriplesMap
                                for s4, p4,o4 in self.graph.triples((sROM,self.r2rmlNS.parentTriplesMap,None)):
                                    graphPredicatObjectMap.add((self.oM,self.r2rmlNS.parentTriplesMap,o4))
#add the parentTriplesMap to the ObjectMap

                        graphHelp["POM"+str(tel)] = graphPredicatObjectMap
                        tel = tel +1
            self.graphs.append(graphHelp)
    def printDictionary(self, keuze):
        for graphHelp in self.graphs:
            if keuze == 1:
                for g in graphHelp["TM"]:
                    print("TM graph: " + str(g))
            if keuze == 2:
                for g in graphHelp["LS"]:
                    print(g)
            if keuze == 3:
                for g in graphHelp["SM"]:
                    print(g)
            if keuze == 4:
                length = len(graphHelp)-3
#Because the dictionary inside graphHelp has first 'TM', 'LM' and 'SM' as keys
# we do the length of the dictionary minus 3
#this way we can use this newly calculated length 
#for the indexes used for the possible multiple PredicateObjectsMaps (POM)
                for i in range(length):
                    print("new POM" + str(i))
                    for g in graphHelp["POM"+str(i)]:
                        print(g)
            if keuze == 5:
                for n,g in graphHelp.items():
                    for stm in g:
                        print(n,stm)
            if keuze == 6:
                for g in graphHelp.values():
                    for stm in g:
                        print(stm)
                
            
    def testmain(self):
        self.createGraph(7,'b',FilesGitHub.CSV)
        self.removeBlankNodesMultipleMaps()
        self.printDictionary(5)
if __name__ == '__main__':
    Rml = RML()
    Rml.testmain()


