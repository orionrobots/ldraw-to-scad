from unittest import TestCase
import mock
import os

from ldraw_to_scad import LDrawConverter

class TestLDrawConverterLine(TestCase):
    def default_runner(self):
        return LDrawConverter()

    def test_it_should_convert_comments(self):
        # setup
        part_lines_to_test =[
            ["0 Stud", "// Stud"],
            ["0", "// "]
        ]
        # Test
        converter = self.default_runner()
        # Assert
        for line, expected in part_lines_to_test:
            output_scad = converter.convert_line(line)
            self.assertEqual(output_scad, [expected])

    def test_it_should_convert_type_1_line_into_module(self):
        # setup
        # This is a silly matrix - but the components are easy to pick out
        #      1 <colour> x  y  z  a  b  c  d  e  f  g  h  i <file>
        part_line = "1 16 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat"
        # Test
        converter = self.default_runner()
        result = converter.convert_line(part_line)
        modules = converter.get_modules()
        # Assert
        self.assertEqual(modules, [
            "module simple_test() {",
            "  // Simple Test File",
            "  // Name: simple_test.dat",
            "",
            "  color(lego_colours[16])",
            "    polyhedron(points=[",
            "      [1, 1, 1],",
            "      [1, 1, -1],",
            "      [-1, 1, -1],",
            "      [-1, 1, 1]",
            "    ], faces = [[0, 1, 2, 3]]);",
            "",
            "}",
        ])
        self.assertEqual(result, [
            "color(lego_colours[16])",
            "  multmatrix([",
            "    [22, 21, 20, 25],",
            "    [19, 18, 17, 24],",
            "    [16, 15, 14, 23],",
            "    [0, 0, 0, 1]",
            "  ])",
            "  simple_test();"
        ])

    def test_it_should_ignore_type_2_line(self):
        # setup
        part_line = "2 24 40 96 -20 -40 96 -20"
        # test
        converter = self.default_runner()
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [])
        # With indent
        output_scad = converter.convert_line(part_line, indent=2)
        # assert
        self.assertEqual(output_scad, [])

    def test_it_should_render_type_3_tri(self):
        # setup
        part_line = "3 16 -2.017 -35.943 0 0 -35.942 -3.6 2.017 -35.943 0"
        # test
        converter = self.default_runner()
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [
            "color(lego_colours[16])",
            "  polyhedron(points=[",
            "    [-2.017, -35.943, 0],",
            "    [0, -35.942, -3.6],",
            "    [2.017, -35.943, 0]",
            "  ], faces = [[0, 1, 2]]);"
        ])
        # test with indent
        output_scad = converter.convert_line(part_line, indent=2)
        # assert
        self.assertEqual(output_scad, [
            "  color(lego_colours[16])",
            "    polyhedron(points=[",
            "      [-2.017, -35.943, 0],",
            "      [0, -35.942, -3.6],",
            "      [2.017, -35.943, 0]",
            "    ], faces = [[0, 1, 2]]);"
        ])

    def test_it_should_render_a_quad(self):
        # setup
        part_line = "4 16 1 1 0 0.9239 1 0.3827 0.9239 0 0.3827 1 0 0"
        # Test
        converter = self.default_runner()
        output_scad = converter.convert_line(part_line)
        # Assert
        self.assertEqual(output_scad, [
            "color(lego_colours[16])",
            "  polyhedron(points=[",
            "    [1, 1, 0],",
            "    [0.9239, 1, 0.3827],",
            "    [0.9239, 0, 0.3827],",
            "    [1, 0, 0]",
            "  ], faces = [[0, 1, 2, 3]]);"
        ])

    def test_it_should_be_able_to_find_part_path(self):
        # WARNING: This test requires having lib/ldraw setup.
        # setup
        #  part tests - name, expected location
        part_tests = [
            ['1.dat', os.path.join('lib', 'ldraw', 'parts', '1.dat')],
            ['4-4cyli.dat', os.path.join('lib', 'ldraw', 'p', '4-4cyli.dat')],
            ['s\\4744s01.dat', os.path.join('lib', 'ldraw', 'parts', 's', '4744s01.dat')]
        ]
        # Test
        converter = self.default_runner()
        converter.index_library()

        # Assert
        for part_name, expected_path in part_tests:
            self.assertEqual(converter.find_part(part_name), expected_path)
        
    def test_it_should_ignore_the_optional_line(self):
        # setup
        part_line = "5 24 0.7071 0 -0.7071 0.7071 1 -0.7071 0.9239 0 -0.3827 0.3827 0 -0.9239"
        # test
        converter = self.default_runner()
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [])


