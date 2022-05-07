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

vv = [cos($vpr.z)*sin($vpr.y)*cos($vpr.x)
        +sin($vpr.z)*sin($vpr.x),
      sin($vpr.z)*sin($vpr.y)*cos($vpr.x)
        -cos($vpr.z)*sin($vpr.x),
      cos($vpr.y)*cos($vpr.x)];

/* makepoly: convert data structure to colored 3d object

   For each face color a polyhedron with a single face
   constructed by the array of points in clockwise
   direction.
*/
module makepoly(poly, step=0, col=false, unit=2/5,
                alt=false, line=0.2)
    for(f=l1([[unit, 0    , 0,    0],
              [0,    0    , unit, 0],
              [0,    -unit, 0,    0]],
           poly, 16, step=-1))
        if(step == 0 || f[3] < step)
        ccolor(
            (f[2] == 16) ?
                (is_num(col) ?
                    ldraw_color(col, alt)[0] : col) : (
            (f[2] == 24) ?
                (is_num(col) ?
                    ldraw_color(col, alt)[1] : "black") : (
            (f[2] < 0) ?
                ldraw_color(-f[2]-1, alt)[1] :
                ldraw_color(f[2], alt)[0])))
        if(f[0]) {
            polyhedron(f[1], [[for(i=[0:1:len(f[1])-1]) i]]);
        } else if (line) {
            if(len(f[1]) == 2 ||
               ((f[1][2]-f[1][0])*cross(f[1][1]-f[1][0],vv))*
               ((f[1][3]-f[1][0])*cross(f[1][1]-f[1][0],vv))
                >0)
            translate(f[1][0])
            rotate([0,
                    acos((f[1][1].z-f[1][0].z)
                        /norm(f[1][1]-f[1][0])),
                    atan2(f[1][1].y-f[1][0].y,
                          f[1][1].x-f[1][0].x)])
            cylinder(norm(f[1][1]-f[1][0]), d=line);
        }

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
    [for(f=lines(poly))
        [f[0],
         rev([for(p=f[1]) M * [p.x, p.y, p.z, 1]],
             f[0] && (det3(M)<0 != invert)),
         (f[2] == 16) ? col : (
         (f[2] == 24) ? (
             (col == 16) ? 24 : (
             (col == 24) ? 16 : -col-1)) : f[2]),
         (step == -1) ? f[3] : step]];

/* rev: reverse an array if condition c is true */
function rev(v, c=true) = c ? [for(i=[1:len(v)]) v[len(v) - i]] : v;

function lines(v) =
    [for (i=0,
          l = [],
          mr=[0, true, false];
          i <= len(v);
          m=metaline(v[i], mr),
          l=concat(l,line(v[i], m)),
          mr=[m[0],
             m[1],
             (v[i][0] == 0) ? m[2] : false],
          i=i+1) l]
    [len(v)];

function metaline(v, meta) =
    (v[0] == 0) ? (
        (v[1] == "STEP") ?
            [meta[0]+1, meta[1], false] : (
        (v[1] == "BFC") ? (
            (v[2] == "CCW") ?
                [meta[0], true, false] : (
            (v[2] == "CW") ?
                [meta[0], false, false] : (
            (v[2] == "INVERTNEXT") ?
                [meta[0], meta[1], true] :
                [meta[0], meta[1], false]))) :
            [meta[0], meta[1], false])) :
        [meta[0], meta[1], meta[2]];

/* line: construct data structure according to specification */
function line(v, meta) =
    (v[0] == 1) ?
        l1([[v[ 5], v[ 6], v[ 7], v[2]],
            [v[ 8], v[ 9], v[10], v[3]],
            [v[11], v[12], v[13], v[4]]],
           v[14],
           v[1],
           meta[2],
           meta[0]) : (
    (v[0] == 2) ?
        [[false,
          [[v[ 2], v[ 3], v[ 4]],
           [v[ 5], v[ 6], v[ 7]]],
          v[1],
          meta[0]]] : (
    (v[0] == 3) ?
        [[true,
          rev([[v[ 2], v[ 3], v[ 4]],
               [v[ 5], v[ 6], v[ 7]],
               [v[ 8], v[ 9], v[10]]],
              meta[1]),
          v[1],
          meta[0]]] : (
    (v[0] == 4) ?
        [[true,
          rev([[v[ 2], v[ 3], v[ 4]],
               [v[ 5], v[ 6], v[ 7]],
               [v[ 8], v[ 9], v[10]],
               [v[11], v[12], v[13]]],
              meta[1]),
          v[1],
          meta[0]]] : (
    (v[0] == 5) ?
        [[false,
          [[v[ 2], v[ 3], v[ 4]],
           [v[ 5], v[ 6], v[ 7]],
           [v[ 8], v[ 9], v[10]],
           [v[11], v[12], v[13]]],
          v[1],
          meta[0]]] : []))));
