"""
Parse a notation by Andras Kornai for expressing hand-curated common-sense
facts.

Kornai's notation is designed for building a formalism of computation known
as Eilenberg machines. We don't really want to be working with Eilenberg
machines, but the graph structure that results from parsing Kornai's notation
contains edges that we can interpret as ConceptNet edges. When they do, they
frequently represent common-sense facts.

Kornai explains his motivation and his representation in his paper
"Competence in Lexical Semantics": http://www.aclweb.org/anthology/S15-1019
"""
import tatsu
from conceptnet5.nodes import standardized_concept_uri, topic_to_concept
from conceptnet5.language.hungarian import decode_prószéky

GRAMMAR = """
start = definition $ ;

unary_identifier = /[-_#a-z0-9]+/ ;
unary_prime = "'" ;
unary_deep_identifier = '=' name:/[A-Z_]+/ ;
encyclopedic_identifier = '@' name:/[-_()A-Za-z0-9]/ ;
binary_identifier = /[_A-Z0-9]+/ ;
disambig = '/' @:/[0-9]+/ ;

unary_p = (name:(unary_identifier | unary_deep_identifier | encyclopedic_identifier | unary_prime) [ num:disambig ] | defa:default_unary) ;
binary_p = name:binary_identifier [ num:disambig ] ;

unary_expr = unary_paren_arg | unary_bracket_arg | unary_p ;
unary_paren_arg = func:unary_p '(' arg:definition ')' ;
unary_bracket_arg = func:unary_p '[' arg:definition ']' ;

binary_expr = binary_full | binary_left_curry | binary_right_curry ;
binary_full = left:expression func:binary_p right:expression ;
binary_left_curry = left:expression func:binary_p ;
binary_right_curry = func:binary_p right:expression ;

default_unary = '<' @:unary_p '>' ;
default_expr = '<' @:expression '>' ;
bracket_expr = '[' @:definition ']' ;

expression = binary_expr | unary_expr | default_expr | bracket_expr ;
definition = ','.{ expression }+ ;
"""


class KornaiNotationSemantics:
    """
    A packrat parser for the notation of the 4lang system, defined formally
    in http://www.aclweb.org/anthology/S15-1019 .
    """
    def unary_deep_identifier(self, ast):
        return '=' + ast['name']

    def encyclopedic_identifier(self, ast):
        return '@' + ast['name']

    def unary_p(self, ast):
        if 'defa' in ast:
            return ast['defa']
        else:
            return KornaiValue(ast['name'], ast['num'])

    def binary_p(self, ast):
        return KornaiValue(ast['name'], ast['num'], arity=2)

    def unary_expr(self, ast):
        if isinstance(ast, KornaiValue):
            return [ast]
        assert isinstance(ast, list)
        return ast

    def unary_paren_arg(self, ast):
        outer = ast['func']
        return [outer.apply(inner) for inner in ast['arg']]

    def unary_bracket_arg(self, ast):
        outer = ast['func']
        return [outer.specify(ast['arg'])]

    def binary_full(self, ast):
        results = []
        for left in ast['left']:
            for right in ast['right']:
                results.append(ast['func'].apply(left, right))
        return results

    def binary_left_curry(self, ast):
        return [ast['func'].apply(left, None) for left in ast['left']]

    def binary_right_curry(self, ast):
        return [ast['func'].apply(None, right) for right in ast['right']]

    def definition(self, ast):
        flattened = [val for sublist in ast for val in sublist]
        assert all(isinstance(val, KornaiValue) for val in flattened)
        return flattened


