import tatsu


GRAMMAR = """
start = definition $ ;

unary_identifier = /[-_#a-z0-9]+/ ;
unary_prime = "'" ;
unary_deep_identifier = '=' name:/[A-Z_]+/ ;
encyclopedic_identifier = '@' name:/[-_()A-Za-z0-9]/ ;
binary_identifier = /[_A-Z0-9]+/ ;
disambig = '/' @:/[0-9]+/ ;

unary_p = name:(unary_identifier | unary_deep_identifier | encyclopedic_identifier | default_unary | unary_prime) [ num:disambig ] ;
binary_p = name:binary_identifier [ num:disambig ] ;

unary_expr = unary_paren_arg | unary_bracket_arg | unary_p ;
unary_paren_arg = func:unary_p '(' arg:definition ')' ;
unary_bracket_arg = func:unary_p '[' arg:definition ']' ;

binary_expr = binary_full | binary_left_curry | binary_right_curry ;
binary_full = left:expression func:binary_p right:expression ;
binary_left_curry = left:expression func:binary_p ;
binary_right_curry = func:binary_p right:expression ;

default_unary = '<' @:unary_identifier '>' ;
default_expr = '<' @:expression '>' ;
bracket_expr = '[' @:definition ']' ;

expression = binary_expr | unary_expr | default_expr | bracket_expr ;
definition = ','.{ expression }+ ;
"""


class KornaiNotationSemantics:
    def unary_deep_identifier(self, ast):
        return '=' + ast['name']

    def encyclopedic_identifier(self, ast):
        return '@' + ast['name']

    def unary_p(self, ast):
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
        assert len(args) == self.arity
        copy = self.copy()
        copy.args = args
        return copy

    def specify(self, facts):
        copy = self.copy()
        copy.specifiers = facts
        return copy

    def complete(self, facts):
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


MODEL = tatsu.compile(GRAMMAR)
SEMANTICS = KornaiNotationSemantics()


def parse(definition, **kwargs):
    return MODEL.parse(definition, semantics=SEMANTICS, **kwargs)