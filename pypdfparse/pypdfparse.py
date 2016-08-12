from __future__ import print_function
from builtins import bytes
from builtins import str
from builtins import object
import os
import sys
import copy
import ast
from ply import lex
from ply import yacc
import pdb
import io
import pprint
import string
import zlib

#
#   SCANNER
#

tokens = (
   'BOOL',
   'NUMBER',
   'LPAREN',
   #'RPAREN',
   'ID',
   'HEX',
   'LTLT',
   'GTGT',
   'LBRACKET',
   'RBRACKET',
   'STREAM',
   'COMMENT',
   'OBJ',
   'ENDOBJ',
   'KEY_R',
   'XREF_TERM',
   'START_XREF',
   'XREF',
   'TRAILER',
   'TEXT',
   'string_LPAREN',
   'LPAREN',
   'RPAREN',
   'almost_anything',
   'escape',
   'anything',
   'EOF',
   #'EOL',
   #'SPACE',
)

class PdfScanner(object):


    def pdf_lexer(self):

        states = (
            ('string', 'exclusive'),
            ('escape', 'exclusive'),
        )

        t_ignore  = ' \t\r\n'

        t_BOOL      = r'(true|false)'
        t_HEX       = r'\<[0-9A-F]*\>'

        t_LBRACKET  = r'\['
        t_RBRACKET  = r'\]'
        t_LTLT      = r'\<\<'
        t_GTGT      = r'\>\>'

        def t_EOF(t):
            r'%%EOF'
            return t

        def t_LPAREN(t):
            r'\('
            t.lexer.push_state('string')
            return t

        def t_string_almost_anything(t):
            r'[^\)\\)]+'
            return t

        def t_string_RPAREN(t):
            r'\)'
            t.lexer.pop_state()
            return t

        def t_string_escape(t):
            r'\\'
            t.lexer.push_state('escape')
            return t

        def t_escape_anything(t):
            r'.'
            t.lexer.pop_state()
            return t

        def t_OBJ(t):
            r'obj'
            return t

        def t_ENDOBJ(t):
            r'endobj'
            return t

        def t_START_XREF(t):
            r'startxref'
            return t

        def t_XREF(t):
            r'xref'
            return t

        def t_TRAILER(t):
            r'trailer'
            return t

        def t_COMMENT(t):
            r'%[\x00-\xFF]+?\n'
            return t

        def t_KEY_R(t):
            r'R^[A-Za-z0-9]'
            return t

        def t_STREAM(t):
            r'stream[\x00-\xFF]+?endstream'
            return t

        def t_HEADER(t):
            r"%%PDF-\d.\d"
            return t

        def t_ID(t):
            r'/[A-Za-z0-9~*,_+\-\:\'\x2e\\#@]+'
            return t

        def t_XREF_TERM(t):
            r'[nf][\r|\n|\r\n]'
            return t

        def t_NUMBER(t):
            r'-?[0-9]+(\.)?([0-9]+)?'
            return t

        def t_TEXT(t):
            r'[A-Za-z0-9=?~/,_+\-\:\'\x2e\\#@\{\}]+'
            return t

        return lex.lex()

    #
    #   TREE CONSTRUCTION
    #

    def pop_until(self, target_token):
        children = []
        while True:
            tok = self.token_stack.pop()
            if tok.type == target_token:
                break
            else:
                children.insert(0, tok)
        return children

    def handle_generic(self, token):
        return token

    def handle_key_r(self, token):
        return Node({ 'type' : 'reference', 'children' : [self.token_stack.pop(),self.token_stack.pop()] })

    def handle_gtgt(self, token):
        return Node({ 'type' : 'dictionary', 'children' : self.pop_until('ltlt') })

    def handle_rbracket(self, token):
        return Node({ 'type' : 'array', 'children' : self.pop_until('lbracket') })

    def handle_rparen(self, token):
        return Node({ 'type' : 'string', 'children' : self.pop_until('lparen') })

    def handle_xref_term(self, token):
        n1 = self.token_stack.pop()
        n2 = self.token_stack.pop()
        return Node({'type' : 'xref', 'coords':(n1,n2)})

    def handle_endobj(self, token):
        intermediate_stack = []
        children = self.pop_until('obj')

        n1 = self.token_stack.pop()
        n2 = self.token_stack.pop()

        return Node({'type' : 'obj', 'children':children, 'coords':(n1,n2)})

    def get_token(self):

        tok = self.token_stream.pop()
        try:
            res = getattr(self,'handle_{0}'.format(tok.type))(tok)
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
            transformed.append(Node({'type':token.type.lower(), 'value':token.value}))
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

        self.tree = Node({'type':'pdf', 'children':copy.deepcopy(self.token_stack)})

        IDKeyValuePacker().visit(self.tree)

        return

