
import rdflib
from rdflib import RDF
from RML import *
from SHACL import *
from FilesGitHub import *
import string
import csv
from requests.exceptions import HTTPError

class RMLtoSHACL:
    def __init__(self):
        self.RML = RML()
        self.readfileObject = FilesGitHub()
        self.shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')
        self.rdfSyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')    
        self.SHACL = SHACL()
        self.sNodeShape = None
        self.propertygraphs = []
        
    def createNodeShape(self, graph):
        #start of SHACL shape
        for s,p,o in graph["TM"]:
            subjectShape = rdflib.URIRef(s+'/shape') 
            #we create a new IRI for the new shape based on the Triples Map IRI
            self.SHACL.graph.add((subjectShape,p,self.shaclNS.NodeShape))
        self.sNodeShape = subjectShape
    def inferclass(self,graphPOM):
        for prefix, ns in self.RML.graph.namespaces():
        #loop over the Predicate Object Maps only looking at the rr:predicate statements
            for s1,p1,o1 in graphPOM.triples((self.RML.sPOM,self.RML.pPred,None)):
                if ns in o1:
                    graph = rdflib.Graph()
                    try:
#first parse the graphs from all the namespaces from the RML mapping and save those graphs in an array
                        graph.parse(ns,format=rdflib.util.guess_format(ns))
                        for s,p,o in graph:
#test if we have an rdfs:domain that belongs to the object of our rr:predicate statement
                            if p == rdflib.RDFS.domain and s==o1:
#add the domain aka class to the shape as sh:targetClass
                                self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetClass,o))
                    except:
                        pass
    def subjectTargetOf(self,graph):
        for s,p,o in graph.triples((self.RML.sPOM,self.RML.pPred,None)):
            if o != rdflib.RDF.type:
                self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetSubjectsOf,o))
    def targetNode(self,graph):
