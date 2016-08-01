import os
import sys
import platform
import copy
from ply import lex
from ply import yacc
import pdb

#
#   SCANNER
#

tokens = (
  #'REFERENCE',
   'PERCENT',
   'HYPHEN',
   'BOOL',
   'NUMBER',
   'SPACE',
   'LPAREN',
   'RPAREN',
   'FSLASH',
   'EOL',
   'ID',
   'HEX',
   'LTLT',
   'GTGT',
   'LBRACKET',
   'RBRACKET',
   'STREAM',
   'BINARY',
   'NULL',
   'COMMENT',
   'OBJ',
   'ENDOBJ',
   'KEY_R',
   'KEY_XREF',
   'TEXT',
)

class PdfScanner():

    def pdf_lexer(self):
        t_ignore  = ' \t\r\n'

        t_BOOL      = r'(true|false)'
        t_HEX       = r'\<[0-9A-F]*\>'
        t_LPAREN    = r'\('
        t_RPAREN    = r'\)'
        t_FSLASH    = r'/'
        t_LBRACKET  = r'\['
        t_RBRACKET  = r'\]'
        t_LTLT      = r'\<\<'
        t_GTGT      = r'\>\>'

        t_OBJ = r'obj'
        t_ENDOBJ = r'endobj'
        t_KEY_R = r'R'
        t_KEY_XREF = r'startxref'
        t_STREAM  = r'stream[\x00-\xFF]+?endstream'
        t_COMMENT = r'%[\x00-\xFF]+?\r\n'

        def t_HEADER(t):
            r"%%PDF-\d.\d"
            return t

        def t_ID(t):
            r'/[A-Za-z0-9]+'
            return t

        def t_TEXT(t):
            r'\(.+\)'
            return t

        def t_NUMBER(t):
            r'[0-9]+(\.)?([0-9]+)?'
            return t

        return lex.lex()

    #
    #   TREE CONSTRUCTION
    #

    def pop_until(self, target_token):
        children = []
        while True:
            try:
                tok = self.token_stack.pop()
                if tok['type'] == target_token:
                    break
                else:
                    children.insert(0, tok)
            except:
                pdb.set_trace()
                pass

        return children

    def handle_generic(self, token):
        return token

    def handle_gtgt(self, token):
        return { 'type' : 'dictionary', 'children' : self.pop_until('ltlt') }

    def handle_rbracket(self, token):
        return { 'type' : 'array', 'children' : self.pop_until('lbracket') }

    def handle_endobj(self, token):

        intermediate_stack = []
        children = self.pop_until('obj')
        n1 = self.token_stack.pop()
        n2 = self.token_stack.pop()

        return {'type' : 'obj', 'children':children, 'coords':(n1,n2)}

    def get_token(self):

        tok = self.token_stream.pop()

        try:
            res = getattr(self,'handle_{0}'.format(tok['type']))(tok)
        except AttributeError:
            res = self.handle_generic(tok)

        return res

    def parse_token_stream(self):

        while True:
            try:
                res = self.get_token()
            except IndexError:
                break

            if res:
                self.token_stack.append(res)
        return

    def transform_tokens(self, tokens):
        transformed = []
        for token in tokens:
            transformed.append({'type':token.type.lower(), 'value':token.value})
        return transformed

    def __init__(self, input):

        lexer = self.pdf_lexer()
        lexer.input(input)
        self.token_stream = []
        self.token_stack = []

        while True:
            tok = lexer.token()
            if not tok:
                break
            self.token_stream.append(tok)

        self.token_stream.reverse()
        self.token_stream = self.transform_tokens(self.token_stream)
        self.parse_token_stream()

        self.tree = {'type':'pdf', 'children':copy.deepcopy(self.token_stack)}

        IDKeyValuePacker().visit(self.tree)

        return

#
#   TREE TRAVERSAL, IN THE STYLE OF AST
#   you cant always get what you want
#

class PdfTreeVisitor():
    def visit_generic(self, node):
        if 'children' in node.keys():
            for child in node['children']:
                try:
                    handler = getattr(self, 'visit_{0}'.format(child['type']))
                except AttributeError:
                    handler = self.visit_generic

                handler(child)

    def visit(self, tree):
        return self.visit_generic(tree)

#
#   MAIN
#

# want to deflate streams?
class StreamIterator(PdfTreeVisitor):
    def visit_stream(self, node):
        raise NotImplementedError
        pass

# second pass to assign values to /id:value pairs
class IDKeyValuePacker(PdfTreeVisitor):
    def visit_dictionary(self, node):
        new_children = []
        old_children = copy.deepcopy(node['children'])
        old_children.reverse()

        while True:
            try:
                tok = old_children.pop()
            except IndexError:
                break
            if tok['type'] == 'id':
                value = old_children.pop()
                tok['children'] = [ value ]
            new_children.append(tok)

        node['children'] = new_children
        pass

def main():

    test_data = open(sys.argv[1]).read()
    scanner = PdfScanner(test_data)

    pdb.set_trace()
    return

if __name__ == "__main__":
    main()
