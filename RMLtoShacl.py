
import rdflib
from rdflib import RDF
from RML import *
from SHACL import *
class RMLtoSHACL:
    def __init__(self):
        self.RML = RML()
        self.RML.createGraph()
        #self.RML.removeBlankNodes()
        self.shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')      
        self.SHACL = SHACL()
        self.sNodeShape = None
        self.propertygraphs = []
    def createNodeShape(self, graph):
        #start of SHACL shape
        for s,p,o in graph["TM"]:      #.triples((None,RDF.type,self.RML.tM)):
            self.SHACL.graph.add((s,p,self.shaclNS.NodeShape))
        self.sNodeShape = s
    def inferclass(self):
        pass
    def subjectTargetOf(self,graph):
        for s,p,o in graph.triples((self.RML.sPOM,self.RML.pPred,None)):
            self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetSubjectsOf,o))  #can we have more than one targetSubjectsOf?
    def targetNode(self,graph):
        #if there's a constant in the subjectmzp we can add this as sh:targetNode for the shape
        for s,p,o in graph['SM'].triples((self.RML.sSM,self.RML.pCons,None)):
            self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetNode,o))

    def findClass(self,graph):
        for s,p,o in graph['SM'].triples((self.RML.sSM,self.RML.pclass,None)):
                self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetClass,o))
        self.inferclass()
    def fillinProperty(self, graph):
        propertyBl = rdflib.BNode()
        graphHelp = rdflib.Graph()
        for s,p,o in graph.triples((self.RML.sPOM,None,None)):
            graphHelp.add((self.sNodeShape,self.shaclNS.property,propertyBl))
            if p==self.RML.pPred :
                graphHelp.add((propertyBl,self.shaclNS.path,o))
            self.findObject(propertyBl,graphHelp,graph)
            self.propertygraphs.append(graphHelp)

            
    def findObject(self,propertyBl,graphHelp, graph):
        #we test if the object is an IRI or a Literal
        for s,p,o in graph.triples((self.RML.oM,None,None)):
            #Test for when it has a template
            result = self.testIfIRIorLiteral(p,o, graphHelp,propertyBl,graph)
            if not result and p == self.RML.pCons:
                graphHelp.add((propertyBl,self.shaclNS.hasValue, o))
            elif p == self.RML.r2rmlNS.parentTriplesMap:
                #test in other graphs
                #for s1,p1,o1 in graph.triples((o,None,None)):
                for graph in self.RML.graphs:
                    for s1,p1,o1 in graph['TM']:
                        if s1 == o:
                            print("Yes")
                            for s2,p2,o2 in graph['SM']:
                                self.testIfIRIorLiteralSubject(p2,o2, graphHelp, propertyBl,graph['SM'])
    def testIfIRIorLiteralSubject(self,p,o, graphHelp, propertyBl,graph):
        #Test for when it has a template
        if p == self.RML.template:
            stringpattern= self.createPattern(o)
            graphHelp.add((propertyBl,self.shaclNS.pattern,stringpattern))
            if p == self.RML.termType and o== self.RML.r2rmlNS.Literal:
                self.literalActions(propertyBl,graphHelp,graph)
            else:
                self.URIActions(propertyBl,graphHelp)
        #test for when it has a Reference
        elif p == self.RML.reference:
            if p == self.RML.termType and o== self.RML.IRI:
                self.URIActions(propertyBl,graphHelp)
            else:
                self.literalActions(propertyBl,graphHelp, graph)
    def testIfIRIorLiteral(self,p,o, graphHelp, propertyBl,graph):
        #Test for when it has a template
        if p == self.RML.template:
            stringpattern= self.createPattern(o)
            graphHelp.add((propertyBl,self.shaclNS.pattern,stringpattern))
            if p == self.RML.termType and o== self.RML.r2rmlNS.Literal:
                self.literalActions(propertyBl,graphHelp,graph)
                return True
            else:
                self.URIActions(propertyBl,graphHelp)
                return True
        #test for when it has a Reference
        elif p == self.RML.reference:
            if p == self.RML.termType and o== self.RML.IRI:
                self.URIActions(propertyBl,graphHelp)
                return True
            else:
                self.literalActions(propertyBl,graphHelp, graph)
                return True

    def literalActions(self,propertyBl,graphHelp, graph):
        graphHelp.add((propertyBl,self.shaclNS.nodeKind,self.shaclNS.Literal))
        #Check for rr:language
        for s,p,o in graph.triples((self.RML.oM,self.RML.pLan,None)):
            graphHelp.add((propertyBl,self.shaclNS.languageIn,o))
        #Check for rr:datatype
        for s,po in graph.triples((self.RML.oM,self.RML.datatype,None)):
            graphHelp.add((propertyBl,self.shaclNS.datatype,o))
    def URIActions(self,propertyBl,graphHelp):
        graphHelp.add((propertyBl,self.shaclNS.nodeKind,self.shaclNS.IRI))
    def createPattern(self,templateString):
        #we want to replace this {word} into a wildcard ='.' 
        parts = templateString.split('{')
        parts2 = []
        for part in parts:
            if '}' in part:
                parts2 = parts2 + part.split('}')
            else:
                parts2 = parts2 + [part]
        string = ''
        tel = 1
        for part in parts2:
            if tel%2 != 0: 
                string = string + part
            else:
                string = string + '.' #wildcard
            tel += 1
        resultaat = rdflib.Literal(string)
        return resultaat
    def finalizeShape(self):
        #adding the idividual propertygraphs to the total shape
        for g in self.propertygraphs:
            self.SHACL.graph = self.SHACL.graph + g
        #self.SHACL.printGraph(1)
    def writeShapeToFile(self):
        for prefix, ns in self.RML.graph.namespaces():
            self.SHACL.graph.bind(prefix,ns)            #@base is used for <> in the RML ttl graph
        self.SHACL.graph.bind('sh','http://www.w3.org/ns/shacl#',False)
        self.SHACL.graph.serialize(destination='output2.ttl', format='turtle')
    def main(self):
        self.RML.removeBlankNodesMultipleMaps()
        for graph in self.RML.graphs:
            self.createNodeShape(graph)
            self.findClass(graph)
            self.targetNode(graph)
            length = len(graph)-3
            #Because the dictionary inside graph has first 'TM', 'LM' and 'SM' as keys we do the length of the dictionary minus 3
            #this way we can use this newly calculated length for the indexes used for the possible multiple PredicateObjectsMaps (POM)
            for i in range(length):
                    self.subjectTargetOf(graph["POM"+str(i)])
                    self.fillinProperty(graph["POM"+str(i)])
        self.finalizeShape()
        self.writeShapeToFile()
        #self.SHACL.printGraph(1)
        print(len(self.SHACL.graph))



RtoS = RMLtoSHACL()
RtoS.main()