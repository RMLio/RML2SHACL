import requests


class FilesGitHub:
    CSV = '-CSV'
    XML = '-XML'
    mySql = '-MySQL'
    Postgre = '-PostgreSQL'
    js = '-JSON'
    sparql = '-SPARQL'
    sqlserver = '-SQLServer'
    FileTypes = [CSV, XML, mySql, Postgre, js, sparql, sqlserver]
    Mappingfile = '/mapping.ttl'
    outputRdfFile = '/output.nq'

    def __init__(self):
        pass

    def getFile(self, number, letter, typeFile, fileNeeded):
        # This function makes it possible to get the RML input files with the matching RDF output file from GitHub
        test_case = "RMLTC%s%s%s" % (str(number).zfill(4), letter, typeFile)
        url = 'https://raw.githubusercontent.com/kg-construct/rml-test-cases/master/test-cases/' + \
            test_case + fileNeeded
        r = requests.get(url)
        r.raise_for_status()  # test if there are any errors when trying to read the testcases
        fileName = fileNeeded.replace('/', '')

        with open(fileName, 'w') as f:
            f.write(r.text)
        with open(f"{test_case}_{fileName}", 'w') as f2:
            f2.write(r.text)

        return fileName

    def testMain(self):
        # self.getFile(1,'a',self.sparql,self.outputRdfFile)
        self.getFile(20, 'a', self.js, self.Mappingfile)


        # self.getFile(10,'a',self.js,self.outputRdfFile)
if __name__ == '__main__':
    FilesGitHub = FilesGitHub()
    FilesGitHub.testMain()
