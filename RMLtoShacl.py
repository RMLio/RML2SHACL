
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
            '''elif p == self.RML.obj:
                graphHelp.add((propertyBl,self.shaclNS.hasValue, o))'''
            '''elif p==self.RML.pPredMap:   #we have a rr:constant, does not work
                for s,p,o in graph.triples((self.RML.pPredMap,self.RML.pCons,None)):
                    print("object constant is" + o)
                    graphHelp.add((propertyBl,self.shaclNS.path,o))'''
            self.findObject(propertyBl,graphHelp,graph)
            self.propertygraphs.append(graphHelp)

            
    def findObject(self,propertyBl,graphHelp, graph):
        for s,p,o in graph.triples((self.RML.oM,None,None)):
            if p == self.RML.template:
                stringpattern= self.createPattern(o)
                graphHelp.add((propertyBl,self.shaclNS.pattern,stringpattern))
                if p == self.RML.termType and o== self.RML.r2rmlNS.Literal:
                    self.literalActions(self.RML.oM,propertyBl,graphHelp,graph)
                else:
                    self.URIActions(propertyBl,graphHelp)
            elif p == self.RML.reference:
                if p == self.RML.termType and o== self.RML.IRI:
                    self.URIActions(propertyBl,graphHelp)
                else:
                    self.literalActions(self.RML.oM,propertyBl,graphHelp, graph)
            elif p == self.RML.pCons:
                graphHelp.add((propertyBl,self.shaclNS.hasValue, o))

    def literalActions(self,sOM,propertyBl,graphHelp, graph):
        graphHelp.add((propertyBl,self.shaclNS.nodeKind,self.shaclNS.Literal))
        for s,p,o in graph.triples((sOM,self.RML.pLan,None)):
            graphHelp.add((propertyBl,self.shaclNS.languageIn,o))
    def URIActions(self,propertyBl,graphHelp):
        graphHelp.add((propertyBl,self.shaclNS.nodeKind,self.shaclNS.IRI))
    def createPattern(self,templateString):
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
    def writeShapeToFile(self):
        for g in self.propertygraphs:
            self.SHACL.graph = self.SHACL.graph + g
        #self.SHACL.printGraph(1)
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
            lengte = len(graph)-3
            for i in range(lengte):
                    self.subjectTargetOf(graph["POM"+str(i)])
                    self.fillinProperty(graph["POM"+str(i)])
        #for g in self.propertygraphs: #is inside of writeShapeToFile maybe place somewhere else
           # self.SHACL.graph = self.SHACL.graph + g
            ##self.RML.printGraph(1)
        self.writeShapeToFile()
        #self.SHACL.printGraph(1)
        print(len(self.SHACL.graph))



RtoS = RMLtoSHACL()
RtoS.main()