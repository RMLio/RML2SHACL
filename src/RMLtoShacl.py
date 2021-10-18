import argparse
import csv
import logging
import os
from pathlib import Path
import string
import time
import timeit
from typing import Any, List

import rdflib
from rdflib import RDF
from requests.exceptions import HTTPError

from FilesGitHub import *
from RML import *
from SHACL import *


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

    def createNodeShape(self, triples_map:TriplesMap, shacl_graph:Graph):
        # start of SHACL shape

        subjectShape = rdflib.URIRef(triples_map.iri + "/shape") 
        shacl_graph.add((subjectShape, rdflib.RDF.type, self.shaclNS.NodeShape))
        self.transformSubjectMap(subjectShape, triples_map.sm, shacl_graph) 


        for pom in triples_map.poms: 
            self.transformPOM(subjectShape, pom)
            
            pass


    def transformIRI(self, node:Identifier, shacl_graph:Graph) -> None: 
        shacl_graph.add((node, self.shaclNS.nodeKind, self.shaclNS.IRI)) 


    def transformList(self, arr:List[Any],  node:Identifier, shacl_graph:Graph) -> None: 
        """
        Transform the given array objects into RDF compliant array list. 
        The transformation is done in the manner of a functional list. 
        """
        current_node = node 
        next_node = rdflib.BNode() 
        size = len(arr) 
        for i, obj in enumerate(arr): 

            shacl_graph.add(
                (current_node, self.rdfSyntax.first, rdflib.Literal(obj))) 

            if i != size-1: 
                shacl_graph.add( 
                    (current_node, self.rdfSyntax.rest, next_node))
            else: 
                shacl_graph.add(
                    (current_node, self.rdfSyntax.rest, self.rdfSyntax.nil))
            current_node = next_node 
            next_node = rdflib.BNode() 


    def transformLiteral(self,node:Identifier, termMap:TermMap, shacl_graph:Graph)-> None: 

        shacl_graph.add( 
            (node, self.shaclNS.NodeKind, self.shaclNS.Literal))

        # Transform rr:language 
        # it can be a list of languages
        language_iri = self.RML.LANGUAGE
        if language_iri in termMap.po_dict: 
            languages_arr = termMap.po_dict[language_iri] 
            
            for language in  languages_arr: 
                languageBlank = rdflib.BNode() 
                shacl_graph.add(
                    (node, self.shaclNS.languageIn, languageBlank))
                self.transformList(language.split('-'), languageBlank, shacl_graph) 
        
        # Transform rr:datatype
        datatype_iri = self.RML.DATATYPE
        if datatype_iri in termMap.po_dict: 
            datatype_term = termMap.po_dict[datatype_iri][0]
            shacl_graph.add((node, self.shaclNS.datatype, datatype_term))
        

    def transformSubjectMap(self, node:Identifier, subjectmap:SubjectMap, shacl_graph:Graph)-> None:
        """
        Transform the given SubjectMap into the corresponding SHACL shapes and 
        store them in the self.SHACL's rdflib graph. 
        """


        for predicate, obj_arr  in subjectmap.po_dict.items(): 
            # Start class and type translation
            if predicate == self.RML.CONSTANT: 
                for el in obj_arr: 
                    shacl_graph.add(
                        (node, self.shaclNS.targetNode, el )) 
            if predicate == self.RML.CLASS: 
                for el in obj_arr: 
                    shacl_graph.add(
                        (node, self.shaclNS.targetClass, el)) 
            # End class and type translation
            

        



        pass

    def transformPOM(self, node:Identifier, pom:PredicateObjectMap) -> None: 
        pass

    def serializeTemplate(self, templateString):
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

        logging.debug("*" * 100)
        logging.debug("RESULTS")
        logging.debug("="*100)
        logging.debug(self.SHACL.results_text)

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

        logging.debug(self.SHACL.results_text)
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
                        logging.debug("="*50)
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
    parser.add_argument("-rml_file", "-f", type=str,
                        help="RML mapping file to be converted into SHACL shapes.")
    parser.add_argument("-logLevel", "-l", type=str, default="INFO",
                        help="Logging level of this script")

    args = parser.parse_args()

    loglevel = args.logLevel
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)

    start = time.time()
    if args.rml_file is None:
        RtoS.main()
    else:
        RtoS.evaluate_file(args.rml_file)

    end = time.time()

    print(f"Elapsed time: {end -start} seconds")
