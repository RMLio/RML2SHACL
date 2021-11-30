import sys 
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import argparse
import csv
import logging
import string
import time
import timeit

from requests.exceptions import HTTPError
from src.FilesGitHub import FilesGitHub 
from src.RML import *
from src.RMLtoShacl import RMLtoSHACL
from src.SHACL import *

def TestGithubFiles(RtoS: RMLtoSHACL, numberInput, letterInput, inputfile):
    number = numberInput
    letter = letterInput
    inputfileType = inputfile
    RtoS.RML.parseGithubFile(number, letter, inputfileType)
    RtoS.RML.removeBlankNodesMultipleMaps()

    for _, triples_map in RtoS.RML.tm_model_dict.items():
        subject_shape_node = RtoS.createNodeShape(triples_map, RtoS.SHACL.graph)

        for pom in triples_map.poms:
            RtoS.transformPOM(subject_shape_node, pom, RtoS.SHACL.graph)

    filenNameShape = 'RMLTC%s%s-%s_outputShape.ttl' % (
        str(numberInput).zfill(4), letterInput, inputfile)
    shapeFileName = RtoS.writeShapeToFile(filenNameShape)
    filenameOutput = RtoS.readfileObject.getFile(
        number, letter, inputfileType, FilesGitHub.outputRdfFile)
    graphOutput = rdflib.Graph()
    graphOutput.parse(
        filenameOutput, format=rdflib.util.guess_format(filenameOutput))
    RtoS.SHACL.Validation(RtoS.SHACL.graph, graphOutput)

    logging.debug("*" * 100)
    logging.debug("RESULTS")
    logging.debug("=" * 100)
    logging.debug(RtoS.SHACL.results_text)
    return shapeFileName

def main(RtoS):
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
                        outputShapeFile = TestGithubFiles(RtoS,
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
        main(RtoS)
    else:
        RtoS.evaluate_file(args.rml_file)

    end = time.time()

    print(f"Elapsed time: {end - start} seconds")
