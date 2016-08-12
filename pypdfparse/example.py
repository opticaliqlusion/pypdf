from pypdfparse import *
import magic
import pdb
import zlib

class PDFStreamIterator(PdfTreeVisitor):
    def __init__(self, tree):
        self.streams = []
        self.visit(tree)

    def visit_stream(self, node):
        stream_data = node.value[6:].lstrip()[:-9].rstrip()
        self.streams.append(stream_data)
        PdfTreeVisitor.visit_generic(self, node)

def main():
    test_data = open(sys.argv[1], "rb").read()
    if type(test_data) != type(""):
        test_data = ''.join([chr(i) for i in test_data])

    scanner = PdfScanner(test_data)

    printable = PDFTreePrinter(scanner.tree)
    print(printable)

    m = magic.Magic()
    streams = PDFStreamIterator(scanner.tree).streams

    type_stream_map = {}
    stream_list = []

    for stream in streams:
        btype = m.id_buffer(stream)
        if m.id_buffer(stream) == 'data':
            try:
                data = zlib.decompress(stream)
            except:
                print("decompression error")
                data = stream
                pass
        else:
            data = stream

        key = m.id_buffer(data)
        if not key in type_stream_map:
            type_stream_map[key] = []

        type_stream_map[key].append(stream)
        stream_list.append(stream)

    print(type_stream_map.keys())

    # perform manual analysis here...
    pdb.set_trace()

    return

if __name__ == "__main__":
    main()
