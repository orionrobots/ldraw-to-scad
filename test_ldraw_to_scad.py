from unittest import TestCase
import mock

class LDrawConverter():
    def __init__(self):
        self.modules = []

    def make_colour(self, colour_index):
        return "color(lego_colours[{0}])".format(colour_index)

    def handle_type_1_line(self, colour_index, x, y, z, a, b, c, d, e, f, g, h, i, filename):
        with open(filename) as fd:
            module_inner = self.convert_file(fd, indent=2)
        module_name = filename.split('.', 1)[0]
        module = [
            "module {}() {{".format(module_name)
        ] + module_inner + [
            "}"
        ]

        return module + [
            self.make_colour(colour_index),
            "  multmatrix([",
            "    [{0}, {1}, {2}, {3}]".format(a, b, c, x),
            "    [{0}, {1}, {2}, {3}]".format(d, e, f, y),
            "    [{0}, {1}, {2}, {3}]".format(g, h, i, z),
            "    [{0}, {1}, {2}, {3}]".format(0, 0, 0, 1),
            "  ])",
            "  {}();".format(module_name)
        ]

    def convert_line(self, part_line, indent=0):
        # Preserve blank lines
        part_line = part_line.strip()
        if part_line == '':
            return [part_line]
        command, rest = part_line.split(maxsplit=1)
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

class TestLDrawConverterLine(TestCase):
    primitive_path = "lib/ldraw/4-4edge.dat"
    def default_runner(self):
        return LDrawConverter()

    def test_it_should_convert_a_comment(self):
        # setup
        part_line = "0 Stud"
        # Test
        converter = self.default_runner()
        output_scad = converter.convert_line(part_line)
        # Assert
        self.assertEqual(output_scad, ["// Stud"])

    def test_it_should_convert_type_1_line_into_module(self):
        # setup
        # This is a silly matrix - but the components are easy to pick out
        #      1 <colour> x  y  z  a  b  c  d  e  f  g  h  i <file>
        part_line = "1 16 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat"
        # Test
        converter = self.default_runner()
        result = converter.convert_line(part_line)
        # Assert
        self.assertEqual(result, [
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
            "color(lego_colours[16]) ",
            "  translate([0, 0, 0])",
            "  multmatrix([",
            "    [22, 21, 20, 25],",
            "    [19, 18, 17, 24],",
            "    [16, 15, 14, 23],",
            "    [ 0,  0,  0,  1]",
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


        