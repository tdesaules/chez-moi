// Rack SBC 5 x 1U - prototype dimensionnel et d'assemblage, mm.
// Voir rack-sbc-test.md. X=largeur, Y=profondeur, Z=hauteur, avant Y=0.
// Les chassis internes ne sont PAS inclus. Ventilateur et volumes 1U = references.
// Inserts Audiophonics 9288 : laiton A FRAPPER, diametre 4, longueur 5.3.
// NF-A20 PWM : 200x200x32 avec patins, entraxe choisi 170x170.

/* [Affichage] */
part = "assembly"; // [assembly,exploded,beam,node,panel,key,coupon]
show_fan = true;
show_slots = false;
// Pour une barre : axis 0=X, 1=Y, 2=Z ; edge 0..3 ; half 0..1.
axis = 0;
edge = 0;
half = 0;
// Pour un noeud : coordonnees 0, 1, 2 sur chaque axe (coin ou milieu d'arete).
node_x = 0;
node_y = 0;
node_z = 0;
// Panneaux : deux colonnes x deux rangees par face.
face = "left"; // [left,right,top,bottom,rear]
column = 0; // [0,1]
row = 0; // [0,1]

/* [Dimensions] */
width = 272.25;
height = 254.25;
depth = 240;
units = 5;
unit_height = 44.45;
gap = 2;
structure = 10;
chassis_width = 222.25;
ear_width = 15;
chassis_clearance = 0.4; // par cote, pris sur les bandes de fixation

/* [Panneaux] */
panel_thickness = 5;
hex_flat = 5; // ouverture entre faces paralleles
web = 2; // distance minimale entre deux ouvertures
panel_border = 8;
fit = 0.2; // jeu par face des emboitements
tile_gap = 0.3;
groove_depth = 2;

/* [Visserie] */
insert_diameter = 3.8; // AVANT-TROU EXPERIMENTAL : tester l'eprouvette
insert_length = 5.3;
insert_depth = 5.6;
screw_clearance = 3.3;
tenon_size = 6;
tenon_length = 8;

/* [Ventilateur] */
fan_size = 200;
fan_thickness = 32;
fan_pitch = 170;
fan_aperture = 190; // zone de grille, a verifier sur le ventilateur reel
fan_boss = 3;

/* [Hidden] */
$fn = $preview ? 24 : 48;
eps = 0.02;
B = structure;
dims = [width, depth, height];
coords = [[0,width/2-B/2,width-B],
          [0,depth/2-B/2,depth-B],
          [0,height/2-B/2,height-B]];
panel_offset = (B-panel_thickness)/2;
fan_rear = depth-panel_offset-panel_thickness-fan_boss;
fan_front = fan_rear-fan_thickness;

assert(abs(height-(2*B+units*unit_height+(units+1)*gap))<0.01,
       "Hauteur incompatible avec les 5U et les 6 jeux de 2 mm");
assert(abs(width-(2*B+2*ear_width+chassis_width))<0.01);
assert(panel_thickness+2*fit < B);
assert(insert_depth < tenon_size);
assert(part=="assembly" || part=="exploded" || part=="beam" || part=="node"
       || part=="panel" || part=="key" || part=="coupon", "Selection inconnue");

function beam_length(a) = (dims[a]-3*B)/2;
function slot_z(i) = B+gap+i*(unit_height+gap);
function interior(v) = v==0 ? 1 : -1;
function is_front_vertical(a,e) = a==2 && floor(e/2)==0;

// Transformation des barres : x local suit l'arete, y/z pointent vers l'interieur.
module edge_transform(a,e) {
    s=e%2; t=floor(e/2);
    if(a==0)
        multmatrix([[1,0,0,0],[0,interior(s),0,s*depth],
                    [0,0,interior(t),t*height],[0,0,0,1]]) children();
    if(a==1)
        multmatrix([[0,interior(s),0,s*width],[1,0,0,0],
                    [0,0,interior(t),t*height],[0,0,0,1]]) children();
    if(a==2)
        multmatrix([[0,interior(s),0,s*width],[0,0,interior(t),t*depth],
                    [1,0,0,0],[0,0,0,1]]) children();
}