class KornaiValue:
    """
    A KornaiValue represents a graph node and the edges pointing away from
    it.

    The node can be unary or binary, indicating the number of outgoing
    edges (or arguments) it takes to express a complete fact using that node.
    One of the arguments may be unspecified, to be filled in later;
    this is represented by the argument value None.

    We allow constructing binary nodes with no arguments, but only so that
    we can apply them to one argument (this is basically currying).

    "Specifiers" are other facts that come along with the fact being expressed,
    as part of a larger graph that we're not really representing. Often they
    have edges pointing _in_ to the node we're returning.
    """
    def __init__(self, name, num=None, arity=1, args=None, specifiers=None):
        self.name = name
        assert isinstance(name, str)
        if num is None:
            self.num = None
        else:
            self.num = int(num)
        self.arity = arity
        assert isinstance(arity, int)
        if args is None:
            self.args = tuple(None for i in range(arity))
        else:
            assert len(args) == arity
            self.args = args
        if specifiers is None:
            self.specifiers = []
        else:
            self.specifiers = specifiers

    def apply(self, *args):
        """
        Set the arguments of this node. Unary nodes must be applied to one
        value, and binary nodes must be applied to two. Up to one of the
        values may be None, indicating that it's a slot that can be filled
        later.
        """
        assert len(args) == self.arity
        copy = self.copy()
        copy.args = args
        return copy

    def specify(self, facts):
        copy = self.copy()
        copy.specifiers = facts
        return copy

    def complete(self, facts):
        """
        When we parse a 4lang definition, we get a list of facts, many of
        which have an unspecified argument.

        We 'complete' the definition by taking a value (which is `self`) and
        filling it in as the unspecified argument of each fact, and also
        filling what we can of the 'specifiers' that come with those facts.
        """
        completed = []
        for fact in facts:
            if fact.arity == 1:
                if fact.args[0] is None:
                    completed.append(fact.apply(self))
                else:
                    completed.append(fact)
            elif fact.arity == 2:
                left, right = fact.args
                if left is None:
                    completed.append(fact.apply(self, right))
                elif right is None:
                    completed.append(fact.apply(left, self))
                else:
                    completed.append(fact)
            if fact.specifiers:
                simple_fact = fact.copy()
                simple_fact.specifiers = []
                completed.extend(simple_fact.complete(fact.specifiers))
        return completed

    def as_tuple(self):
        return (
            self.name, self.num, self.arity, self.args, self.specifiers
        )

    def copy(self):
        return KornaiValue(*self.as_tuple())

    def __eq__(self, other):
        return (
            isinstance(other, KornaiValue) and self.as_tuple() == other.as_tuple()
        )

    def __hash__(self):
        return hash(self.as_tuple())

    def __repr__(self):
        if not self.specifiers and not any(self.args):
            return "KornaiValue(%r, %r, %r)" % (
                self.name, self.num, self.arity
            )
        elif not self.specifiers:
            return "KornaiValue(%r, %r, %r, args=%r)" % (
                self.name, self.num, self.arity, self.args
            )
        else:
            return "KornaiValue(%r, %r, %r, args=%r, specifiers=%r)" % (
                self.name, self.num, self.arity, self.args, self.specifiers
            )


