# pypdf

A PDF parser built on lex, useful for deep inspection and analysis of PDFs [1].

### Usage

Using the `PdfScanner` will result in a tree that can be traversed or manipulated (in the style of the `ast` module) via built in or custom traversals.

```
test_data = open(sys.argv[1]).read()
scanner = PdfScanner(test_data)

printable = PDFTreePrinter(scanner.tree)
print(printable)
```

[1]: http://www.adobe.com/content/dam/Adobe/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf
