import os
import rdflib
from rdflib import RDF
from RML import *
from SHACL import *
from FilesGitHub import *
import string
import csv
from pathlib import Path
from requests.exceptions import HTTPError
import argparse


class RMLtoSHACL:
    def __init__(self):
        self.RML = RML()
        self.readfileObject = FilesGitHub()
        self.shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')
        self.rdfSyntax = rdflib.Namespace(
            'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.SHACL = SHACL()
        self.sNodeShape = None
        self.propertygraphs = []

    def createNodeShape(self, graph):
        # start of SHACL shape
        subjectShape = None
        for s, p, o in graph["TM"]:
            subjectShape = rdflib.URIRef(s+'/shape')
            # we create a new IRI for the new shape based on the Triples Map IRI
            self.SHACL.graph.add((subjectShape, p, self.shaclNS.NodeShape))

        for s2, p2, o2 in graph["SM"]:
            self.testIfIRIorLiteralSubject(p2, o2, self.SHACL.graph,
                                           subjectShape, graph["SM"])

        self.sNodeShape = subjectShape

    def inferclass(self, graphPOM):
        for prefix, ns in self.RML.graph.namespaces():
            # loop over the Predicate Object Maps only looking at the rr:predicate statements
            for s1, p1, o1 in graphPOM.triples((self.RML.sPOM, self.RML.pPred, None)):
                if ns in o1:
                    graph = rdflib.Graph()
                    try:
                        # first parse the graphs from all the namespaces from the RML mapping and save those graphs in an array
                        graph.parse(ns, format=rdflib.util.guess_format(ns))
                        for s, p, o in graph:
                            # test if we have an rdfs:domain that belongs to the object of our rr:predicate statement
                            if p == rdflib.RDFS.domain and s == o1:
                                # add the domain aka class to the shape as sh:targetClass
                                self.SHACL.graph.add(
                                    (self.sNodeShape, self.shaclNS.targetClass, o))
                    except:
                        pass

    def subjectTargetOf(self, graph):
        for s, p, o in graph.triples((self.RML.sPOM, self.RML.pPred, None)):
            if o != rdflib.RDF.type:
                self.SHACL.graph.add(
                    (self.sNodeShape, self.shaclNS.targetSubjectsOf, o))

    def targetNode(self, graph):
        # if there's a constant in the subjectmap we can add this as sh:targetNode for the shape
        for s, p, o in graph['SM'].triples((self.RML.sSM, self.RML.pCons, None)):
            self.SHACL.graph.add((self.sNodeShape, self.shaclNS.targetNode, o))

    def findClass(self, graph):
        for s, p, o in graph['SM'].triples((self.RML.sSM, self.RML.pclass, None)):
            self.SHACL.graph.add(
                (self.sNodeShape, self.shaclNS.targetClass, o))

    def findClassinPrediacteOM(self, graphPOM):
        for s, p, o in graphPOM.triples((self.RML.sPOM, self.RML.pPred, rdflib.RDF.type)):
            for s1, p1, o1 in graphPOM.triples((self.RML.oM, self.RML.pCons, None)):
                self.SHACL.graph.add(
                    (self.sNodeShape, self.shaclNS.targetClass, o1))
        self.inferclass(graphPOM)

    def fillinProperty(self, graphPOM):
        rdfType = False
        propertyBl = rdflib.BNode()
        graphHelp = rdflib.Graph()
        print("#" * 100)
        print("Start of fillinProperty")

        for s, p, o in graphPOM.triples((self.RML.sPOM, None, None)):
            print("Inside fillinProperty")
            print(f"{s}, {p}, {o}")
            # skip predicate object maps with rdf:type since these are already parsed
            # in findClassinPredicateOM() and also skip r2rml:graph since it can become nested
            if o == rdflib.RDF.type or p == self.RML.r2rmlNS.graph:
                continue

            graphHelp.add((self.sNodeShape, self.shaclNS.property, propertyBl))
            if p == self.RML.pPred:
                print("Inside if branch of rr:predicate")
                graphHelp.add((propertyBl, self.shaclNS.path, o))
                self.findObject(propertyBl, graphHelp, graphPOM, rdfType)
                propertyBl = rdflib.BNode()
            else:
                print("else branch of rr:predicate")
                self.findObject(propertyBl, graphHelp, graphPOM, rdfType)
            print("----" * 20)

        self.propertygraphs.append(graphHelp)

    def findObject(self, propertyBl, graphHelp, graphPOM, rdfType):
        # we test if the object is an IRI or a Literal
        print("*"*100)
        print("Finding objects")
        for s, p, o in graphPOM.triples((self.RML.oM, None, None)):
            # Test for when it has a template
            print(f"{s}, {p}, {o}")
            result = self.testIfIRIorLiteral(
                p, o, graphHelp, propertyBl, graphPOM)
            print(result)
            if not result and p == self.RML.pCons and not rdfType:
                # we don't have a Literal nor an IRI
                # if rdfType is True then we have a predicateobject with rdf:type
                # and then we don't have to look at the constant values
                # because it's filled in findClassinPredicateOM()
                graphHelp.add((propertyBl, self.shaclNS.hasValue, o))
            elif p == self.RML.r2rmlNS.parentTriplesMap:
                # to create a SHACL list we need first en rest elements from RDFS
                target_shape = o + "/shape"

                self.SHACL.graph.add(
                    (propertyBl, self.shaclNS.node, target_shape))

        # plus '/shape' because we took the name for the Triples Map and added shape and we need to refer to the shape now
                for graph in self.RML.graphs:
                    for s1, _, _ in graph['TM']:
                        if s1 == o:
                            for s2, p2, o2 in graph['SM']:
                                self.testIfIRIorLiteralSubject(
                                    p2, o2, self.SHACL.graph, target_shape, graph['SM'])
    
    
    def testIfIRIorLiteralSubject(self, p, o, graphHelp, propertyBl, graphSM):
        # Test for when it has a template
        Found = False
        if p == self.RML.template:
            stringpattern = self.createPattern(o)
            graphHelp.add((propertyBl, self.shaclNS.pattern, stringpattern))
            for s1, p1, o1 in graphSM:
                if p1 == self.RML.termType and o1 == self.RML.r2rmlNS.Literal:
                    self.literalActions(propertyBl, graphHelp, graphSM)
                    Found = True
                    break
            if Found == False:
                self.URIActions(propertyBl, graphHelp)
        # test for when it has a Reference
        elif p == self.RML.reference:
            for s1, p1, o1 in graphSM:
                if p1 == self.RML.termType and o1 == self.RML.IRI:
                    self.URIActions(propertyBl, graphHelp)
                    Found = True
                    break
            if Found == False:
                self.literalActions(propertyBl, graphHelp, graphSM)

    def testIfIRIorLiteral(self, p, o, graphHelp, propertyBl, graphPOM):
        # Test for when it has a template
        Found = False
        if p == self.RML.template:
            stringpattern = self.createPattern(o)
            graphHelp.add((propertyBl, self.shaclNS.pattern, stringpattern))
            for s1, p1, o1 in graphPOM:
                if s1 == self.RML.oM and p1 == self.RML.termType and o1 == self.RML.r2rmlNS.Literal:
                    self.literalActions(propertyBl, graphHelp, graphPOM)
                    Found = True
                    break
            if Found == False:
                self.URIActions(propertyBl, graphHelp)
                Found = True
            return Found
        # we return with the value True when we found an IRI of Literal False when we didn't
        # test for when it has a Reference
        elif p == self.RML.reference:
            for s1, p1, o1 in graphPOM:
                if s1 == self.RML.oM and p1 == self.RML.termType and o1 == self.RML.IRI:
                    self.URIActions(propertyBl, graphHelp)
                    Found = True
                    break
            if Found == False:
                self.literalActions(propertyBl, graphHelp, graphPOM)
                Found = True
            return Found

    def literalActions(self, propertyBl, graphHelp, graphPOM):
        graphHelp.add(
            (propertyBl, self.shaclNS.nodeKind, self.shaclNS.Literal))
        # Check for rr:language
        for s, p, o in graphPOM.triples((self.RML.oM, self.RML.pLan, None)):
            parts = o.split('-')
            blankNodelanguageIn = rdflib.BNode()
            graphHelp.add(
                (propertyBl, self.shaclNS.languageIn, blankNodelanguageIn))
            blankNoderest = rdflib.BNode()
            # to create a SHACL list we need first en rest elements from RDFS
            for i in range(0, len(parts)):
                # when we are at the end of a SHACL list we need rdfs:nil
                if i == len(parts)-1 and i != 0:
                    self.SHACL.graph.add(
                        (blankNoderest, self.rdfSyntax.first, rdflib.Literal(parts[i])))
                    self.SHACL.graph.add(
                        (blankNoderest, self.rdfSyntax.rest, self.rdfSyntax.nil))
                elif i == 0:  # the first language tag value needs to be added to the blank node of sh:languageIn
                    self.SHACL.graph.add(
                        (blankNodelanguageIn, self.rdfSyntax.first, rdflib.Literal(parts[i])))
                    if len(parts)-1 == 0:  # we only have one value
                        self.SHACL.graph.add(
                            (blankNodelanguageIn, self.rdfSyntax.rest, self.rdfSyntax.nil))
                    else:
                        self.SHACL.graph.add(
                            (blankNodelanguageIn, self.rdfSyntax.rest, blankNoderest))
                else:
                    blanknoderestTwo = rdflib.BNode()
                    self.SHACL.graph.add(
                        (blankNoderest, self.rdfSyntax.first, rdflib.Literal(parts[i])))
                    self.SHACL.graph.add(
                        (blankNoderest, self.rdfSyntax.rest, blanknoderestTwo))
                    blankNoderest = blanknoderestTwo
        # Check for rr:datatype
        for s, p, o in graphPOM.triples((self.RML.oM, self.RML.datatype, None)):
            graphHelp.add((propertyBl, self.shaclNS.datatype, o))

    def URIActions(self, propertyBl, graphHelp):
        graphHelp.add((propertyBl, self.shaclNS.nodeKind, self.shaclNS.IRI))

    def createPattern(self, templateString):
        # we want to replace this {word} into a wildcard ='.'
        # and '*' means zero or unlimited amount of characters
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
            if tel % 2 != 0:
                string = string + part
            else:
                string = string + '.*'
            #wildcard = '.' + '*'
            tel += 1
        resultaat = rdflib.Literal(string)
        return resultaat

    def finalizeShape(self):
        # adding the idividual propertygraphs to the total shape
        for g in self.propertygraphs:
            self.SHACL.graph = self.SHACL.graph + g
        self.propertygraphs.clear()

    def writeShapeToFile(self, file_name, shape_dir="shapes/"):
        for prefix, ns in self.RML.graph.namespaces():
            self.SHACL.graph.bind(prefix, ns)
            # @base is used for <> in the RML ttl graph
        self.SHACL.graph.bind('sh', 'http://www.w3.org/ns/shacl#', False)
        self.SHACL.graph.bind(
            'rdfs', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')

        parent_folder = os.path.dirname(file_name)

        Path(f"%s%s" % (shape_dir, parent_folder)).mkdir(
            parents=True, exist_ok=True)

        filenNameShape = "%s%s" % (shape_dir, file_name)

        self.SHACL.graph.serialize(destination=filenNameShape, format='turtle')

        return filenNameShape

    def evaluate_file(self, rml_mapping_file):
        self.RML.parseFile(rml_mapping_file)
        self.RML.removeBlankNodesMultipleMaps()
        for graph in self.RML.graphs:
            self.createNodeShape(graph)
            self.findClass(graph)
            self.targetNode(graph)
            length = len(graph)-3
# Because the dictionary inside graph has first 'TM', 'LM' and 'SM'
# as keys we do the length of the dictionary minus 3
# #we can use this newly calculated length for the indexes
# used for the possible multiple PredicateObjectsMaps (POM)
            for i in range(length):
                self.subjectTargetOf(graph["POM"+str(i)])
                self.findClassinPrediacteOM(graph["POM"+str(i)])
                self.fillinProperty(graph["POM"+str(i)])
        self.finalizeShape()

        outputfileName = f"{rml_mapping_file}-output-shape.ttl"
        self.writeShapeToFile(outputfileName)

        validation_shape_graph = rdflib.Graph()
        validation_shape_graph.parse("shacl-shacl.ttl", format="turtle")

        self.SHACL.Validation(validation_shape_graph, self.SHACL.graph)

        print("*" * 100)
        print("RESULTS")
        print("="*100)
        print(self.SHACL.results_text)

        return None

    def MakeTotalShape(self, numberInput, letterInput, inputfile):
        number = numberInput
        letter = letterInput
        inputfileType = inputfile
        self.RML.parseGithubFile(number, letter, inputfileType)
        self.RML.removeBlankNodesMultipleMaps()

        for graph in self.RML.graphs:
            self.createNodeShape(graph)
            self.findClass(graph)
            self.targetNode(graph)
            length = len(graph)-3
# Because the dictionary inside graph has first 'TM', 'LM' and 'SM'
# as keys we do the length of the dictionary minus 3
# #we can use this newly calculated length for the indexes
# used for the possible multiple PredicateObjectsMaps (POM)
            for i in range(length):
                self.subjectTargetOf(graph["POM"+str(i)])
                self.findClassinPrediacteOM(graph["POM"+str(i)])
                self.fillinProperty(graph["POM"+str(i)])
        self.finalizeShape()
        filenNameShape = 'RMLTC%s%s-%s_outputShape.ttl' % (
            str(numberInput).zfill(4), letterInput, inputFile)
        shapeFileName = self.writeShapeToFile(filenNameShape)
        filenameOutput = self.readfileObject.getFile(
            number, letter, inputfileType, FilesGitHub.outputRdfFile)
        graphOutput = rdflib.Graph()
        graphOutput.parse(
            filenameOutput, format=rdflib.util.guess_format(filenameOutput))
        self.SHACL.Validation(self.SHACL.graph, graphOutput)

        print(self.SHACL.results_text)
        return shapeFileName

    def main(self):

        skip_case_dict = dict()
        with open('error_expected.csv', 'r') as file:
            csv_dict = csv.DictReader(file)
            is_first_line = True
            for row in csv_dict:
                if is_first_line:
                    is_first_line = False
                    continue

                if row["number"] in skip_case_dict:
                    skip_case_dict[row["number"]].add(row["letter"])
                else:
                    skip_case_dict[row["number"]] = {row["letter"]}

        validation_shape_graph = rdflib.Graph()
        validation_shape_graph.parse("shacl-shacl.ttl", format="turtle")

        with open('ResultsFinal3.csv', 'w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['number', 'letter', 'file type',
                            'conforms?', 'validation result'])
            for i in range(1, 21):
                # go over all the possible numbers for the file names
                skip_case_dict_key = str(i)
                for letter in string.ascii_lowercase:
                    if skip_case_dict_key in skip_case_dict:
                        if letter in skip_case_dict[skip_case_dict_key]:
                            print(
                                f"Skipped test case RMLTC{str(i).zfill(4)}{letter}")
                            continue
                # go over all the possible letters for the file names
                    for filetype in FilesGitHub.FileTypes:
                        print("="*50)
                        filetypeColomnInput = filetype.replace('-', '')
                        RtoS = RMLtoSHACL()  # create RtoS object again for a fresh start
                        try:
                            outputShapeFile = RtoS.MakeTotalShape(
                                i, letter, filetype)
                            generated_shape_graph = rdflib.Graph()
                            generated_shape_graph.parse(
                                outputShapeFile, format=rdflib.util.guess_format(outputShapeFile))
                            RtoS.SHACL.Validation(
                                validation_shape_graph, generated_shape_graph)
                            print(RtoS.SHACL.__dict__)
                            if RtoS.SHACL.conforms:

                                writer.writerow(
                                    [i, letter, filetypeColomnInput, RtoS.SHACL.conforms, ''])
                            else:
                                writer.writerow(
                                    [i, letter, filetypeColomnInput, RtoS.SHACL.conforms, RtoS.SHACL.results_text])
                            print("Finished processing file: RMLTC%s%s%s" %
                                  (str(i).zfill(4), letter, filetype))
                        except SyntaxError as error:
                            # something wrong with the files on GitHub
                            print(error)
                            writer.writerow(
                                [i, letter, filetypeColomnInput, error])
                            pass
                        except HTTPError as errorHttp:
                            # files do not exist
                            print(errorHttp)
                            pass
                        except Exception as e:
                            # something is wrong with the files on GitHub
                            
                            print(e)
                            writer.writerow(
                                [i, letter, filetypeColomnInput, e])
                            pass
                        del RtoS
                    if letter == 'j':
                        break


if __name__ == "__main__":
    RtoS = RMLtoSHACL()
    parser = argparse.ArgumentParser()
    parser.add_argument("--rml_file", type=str,
                        help="RML mapping file to be converted into SHACL shapes.")
    args = parser.parse_args()
    if args.rml_file is None:
        RtoS.main()
    else:
        RtoS.evaluate_file(args.rml_file)
