import requests
class FilesGitHub:
    CSV = '-CSV'
    XML = '-XML'
    mySql = '-MySQL'
    Postgre = '-PostgreSQL'
    js = '-JSON'
    sparql = '-SPARQL'
    sqlserver = '-SQLServer'
    FileTypes = [CSV, XML,mySql, Postgre,js,sparql,sqlserver]
    Mappingfile = '/mapping.ttl'
    outputRdfFile = '/output.nq'
    def __init__(self):
      pass
    def getFile(self, number,letter,typeFile, fileNeeded): 
        #This function makes it possible to get the RML input files with the matching RDF output file from GitHub 
        if number <10:
            url = 'https://raw.githubusercontent.com/RMLio/rml-test-cases/master/test-cases/RMLTC000' + str(number) +letter + typeFile + fileNeeded
        else: #one 0 less in the base of the URL
            url = 'https://raw.githubusercontent.com/RMLio/rml-test-cases/master/test-cases/RMLTC00' + str(number) +letter +  typeFile + fileNeeded
        r = requests.get(url)
        r.raise_for_status() #test if there are any errors when trying to read the testcases
        fileName = fileNeeded.replace('/','')
        f = open(fileName,'w')
        f.write(r.text)
        f.close()
        return fileName

    def testMain(self):
        #self.getFile(0,'',self.sparql,self.Mappingfile)
        #self.getFile(1,'a',self.sparql,self.outputRdfFile)
        self.getFile(1,'a',self.js,self.Mappingfile)
        #self.getFile(10,'a',self.js,self.outputRdfFile)
if __name__ == '__main__':
    FilesGitHub = FilesGitHub()
    FilesGitHub.testMain()

