import os
import argparse
import queue

ldraw_path = os.getenv('LDRAW_LIB', os.path.join('lib', 'ldraw'))

class ColourConverter:
    def __init__(self):
        self.colours = []

    def read_ldconfig_file(self):
        filename = os.path.join(ldraw_path, 'LDConfig.ldr')
        with open(filename) as fd:
            self.parse_colour_lines(fd)

    def colour_from_hex(self, hex):
        r, g, b = hex[1:3], hex[3:5], hex[5:7]
        r, g, b = int(r, 16), int(g, 16), int(b, 16)
        return r,g,b
        
    def parse_colour_lines(self, text_lines):
        current_colour = {}
        for line in text_lines:
            try:
                line = line.strip()
                if not line or line=='0':
                    continue
                cmd, rest = line.split(' ', 1)
                if rest.startswith("!COLOUR"):
                    items = rest.split()
                    name = items[1]
                    params = items[2:]

                    specials = ['CHROME', 'PEARLESCENT', 'METAL', 'RUBBER']
                    for special in specials:
                        if special in params:
                            params.remove(special)
                    params = [params[i:i+2] for i in range(0, len(params), 2)]
                    params = dict(params)
                    code = int(params['CODE'])

                    current_colour = {
                        'name': name,
                        'code': code,
                        'value': self.colour_from_hex(params['VALUE']),
                        'edge': self.colour_from_hex(params['EDGE'])
                    }
                    self.colours.append(current_colour)
            except:
                print("Error parsing line: '{}'".format(line))
                raise

    def get_lines(self):
        lines = []
        for colour in self.colours:
            r, g, b = colour['value']
            line = 'colour{n} = [{r}, {g}, {b}];'.format(
                n=colour['code'],
                r=round(r/255, 2),
                g=round(g/255, 2),
                b=round(b/255, 2)
            )
            lines.append(line)
        return lines

class Module:
    def __init__(self, filename):
        self.filename = filename
        self.lines = []
        self.module_name = None
        # Name of module only
        self.dependancies = set()

    @staticmethod
    def make_module_name(filename):
        module_name = filename.split('.', 1)[0]
        module_name = module_name.replace('\\', '__').replace('-', '_')
        return 'n__' + module_name

    def get_module_name(self):
        if not self.module_name:
            self.module_name = self.make_module_name(self.filename)
        return self.module_name

    def add_lines(self, lines):
        self.lines.extend(lines)

    def get_lines(self):
        if self.filename == '__main__':
            return self.lines
        else:
            return self.get_module_code()

    def get_module_code(self):
        func_lines = ['  {}'.format(line) 
            for line in self.lines]

        return [
            "module {}() {{".format(self.get_module_name())
        ] + func_lines + [
            "}"
        ]


class LDrawConverter:
    def __init__(self):
        # Ref name: module class
        self.modules = {}
        # Ref - queue of names only
        self.modules_queue = queue.Queue()
        # Path search
        self.index = {}
        self.current_module = None

    def process_lines(self, module, lines):
        self.current_module = module
        result = []
        first_line = True
        for line in lines:
            if first_line and line.startswith("0 FILE"):
                if module.filename == "__main__":
                    continue
            first_line = False
            converted = self.convert_line(line)
            self.current_module.add_lines(converted)

    def process_main(self, input_lines):
        main_module = Module('__main__')
        self.modules[main_module.get_module_name()] = main_module
        self.modules_queue.put(main_module)
        self.process_lines(main_module, input_lines)
        completed = []
        while not self.modules_queue.empty():
            # Get the next queued module
            current_module = self.modules_queue.get()
            # Has it been done?
            if current_module.get_module_name() in completed:
                continue
            # Have we loaded it?
            if not current_module.lines:
                real_filename = self.find_part(current_module.filename)
                with open(real_filename) as fd:
                    lines = fd.readlines()
                self.process_lines(current_module, lines)
            # Check - have we covered it dependancies
            new_dependancy = False
            for dep in current_module.dependancies:
                if dep not in completed:
                    self.modules_queue.put(self.modules[dep])
                    self.modules_queue.put(current_module)
                    new_dependancy = True
            if not new_dependancy:
                # Ok - ready to go - add to completed
                completed.append(current_module.get_module_name())
        # Now we can create output lines - starting at the top
        # of completed modules.
        output_lines = []
        [output_lines.extend(self.modules[module_name].get_lines())
            for module_name in completed]
        return output_lines

    def make_colour(self, colour_index):
        if colour_index == "16":
            return []
        return ["color(colour{0})".format(colour_index)]

    def handle_type_0_line(self, rest):
        # Ignore NOFILE for now
        if rest.startswith("NOFILE"):
            return None
        # Handle the file case
        if rest.startswith("FILE"):
            _, filename = rest.split()
            self.current_module = Module(filename=filename)
            module_name = Module.make_module_name(filename)
            self.modules[module_name] = self.current_module
            return None
        elif rest.startswith("!"):
            return None
        return "// {}".format(rest)

    def handle_type_1_line(self, colour_index, x, y, z, a, b, c, d, e, f, g, h, i, filename):
        module_name = Module.make_module_name(filename)
        if module_name == "n__4_4edge":
            return []
        # Is this a new module?
        if module_name not in self.modules:
            # Create it
            self.modules[module_name] = Module(filename)
        # Add to deps
        self.current_module.dependancies.add(module_name)
        
        return self.make_colour(colour_index) + [
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
            data = self.handle_type_0_line(rest)
            if data:
                result.append(data)
        elif command == "1":
            try:
                result.extend(self.handle_type_1_line(*rest.split()))
            except TypeError:
                raise TypeError("Insufficient arguments in type 1 line", rest)
        elif command == "3":
            colour_index, x1, y1, z1, x2, y2, z2, x3, y3, z3 = rest.split()
            result.extend(self.make_colour(colour_index))
            result.append("  polyhedron(points=[")
            result.append("    [{0}, {1}, {2}],".format(x1, y1, z1))
            result.append("    [{0}, {1}, {2}],".format(x2, y2, z2))
            result.append("    [{0}, {1}, {2}]".format(x3, y3, z3))
            result.append("  ], faces = [[0, 1, 2]]);")
        elif command == "4":
            colour_index, x1, y1, z1, x2, y2, z2, x3, y3, z3, x4, y4, z4 = rest.split()
            result.extend(self.make_colour(colour_index))
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
        special_subs = {
            's': os.path.join(library_root, 'parts', 's'),
            '48' : os.path.join(library_root, 'p', '48')
        }
        for prefix, s_path in special_subs.items():
            for item in os.listdir(s_path):
                if item.endswith('.dat'):
                    self.index[prefix + '\\'+item] = os.path.join(s_path, item)

    def find_part(self, part_name):
        if not self.index:
            self.index_library()
        try:
            filename = self.index[part_name]
        except KeyError:
            filename = self.index[part_name.lower()]
        return filename


def main():
    parser = argparse.ArgumentParser(description='Convert an LDraw part to OpenSCAD')
    parser.add_argument('ldraw_file', metavar='FILENAME')
    parser.add_argument('output_file', metavar='OUTPUT_FILENAME')
    args = parser.parse_args()
    colours = ColourConverter()
    colours.read_ldconfig_file()
    convert = LDrawConverter()
    with open(args.ldraw_file) as fd:
        result = convert.process_main(fd)
    with open(args.output_file, 'w') as fdw:
        fdw.write('\n'.join(colours.get_lines()))
        fdw.write('\n'.join(result))


if __name__ == '__main__':
    main()