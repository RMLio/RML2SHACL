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

    def helpAddTriples(self, shacl_graph: Graph, sub: Identifier,
                       pred: Identifier, obj_arr: Optional[List[Identifier]]) -> None:
        """
        This method takes an array of object terms (obj_arr)  associated with 
        the given predicate (pred) and add them to the 
        subject node (sub) as triples.  
        """

        if obj_arr is None:
            return

        for el in obj_arr:
            shacl_graph.add(
                (sub, pred, el))

    def transformIRI(self, node: Identifier, shacl_graph: Graph) -> None:
        shacl_graph.add((node, self.shaclNS.nodeKind, self.shaclNS.IRI))

    def transformBlankNode(self, node: Identifier, shacl_graph: Graph) -> None:
        shacl_graph.add((node, self.shaclNS.nodeKind, self.shaclNS.BlankNode))

    def transformList(self, node: Identifier, arr: List[Any], shacl_graph: Graph) -> None:
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

            if i != size - 1:
                shacl_graph.add(
                    (current_node, self.rdfSyntax.rest, next_node))
            else:
                shacl_graph.add(
                    (current_node, self.rdfSyntax.rest, self.rdfSyntax.nil))
            current_node = next_node
            next_node = rdflib.BNode()

    def transformLiteral(self, node: Identifier, termMap: TermMap, shacl_graph: Graph) -> None:

        shacl_graph.add((node, self.shaclNS.nodeKind, self.shaclNS.Literal))

        # Transform rr:language 
        # it can be a list of languages
        language_iri = self.RML.LANGUAGE
        if language_iri in termMap.po_dict:
            languages_arr = termMap.po_dict[language_iri]

            for language in languages_arr:
                languageBlank = rdflib.BNode()
                shacl_graph.add(
                    (node, self.shaclNS.languageIn, languageBlank))
                self.transformList(languageBlank, language.split('-'), shacl_graph)

                # Transform rr:datatype
        datatype_iri = self.RML.DATATYPE
        if datatype_iri in termMap.po_dict:
            self.helpAddTriples(shacl_graph, node,
                                self.shaclNS.datatype, termMap.po_dict[datatype_iri])

    def serializeTemplate(self, templateString: Identifier) -> Identifier:
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
            # wildcard = '.' + '*'
            tel += 1
        resultaat = rdflib.Literal(string)
        return resultaat

    def createNodeShape(self, triples_map: TriplesMap, shacl_graph: Graph) -> Identifier:
        # start of SHACL shape

        subjectShape = rdflib.URIRef(triples_map.iri + "/shape")
        shacl_graph.add((subjectShape, rdflib.RDF.type, self.shaclNS.NodeShape))
        self.transformSubjectMap(subjectShape, triples_map.sm, shacl_graph)
        return subjectShape

    def transformSubjectMap(self, node: Identifier, subjectmap: SubjectMap, shacl_graph: Graph) -> None:
        """
        Transform the given SubjectMap into the corresponding SHACL shapes and 
        store them in the self.SHACL's rdflib graph. 
        """

        po_dict = subjectmap.po_dict

        # Start of class and targetNode shacl mapping
        self.helpAddTriples(shacl_graph, node,
                            self.shaclNS.targetNode,
                            po_dict.get(self.RML.CONSTANT, []))

        self.helpAddTriples(shacl_graph, node,
                            self.shaclNS.targetClass,
                            po_dict.get(self.RML.CLASS, []))

        self.helpAddTriples(shacl_graph, node,
                            self.shaclNS["class"],
                            po_dict.get(self.RML.CLASS, []))

        # End of class and targetNode shacl mapping

        # Shacl shl:pattern parsing 
        template_strings = [self.serializeTemplate(x)
                            for x in po_dict.get(self.RML.TEMPLATE, [])]
        self.helpAddTriples(shacl_graph, node,
                            self.shaclNS.pattern, template_strings)

        # Uri or Literal parsing
        self.transformIRIorLiteralorBlankNode(po_dict, node, subjectmap, shacl_graph)

    def transformIRIorLiteralorBlankNode(self, po_dict: Dict[URIRef, List[Any]],
                                         node: Identifier, termMap: TermMap,
                                         shacl_graph: Graph) -> None:
        # Uri or Literal parsing
        type_arr = po_dict.get(self.RML.TERMTYPE)
        if type_arr:
            term_type = type_arr[0]
            if term_type == self.RML.r2rmlNS.Literal:
                self.transformLiteral(node, termMap, shacl_graph)
            elif term_type == self.RML.r2rmlNS.IRI:
                self.transformIRI(node, shacl_graph)
            elif term_type == self.RML.r2rmlNS.BlankNode:
                self.transformBlankNode(node, shacl_graph)
            else:
                print(f"WARNING: {term_type} is not a valid term type for {self}, defaulting to IRI")
                self.transformIRI(node, shacl_graph)

        # default behaviour if no termType is defined 
        elif po_dict.get(self.RML.REFERENCE):
            self.transformLiteral(node, termMap, shacl_graph)
        else:
            self.transformIRI(node, shacl_graph)

    def transformPOM(self, node: Identifier, pom: PredicateObjectMap, shacl_graph: Graph) -> None:

        pm = pom.PM
        om = pom.OM

        # Find the subject's class in 
        # Check if it defines the class of the subject node (node) and 
        # return immediately since the pom is parsed
        pred_constant_objs = pm.po_dict.get(self.RML.CONSTANT)
        if pred_constant_objs and pred_constant_objs[0] == rdflib.RDF.type:
            om_constant_objs = om.po_dict.get(self.RML.CONSTANT)
            self.helpAddTriples(shacl_graph, node,
                                self.shaclNS.targetClass, om_constant_objs)
            return

            # Fill in the sh:property node of the given subject (@param node)
        sh_property = rdflib.BNode()
        shacl_graph.add(
            (node, self.shaclNS.property, sh_property))

        self.transformIRIorLiteralorBlankNode(om.po_dict, sh_property, om, shacl_graph)
        ptm = om.po_dict.get(self.RML.r2rmlNS.parentTriplesMap)
        if ptm:
            ptm = ptm[0] + "/shape"
            shacl_graph.add(
                (sh_property, self.shaclNS.node, ptm))

        self.helpAddTriples(shacl_graph, sh_property,
                            self.shaclNS.path, pm.po_dict.get(self.RML.CONSTANT))

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

        for _, triples_map in self.RML.tm_model_dict.items():
            subject_shape_node = self.createNodeShape(triples_map, self.SHACL.graph)

            for pom in triples_map.poms:
                self.transformPOM(subject_shape_node, pom, self.SHACL.graph)

        outputfileName = f"{rml_mapping_file}-output-shape.ttl"
        self.writeShapeToFile(outputfileName)

        validation_shape_graph = rdflib.Graph()
        validation_shape_graph.parse("shacl-shacl.ttl", format="turtle")

        self.SHACL.Validation(validation_shape_graph, self.SHACL.graph)

        logging.debug("*" * 100)
        logging.debug("RESULTS")
        logging.debug("=" * 100)
        logging.debug(self.SHACL.results_text)

        return None

    def TestGithubFiles(self, numberInput, letterInput, inputfile):
        number = numberInput
        letter = letterInput
        inputfileType = inputfile
        self.RML.parseGithubFile(number, letter, inputfileType)
        self.RML.removeBlankNodesMultipleMaps()

        for _, triples_map in self.RML.tm_model_dict.items():
            subject_shape_node = self.createNodeShape(triples_map, self.SHACL.graph)

            for pom in triples_map.poms:
                self.transformPOM(subject_shape_node, pom, self.SHACL.graph)

        filenNameShape = 'RMLTC%s%s-%s_outputShape.ttl' % (
            str(numberInput).zfill(4), letterInput, inputfile)
        shapeFileName = self.writeShapeToFile(filenNameShape)
        filenameOutput = self.readfileObject.getFile(
            number, letter, inputfileType, FilesGitHub.outputRdfFile)
        graphOutput = rdflib.Graph()
        graphOutput.parse(
            filenameOutput, format=rdflib.util.guess_format(filenameOutput))
        self.SHACL.Validation(self.SHACL.graph, graphOutput)

        logging.debug("*" * 100)
        logging.debug("RESULTS")
        logging.debug("=" * 100)
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
                        logging.debug("=" * 50)
                        filetypeColomnInput = filetype.replace('-', '')
                        RtoS = RMLtoSHACL()  # create RtoS object again for a fresh start
                        try:
                            outputShapeFile = RtoS.TestGithubFiles(
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

    print(f"Elapsed time: {end - start} seconds")