class Node(object):
    def __init__(self, attributes):
        for k in list(attributes.keys()):
            setattr(self, k, attributes[k])

        # some defaults
        if not hasattr(self, 'children'):
            setattr(self, 'children', [])

        if not hasattr(self, 'type'):
            setattr(self, 'type', 'UNKNOWN')

        if not hasattr(self, 'value'):
            setattr(self, 'value', None)

    def __str__(self):
        is_printable = lambda s : all(c in string.printable for c in s)
        if self.value and is_printable(self.value):
            return '<PDF_Node-{0} {1}>'.format(self.type, str(self.value)[:10])
        else:
            return '<PDF_Node-{0}>'.format(self.type)

    def __repr__(self):
        return self.__str__()

    def pprint(self):
        print(PDFTreePrinter(self))

#
#   TREE TRAVERSAL, IN THE STYLE OF AST
#   you cant always get what you want
#

class PdfTreeVisitor(object):
    def visit_generic(self, node):
        if hasattr(node, 'children'):
            for child in node.children:
                try:
                    handler = getattr(self, 'visit_{0}'.format(child.type))
                except AttributeError:
                    handler = self.visit_generic

                handler(child)

    def visit(self, tree):
        return self.visit_generic(tree)

class PdfTreeTransformer(object):
    def visit_generic(self, node):
        children = []
        if hasattr(node, 'children'):
            for child in node.children:
                try:
                    handler = getattr(self, 'visit_{0}'.format(child.type))
                except AttributeError:
                    handler = self.visit_generic

                newchild = handler(child)
                if newchild != None:
                    children.append(newchild)

            node.children = children
        return node

    def visit(self, tree):
        return self.visit_generic(tree)

class IDKeyValuePacker(PdfTreeVisitor):
    '''Second pass visitor to assign values to /id:value pairs'''
    def visit_dictionary(self, node):

        self.visit_generic(node)

        new_children = []
        old_children = copy.deepcopy(node.children)
        old_children.reverse()

        while True:
            try:
                tok = old_children.pop()
            except IndexError:
                break
            if tok.type == 'id':
                value = old_children.pop()
                tok.children = [ value ]
                assert len(tok.children) == 1
            new_children.append(tok)

        node.children = new_children

        pass

class PDFTreePrinter(PdfTreeVisitor):
    '''Printable trees'''
    def __init__(self, tree):
        self.sio = io.BytesIO()
        self.depth = 0

        self.visit(tree)

    def __str__(self):
        return self.sio.getvalue().decode('UTF-8')

    def visit_generic(self, node):
        data = bytes('{0}{1}\n'.format('  '*self.depth, pprint.pformat(node).replace('\n','\n'+'  '*self.depth)), encoding='UTF-8')
        self.sio.write(data)
        self.depth += 1
        PdfTreeVisitor.visit_generic(self, node)
        self.depth -= 1

class PDFTreeNativeTypes(PdfTreeTransformer):
    '''If we want to deal in native python types instead of Node classes'''

    def visit_number(self, node):
        def isfloat(x):
            try:
                a = float(x)
            except ValueError:
                return False
            else:
                return True

        def isint(x):
            try:
                a = float(x)
                b = int(a)
            except ValueError:
                return False
            else:
                return a == b

        if isfloat(node.value):
            return float(node.value)
        elif isint(node.value):
            return int(node.value)
        else:
            raise Exception("could not convert int token to native type")

    def visit_array(self, node):
        self.visit_generic(node)
        return node.children

    def visit_bool(self, node):
        if node.value == 'false':
            return False
        elif node.value == 'true':
            return True
        else:
            raise Exception("Unrecognized bool. There are only 10.")

    def visit_dictionary(self, node):
        self.visit_generic(node)

        retd = {}

        for item in node.children:
            try:
                assert item.type == 'id', "expected ID in dictionary"
                assert item.value[0] == '/', "IDs must begin with fslash"
                assert len(item.children) == 1, "ids may only have one child"
                retd[item.value[1:]] = item.children[0]
            except Exception as e:
                #pdb.set_trace()
                raise e
                pass

        return retd