class TestLDrawConverterFile(TestCase):
    
    def default_runner(self):
        return LDrawConverter()

    def test_reading_file(self):
        # Setup
        test_file = "simple_test.dat"
        # test
        converter = self.default_runner()
        with open(test_file) as fd:
            output = converter.convert_file(fd)
        # assert
        self.assertEqual(output, [
            "// Simple Test File",
            "// Name: simple_test.dat",
            "",
            "color(lego_colours[16])",
            "  polyhedron(points=[",
            "    [1, 1, 1],",
            "    [1, 1, -1],",
            "    [-1, 1, -1],",
            "    [-1, 1, 1]",
            "  ], faces = [[0, 1, 2, 3]]);",
            ""
        ])


    def test_multiple_lines_should_only_make_a_single_module_for_multiple_type_1_refs(self):
        # setup
        lines = [
            "1 16 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat",
            "1 16 2.5 2.4 2.3 2.2 2.1 2.0 1.9 1.8 1.7 1.6 1.5 1.4 simple_test.dat",
        ]
        # Test
        converter = self.default_runner()
        output = converter.convert_lines(lines)
        modules = converter.get_modules()
        # Assert
        self.assertEqual(modules, [
            "module simple_test() {",
            "  // Simple Test File",
            "  // Name: simple_test.dat",
            "",
            "  color(lego_colours[16])",
            "    polyhedron(points=[",
            "      [1, 1, 1],",
            "      [1, 1, -1],",
            "      [-1, 1, -1],",
            "      [-1, 1, 1]",
            "    ], faces = [[0, 1, 2, 3]]);",
            "",
            "}",
        ])
        self.assertEqual(output, [
            "color(lego_colours[16])",
            "  multmatrix([",
            "    [22, 21, 20, 25],",
            "    [19, 18, 17, 24],",
            "    [16, 15, 14, 23],",
            "    [0, 0, 0, 1]",
            "  ])",
            "  simple_test();",
            "color(lego_colours[16])",
            "  multmatrix([",
            "    [2.2, 2.1, 2.0, 2.5],",
            "    [1.9, 1.8, 1.7, 2.4],",
            "    [1.6, 1.5, 1.4, 2.3],",
            "    [0, 0, 0, 1]",
            "  ])",
            "  simple_test();",
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
        output = converter.convert_lines(lines)
        # Assert
        self.assertEqual(output, [
            "// Cylinder 1.0",
            "// Name: 4-4cyli.dat",
            "color(lego_colours[16])",
            "  polyhedron(points=[",
            "    [1, 1, 0],",
            "    [0.9239, 1, 0.3827],",
            "    [0.9239, 0, 0.3827],",
            "    [1, 0, 0]",
            "  ], faces = [[0, 1, 2, 3]]);",
            "color(lego_colours[16])",
            "  polyhedron(points=[",
            "    [0.9239, 1, 0.3827],",
            "    [0.7071, 1, 0.7071],",
            "    [0.7071, 0, 0.7071],",
            "    [0.9239, 0, 0.3827]",
            "  ], faces = [[0, 1, 2, 3]]);",
            "color(lego_colours[16])",
            "  polyhedron(points=[",
            "    [0.7071, 1, 0.7071],",
            "    [0.3827, 1, 0.9239],",
            "    [0.3827, 0, 0.9239],",
            "    [0.7071, 0, 0.7071]",
            "  ], faces = [[0, 1, 2, 3]]);",
        ])


        