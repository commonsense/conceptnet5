from __future__ import unicode_literals, print_function
import inspect
import importlib
import re
import codecs
import argparse

RULE_HEADER_RE = re.compile(r'([ ]*)Parse rules?:', re.IGNORECASE)
INDENT_RE = re.compile(r'([ ]*)')

EBNF_HEADER = """(* Do not edit this file!

This file was autogenerated by conceptnet5.wiktparse.extract_ebnf,
which reads documentation and parse rules out of a Python class.

Instead of changing this file, you should change the file it was
generated from, whose module name is:

    %s

Then run `make` to regenerate this file and the parser.
*)
"""

def extract_ebnf(qualified_class_name):
    module_name, class_name = qualified_class_name.rsplit('.', 1)
    module = importlib.import_module(module_name)
    this_class = getattr(module, class_name)
    ebnf_sections = []
    seen_docs = set()
    seen_names = set()

    # Iterate over superclasses in method-resolution order
    for depth, klass in enumerate(this_class.mro()):
        if klass != object:
            for name, method in inspect.getmembers(klass):
                if inspect.isfunction(method):
                    if name not in seen_names:
                        seen_names.add(name)
                        _, linenum = inspect.getsourcelines(method)
                        doc = inspect.getdoc(method)
                        if doc and doc not in seen_docs:
                            seen_docs.add(doc)
                            ebnf = ebnf_from_docstring(doc)
                            ebnf_sections.append((-depth, linenum, name, ebnf))


    ebnf_sections.sort()
    ebnf_rules = [EBNF_HEADER % module_name] + [sec[3] for sec in ebnf_sections if sec[3]]
    return '\n\n'.join(ebnf_rules)


def ebnf_from_docstring(docstring):
    lines = docstring.split('\n')
    ebnf_lines = []
    comment_lines = []
    start_indent = None
    active_indent = None
    for line in lines:
        if start_indent is None:
            # There's no active rule section, so look for the start of one
            match = RULE_HEADER_RE.match(line)
            if match:
                start_indent = len(match.group(1))
                while comment_lines and comment_lines[-1] == '':
                    comment_lines.pop()
                if comment_lines:
                    ebnf_lines.append('')
                    ebnf_lines.append('(*')
                    ebnf_lines.extend(comment_lines)
                    ebnf_lines.append('*)')
                comment_lines = []
            else:
                comment_lines.append(line.rstrip())
        else:
            # A rule section is active. Find the indentation level, and add
            # everything at that level or greater to the rules. Skip blank
            # lines.
            if line.strip():
                match = INDENT_RE.match(line)
                nspaces = len(match.group(1))
                if active_indent is None:
                    if nspaces <= start_indent:
                        raise IndentationError
                    active_indent = nspaces
                    ebnf_lines.append(line[active_indent:])
                elif nspaces < active_indent:
                    active_indent = None
                    start_indent = None
                    comment_lines.append(line.rstrip())
                else:
                    ebnf_lines.append(line[active_indent:])

    return '\n'.join(ebnf_lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'classname', 
        help='The fully qualified name of the class to extract rules from, '
             'such as '
             'conceptnet5.wiktparse.rules.EnWiktionarySemantics or '
             'conceptnet5.wiktparse.rules.DeWiktionarySemantics'
    )
    parser.add_argument(
        'output_file',
        help='The file to write EBNF rules to'
    )
    args = parser.parse_args()
    ebnf = extract_ebnf(args.classname)
    with codecs.open(args.output_file, 'w', encoding='utf-8') as outfile:
        print(ebnf, file=outfile)
