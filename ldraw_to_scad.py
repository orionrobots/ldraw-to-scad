import os
import argparse


class LDrawConverter():
    def __init__(self):
        self.modules = {}
        self.index = {}

    def make_colour(self, colour_index):
        return "color(lego_colours[{0}])".format(colour_index)

    def get_modules(self):
        result = []
        for module in self.modules.values():
            result.extend(module)
        return result

    def handle_type_1_line(self, colour_index, x, y, z, a, b, c, d, e, f, g, h, i, filename):
        module_name = filename.split('.', 1)[0]
        module_name = module_name.replace('s\\', 's__')

        if filename not in self.modules:
            path = self.find_part(filename)
            with open(path) as fd:
                module_inner = self.convert_file(fd, indent=2)
            self.modules[filename] = [
                "module {}() {{".format(module_name)
            ] + module_inner + [
                "}"
            ]

        return [
            self.make_colour(colour_index),
            "  multmatrix([",
            "    [{0}, {1}, {2}, {3}],".format(a, b, c, x),
            "    [{0}, {1}, {2}, {3}],".format(d, e, f, y),
            "    [{0}, {1}, {2}, {3}],".format(g, h, i, z),
            "    [{0}, {1}, {2}, {3}]".format(0, 0, 0, 1),
            "  ])",
            "  {}();".format(module_name)
        ]

    def convert_line(self, part_line, indent=0):
        # Preserve blank lines
        part_line = part_line.strip()
        if part_line == '':
            return [part_line]
        try:
            command, rest = part_line.split(maxsplit=1)
        except ValueError:
            command = part_line
            rest = ''
        result = []
        if command == "0":
            result.append("// {}".format(rest))
        elif command == "1":
            result.extend(self.handle_type_1_line(*rest.split()))
        elif command == "3":
            colour_index, x1, y1, z1, x2, y2, z2, x3, y3, z3 = rest.split()
            result.append(self.make_colour(colour_index))
            result.append("  polyhedron(points=[")
            result.append("    [{0}, {1}, {2}],".format(x1, y1, z1))
            result.append("    [{0}, {1}, {2}],".format(x2, y2, z2))
            result.append("    [{0}, {1}, {2}]".format(x3, y3, z3))
            result.append("  ], faces = [[0, 1, 2]]);")
        elif command == "4":
            colour_index, x1, y1, z1, x2, y2, z2, x3, y3, z3, x4, y4, z4 = rest.split()
            result.append(self.make_colour(colour_index))
            result.append("  polyhedron(points=[")
            result.append("    [{0}, {1}, {2}],".format(x1, y1, z1))
            result.append("    [{0}, {1}, {2}],".format(x2, y2, z2))
            result.append("    [{0}, {1}, {2}],".format(x3, y3, z3))
            result.append("    [{0}, {1}, {2}]".format(x4, y4, z4))
            result.append("  ], faces = [[0, 1, 2, 3]]);")
        if indent:
            indent_str = ''.join(' ' * indent)
            result = ['{i}{l}'.format(i=indent_str, l=line) for line in result]
        return result

    def convert_lines(self, lines, indent=0):
        result = []
        [result.extend(self.convert_line(line, indent=indent)) for line in lines]
        return result

    def convert_file(self, fd, indent=0):
        return self.convert_lines(fd.readlines(), indent=indent)

    def index_library(self):
        self.index = {}
        paths = ['.']
        for item in os.listdir('.'):
            if item.endswith('.dat'):
                self.index[item] = item

        library_root = os.path.join('lib', 'ldraw')
        for sub_path in ['parts', 'p']:
            whole_path = os.path.join(library_root, sub_path) 
            for item in os.listdir(whole_path):
                if item.endswith('.dat'):
                    self.index[item] = os.path.join(whole_path, item)
        s_path = os.path.join(library_root, 'parts', 's') 
        for item in os.listdir(s_path):
            if item.endswith('.dat'):
                self.index['s\\'+item] = os.path.join(s_path, item)

    def find_part(self, part_name):
        if not self.index:
            self.index_library()
        return self.index[part_name]

def main():
    parser = argparse.ArgumentParser(description='Convert an LDraw part to OpenSCAD')
    parser.add_argument('ldraw_file', metavar='FILENAME')
    parser.add_argument('output_file', metavar='OUTPUT_FILENAME')
    args = parser.parse_args()
    convert = LDrawConverter()
    with open(args.ldraw_file) as fd:
        result = convert.convert_file(fd)
    with open(args.output_file, 'w') as fdw:
        fdw.write('\n'.join(convert.get_modules()))
        fdw.write('\n'.join(result))



if __name__ == '__main__':
    main()