module bore_down(d,h) { translate([0,0,-h]) cylinder(d=d,h=h+eps); }

// Profil longitudinal rainure sur les deux faces interieures.
// Les 12 mm proches des extremites sont pleins pour les emboitements.
module beam(a,e,h) {
    L=beam_length(a);
    start=B+h*(L+B);
    front=is_front_vertical(a,e);
    difference() {
        union() {
            cube([L,B,B]);
            if(front) translate([0,B,0])
                cube([L,ear_width-chassis_clearance,B]);
        }
        for(end=[0,1]) {
            translate([end==0 ? -eps : L-tenon_length-fit,
                       (B-tenon_size)/2-fit,(B-tenon_size)/2-fit])
                cube([tenon_length+fit+eps,tenon_size+2*fit,tenon_size+2*fit]);
            // Vis depuis la face z+ dans le tenon du noeud.
            translate([end==0 ? tenon_length/2 : L-tenon_length/2,B/2,B+eps])
                bore_down(screw_clearance,3+2*eps);
        }
        // En face avant, pas de panneau dans le plan de l'ouverture des racks.
        if(!front) translate([12,B-groove_depth,(B-panel_thickness)/2-fit])
            cube([L-24,groove_depth+eps,panel_thickness+2*fit]);
        translate([12,(B-panel_thickness)/2-fit,B-groove_depth])
            cube([L-24,panel_thickness+2*fit,groove_depth+eps]);
        if(front) for(i=[0:units-1]) {
            x=slot_z(i)+unit_height/2-start;
            if(x>0 && x<L)
                translate([x,B+ear_width/2,-eps])
                    cylinder(d=insert_diameter,h=insert_depth+eps);
        }
    }
}

// Tenon +X, logement d'insert ouvert vers +Z.
module tongue_x() {
    difference() {
        translate([B,(B-tenon_size)/2,(B-tenon_size)/2])
            cube([tenon_length,tenon_size,tenon_size]);
        translate([B+tenon_length/2,B/2,(B+tenon_size)/2+eps])
            bore_down(insert_diameter,insert_depth+eps);
    }
}

// Cube de jonction : coins (3 tenons) ou milieux d'aretes (2 tenons).
module node(ix,iy,iz) {
    indices=[ix,iy,iz];
    middle=(ix==1?1:0)+(iy==1?1:0)+(iz==1?1:0);
    assert(middle<=1,"Noeud invalide : choisir un coin ou milieu d'arete");
    front_mid=iy==0 && iz==1;
    difference() {
        union() {
            cube([B,B,B]);
            for(a=[0:2]) if(middle==0 || indices[a]==1)
                for(sign=indices[a]==1 ? [-1,1] : [indices[a]==0 ? 1 : -1]) {
                    // X/Y : inserts vers l'interieur Z ; Z : vers l'interieur Y.
                    if(a==0)
                        multmatrix([[sign,0,0,sign==1?0:B],
                            [0,1,0,0],[0,0,interior(iz==2?1:0),iz==2?B:0],
                            [0,0,0,1]]) tongue_x();
                    if(a==1)
                        multmatrix([[0,1,0,0],[sign,0,0,sign==1?0:B],
                            [0,0,interior(iz==2?1:0),iz==2?B:0],[0,0,0,1]]) tongue_x();
                    if(a==2)
                        multmatrix([[0,1,0,0],[0,0,interior(iy==2?1:0),iy==2?B:0],
                            [sign,0,0,sign==1?0:B],[0,0,0,1]]) tongue_x();
                }
            if(front_mid) translate([ix==0?B:-(ear_width-chassis_clearance),0,0])
                cube([ear_width-chassis_clearance,B,B]);
        }
        if(front_mid) translate([ix==0?B+ear_width/2:-ear_width/2,-eps,B/2])
            rotate([-90,0,0]) cylinder(d=insert_diameter,h=insert_depth+eps);
    }
}

