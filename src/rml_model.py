from abc import ABC

class TermMap(ABC): 
    def __init__(self, triples:dict):
        self.triples = triples 
        


class SubjectMap(TermMap): 
    def identity(self): 
        pass 

class PredicateMap(TermMap): 
    def identity(self): 
        pass 

class ObjectMap(TermMap): 
    def identity(self): 
        pass 

class GraphMap(TermMap): 
    def identity(self): 
        pass 


