# Rack SBC — prototype v0

Fichier autonome : `rack-sbc-test.scad`. Millimetres. Prototype a valider par
eprouvettes et montage a blanc ; aucune charge admissible n'est encore qualifiee.
Pas de chassis internes ni de fixation specifique aux cartes pour cette version.

## Dimensions

- Exterieur largeur 272,25 × hauteur 254,25 × profondeur 240.
- 5 zones de 44,45, six jeux de 2, structure de 10 en haut et en bas.
- Chassis futurs : largeur exterieure 222,25 hors oreilles.
- Passage avant 223,05 : jeu de 0,4 de chaque cote, pris sur les bandes de 15.
- Panneaux epais de 5 ; hexagones ouverts de 5 entre plats ; nervures de 2.
- Le pas 1U+jeu vaut 46,45 : ce rack n'utilise pas les percages EIA-310.
- Une fixation M3 au centre de chaque U, de chaque cote (10 inserts).

## Ventilateur

Noctua NF-A20 PWM : 200 × 200 × **32 avec patins**, entraxe 170 × 170.
Ventilateur en extraction, entierement interieur. Quatre inserts M3 dans des
bossages arriere ; vis traversant le cadre du ventilateur (longueur a mesurer
avec les patins et rondelles, ne pas talonner dans les inserts).

La face avant du ventilateur est a **197,5 mm de la face avant du rack**.
Prevoir encore du jeu pour les cables et les futurs chassis : ne pas concevoir
des plateaux de 215 ou 240 mm de profondeur. Le support/grille arriere est en
quatre quartiers ; ses bandes pleines centrales renforcent les jonctions.
Un passage de cable de 12 × 6 mm est prevu dans le quartier arriere haut-droit.
Le diametre ajoure 190 est une hypothese a confronter au cadre reel.
La grille fait environ 51 % de vide dans ses zones ajourees ; le debit reel
devra etre teste avec les cartes et leur charge thermique.

La representation du ventilateur est un encombrement transparent, exclu des STL.

## Inserts

Audiophonics reference 9288 : **insert laiton a frapper pour bois/matiere tendre**,
diametre exterieur 4, longueur 5,3, filetage M3. Ce n'est pas un insert thermique.
Le vendeur ne donne pas d'avant-trou pour une piece imprimee.

`part="coupon"` fournit des logements de 3,6 / 3,7 / 3,8 / 3,9 / 4 mm,
profondeur 5,6. La valeur 3,8 du modele est experimentale : choisir apres essais
dans le filament et l'orientation reels, puis changer `insert_diameter`.
Verifier la tenue a l'arrachement et le risque de fissuration avant montage.
Le coupon inclut aussi une rainure, une languette de 5 et une cle de panneau.

## Pieces et selection dans OpenSCAD

Modifier `part` dans le Customizer (ou en tete du fichier) :

| part | Selection | Quantite |
|---|---|---|
| assembly | Vue d'ensemble | reference |
| exploded | Panneaux ecartes de 35 mm | reference |
| beam | axis 0..2, edge 0..3, half 0..1 | 24 |
| node | node_x/y/z 0..2, au maximum une coordonnee egale a 1 | 20 |
| panel | face left/right/top/bottom/rear, column/row 0..1 | 20 |
| key | Cle de jonction 12 × 6 × 2 | 20 |
| coupon | Eprouvettes d'ajustement | 1 jeu |

**Ne pas exporter l'assemblage comme une seule piece a imprimer.**
Chaque barre mesure au plus 121,125 mm de long. Chaque panneau fait environ
128 × 119 mm au maximum avec ses languettes. Les noeuds restent sous 41 mm.
Les pieces individuelles tiennent largement sur 220 × 220, bordure comprise.
Verifier l'orientation dans le slicer : certains noeuds ont des tenons en
surplomb et peuvent demander des supports. La vue eclatee ne separe que les
panneaux ; les barres et leurs noeuds restent a leur position nominale.

## Assemblage propose

1. Imprimer les eprouvettes, puis un noeud, sa barre et un panneau pour montage
   a blanc. Valider jeux, impression des mortaises et maintien des inserts.
2. Installer les inserts des tenons AVANT d'enfiler les barres : un insert par
   tenon, soit 48 pour l'ossature. Les vis M3 traversent la peau de 2 mm des barres
   depuis leur face interieure et se vissent dans les tenons. Commencer l'essai
   avec M3 × 6, puis adapter a la geometrie reelle sans talonnage.
3. Former chaque panneau avec ses quatre tuiles et quatre cles. Les cles alignent
   les chants ; le maintien final vient des languettes dans l'ossature.
4. Assembler progressivement l'ossature autour des panneaux. Les languettes
   sont discontinues pour eviter les noeuds ; fermer les dernieres barres apres
   insertion des panneaux. Ce n'est pas un panneau qui se retire sans ouvrir
   une partie de l'ossature.
5. Poser les 10 inserts avant et les 4 inserts du support ventilateur.
6. Poser le ventilateur, verifier le degagement des pales et faire un montage
   a blanc avant de concevoir les chassis internes.

Total prevu : **62 inserts M3**, 48 vis d'ossature, 4 vis de ventilateur,
plus 10 vis pour les futurs chassis. Les 5 mm des panneaux et les sections de
10 mm sont des contraintes de conception, pas une validation de resistance.

## Utilisation

Depuis la racine du depot :

```bash
# Copier le fichier de test a l'endroit demande :
cp prototypes/rack-sbc-test.scad /tmp/rack-sbc-test.scad
env QT_QPA_PLATFORM=xcb openscad /tmp/rack-sbc-test.scad

# Exemple : eprouvette ou un quartier de panneau lateral
openscad --backend=Manifold -D 'part="coupon"' \
  -o /tmp/rack-coupon.stl /tmp/rack-sbc-test.scad
openscad --backend=Manifold -D 'part="panel"' -D 'face="left"' \
  -D 'column=0' -D 'row=0' -o /tmp/rack-panel.stl /tmp/rack-sbc-test.scad
```

Les fichiers sources sont dans `prototypes`, exclu du deploiement par `.chezmoiignore`.

## Verifications numeriques

- Rendu Manifold de l'ensemble et de la vue eclatee.
- Export et controle des 65 selections individuelles : 24 barres, 20 noeuds,
  20 panneaux et une cle. Maillages fermes et connexes, bases a Z >= 0.
- Emprise maximale des panneaux : 127,775 × 118,775 ; epaisseur jusqu'a 8
  uniquement aux bossages arriere. Toutes les pieces sont sous 210 × 210.
- Controle des intersections solides panneaux/ossature, noeuds/barres et
  encombrement ventilateur/structure : pas de volume d'interference significatif
  (tolerance numerique 0,001 mm3 ; les contacts plans sont attendus).

Ces controles ne remplacent pas la calibration des inserts, la verification du
chemin d'assemblage, ni un essai de rigidite avec les cartes installees.

Sources dimensionnelles :
- https://www.audiophonics.fr/fr/visserie-ecrou-frapper-inserts/insert-en-laiton-pour-bois-filetage-m3-unite-p-9288.html
- https://www.noctua.at/en/products/nf-a20-pwm/specifications