class Vocabulary:
    NAMES_TO_CONCEPTNET_RELATIONS = {
        'ABOUT': '/r/HasContext',
        'AT': '/r/LocatedNear',
        'CAUSE': '/r/Causes',
        'CONTAIN': '/r/HasA',
        'FOR': '/r/UsedFor',
        'FROM': '/r/RelatedTo',
        'HAS': '/r/HasA',
        'IN': '/r/AtLocation',
        'INSTRUMENT': '/r/UsedFor/rev',
        'IS_A': '/r/IsA',
        'LEAD': '/r/ControlledBy/rev',
        'MAKE': '/r/CreatedBy/rev',
        'MEMBER': '/r/PartOf',
        'NEXT_TO': '/r/LocatedNear',
        'PART_OF': '/r/PartOf',
        'RESEMBLE': '/r/SimilarTo',
        'WANT': '/r/CausesDesire',
        # 'after': '/r/HasPrerequisite/rev',
        'can': '/r/CapableOf',   # needs to be can/1246
        'before': '/r/HasPrerequisite',
        'lack': '/r/Antonym'
    }

    POS_MAP = {
        'N': 'n',
        'V': 'v',
        'U': 'v',
        'A': 'a',
        'D': 'r'
    }

    def __init__(self):
        self.name_to_num = {}
        self.num_to_entry = {}

    def add_line(self, line):
        text_en, text_hu, text_la, text_pl, num, _, pos, definition = line.split('\t')[:8]
        if num == '#':
            return
        num = int(num)
        entry = {
            'name': {
                'en': text_en,
                'hu': text_hu,
                'la': text_la,
                'pl': text_pl,
            },
            'num': num,
            'pos': pos,
            'definition': definition,
            'value': KornaiValue(text_en, num)
        }
        self.name_to_num.setdefault(text_en, []).append(num)
        self.num_to_entry[num] = entry
        return entry['value']

    def get_entry(self, value):
        name = value.name
        num = value.num
        if num is not None:
            return self.num_to_entry[num]
        else:
            nums = self.name_to_num.get(name, [])
            if len(nums) == 0:
                # print("Missing entry: %r" % name)
                return None
            elif len(nums) > 1:
                # print("Ambiguous entry: %r" % name)
                return self.num_to_entry[nums[0]]
            else:
                return self.num_to_entry[nums[0]]

    def value_to_conceptnet_term(self, value, lang='en'):
        if value.arity == 2 or value.name.startswith('='):
            return None
        if value.name == "'":
            return None
        if value.name.startswith('@'):
            return topic_to_concept(value.name)

        arg = value.args[0]
        if arg is not None:
            # This is often an adjective-noun phrase, such as four(leg),
            # and the key information is usually on the inside
            return self.value_to_conceptnet_term(arg)

        entry = self.get_entry(value)
        if entry is not None:
            pos = self.POS_MAP.get(entry['pos'], '_')
            text = entry['name'][lang]
            if lang == 'hu' or lang == 'pl':
                text = decode_prószéky(text, lang)
            return standardized_concept_uri(lang, text, pos, '4lang', str(entry['num']))

        return None

    def interpret_definition(self, num, lang='en'):
        term_info = self.num_to_entry[num]
        definition = term_info['definition']
        if not definition:
            return []
        term = self.value_to_conceptnet_term(term_info['value'])
        edges = []
        for fact in term_info['value'].complete(parse(definition)):
            if fact.arity == 1:
                if fact.name in self.NAMES_TO_CONCEPTNET_RELATIONS and fact.args[0]:
                    obj = self.value_to_conceptnet_term(fact.args[0], lang)
                    rel = self.NAMES_TO_CONCEPTNET_RELATIONS[fact.name]
                    if rel and obj:
                        edges.append((rel, term, obj))
                else:
                    # this is an IsA, entailment, or property
                    obj = self.value_to_conceptnet_term(fact, lang)
                    entry = self.get_entry(fact)
                    if entry and term and obj:
                        if entry['pos'] == 'n':
                            edges.append(('/r/IsA', term, obj))
                        elif entry['pos'] == 'v':
                            edges.append(('/r/Entails', term, obj))
                        elif entry['pos'] == 'a':
                            edges.append(('/r/HasProperty', term, obj))
            else:
                if fact.name in self.NAMES_TO_CONCEPTNET_RELATIONS and fact.args[0] and fact.args[1]:
                    subj = self.value_to_conceptnet_term(fact.args[0], lang)
                    obj = self.value_to_conceptnet_term(fact.args[1], lang)
                    rel = self.NAMES_TO_CONCEPTNET_RELATIONS[fact.name]
                    if subj and obj and rel:
                        edges.append((rel, subj, obj))
        return edges

    def read_file(self, filename):
        for line in open(filename):
            print(self.add_line(line))

        for num in sorted(self.num_to_entry):
            for lang in ('en', 'hu', 'la', 'pl'):
                for edge in self.interpret_definition(num, lang):
                    print(edge)


MODEL = tatsu.compile(GRAMMAR)
SEMANTICS = KornaiNotationSemantics()


def parse(definition, **kwargs):
    return MODEL.parse(definition, semantics=SEMANTICS, **kwargs)


if __name__ == '__main__':
    vocab = Vocabulary()
    vocab.read_file('/home/rspeer/corpus/4lang.txt')
