import requests
from pathlib import Path


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
    url = "https://api.github.com/repos/kg-construct/rml-test-cases/git/trees/master"

    def __init__(self):
        pass

    def getTestCasesFolder(self) -> str:
        r = requests.get(self.url)
        r.raise_for_status()  # test if there are any errors when trying to read the testcases

        for trunk in r.json()["tree"]:
            if trunk["path"] == "test-cases":
                return trunk["url"]

        return ""

    def downloadAllTestCases(self):
        root_folder = self.getTestCasesFolder()

        r = requests.get(root_folder)
        r.raise_for_status()
        r = r.json()
        test_folders = [x for x in r["tree"] if x["type"] == "tree"]

        for folder in test_folders:
            folder_name = folder["path"]
            r = requests.get(folder["url"])
            test_mapping_file_url = [x for x in r.json()["tree"] if x["path"] == "mapping.ttl"][0]["url"]

            r = requests.get(test_mapping_file_url)

            print(r)
            return

    def getFile(self, number, letter, typeFile, fileNeeded, save_mapping=True, mapping_dir="mapping/"):
        # This function makes it possible to get the RML input files with the matching RDF output file from GitHub
        test_case = "RMLTC%s%s%s" % (str(number).zfill(4), letter, typeFile)
        url = 'https://raw.githubusercontent.com/kg-construct/rml-test-cases/master/test-cases/' + \
              test_case + fileNeeded
        r = requests.get(url)
        r.raise_for_status()  # test if there are any errors when trying to read the testcases
        fileName = fileNeeded.replace('/', '')

        with open(fileName, 'w') as f:
            f.write(r.text)

        Path(mapping_dir).mkdir(parents=True, exist_ok=True)

        if fileNeeded == self.Mappingfile and save_mapping:
            with open(f"{mapping_dir}{test_case}_{fileName}", 'w') as f2:
                f2.write(r.text)

        return fileName

    def testMain(self):
        # self.getFile(1,'a',self.sparql,self.outputRdfFile)
        self.getFile(20, 'a', self.js, self.Mappingfile)

        # self.getFile(10,'a',self.js,self.outputRdfFile)


if __name__ == '__main__':
    FilesGitHub = FilesGitHub()
    FilesGitHub.testMain()
