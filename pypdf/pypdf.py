import os
import sys
import copy
import ast
from ply import lex
from ply import yacc
import pdb
import StringIO
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
   'RPAREN',
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

        def t_error(t):
            raise Exception("Lexing error")
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

class Node():
    def __init__(self, attributes):
        for k,v in attributes.iteritems():
            setattr(self, k, v)

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

class PdfTreeVisitor():
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

class PdfTreeTransformer():
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

class StreamIterator(PdfTreeTransformer):
    '''For deflating (not crossing) the streams'''
    def visit_obj(self, node):

        try:
            if node.children[0]['Filter'].value=='/FlateDecode':
                stream = node.children[1].value
                node.children[1].value = zlib.decompress(stream[8:-11])
                print(node.children[1].value)
                pdb.set_trace()
        except KeyError:
            pass

        pass

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
        self.sio = StringIO.StringIO()
        self.depth = 0

        self.visit(tree)

    def __str__(self):
        return self.sio.getvalue()

    def visit_generic(self, node):
        self.sio.write('{0}{1}\n'.format('  '*self.depth, pprint.pformat(node).replace('\n','\n'+'  '*self.depth)))
        self.depth += 1
        PdfTreeVisitor.visit_generic(self, node)
        self.depth -= 1

class PDFTreeNativeTypes(PdfTreeTransformer):
    '''If we want to deal in native python types instead of Node classes'''

    def visit_number(self, node):
        return ast.literal_eval(node.value)

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
            assert item.type == 'id', "expected ID in dictionary"
            assert item.value[0] == '/', "IDs must begin with fslash"
            assert len(item.children) == 1, "ids may only have one child"
            retd[item.value[1:]] = item.children[0]

        return retd

#
#   EXAMPLE MAIN
#

def main():

    test_data = open(sys.argv[1]).read()
    scanner = PdfScanner(test_data)

    native_tree = PDFTreeNativeTypes()
    native_tree.visit(scanner.tree)

    printable = PDFTreePrinter(scanner.tree)
    print(printable)

    StreamIterator().visit(scanner.tree)

    return

if __name__ == "__main__":
    main()
