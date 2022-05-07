from unittest import TestCase
import mock
import os

from ldraw_to_scad import LDrawConverter, Module

class TestModule(TestCase):
    def default_runner(self, filename='a_module'):
        return Module(filename=filename)

    def test_it_should_make_sensible_module_names(self):
        # Module names must be valid c identifiers - 
        # setup
        module_names_to_convert = [
            ["stud.dat", "n__stud"],
            ["s\\stuff.dat", "n__s__stuff"],
            ["4744.dat", "n__4744"],
            ["2-4cyli.dat", "n__2_4cyli"]
        ]
        # test
        # assert
        for item, expected in module_names_to_convert:
            self.assertEqual(Module.make_module_name(item), expected)

class TestFindPart(TestCase):
    def default_runner(self, module_filename="__main__"):
        module = Module(module_filename)
        return LDrawConverter(), module


    def test_it_should_be_able_to_find_part_path(self):
        # WARNING: This test requires having lib/ldraw setup.
        # setup
        #  part tests - name, expected location
        part_tests = [
            ['1.dat', os.path.join('lib', 'ldraw', 'parts', '1.dat')],
            ['4-4cyli.dat', os.path.join('lib', 'ldraw', 'p', '4-4cyli.dat')],
            ['s\\4744s01.dat', os.path.join('lib', 'ldraw', 'parts', 's', '4744s01.dat')]
        ]
        def listdir_mock(path):
            return {
                '.': ["simple_test.dat"],
                'lib/ldraw/parts': ['1.dat'],
                'lib/ldraw/p': ['4-4cyli.dat'],
                'lib/ldraw/p/48': [],
                'lib/ldraw/p/8': [],
                'lib/ldraw/parts/s': ['4744s01.dat']
            }[path]

        with mock.patch("os.listdir", listdir_mock):
            # Test
            converter, module = self.default_runner()
            converter.index_library()

        # Assert
        for part_name, expected_path in part_tests:
            self.assertEqual(converter.find_part(part_name), expected_path)


def find_part_mock(_, part_name):
    """Dummy find part - just returns itself"""
    return part_name


def colorfile_mock(library_root):
    """Dummy colorfile - just return empty file"""
    return ""

