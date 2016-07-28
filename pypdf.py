import os
import sys
import platform
import ply.lex as lex

tokens = (
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
   'DICTIONARY',
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
#t_BINARY    = r'[\x00-\x09\x0B-\x0C\x0E-\x1F\x7F-\xFF]+'
t_PERCENT   = r'[\x25]'
t_SPACE     = r'\ '

t_HYPHEN    = r'\-'
t_EOL       = r'[\r|\n]'
t_BOOL      = r'(true|false)'
t_NUMBER    = r'[0-9]+(\.)?([0-9]+)?'
t_HEX       = r'\<[0-9A-F]*\>'
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_FSLASH    = r'/'
t_LBRACKET  = r'\['
t_RBRACKET  = r'\]'
t_LTLT      = r'\<\<'
t_GTGT      = r'\>\>'
#t_BINARY    = r'[\x00-\xFF]'

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
    r'/[A-Za-z]+'
    return t

def t_TEXT(t):
    r'\(.+\)'
    return t

def main():

    lexer = lex.lex()
    lexer.input(open(sys.argv[1], 'rb').read())

    while True:
        tok = lexer.token()
        if not tok:
            break      # No more input
        print(tok)

    return

if __name__ == "__main__":
    main()
