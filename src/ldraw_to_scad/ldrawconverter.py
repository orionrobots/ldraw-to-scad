#!/usr/bin/env python3

""" Translate LDraw library or file to OpenSCAD library or file. """

import os
import importlib_resources


class LDrawConverter:
    """ Convert LDraw files to OpenSCAD """

    def __init__(self, libdir=os.path.join('lib', 'ldraw')):
        self.queue = ({}, set())
        self.filedep = None
        self.settings = {
            'library_root': libdir,
            'scadlibs': '.',
            'scadlibname': 'LDraw',
            'selfcontained': None,
            'line': 0.2,
            'commented': True}
        self.mpd_main = None
        self.index = self.index_library()

    def set(self, key, value):
        """ change a setting """
        self.settings[key] = value

    def colorfile(self):
        """ Translate color specifications. """
        coltxt = ('function ldraw_color(id, alt=false) = alt ?'
                  ' ldraw_color_LDCfgalt(id) :'
                  ' ldraw_color_LDConfig(id);\n')
        for colfile in ['LDConfig', 'LDCfgalt']:
            with open(os.path.join(self.settings['library_root'],
                                   colfile+'.ldr'),
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
                                   'EDGE']:
                            data[opt] = params[pos+4]
                            skip = True
                        elif opt in ['METAL', 'RUBBER', 'PEARLESCENT',
                                     'CHROME', 'MATTE_METALLIC']:
                            data[opt] = True
                        elif opt == 'MATERIAL':
                            data[opt] = params[pos+1:]
                            break
                        else:
                            print(f'Unknown !COLOUR option {opt}!')
                    alpha = int(data["ALPHA"]) if "ALPHA" in data else 255
                    colors.append(
                        f'(id=={data["CODE"]}) ? ["{data["VALUE"]}{alpha:02X}'
                        f'","{data["EDGE"]}"] : (')
            colors.append('(id>=2*16^6) ? [chr(35, [for (i=[5:-1:0])'
                          'let(n=floor(id/16^i)%16) n+(n<10?48:55)]),'
                          'chr(35, [for (i=[5:-1:0])'
                          'let(n=15-floor(id/16^i)%16) n+(n<10?48:55)])] :'
                          '"UNKNOWN"'+')'*len(colors)+';')
            coltxt += '\n'.join(colors) + '\n'
        return coltxt

    def index_library(self):
        """ Index the whole library. """
        index = {}
        for sub_path in ['models', 'parts', 'p']:
            whole_path = os.path.join(self.settings['library_root'], sub_path)
            for item in os.listdir(whole_path):
                if item.endswith('.dat'):
                    index[item] = (sub_path, os.path.splitext(item)[0])
        special_subs = {
            's': os.path.join('parts', 's'),
            '48': os.path.join('p', '48'),
            '8': os.path.join('p', '8')
        }
        for prefix, s_path in special_subs.items():
            for item in os.listdir(os.path.join(self.settings['library_root'],
                                                s_path)):
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
        lfunction = function.lower()
        self.filedep[1].add(lfunction)
        self.filedep[0].discard(lfunction)
        return first

    def get_dummy(self):
        """ get a name for a dummy function """
        cnt = 1
        while f'DUMMY_{cnt}' in self.filedep[1]:
            cnt += 1
        name = f'DUMMY_{cnt}'
        self.filedep[1].add(name)
        return name

    def add_dep(self, function):
        """ add a dependency """
        lfunction = function.lower()
        if lfunction not in self.filedep[1]:
            self.filedep[0].add(lfunction)

    def get_deps(self):
        """ get dependencies """
        return self.filedep[0]

    @staticmethod
    def make_function_name(name):
        """ Calculate OpenSCAD name from LDraw name. """
        function_name = name.lower().split('.', 1)[0]
        function_name = function_name.replace('\\', '__').replace('-', '_').\
            replace('+', '_').replace(' ', '_').replace('#', '_')
        return 'ldraw_lib__' + function_name

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
                result.append(f"function {intfile_name}() = [")
        if len(params) >= 2 and params[1] == 'NOFILE':
            intfile = self.get_dummy()
            result.append("];")
            intfile_name = LDrawConverter.make_function_name(intfile)
            result.append(f"function {intfile_name}() = [")

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
            keyname = params[14].replace('/', '\\')
            self.add_dep(keyname)
            if params[1][0:3] == '0x2':
                params[1] = str(int(params[1], 0))
            result.append(
                f"  [{','.join(params[:14])}, "
                f"{LDrawConverter.make_function_name(keyname)}()],")
        elif params[0] in ["2", "3", "4", "5"]:
            if params[1][0:3] == '0x2':
                params[1] = str(int(params[1], 0))
            outparams = params[:{'2': 8, '3': 11, '4': 14, '5': 14}[params[0]]]
            result.append(f"  [{','.join(outparams)}],")
        return result

    def include(self, comp, path):
        """ Generate use statement. """
        relpath = (
            os.path.join(self.settings['scadlibname'], *comp) if path == '/'
            else os.path.relpath(os.path.join(*comp), path))
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
            result = [f"function {function_name}() = ["] + result + ["];"]
        else:
            result = [self.include(['lib'], path)] + \
                     [self.include(self.find_part(name), path)
                      for name in sorted(self.get_deps())] + \
                     [f"function {function_name}() = ["] + result + ["];"] + \
                     [f"module {function_name}(step=0, col=false, unit=2/5, "
                      f"alt=false, line=0.2, solid=!$preview)"] + \
                     [f"    makepoly({function_name}(), step=step, col=col, "
                      f"unit=unit, alt=alt, line=line, solid=solid);"] + \
                     [f"{function_name}(line={self.settings['line']});"]
        if self.mpd_main and self.mpd_main != name:
            main_function = LDrawConverter.make_function_name(self.mpd_main)
            result.append(f"function {main_function}() = {function_name}();")
            result.append(f"module {main_function}(step=0, col=false, "
                          f"unit=2/5, alt=false, line=0.2, solid=!$preview)")
            result.append(f"    {function_name}(step=step, col=col, "
                          f"unit=unit, alt=alt, line=line, solid=solid);")
        return result

    def enqueue(self, name, path=None, ldrfile=None, scadfile=None):
        """ enqueue a file to be processed """
        if name not in self.queue[1]:
            lpath = None
            base = None
            if not ldrfile:
                lpath, base = self.find_part(name)
            self.queue[0][name] = (
                path if path else lpath,
                (ldrfile if ldrfile else
                 os.path.join(self.settings['library_root'], lpath, base) +
                 ('.dat' if lpath != 'models' else '.ldr')),
                (scadfile if scadfile else
                 os.path.join(self.settings['scadlibs'],
                              self.settings['scadlibname'],
                              lpath, base) + '.scad'))

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
        self.queue[1].clear()

    def convert_lib(self, self_contained=False):
        """ Convert the whole library """
        for name in self.index:
            self.enqueue(name)
        libref = importlib_resources.files(__name__) / 'lib.scad'
        if self_contained:
            with open(os.path.join(self.settings['scadlibs'],
                                   self.settings['scadlibname']+'.scad'),
                      'w', encoding="utf-8") as fdw:
                self.settings['selfcontained'] = fdw
                fdw.write(self.colorfile())
                with importlib_resources.as_file(libref) as libpath:
                    with open(libpath, encoding="utf-8") as filedata:
                        lines = filedata.readlines()
                fdw.write(''.join(lines))
                self.process_queue()
        else:
            os.makedirs(os.path.join(self.settings['scadlibs'],
                                     self.settings['scadlibname']),
                        exist_ok=True)
            with importlib_resources.as_file(libref) as libpath:
                with open(libpath, encoding="utf-8") as filedata:
                    lines = filedata.readlines()
            with open(os.path.join(self.settings['scadlibs'],
                                   self.settings['scadlibname'], 'lib.scad'),
                      'w', encoding="utf-8") as fdw:
                fdw.write('use <colors.scad>\n')
                fdw.write(''.join(lines))
            with open(os.path.join(self.settings['scadlibs'],
                                   self.settings['scadlibname'],
                                   'colors.scad'),
                      'w', encoding="utf-8") as fdw:
                fdw.write(self.colorfile())
            self.process_queue()

    def convert_file(self, ldrfile, scadfile, self_contained=False):
        """ Convert a single file """
        self.enqueue('__main__', '/', ldrfile, scadfile)
        if self_contained:
            with open(scadfile, 'w', encoding="utf-8") as fdw:
                self.settings['selfcontained'] = fdw
                fdw.write(self.colorfile())
                libref = importlib_resources.files(__name__) / 'lib.scad'
                with importlib_resources.as_file(libref) as libpath:
                    with open(libpath, encoding="utf-8") as filedata:
                        lines = filedata.readlines()
                fdw.write(''.join(lines))
                fdw.write('makepoly(ldraw_lib____main__(), '
                          f"line={self.settings['line']});\n")
                self.process_queue()
        else:
            self.process_queue()
