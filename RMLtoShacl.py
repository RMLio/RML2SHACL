
import rdflib
from rdflib import RDF
from RML import *
from SHACL import *
class RMLtoSHACL:
    def __init__(self):
        self.RML = RML()
        self.RML.createGraph()
        self.RML.removeBlankNodes()
        self.rmlNS = rdflib.Namespace('http://semweb.mmlab.be/ns/rml#')
        self.r2rmlNS = rdflib.Namespace('http://www.w3.org/ns/r2rml#')
        self.shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')  #iets doen met bind?
        self.exNM = rdflib.Namespace("http://example.org/")
        self.SHACL = SHACL()
        self.template = self.r2rmlNS.template
        self.reference = self.rmlNS.reference
        self.termType = self.r2rmlNS.termType
        self.sNodeShape = None
    def createNodeShape(self):
        #start of SHACL shape
        for s,p,o in self.RML.graph.triples((None,RDF.type,self.r2rmlNS.TriplesMap)):
            self.SHACL.graph.add((s,p,self.shaclNS.NodeShape))
        self.sNodeShape = s
    def inferclass(self):
        pass
    def subjectTargetOf(self):
        sPOM  = self.r2rmlNS.predicateObjectMap #adding this to the RML class maybe better in stead of typing this mutliptle times as in (1) too
        pPred = self.r2rmlNS.predicate
        for s,p,o in self.RML.graph.triples((sPOM,pPred,None)):
            self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetSubjectsOf,o))  #can we have more than one targetSubjectsOf?

    def findClass(self):
        sSM = self.r2rmlNS.subjectMap
        pclass = self.r2rmlNS['class']
        for s,p,o in self.RML.graph.triples((sSM,pclass,None)):
                self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetClass,o))
    def fillinProperty(self):           #still have to add something when working with multiple predicateObjectMaps (maybe add little sub graphs for SHACL class? (array))
        sPOM  = self.r2rmlNS.predicateObjectMap                                         #(1)
        pPred = self.r2rmlNS.predicate
        for s,p,o in self.RML.graph.triples((sPOM,pPred,None)):
            self.SHACL.graph.add((self.shaclNS.property,self.shaclNS.path,o))
    def findObject(self):
        sOM  = self.r2rmlNS.objectMap
        for s,p,o in self.RML.graph.triples((sOM,None,None)):
            if p == self.template:
                stringpattern= self.createPattern(o)
                self.SHACL.graph.add((self.shaclNS.property,self.shaclNS.pattern,stringpattern))
                for s,p,o in self.RML.graph.triples((sOM,None,None)):
                    if p == self.termType and o== self.r2rmlNS.Literal:
                        self.literalActions(sOM)
                    else:
                        self.URIActions()
        
            elif p == self.reference:
                for s,p,o in self.RML.graph.triples((sOM,None,None)):
                    if p == self.termType and o== self.r2rmlNS.IRI:
                        self.URIActions()
                    else:
                        self.literalActions(sOM)
    def literalActions(self,sOM):
        self.SHACL.graph.add((self.shaclNS.property,self.shaclNS.nodeKind,self.shaclNS.Literal))
        pLan  = self.r2rmlNS.language
        for s,p,o in self.RML.graph.triples((sOM,pLan,None)):
            self.SHACL.graph.add((self.shaclNS.property,self.shaclNS.language,o))
    def URIActions(self):
        self.SHACL.graph.add((self.shaclNS.property,self.shaclNS.nodeKind,self.shaclNS.IRI))
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
        return string
    def writeShapeToFile(self):
        for prefix, ns in self.RML.graph.namespaces():
            self.SHACL.graph.bind(prefix,ns)            #@base is not possible to find immediatly
        self.SHACL.graph.bind('sh','http://www.w3.org/ns/shacl#',False)
        self.SHACL.graph.serialize(destination='output2.ttl', format='turtle')
    def main(self):
        self.createNodeShape()
        self.findClass()
        self.subjectTargetOf()
        self.fillinProperty()
        self.findObject()
        self.SHACL.printGraph(1)
        #self.RML.printGraph(1)
        self.writeShapeToFile()
        


RtoS = RMLtoSHACL()
RtoS.main()