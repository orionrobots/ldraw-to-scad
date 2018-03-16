from unittest import TestCase
import mock
import os

from ldraw_to_scad import LDrawConverter, Module, ColourConverter

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

class TestColourConverter(TestCase):
    def default_runner(self):
        return ColourConverter()
    
    def test_reading_one_line_ignoring_other_bit(self):
        # setup
        sample = [
            "",
            "  ",
            "0 // LDraw Solid Colours",
            "0                              // LEGOID  26 - Black",
            "0 !COLOUR Black                CODE   0   VALUE #05131D   EDGE #595959",
            "0 !COLOUR Trans_Clear          CODE  47   VALUE #FCFCFC   EDGE #C3C3C3   ALPHA 128",
            "0 !COLOUR Chrome_Gold          CODE 334   VALUE #BBA53D   EDGE #BBB23D   CHROME",
            "0 !COLOUR Pearl_White          CODE 183   VALUE #F2F3F2   EDGE #333333   PEARLESCENT",
            "0 !COLOUR Metallic_Silver      CODE  80   VALUE #A5A9B4   EDGE #333333   METAL",
            "0 !COLOUR Rubber_Yellow        CODE  65   VALUE #F5CD2F   EDGE #333333   RUBBER"
        ]
        # Test
        converter = self.default_runner()
        converter.parse_colour_lines(sample)
        # assert
        self.assertEqual(
            converter.colours[0],
            {
                'code': 0, 
                'name': 'Black', 
                'value': (5, 19, 29),# '#05131D', 
                'edge': (89, 89, 89) #'#595959'
            }
        )
        

    def test_it_can_output_a_colour_list(self):
        # setup
        converter = self.default_runner()
        converter.colours = [
            {
                'code': 52,
                'name': 'Blue',
                'value': (0, 55, 191),
                'edge': (89, 89, 89)
            }
        ]
        # test
        output = converter.get_lines()
        # assert
        self.assertListEqual(
            output, [
                'colour52 = [0.0, 0.22, 0.75];'
            ]
        )

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


    def test_it_should_remove_0_meta_commands(self):
        # setup
        lines =[
            "0 !META stuff",
            "0 Normal Comment"
        ]
        converter, module = self.default_runner()
        converter.current_module = module
        # Test
        converter.process_lines(module, lines)
        # Assert
        self.assertListEqual(
            module.lines,
            [
                "// Normal Comment"
            ]
        )

    def test_it_should_convert_type_1_line_into_module_ref(self):
        # setup
        # This is a silly matrix - but the components are easy to pick out
        #      1 <colour> x  y  z  a  b  c  d  e  f  g  h  i <file>
        part_line = "1 1 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat"
        converter, module = self.default_runner()
        # Test
        converter.current_module = module
        result = converter.convert_line(part_line)
        # Assert
        print(module.dependancies)
        self.assertIn('n__simple_test', module.dependancies)
        self.assertEqual(result, [
            "color(colour1)",
            "  multmatrix([",
            "    [22, 21, 20, 25],",
            "    [19, 18, 17, 24],",
            "    [16, 15, 14, 23],",
            "    [0, 0, 0, 1]",
            "  ])",
            "  n__simple_test();"
        ])


    def test_it_should_ignore_type_1_ref_to_4_4edge(self):
        # setup
        # This is a silly matrix - but the components are easy to pick out
        #      1 <colour> x  y  z  a  b  c  d  e  f  g  h  i <file>
        part_line = "1 1 25 24 23 22 21 20 19 18 17 16 15 14 4_4edge.dat"
        converter, module = self.default_runner()
        # Test
        converter.current_module = module
        result = converter.convert_line(part_line)
        # Assert
        print(module.dependancies)
        self.assertNotIn('n__4_4edge', module.dependancies)
        self.assertEqual(result, [])

    def test_it_should_convert_type_1_16_with_no_colour(self):
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
            "  multmatrix([",
            "    [22, 21, 20, 25],",
            "    [19, 18, 17, 24],",
            "    [16, 15, 14, 23],",
            "    [0, 0, 0, 1]",
            "  ])",
            "  n__simple_test();"
        ])

    def test_it_should_ignore_type_2_line(self):
        # setup
        part_line = "2 24 40 96 -20 -40 96 -20"
        converter, module = self.default_runner()
        # test
        converter.current_module = module
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [])
        # With indent
        output_scad = converter.convert_line(part_line, indent=2)
        # assert
        self.assertEqual(output_scad, [])

    def test_it_should_render_type_3_tri(self):
        # setup
        part_line = "3 1 -2.017 -35.943 0 0 -35.942 -3.6 2.017 -35.943 0"
        converter, module = self.default_runner()
        # test
        converter.current_module = module
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [
            "color(colour1)",
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
            "  color(colour1)",
            "    polyhedron(points=[",
            "      [-2.017, -35.943, 0],",
            "      [0, -35.942, -3.6],",
            "      [2.017, -35.943, 0]",
            "    ], faces = [[0, 1, 2]]);"
        ])

    def test_it_should_render_a_quad(self):
        # setup
        part_line = "4 1 1 1 0 0.9239 1 0.3827 0.9239 0 0.3827 1 0 0"
        converter, module = self.default_runner()
        # Test
        converter.current_module = module
        output_scad = converter.convert_line(part_line)
        # Assert
        self.assertEqual(output_scad, [
            "color(colour1)",
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
        converter, module = self.default_runner()
        converter.index_library()

        # Assert
        for part_name, expected_path in part_tests:
            self.assertEqual(converter.find_part(part_name), expected_path)

    def test_it_should_ignore_the_optional_line(self):
        # setup
        part_line = "5 24 0.7071 0 -0.7071 0.7071 1 -0.7071 0.9239 0 -0.3827 0.3827 0 -0.9239"
        # test
        converter, module = self.default_runner()
        converter.current_module = module
        output_scad = converter.convert_line(part_line)
        # assert
        self.assertEqual(output_scad, [])

    def test_multiple_lines(self):
        # setup
        lines = [
            "0 Cylinder 1.0",
            "0 Name: 4-4cyli.dat",
            "4 1 1 1 0 0.9239 1 0.3827 0.9239 0 0.3827 1 0 0",
            "5 24 1 0 0 1 1 0 0.9239 0 0.3827 0.9239 0 -0.3827",
            "4 1 0.9239 1 0.3827 0.7071 1 0.7071 0.7071 0 0.7071 0.9239 0 0.3827",
            "5 24 0.9239 0 0.3827 0.9239 1 0.3827 0.7071 0 0.7071 1 0 0",
            "4 1 0.7071 1 0.7071 0.3827 1 0.9239 0.3827 0 0.9239 0.7071 0 0.7071",
        ]
        # Test
        converter, module = self.default_runner()
        converter.process_lines(module, lines)
        # Assert
        self.assertEqual(module.lines, [
            "// Cylinder 1.0",
            "// Name: 4-4cyli.dat",
            "color(colour1)",
            "  polyhedron(points=[",
            "    [1, 1, 0],",
            "    [0.9239, 1, 0.3827],",
            "    [0.9239, 0, 0.3827],",
            "    [1, 0, 0]",
            "  ], faces = [[0, 1, 2, 3]]);",
            "color(colour1)",
            "  polyhedron(points=[",
            "    [0.9239, 1, 0.3827],",
            "    [0.7071, 1, 0.7071],",
            "    [0.7071, 0, 0.7071],",
            "    [0.9239, 0, 0.3827]",
            "  ], faces = [[0, 1, 2, 3]]);",
            "color(colour1)",
            "  polyhedron(points=[",
            "    [0.7071, 1, 0.7071],",
            "    [0.3827, 1, 0.9239],",
            "    [0.3827, 0, 0.9239],",
            "    [0.7071, 0, 0.7071]",
            "  ], faces = [[0, 1, 2, 3]]);",
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
        self.assertEqual(output, [
            "// Simple Test File",
            "// Name: simple_test.dat",
            "",
            "color(colour1)",
            "  polyhedron(points=[",
            "    [1, 1, 1],",
            "    [1, 1, -1],",
            "    [-1, 1, -1],",
            "    [-1, 1, 1]",
            "  ], faces = [[0, 1, 2, 3]]);",
            "",
        ])
    
    def test_it_process_type_1_line_into_module(self):
        # setup
        part_lines = ["1 1 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat"]
        converter, _ = self.default_runner()
        # test
        result = converter.process_main(part_lines)
        # assert
        self.assertListEqual(
            result,
            [
                "module n__simple_test() {",
                "  // Simple Test File",
                "  // Name: simple_test.dat",
                "  ",
                "  color(colour1)",
                "    polyhedron(points=[",
                "      [1, 1, 1],",
                "      [1, 1, -1],",
                "      [-1, 1, -1],",
                "      [-1, 1, 1]",
                "    ], faces = [[0, 1, 2, 3]]);",
                "  ",
                "}",
                "color(colour1)",
                "  multmatrix([",
                "    [22, 21, 20, 25],",
                "    [19, 18, 17, 24],",
                "    [16, 15, 14, 23],",
                "    [0, 0, 0, 1]",
                "  ])",
                "  n__simple_test();"
            ]
        )

    def test_multiple_lines_should_only_make_a_single_module_for_multiple_type_1_refs(self):
        # setup
        lines = [
            "1 1 25 24 23 22 21 20 19 18 17 16 15 14 simple_test.dat",
            "1 1 2.5 2.4 2.3 2.2 2.1 2.0 1.9 1.8 1.7 1.6 1.5 1.4 simple_test.dat",
        ]
        # Test
        converter, _ = self.default_runner()
        result = converter.process_main(lines)
        # Assert
        self.assertEqual(result, [
            "module n__simple_test() {",
            "  // Simple Test File",
            "  // Name: simple_test.dat",
            "  ",
            "  color(colour1)",
            "    polyhedron(points=[",
            "      [1, 1, 1],",
            "      [1, 1, -1],",
            "      [-1, 1, -1],",
            "      [-1, 1, 1]",
            "    ], faces = [[0, 1, 2, 3]]);",
            "  ",
            "}",
            "color(colour1)",
            "  multmatrix([",
            "    [22, 21, 20, 25],",
            "    [19, 18, 17, 24],",
            "    [16, 15, 14, 23],",
            "    [0, 0, 0, 1]",
            "  ])",
            "  n__simple_test();",
            "color(colour1)",
            "  multmatrix([",
            "    [2.2, 2.1, 2.0, 2.5],",
            "    [1.9, 1.8, 1.7, 2.4],",
            "    [1.6, 1.5, 1.4, 2.3],",
            "    [0, 0, 0, 1]",
            "  ])",
            "  n__simple_test();",
        ])

    def test_try_simplest_mpd(self):
        # setup
        lines = [
            # 1 - ref the mpd
            "1 1 225 224 223 222 221 220 219 218 217 216 215 214 mdr_inner.ldr",
            "0 NOFILE",
            "0 FILE mdr_inner.ldr",
            "4 1 1 1 0 0.9239 1 0.3827 0.9239 0 0.3827 1 0 0",
            "0 NOFILE"
        ]
        # test
        converter, _ = self.default_runner()
        result = converter.process_main(lines)
        # assert
        self.assertEqual(result, [
            "module n__mdr_inner() {",
            "  color(colour1)",
            "    polyhedron(points=[",
            "      [1, 1, 0],",
            "      [0.9239, 1, 0.3827],",
            "      [0.9239, 0, 0.3827],",
            "      [1, 0, 0]",
            "    ], faces = [[0, 1, 2, 3]]);",
            "}",
            "color(colour1)",
            "  multmatrix([",
            "    [222, 221, 220, 225],",
            "    [219, 218, 217, 224],",
            "    [216, 215, 214, 223],",
            "    [0, 0, 0, 1]",
            "  ])",
            "  n__mdr_inner();",
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
        self.assertListEqual(output,
        [
            "module n__simple_test() {",
            "  // Simple Test File",
            "  // Name: simple_test.dat",
            "  ",
            "  color(colour1)",
            "    polyhedron(points=[",
            "      [1, 1, 1],",
            "      [1, 1, -1],",
            "      [-1, 1, -1],",
            "      [-1, 1, 1]",
            "    ], faces = [[0, 1, 2, 3]]);",
            "  ",
            "}",
            "module n__mdr_inner() {",
            "  color(colour1)",
            "    multmatrix([",
            "      [22, 21, 20, 25],",
            "      [19, 18, 17, 24],",
            "      [16, 15, 14, 23],",
            "      [0, 0, 0, 1]",
            "    ])",
            "    n__simple_test();",
            "}",
            "// Simple MPD File",
            "// Name: mdp_test.dat",
            "",
            "color(colour1)",
            "  multmatrix([",
            "    [222, 221, 220, 225],",
            "    [219, 218, 217, 224],",
            "    [216, 215, 214, 223],",
            "    [0, 0, 0, 1]",
            "  ])",
            "  n__mdr_inner();",
            ""
        ])