#if there's a constant in the subjectmap we can add this as sh:targetNode for the shape
        for s,p,o in graph['SM'].triples((self.RML.sSM,self.RML.pCons,None)):
            self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetNode,o))

    def findClass(self,graph):
        for s,p,o in graph['SM'].triples((self.RML.sSM,self.RML.pclass,None)):
                self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetClass,o))
        
    def findClassinPrediacteOM(self,graphPOM):
        for s,p,o in graphPOM.triples((self.RML.sPOM,self.RML.pPred,rdflib.RDF.type)):
            for s1,p1,o1 in graphPOM.triples((self.RML.oM,self.RML.pCons,None)):
                self.SHACL.graph.add((self.sNodeShape,self.shaclNS.targetClass,o1))
        self.inferclass(graphPOM)
    def fillinProperty(self, graphPOM):
        rdfType = False
        propertyBl = rdflib.BNode()
        graphHelp = rdflib.Graph()
        for s,p,o in graphPOM.triples((self.RML.sPOM,None,None)):
            if o != rdflib.RDF.type: #We skip the predicate object maps that have rdf:type because those are added in findClassinPredicateOM()
                graphHelp.add((self.sNodeShape,self.shaclNS.property,propertyBl))
                if p==self.RML.pPred:
                    graphHelp.add((propertyBl,self.shaclNS.path,o))
            else:
                rdfType = True #important to give this information to the findObject() function
            self.findObject(propertyBl,graphHelp,graphPOM,rdfType)
            self.propertygraphs.append(graphHelp)

            
    def findObject(self,propertyBl,graphHelp, graphPOM,rdfType):
        #we test if the object is an IRI or a Literal
        for s,p,o in graphPOM.triples((self.RML.oM,None,None)):
            #Test for when it has a template
            result = self.testIfIRIorLiteral(p,o, graphHelp,propertyBl,graphPOM)
            if not result and p == self.RML.pCons and not rdfType:
            #we don't have a Literal nor an IRI
            #if rdfType is True then we have a predicateobject with rdf:type 
            #and then we don't have to look at the constant values 
            #because it's filled in findClassinPredicateOM()
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
        #plus '/shape' because we took the name for the Triples Map and added shape and we need to refer to the shape now

                for graph in self.RML.graphs:
                    for s1,p1,o1 in graph['TM']:
                        if s1 == o:
                            for s2,p2,o2 in graph['SM']:
                                self.testIfIRIorLiteralSubject(p2,o2, self.SHACL.graph, blankNodefirst,graph['SM'])
                #we also have to add the sh:path inside the sh:and
                for s,p,o in graphPOM:
                    if p==self.RML.pPred:
                        graphHelp.add((blankNodefirst,self.shaclNS.path,o))
    def testIfIRIorLiteralSubject(self,p,o, graphHelp, propertyBl,graphSM):
        #Test for when it has a template
        Found = False
        if p == self.RML.template:
            stringpattern= self.createPattern(o)
            graphHelp.add((propertyBl,self.shaclNS.pattern,stringpattern))
            for s1, p1, o1 in graphSM:
                if p1 == self.RML.termType and o1== self.RML.r2rmlNS.Literal:
                    self.literalActions(propertyBl,graphHelp,graphSM)
                    Found = True
                    break
            if Found == False:
                self.URIActions(propertyBl,graphHelp)
        #test for when it has a Reference
        elif p == self.RML.reference:
            for s1, p1, o1 in graphSM:
                if p1 == self.RML.termType and o1== self.RML.IRI:
                    self.URIActions(propertyBl,graphHelp)
                    Found = True
                    break
            if Found == False:
                self.literalActions(propertyBl,graphHelp, graphSM)
    def testIfIRIorLiteral(self,p,o, graphHelp, propertyBl,graphPOM):
        #Test for when it has a template
        Found = False
        if p == self.RML.template:
            stringpattern= self.createPattern(o)
            graphHelp.add((propertyBl,self.shaclNS.pattern,stringpattern))
            for s1,p1,o1 in graphPOM:
                if s1 == self.RML.oM and p1 == self.RML.termType and o1== self.RML.r2rmlNS.Literal:
                    self.literalActions(propertyBl,graphHelp,graphPOM)
                    Found = True
                    break
            if Found == False:
                    self.URIActions(propertyBl,graphHelp)
                    Found = True
            return Found 
        #we return with the value True when we found an IRI of Literal False when we didn't
        #test for when it has a Reference
        elif p == self.RML.reference:
            for s1,p1,o1 in graphPOM:
                if s1 == self.RML.oM and p1 == self.RML.termType and o1== self.RML.IRI:
                    self.URIActions(propertyBl,graphHelp)
                    Found = True
                    break;
            if Found == False:
                self.literalActions(propertyBl,graphHelp, graphPOM)
                Found = True
            return Found

    def literalActions(self,propertyBl,graphHelp, graphPOM):
        graphHelp.add((propertyBl,self.shaclNS.nodeKind,self.shaclNS.Literal))
        #Check for rr:language
        for s,p,o in graphPOM.triples((self.RML.oM,self.RML.pLan,None)):
            parts = o.split('-')
            blankNodelanguageIn = rdflib.BNode()
            graphHelp.add((propertyBl,self.shaclNS.languageIn,blankNodelanguageIn))
            blankNoderest = rdflib.BNode()
            #to create a SHACL list we need first en rest elements from RDFS
            for i in range (0,len(parts)):
                if i == len(parts)-1 and i!=0: #when we are at the end of a SHACL list we need rdfs:nil
                    self.SHACL.graph.add((blankNoderest, self.rdfSyntax.first, rdflib.Literal(parts[i])))
                    self.SHACL.graph.add((blankNoderest,self.rdfSyntax.rest,self.rdfSyntax.nil))
                elif i==0: #the first language tag value needs to be added to the blank node of sh:languageIn
                    self.SHACL.graph.add((blankNodelanguageIn, self.rdfSyntax.first, rdflib.Literal(parts[i])))
                    if len(parts)-1 == 0: #we only have one value
                        self.SHACL.graph.add((blankNodelanguageIn, self.rdfSyntax.rest, self.rdfSyntax.nil))
                    else:
                        self.SHACL.graph.add((blankNodelanguageIn, self.rdfSyntax.rest, blankNoderest))
                else:
                    blanknoderestTwo = rdflib.BNode()
                    self.SHACL.graph.add((blankNoderest, self.rdfSyntax.first, rdflib.Literal(parts[i])))
                    self.SHACL.graph.add((blankNoderest, self.rdfSyntax.rest, blanknoderestTwo))
                    blankNoderest = blanknoderestTwo        
        #Check for rr:datatype
        for s,p,o in graphPOM.triples((self.RML.oM,self.RML.datatype,None)):
            graphHelp.add((propertyBl,self.shaclNS.datatype,o))
    def URIActions(self,propertyBl,graphHelp):
        graphHelp.add((propertyBl,self.shaclNS.nodeKind,self.shaclNS.IRI))
    def createPattern(self,templateString):
        #we want to replace this {word} into a wildcard ='.' 
        #and '*' means zero or unlimited amount of characters 
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
                string = string + '.*' 
            #wildcard = '.' + '*'
            tel += 1
        resultaat = rdflib.Literal(string)
        return resultaat
    def finalizeShape(self):
        #adding the idividual propertygraphs to the total shape
        for g in self.propertygraphs:
            self.SHACL.graph = self.SHACL.graph + g
        self.propertygraphs.clear()
    def writeShapeToFile(self, numberInput, letterInput, inputFile):
        for prefix, ns in self.RML.graph.namespaces():    
            self.SHACL.graph.bind(prefix,ns)
             #@base is used for <> in the RML ttl graph
        self.SHACL.graph.bind('sh','http://www.w3.org/ns/shacl#',False)
        self.SHACL.graph.bind('rdfs','http://www.w3.org/1999/02/22-rdf-syntax-ns#')

        if numberInput >= 10: 
            start = "RMLTC00"
        else: 
            start = "RMLTC000"

        filenNameShape = '%s%s%s-%s_outputShape.ttl' % (start, numberInput, letterInput, inputFile) 

        self.SHACL.graph.serialize(destination=filenNameShape, format='turtle')
    def MakeTotalShape(self,numberInput,letterInput, inputfile):
        number = numberInput
        letter = letterInput
        inputfileType = inputfile 
        self.RML.createGraph(number,letter,inputfileType)
        self.RML.removeBlankNodesMultipleMaps()
        for graph in self.RML.graphs:
            self.createNodeShape(graph)
            self.findClass(graph)
            self.targetNode(graph)
            length = len(graph)-3
