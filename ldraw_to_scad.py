#!/usr/bin/env python3

import os
import argparse
import queue

class Module():
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
        return self.get_module_code()

    def get_module_code(self):
        func_lines = ['  {}'.format(line) 
            for line in self.lines]

        return [
            "function {}() = concat(".format(self.get_module_name())
        ] + func_lines + [
            "[]);"
        ]


def colorfile(library_root):
    """ Translate color specifications. """
    coltxt = ('function ldraw_color(id, alt=false) = alt ?'
              ' ldraw_color_LDCfgalt(id) :'
              ' ldraw_color_LDConfig(id);\n')
    for colfile in ['LDConfig', 'LDCfgalt']:
        with open(os.path.join(library_root, colfile+'.ldr'),
                  encoding="utf-8", errors='replace') as filedata:
            lines = filedata.readlines()
        colors = [f'function ldraw_color_{colfile}(id) = (']
        for line in lines:
            params = line.split()
            if len(params) >= 2 and params[0] == '0' and \
               params[1] == '!COLOUR':
                data = {}
                if len(params) == 2:
                    print('!COLOUR line with no data!')
                data['name'] = params[2]
                skip = False
                for pos, opt in enumerate(params[3:]):
                    if skip:
                        skip = False
                        continue
                    if opt in ['CODE', 'VALUE', 'ALPHA', 'LUMINANCE', 'EDGE',
                               'SIZE', 'MINSIZE', 'MAXSIZE', 'FRACTION',
                               'VFRACTION', 'MATERIAL']:
                        data[opt] = params[pos+4]
                        skip = True
                    elif opt in ['METAL', 'RUBBER', 'PEARLESCENT', 'CHROME']:
                        data[opt] = True
                    else:
                        print(f'Unknown !COLOUR option {opt}!')
                colors.append(
                    f'(id=={data["CODE"]}) ? ["{data["VALUE"]}'
                    f'{(int(data["ALPHA"]) if "ALPHA" in data else 255):02X}'
                    f'","{data["EDGE"]}"] : (')
        colors.append('"UNKNOWN"'+')'*len(colors)+';')
        coltxt += '\n'.join(colors) + '\n'
    return coltxt


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
        var = {'ccw': True, 'invertnext': False, 'step': 0}
        result = []
        first_line = True
        for line in lines:
            if first_line and line.startswith("0 FILE"):
                if module.filename == "__main__":
                    continue
            first_line = False
            converted = self.convert_line(var, line)
            self.current_module.add_lines(converted)

    def get_module_lines(self, module_name):
        real_filename = self.find_part(module_name)
        with open(real_filename) as fd:
            lines = fd.readlines()
        return lines

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
                print("Main module lines is", len(main_module.lines))
                lines = self.get_module_lines(current_module.filename)
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
        with open('lib.scad') as fd:
            output_lines = [ colorfile(os.path.join('lib', 'ldraw')) +
                             ''.join(fd.readlines()) +
                             '\nmakepoly(n____main__());' ]
        [output_lines.extend(self.modules[module_name].get_lines())
            for module_name in completed]
        return output_lines

    def handle_type_0_line(self, var, rest):
        # Ignore NOFILE for now
        if rest.startswith("NOFILE"):
            return False, ""
        # Handle the file case
        if rest.startswith("FILE"):
            _, filename = rest.split()
            self.current_module = Module(filename=filename)
            module_name = Module.make_module_name(filename)
            self.modules[module_name] = self.current_module
            return True, ''
        if rest.startswith("BFC"):
            params = rest.split()
            for param in params[1:]:
                if param == 'CCW':
                    var['ccw'] = True
                elif param == 'CW':
                    var['ccw'] = False
                elif param == 'INVERTNEXT':
                    var['invertnext'] = True
            return False, ""
        if rest.startswith('STEP'):
            var['step'] += 1
            return False, ""

        return False, "// {}".format(rest)

    def handle_type_1_line(self, var, colour_index, x, y, z, a, b, c, d, e, f, g, h, i, filename):
        module_name = Module.make_module_name(filename)
        # Is this a new module?
        if module_name not in self.modules:
            # Create it
            self.modules[module_name] = Module(filename)
        # Add to deps
        self.current_module.dependancies.add(module_name)

        return [
                "line([1, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {},"
                " {}, {}(), {}, {}]),".format(
                    colour_index, x, y, z, a, b, c, d, e, f, g, h, i,
                    module_name, 'true' if var['invertnext'] else 'false',
                    var['step'])
        ]

    def convert_line(self, var, part_line, indent=0):
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
            var['invertnext'] = False
            is_new_module, data = self.handle_type_0_line(var, rest)
            if not is_new_module:
                result.append(data)
            else:
                var['ccw'] = True
        elif command == "1":
            try:
                result.extend(self.handle_type_1_line(var, *rest.split()))
            except TypeError:
                raise TypeError("Insufficient arguments in type 1 line", rest)
            var['invertnext'] = False
        elif command == "2":
            var['invertnext'] = False
            result.append(("line([{}, {}, {}]),").format(
                command, ', '.join(rest.split()[:7]),
                var['step']))
        elif command == "3":
            var['invertnext'] = False
            result.append("line([{}, {}, {}, {}]),".format(
                command, ', '.join(rest.split()[:10]),
                'true' if var['ccw'] else 'false',
                var['step']))
        elif command == "4":
            var['invertnext'] = False
            result.append("line([{}, {}, {}, {}]),".format(
                command, ', '.join(rest.split()[:13]),
                'true' if var['ccw'] else 'false',
                var['step']))
        elif command == "5":
            var['invertnext'] = False
            result.append(("line([{}, {}, {}]),").format(
                command, ', '.join(rest.split()[:13]),
                var['step']))
        if indent:
            indent_str = ''.join(' ' * indent)
            result = ['{i}{l}'.format(i=indent_str, l=line) for line in result]
        return result

    def index_library(self):
        """Create an index of all LDRAW library items.
        The index is a dictionary:
        {"part_prefix\\part_name": "real_file_name.dat"},
        eg:
        {"1.dat": }
        """
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
            '48' : os.path.join(library_root, 'p', '48'),
            '8' : os.path.join(library_root, 'p', '8')
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
    convert = LDrawConverter()
    with open(args.ldraw_file) as fd:
        result = convert.process_main(fd)
    with open(args.output_file, 'w') as fdw:
        fdw.write('\n'.join(result))


if __name__ == '__main__':
    main()
