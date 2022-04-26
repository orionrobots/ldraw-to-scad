from unittest import TestCase
import mock
import os

from ldraw_to_scad import LDrawConverter

class TestModule(TestCase):
    def default_runner(self):
        return LDrawConverter()

    def test_it_should_make_sensible_function_names(self):
        # Module names must be valid c identifiers - 
        # setup
        function_names_to_convert = [
            ["stud.dat", "ldraw_lib__stud()"],
            ["s\\stuff.dat", "ldraw_lib__s__stuff()"],
            ["4744.dat", "ldraw_lib__4744()"],
            ["2-4cyli.dat", "ldraw_lib__2_4cyli()"]
        ]
        # test
        # assert
        for item, expected in function_names_to_convert:
            self.assertEqual(LDrawConverter.make_function_name(item), expected)

def listdir_mock(path):
    return {
        '.': ["simple_test.dat"],
        'lib/ldraw/models': [],
        'lib/ldraw/parts': ['1.dat'],
        'lib/ldraw/p': ['4-4cyli.dat'],
        'lib/ldraw/p/48': [],
        'lib/ldraw/p/8': [],
        'lib/ldraw/parts/s': ['4744s01.dat']
    }[path]

class TestFindPart(TestCase):
    def default_runner(self):
        return LDrawConverter()


    def test_it_should_be_able_to_find_part_path(self):
        # WARNING: This test requires having lib/ldraw setup.
        # setup
        #  part tests - name, expected location
        part_tests = [
            ['1.dat', ('parts', '1')],
            ['4-4cyli.dat', ('p', '4-4cyli')],
            ['s\\4744s01.dat', (os.path.join('parts', 's'), '4744s01')]
        ]
        with mock.patch("os.listdir", listdir_mock):
            # Test
            converter = self.default_runner()

        # Assert
        for part_name, expected_path in part_tests:
            self.assertEqual(converter.find_part(part_name), expected_path)


def find_part_mock(_, part_name):
    """Dummy find part - just returns itself"""
    return ['.', os.path.splitext(part_name)[0]]


def colorfile_mock(_, library_root):
    """Dummy colorfile - just return empty file"""
    return ""