#Because the dictionary inside graph has first 'TM', 'LM' and 'SM' 
# as keys we do the length of the dictionary minus 3
# #we can use this newly calculated length for the indexes
# used for the possible multiple PredicateObjectsMaps (POM)
            for i in range(length):
                    self.subjectTargetOf(graph["POM"+str(i)])
                    self.findClassinPrediacteOM(graph["POM"+str(i)])
                    self.fillinProperty(graph["POM"+str(i)])
        self.finalizeShape()
        self.writeShapeToFile(number, letter, inputfileType)
        filenameOutput = self.readfileObject.getFile(number,letter,inputfileType,FilesGitHub.outputRdfFile)
        graphOutput = rdflib.Graph()
        graphOutput.parse(filenameOutput,format=rdflib.util.guess_format(filenameOutput))
        self.SHACL.Validation(self.SHACL.graph,graphOutput) 
        return filenameOutput

    def main(self):
        with open('ResultsFinal3.csv','w', newline= '') as file:
            writer = csv.writer(file, delimiter = ';')
            writer.writerow(['number', 'letter','file type', 'conforms?', 'validation result'])
            for i in range(1,21):
            #go over all the possible numbers for the file names
                for letter in string.ascii_lowercase: 
                #go over all the possible letters for the file names
                    for filetype in FilesGitHub.FileTypes:
                        filetypeColomnInput = filetype.replace('-','')
                        RtoS = RMLtoSHACL() #create RtoS object again for a fresh start
                        try:
                            output = RtoS.MakeTotalShape(i,letter,filetype)
                            if RtoS.SHACL.conforms:
                                writer.writerow([i, letter,filetypeColomnInput,RtoS.SHACL.conforms, ''])
                            else:
                                writer.writerow([i, letter,filetypeColomnInput,RtoS.SHACL.conforms, RtoS.SHACL.results_text]) 
                            print("Finished processing file: %s" % (output))
                        except SyntaxError as error:        
                            #something wrong with the files on GitHub
                            print(error)
                            writer.writerow([i, letter,filetypeColomnInput ,error])
                            pass
                        except HTTPError as errorHttp: 
                            #files do not exist
                            print(errorHttp)
                            pass
                        except Exception as e: 
                            #something is wrong with the files on GitHub
                            print(e)
                            writer.writerow([i, letter,filetypeColomnInput ,e])
                            pass
                        del RtoS
                    if letter == 'j':
                        break;

if __name__ == "__main__":
    RtoS = RMLtoSHACL()
    RtoS.main()
