""" test cases for ldraw_to_scad.py """

from unittest import TestCase
import os
import mock

from ldraw_to_scad import LDrawConverter


class TestModule(TestCase):
    """ tests for generation of function names """
    def test_it_should_make_sensible_function_names(self):
        """ Module names must be valid c identifiers """
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
    """ mock the listdir function """
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
    """ tests for finding parts in the index """
    def test_it_should_be_able_to_find_part_path(self):
        """ test that find_part() finds the location of parts """
        # setup
        #  part tests - name, expected location
        part_tests = [
            ['1.dat', ('parts', '1')],
            ['4-4cyli.dat', ('p', '4-4cyli')],
            ['s\\4744s01.dat', (os.path.join('parts', 's'), '4744s01')]
        ]
        with mock.patch("os.listdir", listdir_mock):
            # Test
            converter = LDrawConverter()

        # Assert
        for part_name, expected_path in part_tests:
            self.assertEqual(converter.find_part(part_name), expected_path)


def find_part_mock(_, part_name):
    """Dummy find part - just returns itself"""
    return ['.', os.path.splitext(part_name)[0]]


def colorfile_mock(_, _library_root):
    """Dummy colorfile - just return empty file"""
    return ""


@mock.patch("os.listdir", listdir_mock)
@mock.patch("ldraw_to_scad.LDrawConverter.find_part", find_part_mock)
@mock.patch("ldraw_to_scad.LDrawConverter.colorfile", colorfile_mock)
class TestLDrawConverter(TestCase):
    """ test conversion of data """
    def test_it_should_convert_comments(self):
        """ test that comments get converted """
        # setup
        part_lines_to_test = [
            ["0 Stud", "// 0 Stud"],
            ["0", "// 0"]
        ]
        converter = LDrawConverter()
        # Test
        # Assert
        for line, expected in part_lines_to_test:
            output_scad = converter.convert_line(line)
            self.assertEqual(output_scad, [expected])

    def test_it_should_convert_type_1_line_into_function_ref(self):
        """ test conversion of type 1 lines """
        # setup
        part_line = "1 16 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat"
        converter = LDrawConverter(commented=False)
        converter.filedep = [set(), set()]
        # Test
        result = converter.convert_line(part_line)
        # Assert
        print(converter.filedep[0])
        self.assertIn('simple_test.dat', converter.filedep[0])
        self.assertEqual(result, [
            ("  [1,16,25,24,23,22,21,20,19,18,17,16,15,14, "
             "ldraw_lib__simple_test()],")
        ])

    def test_it_should_render_type_2_line(self):
        """ test conversion of type 2 lines """
        # setup
        part_line = "2 24 40 96 -20 -40 96 -20"
        converter = LDrawConverter(commented=False)
        # test
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [
            "  [2,24,40,96,-20,-40,96,-20],"
        ])

    def test_it_should_render_type_3_tri(self):
        """ test conversion of type 3 lines """
        # setup
        part_line = "3 16 -2.017 -35.943 0 0 -35.942 -3.6 2.017 -35.943 0"
        converter = LDrawConverter(commented=False)
        # test
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [
            "  [3,16,-2.017,-35.943,0,0,-35.942,-3.6,2.017,-35.943,0],"
        ])

    def test_it_should_render_a_quad(self):
        """ test conversion of type 4 lines """
        # setup
        part_line = "4 16 1 1 0 0.9239 1 0.3827 0.9239 0 0.3827 1 0 0"
        converter = LDrawConverter(commented=False)
        # Test
        output_scad = converter.convert_line(part_line)
        # Assert
        self.assertEqual(output_scad, [
            "  [4,16,1,1,0,0.9239,1,0.3827,0.9239,0,0.3827,1,0,0],"
        ])

    def test_it_should_render_the_optional_line(self):
        """ test conversion of type 5 lines """
        # setup
        part_line = ("5 24 0.7071 0 -0.7071 0.7071 1 -0.7071 "
                     "0.9239 0 -0.3827 0.3827 0 -0.9239")
        # test
        converter = LDrawConverter(commented=False)
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [
            ('  [5,24,0.7071,0,-0.7071,0.7071,1,-0.7071,'
             '0.9239,0,-0.3827,0.3827,0,-0.9239],')
        ])

    def test_multiple_lines(self):
        """ test conversion of multiple lines """
        # setup
        lines = [
            "0 Cylinder 1.0",
            "0 Name: 4-4cyli.dat",
            "4 16 1 1 0 0.9239 1 0.3827 0.9239 0 0.3827 1 0 0",
            "5 24 1 0 0 1 1 0 0.9239 0 0.3827 0.9239 0 -0.3827",
            ("4 16 0.9239 1 0.3827 0.7071 1 0.7071 "
             "0.7071 0 0.7071 0.9239 0 0.3827"),
            "5 24 0.9239 0 0.3827 0.9239 1 0.3827 0.7071 0 0.7071 1 0 0",
            ("4 16 0.7071 1 0.7071 0.3827 1 0.9239 "
             "0.3827 0 0.9239 0.7071 0 0.7071"),
        ]
        # Test
        converter = LDrawConverter()
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
            ("// 4 16 0.9239 1 0.3827 0.7071 1 0.7071 "
             "0.7071 0 0.7071 0.9239 0 0.3827"),
            ("  [4,16,0.9239,1,0.3827,0.7071,1,0.7071,"
             "0.7071,0,0.7071,0.9239,0,0.3827],"),
            "// 5 24 0.9239 0 0.3827 0.9239 1 0.3827 0.7071 0 0.7071 1 0 0",
            "  [5,24,0.9239,0,0.3827,0.9239,1,0.3827,0.7071,0,0.7071,1,0,0],",
            ("// 4 16 0.7071 1 0.7071 0.3827 1 0.9239 "
             "0.3827 0 0.9239 0.7071 0 0.7071"),
            ("  [4,16,0.7071,1,0.7071,0.3827,1,0.9239,"
             "0.3827,0,0.9239,0.7071,0,0.7071],"),
            "];",
            "makepoly(ldraw_lib____main__(), line=0.2);"
        ])

    def test_reading_file(self):
        """ test conversion of file content """
        # Setup
        test_file = "simple_test.dat"
        # test
        converter = LDrawConverter()
        with open(test_file, encoding="utf-8") as fdr:
            lines = fdr.readlines()
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
        """ test whole function creation from type 1 line """
        # setup
        part_lines = [
            "1 16 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat"]
        converter = LDrawConverter(commented=False)
        # test
        result = converter.process_lines('__main__', '/', part_lines)
        # assert
        self.assertListEqual(
            result,
            [
                "use <openscad/lib.scad>",
                "use <openscad/./simple_test.scad>",
                "function ldraw_lib____main__() = [",
                ("  [1,16,25,24,23,22,21,20,19,18,17,16,15,14, "
                 "ldraw_lib__simple_test()],"),
                "];",
                "makepoly(ldraw_lib____main__(), line=0.2);"
            ]
        )

    def test_multiple_type_1_lines_should_only_reference_functions_once(self):
        """ test that single function is only referenced/included once """
        # setup
        lines = [
            "1 16 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat",
            ("1 16 2.5 2.4 2.3 2.2 2.1 2.0 1.9 1.8 1.7 1.6 1.5 1.4 "
             "simple_test.dat"),
        ]
        # Test
        converter = LDrawConverter(commented=False)
        result = converter.process_lines('__main__', '/', lines)
        # Assert
        self.assertEqual(result, [
            "use <openscad/lib.scad>",
            "use <openscad/./simple_test.scad>",
            "function ldraw_lib____main__() = [",
            ("  [1,16,25,24,23,22,21,20,19,18,17,16,15,14, "
             "ldraw_lib__simple_test()],"),
            ("  [1,16,2.5,2.4,2.3,2.2,2.1,2.0,1.9,1.8,1.7,1.6,1.5,1.4, "
             "ldraw_lib__simple_test()],"),
            "];",
            "makepoly(ldraw_lib____main__(), line=0.2);"
        ])

    def test_try_simplest_mpd(self):
        """ test MPD functionality """
        # setup
        lines = [
            # 1 - ref the mpd
            "0 BFC CW",
            ("1 16 225 224 223 222 221 220 219 218 217 216 215 214 "
             "mdr_inner.ldr"),
            "0 NOFILE",
            "0 FILE mdr_inner.ldr",
            "0 BFC CW",
            "4 16 1 1 0 0.9239 1 0.3827 0.9239 0 0.3827 1 0 0",
            "0 NOFILE"
        ]
        # test
        converter = LDrawConverter(commented=False)
        result = converter.process_lines('__main__', '/', lines)
        # assert
        self.assertEqual(result, [
            "use <openscad/lib.scad>",
            "function ldraw_lib____main__() = [",
            '  [0,"BFC","CW"],',
            ("  [1,16,225,224,223,222,221,220,219,218,217,216,215,214, "
             "ldraw_lib__mdr_inner()],"),
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
        """ test a complete MPD file """
        # Setup
        mpd_filename = "mpd_test.dat"
        # Test
        converter = LDrawConverter()
        with open(mpd_filename, encoding="utf-8") as fdr:
            lines = fdr.readlines()
        output = converter.process_lines('__main__', '/', lines)
        # Assert
        self.assertListEqual(output, [
            "use <openscad/lib.scad>",
            "use <openscad/./simple_test.scad>",
            "function ldraw_lib____main__() = [",
            "// 0 FILE mdp_test.dat",
            "// 0 Simple MPD File",
            "// 0 Name: mdp_test.dat",
            "// 0 BFC CW",
            '  [0,"BFC","CW"],',
            "// ",
            ("// 1 16 225 224 223 222 221 220 219 218 217 216 215 214 "
             "mdr_inner.ldr"),
            ("  [1,16,225,224,223,222,221,220,219,218,217,216,215,214, "
             "ldraw_lib__mdr_inner()],"),
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
            ("  [1,16,25,24,23,22,21,20,19,18,17,16,15,14, "
             "ldraw_lib__simple_test()],"),
            "// 0 NOFILE",
            "];",
            "function ldraw_lib__dummy_2() = [",
            "];",
            "makepoly(ldraw_lib____main__(), line=0.2);",
            "function ldraw_lib__mdp_test() = ldraw_lib____main__();\n"
        ])