@mock.patch("os.listdir", listdir_mock)
@mock.patch("ldraw_to_scad.LDrawConverter.find_part", find_part_mock)
@mock.patch("ldraw_to_scad.LDrawConverter.colorfile", colorfile_mock)
# @mock.patch("ldraw_to_scad.LDrawConverter.get_function_lines", mock.Mock(return_value=[]))
class TestLDrawConverter(TestCase):
    def default_runner(self, commented=True):
        return LDrawConverter(commented=commented)

    def test_it_should_convert_comments(self):
        # setup
        part_lines_to_test =[
            ["0 Stud", "// 0 Stud"],
            ["0", "// 0"]
        ]
        converter = self.default_runner()
        # Test
        # Assert
        for line, expected in part_lines_to_test:
            output_scad = converter.convert_line(line)
            self.assertEqual(output_scad, [expected])

    def test_it_should_convert_type_1_line_into_function_ref(self):
        # setup
        # This is a silly matrix - but the components are easy to pick out
        #      1 <colour> x  y  z  a  b  c  d  e  f  g  h  i <file>
        part_line = "1 16 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat"
        converter = self.default_runner(commented=False)
        converter.filedep = [set(), set()]
        # Test
        result = converter.convert_line(part_line)
        # Assert
        print(converter.filedep[0])
        self.assertIn('simple_test.dat', converter.filedep[0])
        self.assertEqual(result, [
            "  [1,16,25,24,23,22,21,20,19,18,17,16,15,14, ldraw_lib__simple_test()],"
        ])

    def test_it_should_render_type_2_line(self):
        # setup
        part_line = "2 24 40 96 -20 -40 96 -20"
        converter = self.default_runner(commented=False)
        # test
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [
            "  [2,24,40,96,-20,-40,96,-20],"
        ])

    def test_it_should_render_type_3_tri(self):
        # setup
        part_line = "3 16 -2.017 -35.943 0 0 -35.942 -3.6 2.017 -35.943 0"
        converter = self.default_runner(commented=False)
        # test
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [
            "  [3,16,-2.017,-35.943,0,0,-35.942,-3.6,2.017,-35.943,0],"
        ])

    def test_it_should_render_a_quad(self):
        # setup
        part_line = "4 16 1 1 0 0.9239 1 0.3827 0.9239 0 0.3827 1 0 0"
        converter = self.default_runner(commented=False)
        # Test
        output_scad = converter.convert_line(part_line)
        # Assert
        self.assertEqual(output_scad, [
            "  [4,16,1,1,0,0.9239,1,0.3827,0.9239,0,0.3827,1,0,0],"
        ])

    def test_it_should_render_the_optional_line(self):
        # setup
        part_line = "5 24 0.7071 0 -0.7071 0.7071 1 -0.7071 0.9239 0 -0.3827 0.3827 0 -0.9239"
        # test
        converter = self.default_runner(commented=False)
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [
            '  [5,24,0.7071,0,-0.7071,0.7071,1,-0.7071,0.9239,0,-0.3827,0.3827,0,-0.9239],'
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
        converter = self.default_runner()
        result = converter.process_lines('__main__', '/', lines)
        # Assert
        self.assertEqual(result, [
            "use <openscad/lib.scad>",
            "function ldraw_lib____main__() = [",
            "// 0 Cylinder 1.0",
            "// 0 Name: 4-4cyli.dat",
            "// 4 16 1 1 0 0.9239 1 0.3827 0.9239 0 0.3827 1 0 0",
            "  [4,16,1,1,0,0.9239,1,0.3827,0.9239,0,0.3827,1,0,0],",
            "// 5 24 1 0 0 1 1 0 0.9239 0 0.3827 0.9239 0 -0.3827",
            "  [5,24,1,0,0,1,1,0,0.9239,0,0.3827,0.9239,0,-0.3827],",
            "// 4 16 0.9239 1 0.3827 0.7071 1 0.7071 0.7071 0 0.7071 0.9239 0 0.3827",
            "  [4,16,0.9239,1,0.3827,0.7071,1,0.7071,0.7071,0,0.7071,0.9239,0,0.3827],",
            "// 5 24 0.9239 0 0.3827 0.9239 1 0.3827 0.7071 0 0.7071 1 0 0",
            "  [5,24,0.9239,0,0.3827,0.9239,1,0.3827,0.7071,0,0.7071,1,0,0],",
            "// 4 16 0.7071 1 0.7071 0.3827 1 0.9239 0.3827 0 0.9239 0.7071 0 0.7071",
            "  [4,16,0.7071,1,0.7071,0.3827,1,0.9239,0.3827,0,0.9239,0.7071,0,0.7071],",
            "];",
            "makepoly(ldraw_lib____main__(), line=0.2);"
        ])

    def test_reading_file(self):
        # Setup
        test_file = "simple_test.dat"
        # test
        converter = self.default_runner()
        with open(test_file) as fd:
            lines = fd.readlines()
        output = converter.process_lines('__main__', '/', lines)
        # assert
        self.assertEqual(output, [
            "use <openscad/lib.scad>",
            "function ldraw_lib____main__() = [",
            "// 0 Simple Test File",
            "// 0 Name: simple_test.dat",
            "// 0 BFC CW",
            '  [0,"BFC","CW"],',
            "// ",
            "// 4 16  1 1  1  1 1 -1 -1 1 -1 -1 1  1",
            "  [4,16,1,1,1,1,1,-1,-1,1,-1,-1,1,1],",
            "// ",
            "];",
            "makepoly(ldraw_lib____main__(), line=0.2);"
        ])
    
    def test_it_process_type_1_line_into_function(self):
        # setup
        part_lines = ["1 16 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat"]
        converter = self.default_runner(commented=False)
        # test
        result = converter.process_lines('__main__', '/', part_lines)
        # assert
        self.assertListEqual(
            result,
            [
                "use <openscad/lib.scad>",
                "use <openscad/./simple_test.scad>",
                "function ldraw_lib____main__() = [",
                "  [1,16,25,24,23,22,21,20,19,18,17,16,15,14, ldraw_lib__simple_test()],",
                "];",
                "makepoly(ldraw_lib____main__(), line=0.2);"
            ]
        )

    def test_multiple_lines_should_only_make_a_single_function_for_multiple_type_1_refs(self):
        # setup
        lines = [
            "1 16 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat",
            "1 16 2.5 2.4 2.3 2.2 2.1 2.0 1.9 1.8 1.7 1.6 1.5 1.4 simple_test.dat",
        ]
        # Test
        converter = self.default_runner(commented=False)
        result = converter.process_lines('__main__', '/', lines)
        # Assert
        self.assertEqual(result, [
            "use <openscad/lib.scad>",
            "use <openscad/./simple_test.scad>",
            "function ldraw_lib____main__() = [",
            "  [1,16,25,24,23,22,21,20,19,18,17,16,15,14, ldraw_lib__simple_test()],",
            "  [1,16,2.5,2.4,2.3,2.2,2.1,2.0,1.9,1.8,1.7,1.6,1.5,1.4, ldraw_lib__simple_test()],",
            "];",
            "makepoly(ldraw_lib____main__(), line=0.2);"
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
        converter = self.default_runner(commented=False)
        result = converter.process_lines('__main__', '/', lines)
        # assert
        self.assertEqual(result, [
            "use <openscad/lib.scad>",
            "function ldraw_lib____main__() = [",
            '  [0,"BFC","CW"],',
            "  [1,16,225,224,223,222,221,220,219,218,217,216,215,214, ldraw_lib__mdr_inner()],",
            "];",
            "function ldraw_lib__dummy_1() = [",
            "];",
            "function ldraw_lib__mdr_inner() = [",
            '  [0,"BFC","CW"],',
            "  [4,16,1,1,0,0.9239,1,0.3827,0.9239,0,0.3827,1,0,0],",
            "];",
            "function ldraw_lib__dummy_2() = [",
            "];",
            "makepoly(ldraw_lib____main__(), line=0.2);"
        ])

    def test_loading_an_mpd(self):
        # Setup
        mpd_filename = "mpd_test.dat"
        # Test
        converter = self.default_runner()
        with open(mpd_filename) as fd:
            lines = fd.readlines()
        output = converter.process_lines('__main__', '/', lines)
        # Assert
        self.maxDiff = None
        self.assertListEqual(output,
        [
            "use <openscad/lib.scad>",
            "use <openscad/./simple_test.scad>",
            "function ldraw_lib____main__() = [",
            "// 0 FILE mdp_test.dat",
            "// 0 Simple MPD File",
            "// 0 Name: mdp_test.dat",
            "// 0 BFC CW",
            '  [0,"BFC","CW"],',
            "// ",
            "// 1 16 225 224 223 222 221 220 219 218 217 216 215 214 mdr_inner.ldr",
            "  [1,16,225,224,223,222,221,220,219,218,217,216,215,214, ldraw_lib__mdr_inner()],",
            "// ",
            "// 0 NOFILE",
            "];",
            "function ldraw_lib__dummy_1() = [",
            "// 0 FILE mdr_inner.ldr",
            "];",
            "function ldraw_lib__mdr_inner() = [",
            "// 0 BFC CW",
            '  [0,"BFC","CW"],',
            "// 1 16 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat",
            "  [1,16,25,24,23,22,21,20,19,18,17,16,15,14, ldraw_lib__simple_test()],",
            "// 0 NOFILE",
            "];",
            "function ldraw_lib__dummy_2() = [",
            "];",
            "makepoly(ldraw_lib____main__(), line=0.2);",
            "function ldraw_lib__mdp_test() = ldraw_lib____main__();\n"
        ])
