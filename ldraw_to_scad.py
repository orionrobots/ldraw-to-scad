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
        bfc = {'ccw': True, 'invertnext': False}
        result = []
        first_line = True
        for line in lines:
            if first_line and line.startswith("0 FILE"):
                if module.filename == "__main__":
                    continue
            first_line = False
            converted = self.convert_line(bfc, line)
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
        output_lines = ["""
/* general data structure:
      array of
          vectors of
              array of points (face)
              color index
*/

/* makepoly: convert data structure to colored 3d object

   For each face color a polyhedron with a single face
   constructed by the array of points in clockwise
   direction.
*/
module makepoly(poly)
    for(f=poly)
        color(lego_colours[f[1]])
            polyhedron(f[0], [[for(i=[0:1:len(f[0])-1]) i]]);

/* det3: calculate the determinant of a 3x3 matrix */
function det3(M) = + M[0][0] * M[1][1] * M[2][2]
                   + M[0][1] * M[1][2] * M[2][0]
                   + M[0][2] * M[1][0] * M[2][1]
                   - M[0][2] * M[1][1] * M[2][0]
                   - M[0][1] * M[1][0] * M[2][2]
                   - M[0][0] * M[1][2] * M[2][1];

/* l1: transform the subpart according to a line 1 specification
   For each face:
       Transform the array of points by matrix multiplication.
       Reverse the face direction if:
           - determinant of the non-absolute
             3x3 matrix part is negative
           - requested by BFC INVERTNEXT
       Replace the face color with the specified one if the
           original color was 16.
*/
function l1(M, poly, col, invert) =
    [for(f=poly) [
        rev([for(p=f[0]) M * [p.x, p.y, p.z, 1]],
            det3(M)<0 != invert),
        (f[1] == 16) ? col : f[1]
    ]];

/* rev: reverse an array if condition c is true */
function rev(v, c=true) = c ? [for(i=[1:len(v)]) v[len(v) - i]] : v;

/* line: construct data structure according to specification */
function line(v) =
    (v[0] == 1) ?
        l1([[v[ 5], v[ 6], v[ 7], v[2]],
            [v[ 8], v[ 9], v[10], v[3]],
            [v[11], v[12], v[13], v[4]]],
           v[14], v[1], (len(v)>15) ? v[15] : false) : (
    (v[0] == 3) ?
        [[rev([[v[ 2], v[ 3], v[ 4]],
               [v[ 5], v[ 6], v[ 7]],
               [v[ 8], v[ 9], v[10]]],
              (len(v)>11) ? v[11] : true), v[1]]] : (
    (v[0] == 4) ?
        [[rev([[v[ 2], v[ 3], v[ 4]],
               [v[ 5], v[ 6], v[ 7]],
               [v[ 8], v[ 9], v[10]],
               [v[11], v[12], v[13]]],
              (len(v)>14) ? v[14] : true), v[1]]] : []));

makepoly(n____main__());
        """]
        [output_lines.extend(self.modules[module_name].get_lines())
            for module_name in completed]
        return output_lines

    def handle_type_0_line(self, bfc, rest):
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
                    bfc['ccw'] = True
                elif param == 'CW':
                    bfc['ccw'] = False
                elif param == 'INVERTNEXT':
                    bfc['invertnext'] = True
            return False, ""

        return False, "// {}".format(rest)

    def handle_type_1_line(self, bfc, colour_index, x, y, z, a, b, c, d, e, f, g, h, i, filename):
        module_name = Module.make_module_name(filename)
        # Is this a new module?
        if module_name not in self.modules:
            # Create it
            self.modules[module_name] = Module(filename)
        # Add to deps
        self.current_module.dependancies.add(module_name)

        return [
                "line([1, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {},"
                " {}, {}(), {}]),".format(
                    colour_index, x, y, z, a, b, c, d, e, f, g, h, i,
                    module_name, 'true' if bfc['invertnext'] else 'false')
        ]

    def convert_line(self, bfc, part_line, indent=0):
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
            bfc['invertnext'] = False
            is_new_module, data = self.handle_type_0_line(bfc, rest)
            if not is_new_module:
                result.append(data)
            else:
                bfc['ccw'] = True
        elif command == "1":
            try:
                result.extend(self.handle_type_1_line(bfc, *rest.split()))
            except TypeError:
                raise TypeError("Insufficient arguments in type 1 line", rest)
            bfc['invertnext'] = False
        elif command == "3":
            bfc['invertnext'] = False
            result.append("line([{}, {}, {}]),".format(
                command, ', '.join(rest.split()[:10]),
                'true' if bfc['ccw'] else 'false'))
        elif command == "4":
            bfc['invertnext'] = False
            result.append("line([{}, {}, {}]),".format(
                command, ', '.join(rest.split()[:13]),
                'true' if bfc['ccw'] else 'false'))
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