// Ouvertures hexagonales : reseau triangulaire, espace minimal = web.
module honeycomb(w,h) {
    R=(hex_flat+web)/sqrt(3);
    for(i=[-1:ceil(w/(1.5*R))+1])
        for(j=[-1:ceil(h/(hex_flat+web))+1])
            translate([i*1.5*R,(j+(i%2)/2)*(hex_flat+web)])
                circle(r=hex_flat/sqrt(3),$fn=6);
}

function panel_dims(f) = (f=="left" || f=="right") ? [depth,height] :
                         f=="rear" ? [width,height] : [width,depth];

// Une tuile imprimee a plat, epaisseur 5 mm, bords pleins, languettes externes.
// Mortaises sur les deux bords internes pour les cles independantes.
module panel(f,c,r) {
    ds=panel_dims(f);
    w=(ds[0]-2*B-tile_gap)/2;
    h=(ds[1]-2*B-tile_gap)/2;
    ox=B+c*(w+tile_gap);
    oy=B+r*(h+tile_gap);
    rear=f=="rear";
    difference() {
        union() {
            cube([w,h,panel_thickness]);
            // Tabs discontinus : evitent les noeuds et les extremites des barres.
            translate([c==0?-groove_depth+fit:w,20,0])
                cube([groove_depth-fit,h-40,panel_thickness]);
            translate([20,r==0?-groove_depth+fit:h,0])
                cube([w-40,groove_depth-fit,panel_thickness]);
            if(rear) for(sx=[-1,1],sy=[-1,1]) {
                x=width/2+sx*fan_pitch/2-ox;
                y=height/2+sy*fan_pitch/2-oy;
                if(x>0 && x<w && y>0 && y<h)
                    translate([x,y,panel_thickness-eps]) cylinder(d=12,h=fan_boss+eps);
            }
        }
        translate([0,0,-eps]) linear_extrude(panel_thickness+2*eps)
            difference() {
                intersection() {
                    translate([panel_border,panel_border])
                        square([w-2*panel_border,h-2*panel_border]);
                    honeycomb(w,h);
                    if(rear) translate([width/2-ox,height/2-oy]) circle(d=fan_aperture);
                }
                if(rear) for(sx=[-1,1],sy=[-1,1])
                    translate([width/2+sx*fan_pitch/2-ox,height/2+sy*fan_pitch/2-oy])
                        circle(d=14);
            }
        // Cles 12 x 6 x 2 : logement 6.4 de profondeur, 6.4 de large, 2.4 epais.
        translate([c==0?w-6.4:-eps,h/2-3.2,(panel_thickness-2.4)/2])
            cube([6.4+eps,6.4,2.4]);
        translate([w/2-3.2,r==0?h-6.4:-eps,(panel_thickness-2.4)/2])
            cube([6.4,6.4+eps,2.4]);
        // Passage de cable dans le quartier arriere haut-droit, hors ventilateur.
        if(rear && c==1 && r==1)
            translate([w-25,h-16,-eps]) cube([12,6,panel_thickness+2*eps]);
        if(rear) for(sx=[-1,1],sy=[-1,1]) {
            x=width/2+sx*fan_pitch/2-ox;
            y=height/2+sy*fan_pitch/2-oy;
            if(x>0 && x<w && y>0 && y<h)
                translate([x,y,panel_thickness+fan_boss+eps])
                    bore_down(insert_diameter,insert_depth+eps);
        }
    }
}

module face_transform(f,explode=0) {
    if(f=="left")
        multmatrix([[0,0,1,panel_offset-explode],[1,0,0,0],[0,1,0,0],[0,0,0,1]]) children();
    if(f=="right")
        multmatrix([[0,0,-1,width-panel_offset+explode],[1,0,0,0],[0,1,0,0],[0,0,0,1]]) children();
    if(f=="bottom") translate([0,0,panel_offset-explode]) children();
    if(f=="top") translate([0,0,height-panel_offset+explode]) mirror([0,0,1]) children();
    if(f=="rear")
        multmatrix([[1,0,0,0],[0,0,-1,depth-panel_offset+explode],
                    [0,1,0,0],[0,0,0,1]]) children();
}

