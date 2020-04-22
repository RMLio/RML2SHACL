
import rdflib
from rdflib import RDF
from RML import *
from SHACL import *
import requests
class FilesGitHub:
    def __init__(self):
        self.CSV = '-CSV'
        self.XML = '-XML'
        self.mySql = '-MySQL'
        self.Postgre = '-PostgreSQL'
        self.js = '-JSON'
        self.sparql = '-SPARQL'
        self.sqlserver = '-SQLServer'
        self.Mappingfile = '/mapping.ttl'
        self.outputRdfFile = '/output.nq'
    def getFile(self, nummer,letter,typeFile, fileNeeded): 
        #This function makes it possible to get the RML input files with the matching RDF output file from GitHub 
        if nummer <10:
            url = 'https://raw.githubusercontent.com/RMLio/rml-test-cases/master/test-cases/RMLTC000' + str(nummer) +letter + typeFile + fileNeeded
        else: #one 0 less in the base of the URL
            url = 'https://raw.githubusercontent.com/RMLio/rml-test-cases/master/test-cases/RMLTC00' + str(nummer) +letter +  typeFile + fileNeeded
        r = requests.get(url)
        if str(r) == '<Response [404]>':
            print('File not found.')
            return None
        else:
            fileName = fileNeeded.replace('/','')
            f = open(fileName,'w')
            f.write(r.text)
            f.close()
            return fileName
class RMLtoSHACL:
    def __init__(self):
        self.RML = RML()
        self.readfileObject = FilesGitHub()
        #self.RML.removeBlankNodes()
        self.shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')
        self.rdfSyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')    
        self.SHACL = SHACL()
        self.sNodeShape = None
        self.propertygraphs = []
        
    def createNodeShape(self, graph):
        #start of SHACL shape
        for s,p,o in graph["TM"]:      #.triples((None,RDF.type,self.RML.tM)):
            subjectShape = rdflib.URIRef(s+'/shape') #we create a new IRI for the new shape based on the triple map IRI
            self.SHACL.graph.add((subjectShape,p,self.shaclNS.NodeShape))
        self.sNodeShape = subjectShape
    def inferclass(self):
        pass
    def subjectTargetOf(self,graph):
        for s,p,o in graph.triples((self.RML.sPOM,self.RML.pPred,None)):
            if o != rdflib.RDF.type:
                self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetSubjectsOf,o))
    def targetNode(self,graph):
        #if there's a constant in the subjectmzp we can add this as sh:targetNode for the shape
        for s,p,o in graph['SM'].triples((self.RML.sSM,self.RML.pCons,None)):
            self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetNode,o))

    def findClass(self,graph):
        for s,p,o in graph['SM'].triples((self.RML.sSM,self.RML.pclass,None)):
                self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetClass,o))
        self.inferclass()
    def findClassinPrediacteOM(self,graph):
        for s,p,o in graph.triples((self.RML.sPOM,self.RML.pPred,rdflib.RDF.type)):
            for s,p,o in graph.triples((self.RML.oM,self.RML.pCons,None)):
                self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetClass,o))
    def fillinProperty(self, graph):
        propertyBl = rdflib.BNode()
        graphHelp = rdflib.Graph()
        for s,p,o in graph.triples((self.RML.sPOM,None,None)):
            graphHelp.add((self.sNodeShape,self.shaclNS.property,propertyBl))
            if p==self.RML.pPred:
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
                andBlankNode = rdflib.BNode()
                newIRIand = rdflib.URIRef(self.shaclNS + 'and')
                self.SHACL.graph.add((self.sNodeShape,newIRIand,andBlankNode))
                blankNodefirst = rdflib.BNode()
                blankNoderest = rdflib.BNode()
                #to create a SHACL list we need first en rest elements from RDFS
                self.SHACL.graph.add((andBlankNode, self.rdfSyntax.first, blankNodefirst))
                self.SHACL.graph.add((andBlankNode, self.rdfSyntax.rest, blankNoderest))
                self.SHACL.graph.add((blankNoderest,self.rdfSyntax.rest,self.rdfSyntax.nil))
                blankNodefirstTwo = rdflib.BNode()
                self.SHACL.graph.add((blankNoderest,self.rdfSyntax.first,blankNodefirstTwo))
                self.SHACL.graph.add((blankNodefirstTwo,self.shaclNS.node,o+'/shape'))

                for graph in self.RML.graphs:
                    for s1,p1,o1 in graph['TM']:
                        if s1 == o:
                            for s2,p2,o2 in graph['SM']:
                                self.testIfIRIorLiteralSubject(p2,o2, self.SHACL.graph, blankNodefirst,graph['SM'])
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
        self.SHACL.graph.bind('rdfs','http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.SHACL.graph.serialize(destination='output2.ttl', format='turtle')
    def main(self):
        number = 8
        letter = 'b'
        inputfileType = self.readfileObject.CSV
        self.RML.createGraph(number,letter,inputfileType)
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
                    self.findClassinPrediacteOM(graph["POM"+str(i)])
                    self.fillinProperty(graph["POM"+str(i)])
        self.finalizeShape()
        self.writeShapeToFile()
        #self.SHACL.printGraph(1)
        print(len(self.SHACL.graph))
        filenameOutput = self.readfileObject.getFile(number,letter,inputfileType,self.readfileObject.outputRdfFile)
        graphOutput = rdflib.Graph()
        graphOutput.parse(filenameOutput,format="turtle")
        self.SHACL.Validation(self.SHACL.graph,graphOutput) 


RtoS = RMLtoSHACL()
RtoS.main()