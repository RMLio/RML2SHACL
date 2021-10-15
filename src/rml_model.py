from abc import ABC, abstractmethod, abstractstaticmethod
from typing import List
from pprint import pprint
from json import dumps
from dataclasses import dataclass
from enum import Enum, auto



class TermType(Enum): 
    IRI = auto() 
    BLANK = auto() 
    LITERAL = auto() 

# Term models
@dataclass
class Term(ABC): 
    value: str
    term_type: TermType 


@dataclass
class Iri(Term): 
    term_type:TermType = TermType.IRI 

    def __post_init__(self):
        if self.value[0] + self.value[-1] != "<>": 
            raise Exception(f"Ivalid IRI: {self.value}")

@dataclass
class Blank(Term): 
    term_type:TermType = TermType.BLANK


@dataclass
class Literal(Term): 
    term_type:TermType = TermType.LITERAL



@dataclass 
class Triple():
    s:Term 
    p:Term
    o:Term

    def __post_init__(self): 

        if not (self.s.term_type == TermType.IRI) and not (self.s.term_type == TermType.BLANK): 
            raise Exception(f"Subject has to be an IRI or Blank {self.s}") 
        if not self.p.term_type == TermType.IRI: 
            raise Exception(f"Predicate has to be an IRI {self.p}")



# TermMaps models 
@dataclass
class TermMap(ABC): 
    triples:List[Triple]

    def __init__(self, triples: List[Triple], **_):
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


@dataclass
class PredicateObjectMap(TermMap):
    triples:List[Triple] 
    PMs:List[PredicateMap]  
    OMs:List[ObjectMap]

    def __post_init__(self):
        if not self.PMs or not self.OMs: 
            raise Exception("Cannot have empty predicate or object maps\n" + 
                            f"PMs: {self.PMs}\n" + 
                            f"OMs: {self.OMs}\n") 

        if len(self.PMs) != len(self.OMs):
            raise Exception("Number of predicate maps should be equal to the number of object maps in the POM \n" + 
                            f"PMs: {self.PMs}\n" + 
                            f"OMs: {self.OMs}\n")

    def identity(self): 
        pass

# END TermMaps models 

@dataclass
class TripleMap(): 
    sm:SubjectMap 
    poms:List[PredicateObjectMap] 
    logical_source: Triple 
    gm: GraphMap = None 
    triples: List[Triple] = None

if __name__ == "__main__":

    sm = SubjectMap(
        [Triple(Iri("<lksdjflj>"), Iri("<klsjdf>"), Literal("klsdjlfj"))])
    pm = PredicateMap(
        [Triple(Iri("<lksdjflj>"), Iri("<klsjdf>"), Literal("klsdjlfj"))])
    om = ObjectMap(
        [Triple(Iri("<lksdjflj>"), Iri("<klsjdf>"), Literal("klsdjlfj"))])

    logical_source = Triple(Iri("<lksdjflj>"), Iri(
        "<klsjdf>"), Literal("klsdjlfj"))
    gm = GraphMap(  
        [Triple(Iri("<lksdjflj>"), Iri("<klsjdf>"), Literal("klsdjlfj"))])

    pom = PredicateObjectMap([Triple(Iri("<lksdjflj>"), Iri("<klsjdf>"), Literal("ljsdfj"))],
                             PMs=[pm], OMs=[om])

    TM = TripleMap(sm,[pom], logical_source) 

    pprint(TM)
