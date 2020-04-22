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
    def getFile(self, number,letter,typeFile, fileNeeded): 
        #This function makes it possible to get the RML input files with the matching RDF output file from GitHub 
        if number <10:
            url = 'https://raw.githubusercontent.com/RMLio/rml-test-cases/master/test-cases/RMLTC000' + str(number) +letter + typeFile + fileNeeded
        else: #one 0 less in the base of the URL
            url = 'https://raw.githubusercontent.com/RMLio/rml-test-cases/master/test-cases/RMLTC00' + str(number) +letter +  typeFile + fileNeeded
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

    def testMain(self):
        #self.getFile(0,'',self.sparql,self.Mappingfile)
        #self.getFile(1,'a',self.sparql,self.outputRdfFile)
        self.getFile(10,'a',self.js,self.Mappingfile)
        self.getFile(10,'a',self.js,self.outputRdfFile)

FilesGitHub = FilesGitHub()
FilesGitHub.testMain()

