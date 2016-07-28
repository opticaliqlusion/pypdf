import os
import sys
import platform
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

literals = [ '%' ]
t_ignore  = ' \t\r\n'


t_PERCENT   = r'[\x25]'
t_SPACE     = r'\ '

t_HYPHEN    = r'\-'
t_EOL       = r'[\r|\n]'
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

#def t_REFERENCE(t):
#    r'[0-9]+ [0-9]+ R'
#    return t

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
#
#   PARSER
#

def p_pdf(t):
    'pdf : obj_list'
    t[0] = {'type':'pdf', 'children' : [t[1]] }
    return t

def p_obj_list(t):
    '''obj_list : obj_list obj
                 | obj'''
    if t.slice[0] == 'item_list':
        t[0] = {'type':'obj_list', 'children' : t[0]['children'] + [t[1]] }
    else:
        t[0] = {'type':'obj_list', 'children' : [t[1]] }
    return t

def p_obj(t):
    '''obj : NUMBER NUMBER OBJ item_list ENDOBJ
           | COMMENT'''
    if t.slice[1].type == 'COMMENT':
        pass
    else:
        t[0] = {'type' : 'obj', 'children' : [t[1], t[2], t[4]]}
    pass

def p_item(t):
    r'''item : dictionary
             | array
             | indirect_reference
             | ID
             | STREAM
             | HEX'''
    t[0] = t[1]
    pass

def p_item_list(t):
    r'''item_list : item_list item
                  | item'''
    if t.slice[0] == 'item_list':
        t[0] = {'type':'item_list', 'children' : t[0]['children'] + [t[1]] }
    else:
        t[0] = {'type':'item_list', 'children' : [t[1]] }
    pass

def p_value_list(t):
    r'''value_list : value_list value
                  | value'''
    if t.slice[0] == 'item_list':
        t[0] = {'type':'value_list', 'children' : t[0]['children'] + [t[1]] }
    else:
        t[0] = {'type':'value_list', 'children' : [t[1]] }
    pass

def p_key_value_list(t):
    r'''key_value_list : key_value_list key_value
                       | key_value'''
    if t.slice[0] == 'key_value_list':
        t[0] = {'type':'key_value_list', 'children' : t[0]['children'] + [t[1]] }
    else:
        t[0] = {'type':'key_value_list', 'children' : [t[1]] }
    pass

def p_key_value(t):
    r'''key_value : ID value'''
    t[0] = t[1]
    pass

def p_value(t):
    r'''value : dictionary
             | array
             | indirect_reference
             | NUMBER
             | HEX
             | STREAM
             | TEXT
             | BOOL
             | empty'''
    t[0] = t[1]
    pass

def p_indirect_reference(t):
    r'''indirect_reference : NUMBER NUMBER KEY_R'''
    t[0] = {'type':'indirect_reference', 'children' : [t[1], t[2]] }
    pass


def p_empty(t):
    r'empty :'
    pass

def p_array(t):
    r'''array : LBRACKET value_list RBRACKET'''
    t[0] = {'type':'array', 'children' : t[2] }
    pass

def p_dictionary(t):
    r'''dictionary : LTLT key_value_list GTGT'''
    t[0] = {'type':'dictionary', 'children' : t[2] }
    pass

def p_error(t):
    print("ERROR: {0}".format(t))
    pdb.set_trace()
    pass

#
#   MAIN
#

def main():

    test_data = open(sys.argv[1]).read()

    # test the lexer
    lexer = lex.lex()
    lexer.input(test_data)
    token_list = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        #print(tok)
        token_list.append(tok)

    pdb.set_trace()

    # test the parser
    parser = yacc.yacc(write_tables=False, debug=True)
    res = parser.parse(test_data, lexer=lex.lex(), debug=True)

    pdb.set_trace()

    return

if __name__ == "__main__":
    main()
