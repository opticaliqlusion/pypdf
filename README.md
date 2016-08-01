# pypdf

A PDF parser built on lex, useful for deep inspection and analysis of PDFs ([1]).

### Parsing

Using the `PdfScanner` will result in a tree that can be traversed or manipulated (in the style of the `ast` module) via built in or custom traversals.

```
test_data = open(sys.argv[1]).read()
scanner = PdfScanner(test_data)

printable = PDFTreePrinter(scanner.tree)
print(printable)
```

### PDF Traversal and Manipulation

The intermediate representation  can be easily manipulated or inspected by extending the `PdfTreeVisitor` and `PdfTreeTransformer` classes, implementing visitor functions for each relevent type of node.

The following example prints all the binary streams found in the PDF.

```
class StreamIterator(PdfTreeVisitor):
    '''For deflating (not crossing) the streams'''
    def visit_stream(self, node):
        print(node.value)
        pass
...
StreamIterator().visit(tree)
```

[1]: http://www.adobe.com/content/dam/Adobe/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf

