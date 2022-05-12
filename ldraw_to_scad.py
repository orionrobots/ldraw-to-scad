#!/usr/bin/env python3

""" Translate LDraw library or file to OpenSCAD library or file. """

import os
import argparse


class LDrawConverter:
    """ Convert LDraw files to OpenSCAD """

    def __init__(self, line=0.2, commented=True):
        self.library_root = os.path.join('lib', 'ldraw')
        self.index = self.index_library()
        self.queue = ({}, set())
        self.filedep = None
        self.settings = {
            'selfcontained': None,
            'line': line,
            'commented': commented}
        self.mpd_main = None

    def colorfile(self):
        """ Translate color specifications. """
        coltxt = ('function ldraw_color(id, alt=false) = alt ?'
                  ' ldraw_color_LDCfgalt(id) :'
                  ' ldraw_color_LDConfig(id);\n')
        for colfile in ['LDConfig', 'LDCfgalt']:
            with open(os.path.join(self.library_root, colfile+'.ldr'),
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
                        if opt in ['CODE', 'VALUE', 'ALPHA', 'LUMINANCE',
                                   'EDGE', 'SIZE', 'MINSIZE', 'MAXSIZE',
                                   'FRACTION', 'VFRACTION', 'MATERIAL']:
                            data[opt] = params[pos+4]
                            skip = True
                        elif opt in ['METAL', 'RUBBER', 'PEARLESCENT',
                                     'CHROME']:
                            data[opt] = True
                        else:
                            print(f'Unknown !COLOUR option {opt}!')
                    alpha = int(data["ALPHA"]) if "ALPHA" in data else 255
                    colors.append(
                        f'(id=={data["CODE"]}) ? ["{data["VALUE"]}{alpha:02X}'
                        f'","{data["EDGE"]}"] : (')
            colors.append('"UNKNOWN"'+')'*len(colors)+';')
            coltxt += '\n'.join(colors) + '\n'
        return coltxt

    def index_library(self):
        """ Index the whole library. """
        index = {}
        for sub_path in ['models', 'parts', 'p']:
            whole_path = os.path.join(self.library_root, sub_path)
            for item in os.listdir(whole_path):
                if item.endswith('.dat'):
                    index[item] = (sub_path, os.path.splitext(item)[0])
        special_subs = {
            's': os.path.join('parts', 's'),
            '48': os.path.join('p', '48'),
            '8': os.path.join('p', '8')
        }
        for prefix, s_path in special_subs.items():
            for item in os.listdir(os.path.join(self.library_root, s_path)):
                if item.endswith('.dat'):
                    index[prefix + '\\'+item] = (s_path,
                                                 os.path.splitext(item)[0])
        return index

    def find_part(self, part_name):
        """ Find a part in the library. """
        try:
            filename = self.index[part_name]
        except KeyError:
            filename = self.index[part_name.lower()]
        return filename

    def implement_function(self, function):
        """ register implementation of a function """
        first = not self.filedep[1]
        self.filedep[1].add(function)
        self.filedep[0].discard(function)
        return first

    def get_dummy(self):
        """ get a name for a dummy function """
        cnt = 1
        while f'DUMMY_{cnt}' in self.filedep[1]:
            cnt += 1
        name = f'DUMMY_{cnt}'
        self.implement_function(name)
        return name

    def add_dep(self, function):
        """ add a dependency """
        if function not in self.filedep[1]:
            self.filedep[0].add(function)

    def get_deps(self):
        """ get dependencies """
        return self.filedep[0]

    @staticmethod
    def make_function_name(name):
        """ Calculate OpenSCAD name from LDraw name. """
        function_name = name.lower().split('.', 1)[0]
        function_name = function_name.replace('\\', '__').replace('-', '_').\
            replace(' ', '_')
        return 'ldraw_lib__' + function_name + '()'

    def convert_line_0(self, result, params, stripped):
        """ Translate a '0' line. """
        if len(params) >= 2 and params[1] == 'BFC':
            for bfc in params[2:]:
                result.append(f'  [0,"BFC","{bfc}"],')
        if len(params) >= 2 and params[1] == 'STEP':
            result.append('  [0,"STEP"],')
        if len(params) >= 2 and params[1] == 'FILE':
            intfile = stripped.split(maxsplit=2)[2]
            if self.implement_function(intfile):
                self.mpd_main = intfile
            else:
                result.append("];")
                intfile_name = LDrawConverter.make_function_name(intfile)
                result.append(f"function {intfile_name} = [")
        if len(params) >= 2 and params[1] == 'NOFILE':
            intfile = self.get_dummy()
            result.append("];")
            intfile_name = LDrawConverter.make_function_name(intfile)
            result.append(f"function {intfile_name} = [")

    def convert_line(self, part_line):
        """ Translate a single line. """
        stripped = part_line.rstrip()
        result = [f"// {stripped}"] if self.settings['commented'] else []
        params = stripped.split(maxsplit=14)
        if not params:
            return result
        if params[0] == "0":
            self.convert_line_0(result, params, stripped)
        elif params[0] == "1":
            self.add_dep(params[14])
            result.append(
                f"  [{','.join(params[:14])}, "
                f"{LDrawConverter.make_function_name(params[14])}],")
        elif params[0] in ["2", "3", "4", "5"]:
            outparams = params[:{'2': 8, '3': 11, '4': 14, '5': 14}[params[0]]]
            result.append(f"  [{','.join(outparams)}],")
        return result

    @staticmethod
    def include(comp, path):
        """ Generate use statement. """
        relpath = (
            os.path.join('openscad', *comp) if path == '/' else
            os.path.relpath(os.path.join(*comp), path))
        return f'use <{relpath}.scad>'

    def process_lines(self, name, path, lines):
        """ Translate all lines of a file. """
        self.filedep = (set(), set())
        self.mpd_main = None
        result = []
        for line in lines:
            result.extend(self.convert_line(line))
        function_name = LDrawConverter.make_function_name(name)
        if self.settings['selfcontained']:
            for file in self.get_deps():
                self.enqueue(file, path)
            result = [f"function {function_name} = ["] + result + ["];"]
        else:
            result = [LDrawConverter.include(['lib'], path)] + \
                     [LDrawConverter.include(self.find_part(name), path)
                      for name in sorted(self.get_deps())] + \
                     [f"function {function_name} = ["] + result + ["];"] + \
                     [f"makepoly({function_name}, "
                      f"line={self.settings['line']});"]
        if self.mpd_main and self.mpd_main != name:
            main_function = LDrawConverter.make_function_name(self.mpd_main)
            result.append(f"function {main_function} = {function_name};\n")
        return result

    def enqueue(self, name, path=None, ldrfile=None, scadfile=None):
        """ enqueue a file to be processed """
        if name not in self.queue[1]:
            if not ldrfile:
                lpath, base = self.find_part(name)
            self.queue[0][name] = (
                path if path else lpath,
                (ldrfile if ldrfile else
                 os.path.join(self.library_root, lpath, base) +
                 ('.dat' if lpath != 'models' else '.ldr')),
                (scadfile if scadfile else
                 os.path.join('openscad', lpath, base) + '.scad'))

    def process_queue(self):
        """ process enqueued files """
        while self.queue[0]:
            name = sorted(self.queue[0].keys())[0]
            path, ldrfile, scadfile = self.queue[0].pop(name)
            self.queue[1].add(name)
            with open(ldrfile, encoding="utf-8", errors='replace') as filedata:
                lines = filedata.readlines()
            result = '\n'.join(self.process_lines(name, path, lines))
            if self.settings['selfcontained']:
                self.settings['selfcontained'].write(result)
            else:
                scaddir = os.path.dirname(scadfile)
                if scaddir:
                    os.makedirs(os.path.dirname(scadfile), exist_ok=True)
                with open(scadfile, 'w', encoding="utf-8") as fdw:
                    fdw.write(result)

    def convert_lib(self, selfcontained=False):
        """ Convert the whole library """
        for name in self.index:
            self.enqueue(name)
        if selfcontained:
            with open('openscad.scad', 'w', encoding="utf-8") as fdw:
                self.settings['selfcontained'] = fdw
                fdw.write(self.colorfile())
                with open('lib.scad', encoding="utf-8") as filedata:
                    lines = filedata.readlines()
                fdw.write(''.join(lines))
                self.process_queue()
        else:
            os.makedirs('openscad', exist_ok=True)
            with open('lib.scad', encoding="utf-8") as filedata:
                lines = filedata.readlines()
            with open(os.path.join('openscad', 'lib.scad'), 'w',
                      encoding="utf-8") as fdw:
                fdw.write('use <colors.scad>\n')
                fdw.write(''.join(lines))
            with open(os.path.join('openscad', 'colors.scad'), 'w',
                      encoding="utf-8") as fdw:
                fdw.write(self.colorfile())
            self.process_queue()

    def convert_file(self, ldrfile, scadfile, selfcontained=False):
        """ Convert a single file """
        self.enqueue('__main__', '/', ldrfile, scadfile)
        if selfcontained:
            with open(scadfile, 'w', encoding="utf-8") as fdw:
                self.settings['selfcontained'] = fdw
                fdw.write(self.colorfile())
                with open('lib.scad', encoding="utf-8") as filedata:
                    lines = filedata.readlines()
                fdw.write(''.join(lines))
                fdw.write('makepoly(ldraw_lib____main__(), '
                          f"line={self.settings['line']});\n")
                self.process_queue()
        else:
            self.process_queue()


def main():
    """ Main function """
    parser = argparse.ArgumentParser(
        description='Convert an LDraw part to OpenSCAD')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-l', '--library', action='store_true',
        help='translate the library')
    parser.add_argument(
        '-s', '--selfcontained', action='store_true',
        help='create self-contained files')
    parser.add_argument(
        '-u', '--uncommented', action='store_true',
        help='create uncommented files')
    group.add_argument('ldraw_file', nargs='?', metavar='FILENAME',
                       help='source file to translate')
    parser.add_argument('output_file', nargs='?', metavar='OUTPUT_FILENAME',
                        help='name of the translated file')
    parser.add_argument(
        '--line', default=0.2, type=float, metavar='LINE_WIDTH',
        help='width of lines, 0 for no lines')
    args = parser.parse_args()
    converter = LDrawConverter(line=args.line, commented=not args.uncommented)
    if args.library:
        print("Translating library...")
        converter.convert_lib(args.selfcontained)
    else:
        scadfile = args.output_file if args.output_file else \
                   os.path.splitext(args.ldraw_file)[0] + '.scad'
        print(f"Translating {args.ldraw_file} to {scadfile}...")
        converter.convert_file(args.ldraw_file, scadfile, args.selfcontained)


if __name__ == '__main__':
    main()
