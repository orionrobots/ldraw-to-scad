/* general data structure:
      array of
          vectors of
              array of points (face)
              color index
*/

module ccolor(col) {
    if (col) color(col) children();
    else children();
}

/* makepoly: convert data structure to colored 3d object

   For each face color a polyhedron with a single face
   constructed by the array of points in clockwise
   direction.
*/
module makepoly(poly, step=0, col=false, unit=2/5,
                alt=false)
    for(f=l1([[unit, 0    , 0,    0],
              [0,    0    , unit, 0],
              [0,    -unit, 0,    0]],
           poly, 16, step=-1))
        if(step == 0 || f[2] < step)
        ccolor((f[1] == 16) ?
                    (is_num(col) ?
                        ldraw_color(col, alt) : col) :
                    ldraw_color(f[1], alt))
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
function l1(M, poly, col, invert=false, step=0) =
    [for(f=poly) [
        rev([for(p=f[0]) M * [p.x, p.y, p.z, 1]],
            det3(M)<0 != invert),
        (f[1] == 16) ? col : f[1],
        (step == -1) ? f[2] : step
    ]];

/* rev: reverse an array if condition c is true */
function rev(v, c=true) = c ? [for(i=[1:len(v)]) v[len(v) - i]] : v;

/* line: construct data structure according to specification */
function line(v) =
    (v[0] == 1) ?
        l1([[v[ 5], v[ 6], v[ 7], v[2]],
            [v[ 8], v[ 9], v[10], v[3]],
            [v[11], v[12], v[13], v[4]]],
           v[14],
           v[1],
           (len(v)>15) ? v[15] : false,
           (len(v)>16) ? v[16] : 0) : (
    (v[0] == 3) ?
        [[rev([[v[ 2], v[ 3], v[ 4]],
               [v[ 5], v[ 6], v[ 7]],
               [v[ 8], v[ 9], v[10]]],
              (len(v)>11) ? v[11] : true),
          v[1],
          (len(v)>12) ? v[12] : 0]] : (
    (v[0] == 4) ?
        [[rev([[v[ 2], v[ 3], v[ 4]],
               [v[ 5], v[ 6], v[ 7]],
               [v[ 8], v[ 9], v[10]],
               [v[11], v[12], v[13]]],
              (len(v)>14) ? v[14] : true),
          v[1],
          (len(v)>15) ? v[15] : 0]] : []));