@mock.patch("ldraw_to_scad.LDrawConverter.find_part", find_part_mock)
@mock.patch("ldraw_to_scad.colorfile", colorfile_mock)
# @mock.patch("ldraw_to_scad.LDrawConverter.get_module_lines", mock.Mock(return_value=[]))
class TestLDrawConverter(TestCase):
    def default_runner(self, module_filename="__main__"):
        module = Module(module_filename)
        return LDrawConverter(), module

    def test_it_should_convert_comments(self):
        # setup
        part_lines_to_test =[
            ["0 Stud", "// Stud"],
            ["0", "// "]
        ]
        converter, module = self.default_runner()
        converter.current_module = module
        # Test
        # Assert
        for line, expected in part_lines_to_test:
            output_scad = converter.convert_line(line)
            self.assertEqual(output_scad, [expected])

    def test_it_should_convert_type_1_line_into_module_ref(self):
        # setup
        # This is a silly matrix - but the components are easy to pick out
        #      1 <colour> x  y  z  a  b  c  d  e  f  g  h  i <file>
        part_line = "1 16 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat"
        converter, module = self.default_runner()
        # Test
        converter.current_module = module
        result = converter.convert_line(part_line)
        # Assert
        print(module.dependancies)
        self.assertIn('n__simple_test', module.dependancies)
        self.assertEqual(result, [
            "[1, 16, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, n__simple_test()],"
        ])

    def test_it_should_render_type_2_line(self):
        # setup
        part_line = "2 24 40 96 -20 -40 96 -20"
        converter, module = self.default_runner()
        # test
        converter.current_module = module
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, ['[2, 24, 40, 96, -20, -40, 96, -20],'])
        # With indent
        output_scad = converter.convert_line(part_line, indent=2)
        # assert
        self.assertEqual(output_scad, ['  [2, 24, 40, 96, -20, -40, 96, -20],'])

    def test_it_should_render_type_3_tri(self):
        # setup
        part_line = "3 16 -2.017 -35.943 0 0 -35.942 -3.6 2.017 -35.943 0"
        converter, module = self.default_runner()
        # test
        converter.current_module = module
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [
            "[3, 16, -2.017, -35.943, 0, 0, -35.942, -3.6, 2.017, -35.943, 0],"
        ])
        # test with indent
        output_scad = converter.convert_line(part_line, indent=2)
        # assert
        self.assertEqual(output_scad, [
            "  [3, 16, -2.017, -35.943, 0, 0, -35.942, -3.6, 2.017, -35.943, 0],"
        ])

    def test_it_should_render_a_quad(self):
        # setup
        part_line = "4 16 1 1 0 0.9239 1 0.3827 0.9239 0 0.3827 1 0 0"
        converter, module = self.default_runner()
        # Test
        converter.current_module = module
        output_scad = converter.convert_line(part_line)
        # Assert
        self.assertEqual(output_scad, [
            "[4, 16, 1, 1, 0, 0.9239, 1, 0.3827, 0.9239, 0, 0.3827, 1, 0, 0],"
        ])

    def test_it_should_render_the_optional_line(self):
        # setup
        part_line = "5 24 0.7071 0 -0.7071 0.7071 1 -0.7071 0.9239 0 -0.3827 0.3827 0 -0.9239"
        # test
        converter, module = self.default_runner()
        converter.current_module = module
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [
            '[5, 24, 0.7071, 0, -0.7071, 0.7071, 1, -0.7071, 0.9239, 0, -0.3827, 0.3827, 0, -0.9239],'
        ])

    def test_multiple_lines(self):
        # setup
        lines = [
            "0 Cylinder 1.0",
            "0 Name: 4-4cyli.dat",
            "4 16 1 1 0 0.9239 1 0.3827 0.9239 0 0.3827 1 0 0",
            "5 24 1 0 0 1 1 0 0.9239 0 0.3827 0.9239 0 -0.3827",
            "4 16 0.9239 1 0.3827 0.7071 1 0.7071 0.7071 0 0.7071 0.9239 0 0.3827",
            "5 24 0.9239 0 0.3827 0.9239 1 0.3827 0.7071 0 0.7071 1 0 0",
            "4 16 0.7071 1 0.7071 0.3827 1 0.9239 0.3827 0 0.9239 0.7071 0 0.7071",
        ]
        # Test
        converter, module = self.default_runner()
        converter.process_lines(module, lines)
        # Assert
        self.assertEqual(module.lines, [
            "// Cylinder 1.0",
            "// Name: 4-4cyli.dat",
            "[4, 16, 1, 1, 0, 0.9239, 1, 0.3827, 0.9239, 0, 0.3827, 1, 0, 0],",
            "[5, 24, 1, 0, 0, 1, 1, 0, 0.9239, 0, 0.3827, 0.9239, 0, -0.3827],",
            "[4, 16, 0.9239, 1, 0.3827, 0.7071, 1, 0.7071, 0.7071, 0, 0.7071, 0.9239, 0, 0.3827],",
            "[5, 24, 0.9239, 0, 0.3827, 0.9239, 1, 0.3827, 0.7071, 0, 0.7071, 1, 0, 0],",
            "[4, 16, 0.7071, 1, 0.7071, 0.3827, 1, 0.9239, 0.3827, 0, 0.9239, 0.7071, 0, 0.7071],",
        ])

    def test_reading_file(self):
        # Setup
        test_file = "simple_test.dat"
        # test
        converter, _ = self.default_runner()
        with open(test_file) as fd:
            lines = fd.readlines()
        output = converter.process_main(lines)
        # assert
        self.assertEqual(output[1:], [
            "function n____main__() = [",
            "  // Simple Test File",
            "  // Name: simple_test.dat",
            '  [0,"BFC","CW"],',
            "  ",
            "  [4, 16, 1, 1, 1, 1, 1, -1, -1, 1, -1, -1, 1, 1],",
            "  ",
            "];"
        ])
    
    def test_it_process_type_1_line_into_module(self):
        # setup
        part_lines = ["1 16 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat"]
        converter, _ = self.default_runner()
        # test
        result = converter.process_main(part_lines)
        # assert
        self.assertListEqual(
            result[1:],
            [
                "function n__simple_test() = [",
                "  // Simple Test File",
                "  // Name: simple_test.dat",
                '  [0,"BFC","CW"],',
                "  ",
                "  [4, 16, 1, 1, 1, 1, 1, -1, -1, 1, -1, -1, 1, 1],",
                "  ",
                "];",
                "function n____main__() = [",
                "  [1, 16, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, n__simple_test()],",
                "];"
            ]
        )

    def test_multiple_lines_should_only_make_a_single_module_for_multiple_type_1_refs(self):
        # setup
        lines = [
            "1 16 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat",
            "1 16 2.5 2.4 2.3 2.2 2.1 2.0 1.9 1.8 1.7 1.6 1.5 1.4 simple_test.dat",
        ]
        # Test
        converter, _ = self.default_runner()
        result = converter.process_main(lines)
        # Assert
        self.assertEqual(result[1:], [
            "function n__simple_test() = [",
            "  // Simple Test File",
            "  // Name: simple_test.dat",
            '  [0,"BFC","CW"],',
            "  ",
            "  [4, 16, 1, 1, 1, 1, 1, -1, -1, 1, -1, -1, 1, 1],",
            "  ",
            "];",
            "function n____main__() = [",
            "  [1, 16, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, n__simple_test()],",
            "  [1, 16, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0, 1.9, 1.8, 1.7, 1.6, 1.5, 1.4, n__simple_test()],",
            "];"
        ])

    def test_try_simplest_mpd(self):
        # setup
        lines = [
            # 1 - ref the mpd
            "0 BFC CW",
            "1 16 225 224 223 222 221 220 219 218 217 216 215 214 mdr_inner.ldr",
            "0 NOFILE",
            "0 FILE mdr_inner.ldr",
            "0 BFC CW",
            "4 16 1 1 0 0.9239 1 0.3827 0.9239 0 0.3827 1 0 0",
            "0 NOFILE"
        ]
        # test
        converter, _ = self.default_runner()
        result = converter.process_main(lines)
        # assert
        self.assertEqual(result[1:], [
            "function n__mdr_inner() = [",
            '  [0,"BFC","CW"],',
            "  [4, 16, 1, 1, 0, 0.9239, 1, 0.3827, 0.9239, 0, 0.3827, 1, 0, 0],",
            "  ",
            "];",
            "function n____main__() = [",
            '  [0,"BFC","CW"],',
            "  [1, 16, 225, 224, 223, 222, 221, 220, 219, 218, 217, 216, 215, 214, n__mdr_inner()],",
            "  ",
            "];",
        ])

    def test_loading_an_mpd(self):
        # Setup
        mpd_filename = "mpd_test.dat"
        # Test
        converter, _ = self.default_runner()
        with open(mpd_filename) as fd:
            output = converter.process_main(fd)
        # Assert
        self.maxDiff = None
        self.assertListEqual(output[1:],
        [
            "function n__simple_test() = [",
            "  // Simple Test File",
            "  // Name: simple_test.dat",
            '  [0,"BFC","CW"],',
            "  ",
            "  [4, 16, 1, 1, 1, 1, 1, -1, -1, 1, -1, -1, 1, 1],",
            "  ",
            "];",
            "function n__mdr_inner() = [",
            '  [0,"BFC","CW"],',
            "  [1, 16, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, n__simple_test()],",
            "  ",
            "];",
            "function n____main__() = [",
            "  // Simple MPD File",
            "  // Name: mdp_test.dat",
            '  [0,"BFC","CW"],',
            "  ",
            "  [1, 16, 225, 224, 223, 222, 221, 220, 219, 218, 217, 216, 215, 214, n__mdr_inner()],",
            "  ",
            "  ",
            "];",
        ])