module panel_face(f,explode=0) {
    ds=panel_dims(f);
    w=(ds[0]-2*B-tile_gap)/2;
    h=(ds[1]-2*B-tile_gap)/2;
    face_transform(f,explode) {
        for(c=[0,1],r=[0,1])
            translate([B+c*(w+tile_gap),B+r*(h+tile_gap),0]) panel(f,c,r);
        // Quatre cles par face, a inserer avant la fermeture du cadre.
        for(r=[0,1]) translate([ds[0]/2-6,B+r*(h+tile_gap)+h/2-3,1.5]) key();
        for(c=[0,1]) translate([B+c*(w+tile_gap)+w/2+3,ds[1]/2-6,1.5])
            rotate([0,0,90]) key();
    }
}

module key() { cube([12,6,2]); }

module frame() {
    for(ix=[0:2],iy=[0:2],iz=[0:2])
        if((ix==1?1:0)+(iy==1?1:0)+(iz==1?1:0)<=1)
            color("#e8b65d") translate([coords[0][ix],coords[1][iy],coords[2][iz]])
                node(ix,iy,iz);
    for(a=[0:2],e=[0:3],h=[0:1])
        color("#405d70") edge_transform(a,e)
            translate([B+h*(beam_length(a)+B),0,0]) beam(a,e,h);
}

module fan_reference() {
    // Encombrement uniquement, pas une reproduction du cadre arrondi Noctua.
    color([0.55,0.35,0.22,0.65])
        translate([width/2,fan_front+fan_thickness/2,height/2]) rotate([90,0,0])
            difference() {
                cube([fan_size,fan_size,fan_thickness],center=true);
                cylinder(d=fan_aperture,h=fan_thickness+2,center=true);
                for(x=[-1,1],y=[-1,1]) translate([x*fan_pitch/2,y*fan_pitch/2,0])
                    cylinder(d=screw_clearance,h=fan_thickness+2,center=true);
            }
}

module assembly(explode=0) {
    frame();
    for(f=["left","right","top","bottom","rear"])
        color([0.7,0.78,0.82,1]) panel_face(f,explode);
    if(show_fan) %fan_reference();
    if(show_slots) for(i=[0:units-1])
        %translate([(width-chassis_width)/2,10,slot_z(i)])
            cube([chassis_width,fan_front-15,unit_height]);
    echo("EXTERIEUR XYZ",[width,depth,height]);
    echo("Largeur libre avant",chassis_width+2*chassis_clearance);
    echo("Face avant du ventilateur depuis Y=0",fan_front);
    echo("Avant-trou insert a calibrer",insert_diameter);
}

module coupon() {
    // Tester d'abord les 5 diametres, sans frapper une piece structurelle.
    difference() {
        cube([80,20,10]);
        for(i=[0:4]) translate([8+i*16,10,10+eps]) bore_down(3.6+i*0.1,insert_depth+eps);
        for(i=[0:4]) translate([3+i*16,1,9.4])
            linear_extrude(0.7) text(str(3.6+i*0.1),size=3);
    }
    // Echantillon de rainure 5.4 mm et languette de panneau 5 mm.
    translate([0,25,0]) difference() {
        cube([35,10,10]);
        translate([-eps,8,2.3]) cube([35+2*eps,2+eps,5.4]);
    }
    translate([40,25,0]) cube([30,15,5]);
    translate([0,42,0]) key();
}

if(part=="assembly") assembly();
if(part=="exploded") assembly(35);
if(part=="beam") beam(axis,edge,half);
if(part=="node") {
    // Mettre les tenons inferieurs sur Z=0 et garder X/Y positifs.
    translate([tenon_length,tenon_length,(node_z==1 || node_z==2)?tenon_length:0])
        node(node_x,node_y,node_z);
}
if(part=="panel") translate([groove_depth,groove_depth,0]) panel(face,column,row);
if(part=="key") key();
if(part=="coupon") coupon();
