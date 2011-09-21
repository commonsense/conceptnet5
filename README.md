Assertions
----------

An Assertion is a node with {'type': 'assertion'}. It's a node, not an edge,
because it has to be reified.

An Assertion has "arg1", "arg2", and possibly more links pointing to concepts.
It also has a "rel" link for its relation, which may be treated as an "arg0" in
some contexts.

Polarity is represented by a new kind of relation (a negative relation).

The Assertion should be marked with what language it's in (English? Chinese?
CycL?), and what dataset it's from (this is important so that we can sort out
what data we're allowed to distribute in complex cases).

Concepts
--------
Concepts have a standardized name ("dog") and a language ("en"). Relations are
concepts.

Assertions are interchangeable with concepts, even though concepts don't have
arguments, and assertions don't have names.

Expressions
-----------
An expression is like an assertion, but describes exactly how a fact is
expressed in natural language.

Many of our data sources will have expressions, but not all.

Each Expression has an "assertion" link pointing to its equivalent assertion.

Knowledge sources
-----------------
People, rules, and databases are knowledge sources. They should have a
canonical name that's a URL. Knowledge sources can justify things.

Conjunctions
------------
Sometimes it takes a conjunction of knowledge sources to justify things. In
that case, they justify the Conjunction (an AND node), and the Conjunction
justifies something else.
