from unittest import TestCase
import mock

class LDrawConverter():
    def convert_line(self, part_line):
        command, rest = part_line.split(' ', 1)
        result = []
        if command == "0":
            result.append("// {}".format(rest))
        elif command == "3":
            colour_index, x1, y1, z1, x2, y2, z2, x3, y3, z3 = rest.split(' ')
            result.append("color(lego_colours[{0}])".format(colour_index))
            result.append("  polyhedron(points=[")
            result.append("    [{0}, {1}, {2}],".format(x1, y1, z1))
            result.append("    [{0}, {1}, {2}],".format(x2, y2, z2))
            result.append("    [{0}, {1}, {2}]".format(x3, y3, z3))
            result.append("  ], faces = [[0, 1, 2]]);")
        elif command == "4":
            colour_index, x1, y1, z1, x2, y2, z2, x3, y3, z3, x4, y4, z4 = rest.split(' ')
            result.append("color(lego_colours[{0}])".format(colour_index))
            result.append("  polyhedron(points=[")
            result.append("    [{0}, {1}, {2}],".format(x1, y1, z1))
            result.append("    [{0}, {1}, {2}],".format(x2, y2, z2))
            result.append("    [{0}, {1}, {2}],".format(x3, y3, z3))
            result.append("    [{0}, {1}, {2}]".format(x4, y4, z4))
            result.append("  ], faces = [[0, 1, 2, 3]]);")
        return result

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
        
    def test_it_should_ignore_the_optional_line(self):
        # setup
        part_line = "5 24 0.7071 0 -0.7071 0.7071 1 -0.7071 0.9239 0 -0.3827 0.3827 0 -0.9239"
        # test
        converter = self.default_runner()
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [])

    def test_it_should_ignore_type_2_line(self):
        # setup
        part_line = "2 24 40 96 -20 -40 96 -20"
        # test
        converter = self.default_runner()
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [])


class TestLDrawConverterLine(TestCase):
    primitive_path = "lib/ldraw/4-4edge.dat"
    def default_runner(self):
        return LDrawConverter()
        