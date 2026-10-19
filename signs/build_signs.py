#!/usr/bin/env python3
"""Build an editable, photograph-derived SVG sign library. No external packages."""
from pathlib import Path
import json
import html
import re
import zipfile
from label_rules import normalize_name

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'svg'
OUT.mkdir(exist_ok=True)
RED, BLUE, GREEN, INK = '#c5243d', '#086ba8', '#187a57', '#17212b'
items = []
label_overrides = json.loads((ROOT / "catalog-labels.json").read_text()) if (ROOT / "catalog-labels.json").exists() else {}

def path(d, fill=INK, stroke=None, sw=6, **attrs):
    extra = ''.join(f' {k.replace("_", "-")}="{v}"' for k,v in attrs.items())
    return f'<path d="{d}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"' if stroke else '') + extra + '/>'

def rect(x,y,w,h,fill=INK,rx=0):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"/>'

def circle(x,y,r,fill=INK,stroke=None,sw=5):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="{sw}"' if stroke else '') + '/>'

def text(s,x=100,y=110,size=42,fill=INK,weight=700,anchor='middle'):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" fill="{fill}">{html.escape(str(s))}</text>'

def group(s,transform): return f'<g transform="{transform}">{s}</g>'
def line(d,color=INK,sw=8): return path(d,'none',color,sw)
def arrow(color=INK): return path('M88 156 V78 H64 L100 39 L136 78 H112 V156 Z',color)
def turn(color=INK): return path('M80 157 V111 Q80 78 112 78 H124 V57 L157 90 L124 123 V102 H114 Q104 102 104 114 V157 Z',color)
def uturn(color=INK): return path('M49 152 V78 A43 43 0 0 1 86 35 A43 43 0 0 1 135 78 V112 H157 L123 151 L89 112 H111 V78 A19 19 0 0 0 73 78 V152 Z',color)

def person(color=INK):
    return circle(105,49,11,color)+line('M101 67 L88 104 L114 127 L122 155 M89 103 L68 149 M99 75 L124 96 L141 96 M97 75 L78 84 L66 105',color,12)

def bike(color=INK):
    return circle(55,127,26,'none',color,5)+circle(145,127,26,'none',color,5)+line('M55 127 L79 86 L108 127 H55 M79 86 H125 L108 127 M145 127 L122 71 H137 M73 76 H91',color,5)

def car(color=INK):
    return path('M48 111 L58 80 Q61 72 71 72 H130 Q140 72 143 80 L153 111 V144 H139 V132 H62 V144 H48 Z',color)+path('M64 106 L72 84 H129 L137 106 Z','white')+rect(61,115,20,9,'white',3)+rect(121,115,20,9,'white',3)

def car_side(color=INK):
    return path('M31 109 H52 L70 86 H121 L142 107 H163 V132 H31 Z',color)+path('M64 107 L77 94 H112 L126 107 Z','white')+circle(64,134,13,color)+circle(137,134,13,color)

def truck(color=INK):
    return rect(30,78,94,51,color,3)+path('M126 92 H151 L170 112 V138 H126 Z',color)+rect(134,100,14,15,'white',1)+circle(59,140,15,color)+circle(144,140,15,color)

def bus(color=INK):
    s=rect(27,75,146,64,color,8)
    for x in range(38,158,22): s+=rect(x,85,16,25,BLUE if color=='white' else 'white',2)
    return s+circle(57,140,13,color)+circle(144,140,13,color)

def motorcycle(color=INK):
    return circle(53,130,24,'none',color,6)+circle(145,130,24,'none',color,6)+path('M50 127 L77 99 H112 L128 115 H81 L69 131 Z',color)+line('M101 81 H124 L146 130 M72 95 H91',color,7)

def tractor(color=INK):
    return circle(76,131,28,color)+circle(148,142,17,color)+circle(76,131,14,'white')+circle(76,131,8,color)+path('M51 98 H107 V118 H152 V98 H110 V80 H88 V54 H80 V86 H58 V65 H50 Z',color)

def cow(color=INK):
    return path('M43 85 Q70 71 112 82 L132 67 L155 70 L170 84 L153 96 H136 L127 119 L126 150 H115 L109 123 H75 L66 151 H55 L57 118 L45 109 L40 134 H32 L34 94 L24 114 L20 109 L33 84 Z',color)+path('M138 73 L131 57 L145 67 L153 57 L156 74 Z',color)

def horse(color=INK):
    return path('M28 111 L45 86 L100 87 L115 69 L118 48 L135 59 L153 79 L147 91 L132 85 L121 110 L137 145 L126 150 L105 120 H76 L58 151 L47 147 L57 115 L42 105 L31 136 L21 133 Z',color)

def deer(color=INK):
    return path('M33 105 L53 88 L98 88 L125 65 L130 85 L113 110 L132 139 L122 144 L99 117 H70 L48 145 L38 139 L53 112 Z',color)+line('M124 72 L134 51 L145 45 M134 52 L128 42 M132 62 L150 57',color,5)

def plane(color=INK):
    return path('M94 28 H106 L110 81 L165 111 V124 L109 107 L107 148 L128 161 V172 L100 163 L72 172 V161 L93 148 L91 107 L35 124 V111 L90 81 Z',color)

def train(color=INK):
    return path('M37 97 H111 V64 H136 V94 H157 V124 H37 Z',color)+rect(42,83,58,18,color)+circle(56,130,13,color)+circle(91,130,13,color)+circle(138,130,13,color)+circle(141,53,13,color)+circle(122,43,11,color)

def pedestrians(color=INK):
    return group(person(color),'translate(1 17) scale(.76)')+group(person(color),'translate(78 47) scale(.58)')

def fence(color=INK):
    s=rect(38,100,124,9,color)+rect(38,125,124,8,color)
    for x in range(47,160,20): s+=path(f'M{x} 145 V91 L{x+5} 82 L{x+10} 91 V145 Z',color)
    return s

def roundabout(color=INK):
    s=''
    for a in [0,120,240]:
        s+=group(line('M78 54 A50 50 0 0 1 145 94',color,13)+path('M127 84 L151 108 L165 77 Z',color),f'rotate({a} 100 100)')
    return s

def add(code,label,category,art,source='IMG-20261014-WA0091.jpg',note='',width=200,height=200):
    slug=re.sub(r'[^a-z0-9]+','-',label.lower()).strip('-')
    ident=f'{code.lower()}-{slug}'
    junction_names = {
        'I28': 'Ferry service',
        'W27': 'Junction ahead',
        'W28A': 'Junction with minor roads on both sides ahead',
        'W28B': 'Junction with a minor road joining from the right ahead',
        'W29': 'Junction with an accelerating lane from the right ahead',
    }
    label=junction_names.get(code,label)
    label=label_overrides.get(ident,normalize_name(label,category))
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n<title id="title">{html.escape(label)}</title>\n<desc id="desc">Redrawn from {source}. {html.escape(note or "Photo-derived artwork; verify against the applicable road-sign standard before instructional use.")}</desc>\n{art}\n</svg>\n'
    (OUT/f'{ident}.svg').write_text(svg)
    items.append(dict(id=ident,code=code,label=label,category=category,svg=f'svg/{ident}.svg',source=source,status='needs-verification',notes=note or 'Photo-derived reconstruction; label and geometry require verification.'))

def warning(code,label,icon,note=''):
    frame=path('M100 16 L190 179 H10 Z',RED,RED,9)+path('M100 39 L172 168 H28 Z','white')
    add(code,label,'Warning',frame+group(icon,'translate(36 51) scale(.64)'),note=note)

warning('W01','Bend left',line('M117 158 V116 Q117 97 94 87 L72 76',sw=21))
warning('W02','Bend right',line('M83 158 V116 Q83 97 106 87 L128 76',sw=21))
warning('W03','Double bend first left',line('M124 155 V113 L76 131 V74',sw=19))
warning('W04','Double bend first right',line('M76 155 V113 L124 131 V74',sw=19))
warning('W05','Steep descent',path('M27 154 H174 L27 109 Z')+group(car_side(),'translate(17 33) scale(.72) rotate(17 100 100)'), 'Gradient number is unreadable in the photo and has been omitted.')
warning('W06','Steep ascent',path('M27 154 H174 V109 Z')+group(car_side(),'translate(17 33) scale(.72) rotate(-17 100 100)'), 'Gradient number is unreadable in the photo and has been omitted.')
warning('W07','Road narrows on both sides',line('M68 155 V116 L80 96 V63 M132 155 V116 L120 96 V63',sw=13))
warning('W08','Road narrows on right',line('M70 155 V64 M132 155 V115 L115 94 V64',sw=13))
warning('W09','Road narrows on left',line('M130 155 V64 M68 155 V115 L85 94 V64',sw=13))
warning('W10','Quayside or river bank',path('M30 105 H111 V146 H30 Z')+group(car_side(),'translate(29 -15) scale(.7) rotate(30 100 100)')+line('M117 139 Q129 131 140 139 T164 139 M112 151 Q124 143 136 151 T164 151',sw=4))
warning('W11','Uneven road',path('M26 153 Q43 121 64 144 Q83 103 105 143 Q129 119 150 147 L173 155 Z'))
warning('W12','Road hump',path('M27 152 H57 Q100 102 143 152 H173 V162 H27 Z'))
warning('W13A','Dip in road',path('M26 130 H54 Q100 173 146 130 H174 V161 H26 Z'))
warning('W13B','Ford',path('M25 129 H48 Q100 175 151 129 H175 V166 H25 Z')+line('M68 125 Q79 120 90 125 T112 125 T134 125 M65 135 Q77 130 89 135 T113 135 T137 135',sw=3))
warning('W14','Slippery road',group(car(),'translate(28 5) scale(.7) rotate(14 100 100)')+line('M76 112 C46 131 115 130 72 157 M119 116 C91 139 151 135 115 159',sw=6))
warning('W15','Loose stones',path('M25 156 H175 V164 H25 Z')+group(car_side(),'translate(83 57) scale(.48)')+line('M105 146 L54 126 M104 139 L73 101 M111 134 L98 94',sw=3)+circle(55,120,4)+circle(72,94,4)+circle(90,110,3)+circle(53,142,3))
warning('W16','Falling rocks',path('M27 163 L65 63 L101 163 Z')+path('M99 78 L110 70 L119 81 L110 91 Z M115 103 L129 99 L135 113 L121 120 Z M127 139 L139 126 L151 140 L144 151 Z'))
warning('W17','Pedestrian crossing',group(person(),'translate(26 10) scale(.78)')+line('M39 160 H60 M72 160 H93 M105 160 H126 M138 160 H159',sw=4))
warning('W18','Children crossing',pedestrians())
warning('W19','Cyclists',group(bike(),'translate(17 31) scale(.83)')+circle(101,69,10)+line('M97 84 L82 105 L113 117 M99 85 L119 97 H135',sw=9))
warning('W20','Cattle',group(cow(),'translate(10 28) scale(.9)'))
warning('W21','Wild animals',group(deer(),'translate(10 19) scale(.9)'))
warning('W22','Road works',circle(100,65,10)+line('M96 82 L85 111 L71 151 M86 111 L110 149 M96 87 L118 101 M117 90 L141 146',sw=10)+path('M117 158 L148 130 L173 158 Z'))
warning('W23','Traffic signals',rect(82,60,36,96,INK,8)+circle(100,78,12,RED)+circle(100,108,12,'#e5ab23')+circle(100,138,12,GREEN))
warning('W24','Low flying aircraft',group(plane(),'translate(20 24) scale(.8) rotate(-35 100 100)'))
warning('W25','Two way traffic',group(arrow(),'translate(0 29) scale(.7)')+group(arrow(),'translate(60 29) scale(.7) rotate(180 100 100)'))
warning('W26','Other danger',rect(90,65,20,62,INK,8)+circle(100,148,11))
warning('W27','Crossroads',line('M64 84 L136 156 M136 84 L64 156',sw=16), 'X-shaped junction symbol corrected to the user sketch on 2026-10-17.')
warning('W28A','Junction ahead with priority',path('M84 75 L100 57 L116 75 V105 H155 V122 H116 V160 H84 V122 H45 V105 H84 Z'), 'Thick main road with thinner minor roads on both sides, matching the user sketch.')
warning('W28B','Side road on right',path('M84 75 L100 57 L116 75 V105 H155 V122 H116 V160 H84 Z'), 'Thick main road with a thinner minor road joining from the right, matching the user sketch.')
warning('W29','Merging traffic from left',path('M84 75 L100 57 L116 75 V98 L150 135 L138 147 L116 123 V160 H84 Z'), 'Thick main road with an angled accelerating lane joining from the lower right, matching the user sketch.')
warning('W30','Roundabout ahead',group(roundabout(),'translate(26 32) scale(.74)'))
warning('W31','Level crossing with gate',group(fence(),'translate(5 18) scale(.95)'))
warning('W32','Level crossing without gate',group(train(),'translate(16 28) scale(.84)'))

def disc(icon,color=BLUE): return circle(100,100,91,color)+circle(100,100,87,'none','white',2)+icon
def mandatory(code,label,icon,note=''): add(code,label,'Mandatory',disc(icon),note=note)
mandatory('M01','Turn left',group(arrow('white'),'rotate(-90 100 100)'))
mandatory('M02','Ahead only',arrow('white'))
mandatory('M03','Turn right ahead',turn('white'))
mandatory('M04','Ahead or right',arrow('white')+path('M99 96 H136 V75 L169 108 L136 141 V120 H99 Z','white'))
mandatory('M05','Keep left',group(arrow('white'),'rotate(-135 100 100)'))
mandatory('M06','Cycle route',bike('white'))
mandatory('M07','Minimum speed 30',text('30',y=126,size=80,fill='white'))
mandatory('M08','Pedestrian route',pedestrians('white'))
mandatory('M09','Cattle route',cow('white'), 'Animal silhouette and official sign meaning require verification.')
mandatory('M10','End of minimum speed 30',text('30',y=126,size=80,fill='white')+line('M55 154 L149 46',RED,10)+line('M44 144 L138 36',RED,5)+line('M66 165 L160 57',RED,5))
add('EX01','U turn arrow','Mandatory',disc(uturn('white')),'IMG-20261014-WA0092.jpg','Separate blue U-turn sign to the right of the poster; verify its intended use.')

def ring(icon,slash=False):
    return circle(100,100,91,RED)+circle(100,100,74,'white')+icon+(line('M43 39 L158 162',RED,16) if slash else '')
def regulatory(code,label,icon,slash=False,note=''):
    add(code,label,'Regulatory',ring(icon,slash),note=note)

add('R01','Stop','Regulatory',path('M61 9 H139 L191 61 V139 L139 191 H61 L9 139 V61 Z',RED)+path('M64 16 H136 L184 64 V136 L136 184 H64 L16 136 V64 Z','none','white',3)+text('STOP',y=120,size=53,fill='white'))
add('R02','Give way','Regulatory',path('M12 15 H188 L100 186 Z',RED)+path('M37 32 H163 L100 148 Z','white'))
# No entry has a solid red face rather than the white face used by the other restrictions.
add('P01','No entry','Regulatory',circle(100,100,91,RED)+rect(36,85,128,30,'white'))
regulatory('P02','No vehicles', '')
regulatory('P03','No motor cars',group(car(),'translate(17 17) scale(.83)'),True)
regulatory('P04','No motorcycles',group(motorcycle(),'translate(14 14) scale(.86)'),True)
regulatory('P05','No bicycles',group(bike(),'translate(14 14) scale(.86)'),True)
regulatory('P06','No pedestrians',group(person(),'translate(14 14) scale(.86)'),True)
regulatory('P07','No animal drawn vehicles',group(horse(),'translate(54 45) scale(.57)')+rect(37,95,54,26)+circle(51,130,14)+circle(87,130,10),True,'The cart and animal are reconstructed silhouettes; confirm against a clearer original.')
regulatory('P08','No handcarts',rect(41,103,78,15)+circle(65,133,18)+line('M117 104 L135 90',sw=7)+group(person(),'translate(91 37) scale(.58)'),True)
regulatory('P09','No tractors',group(tractor(),'translate(14 14) scale(.86)'),True)
regulatory('P10','No goods vehicles',group(truck(),'translate(14 14) scale(.86)'),True)
regulatory('P11','No motor vehicles',group(car(),'translate(48 21) scale(.52)')+group(motorcycle(),'translate(43 84) scale(.57)'),True)
regulatory('P12','No motor vehicles or animal drawn vehicles',group(car(),'translate(48 9) scale(.52)')+group(horse(),'translate(34 85) scale(.45)')+group(motorcycle(),'translate(92 87) scale(.4)'),True,'The lower symbols are small in the source; this combination needs confirmation.')
regulatory('P13','Maximum width 2 m',text('2m',y=120,size=57)+path('M30 100 L47 88 V112 Z M170 100 L153 88 V112 Z'))
regulatory('P14','Maximum height 3.5 m',text('3.5m',y=119,size=46)+path('M100 44 L86 28 H114 Z M100 156 L86 172 H114 Z'))
regulatory('P15','Maximum gross weight 5 t',text('5',x=88,y=125,size=73)+text('T',x=125,y=105,size=35))
regulatory('P16','Maximum axle weight 2 t',text('2T',y=87,size=40)+rect(54,122,92,9)+rect(52,106,13,39,INK,5)+rect(135,106,13,39,INK,5)+path('M96 91 H104 V106 H113 L100 119 L87 106 H96 Z'))
regulatory('P17','Maximum vehicle length 10 m',group(truck(),'translate(39 11) scale(.61)')+text('10m',y=144,size=32)+path('M39 134 L55 126 V142 Z M161 134 L145 126 V142 Z'))
regulatory('P18','Minimum following distance 70 m',text('70m',y=96,size=43)+group(car_side(),'translate(14 68) scale(.46)')+group(car_side(),'translate(93 68) scale(.46)'),False,'The photographed sign shows 70 m; verify the official label and vehicle silhouettes.')
regulatory('P19','No left turn',group(turn(),'translate(200 0) scale(-1 1)'),True)
regulatory('P20','No right turn',turn(),True)
regulatory('P21','No U turn',group(uturn(),'translate(18 18) scale(.82)'),True)
regulatory('P22','No overtaking',group(car(),'translate(21 41) scale(.57)')+group(car(RED),'translate(91 41) scale(.57)'))
regulatory('P23','No overtaking by goods vehicles',group(car(),'translate(19 52) scale(.52)')+group(truck(RED),'translate(93 38) scale(.51)'))
regulatory('P24','Maximum speed 50',text('50',y=127,size=79))
regulatory('P25','No sounding horn',path('M48 88 H72 L114 66 V137 L72 115 H48 Z')+line('M117 100 C161 73 162 125 122 118',sw=7),True)
regulatory('P26','Stop children crossing',rect(38,92,124,20)+text('STOP',y=76,size=25)+text('CHILDREN',y=144,size=19))
regulatory('P27','Give priority to oncoming traffic',group(arrow(RED),'translate(13 30) scale(.66)')+group(arrow(),'translate(76 30) scale(.66) rotate(180 100 100)'))
def end_slashes():
    return ''.join(line(f'M{42+i*8} {158+i*0} L{145+i*8} 55',INK,3) for i in range(4))
add('P28','End of restrictions','Regulatory',circle(100,100,90,'white',INK,2)+end_slashes())
add('P29','End of maximum speed 40','Regulatory',circle(100,100,90,'white',INK,2)+text('40',y=126,size=78)+end_slashes())
add('P30','No parking','Regulatory',circle(100,100,91,RED)+circle(100,100,74,BLUE)+line('M43 39 L158 162',RED,16))
add('P31','No stopping','Regulatory',circle(100,100,91,RED)+circle(100,100,74,BLUE)+line('M43 39 L158 162 M158 39 L43 162',RED,15))
add('P32','No parking zone','Regulatory',rect(13,5,174,190,'white',9)+path('M22 6 H178 Q187 6 187 15 V185 Q187 195 177 195 H23 Q13 195 13 185 V16 Q13 6 22 6 Z','none',INK,2)+group(circle(100,100,91,RED)+circle(100,100,74,BLUE)+line('M43 39 L158 162',RED,16),'translate(32 4) scale(.68)')+text('ZONE',y=177,size=33))

SRC2='IMG-20261014-WA0092.jpg'
def panel(icon,bg=BLUE):
    return rect(13,8,174,184,'white',10)+rect(17,12,166,176,bg,8)+rect(24,19,152,162,'none',4)+icon
def info(code,label,icon,note=''):
    add(code,label,'Information and services',panel(icon),SRC2,note)
def inset(icon): return rect(42,38,116,124,'white',3)+group(icon,'translate(35 32) scale(.65)')
info('I01','Parking',text('P',y=146,size=128,fill='white'))
info('I02','Parking 500 m',text('Parking',y=88,size=34,fill='white')+text('500m',y=130,size=38,fill='white'))
info('I03','Pedestrian crossing information',path('M100 32 L167 161 H33 Z','white')+group(person(),'translate(35 46) scale(.63)')+line('M59 157 H73 M81 157 H95 M103 157 H117 M125 157 H139',BLUE,3))
info('I04','Hospital',text('H',y=129,size=114,fill='white')+text('Hospital',y=168,size=25,fill='white'))
info('I05','One way right',group(arrow('white'),'rotate(90 100 100)'))
info('I06','One way left',group(arrow('white'),'translate(22 4) scale(.78) rotate(-90 100 100)')+text('ONE WAY',y=170,size=23,fill='white'))
info('I07','No through road',rect(88,75,24,85,'white')+rect(51,49,98,29,RED))
info('I08','Cycle facility',bike('white'))
info('I09','In',text('IN',y=129,size=78,fill='white'))
info('I10','Out',text('OUT',y=124,size=62,fill='white'))
info('I11','No entry text',text('NO',y=87,size=42,fill='white')+text('ENTRY',y=134,size=37,fill='white'))
info('I12','No exit text',text('NO',y=87,size=42,fill='white')+text('EXIT',y=134,size=42,fill='white'))
info('I13','Taxi',text('Taxi',y=122,size=62,fill='white'))
info('I14','Bus stop',group(bus('white'),'translate(6 0) scale(.94)'))
info('I15','Priority over oncoming traffic',group(arrow('white'),'translate(12 22) scale(.73)')+group(arrow(RED),'translate(76 22) scale(.73) rotate(180 100 100)'))
info('I16','First aid',rect(37,30,126,142,'white',3)+rect(85,57,30,88,RED)+rect(56,86,88,30,RED))
info('I17','Telephone',inset(path('M78 39 Q58 37 58 59 V126 Q58 153 81 156 L104 143 L95 118 L77 124 V72 L94 74 L103 45 Z')))
info('I18','Fuel station',inset(rect(46,64,65,93,INK,6)+rect(55,75,47,30,'white',3)+rect(34,152,91,10)+line('M112 92 Q143 80 143 107 V133 Q143 148 129 140 L126 76 L140 57',sw=7)))
info('I19','Accommodation',inset(rect(38,102,125,35)+rect(33,83,8,72)+rect(157,107,8,48)+circle(62,89,11)+path('M79 84 H136 Q157 84 157 103 H79 Z')))
info('I20','Restaurant',inset(line('M58 48 V78 Q58 94 77 94 V155 M76 47 V79 M93 48 V78 Q93 94 77 94 M133 47 V155 M133 47 Q105 78 133 102',sw=9)))
info('I21','Refreshments',inset(path('M45 77 H132 L121 129 Q114 145 87 145 Q60 145 55 129 Z')+path('M132 83 H155 Q172 115 128 125','none',INK,8)+rect(40,151,110,6)))
info('I22','Picnic site',inset(path('M100 36 L64 88 H81 L54 121 H89 V158 H111 V121 H146 L119 88 H136 Z')+rect(27,145,67,7)+rect(35,152,7,18)+rect(75,152,7,18)))
info('I23','Walking route',inset(pedestrians()))
info('I24','Camping site',inset(path('M100 44 L166 150 H34 Z')+path('M100 87 L135 150 H65 Z','white')+line('M91 42 L109 60 M109 42 L91 60',sw=5)))
info('I25','Caravan site',inset(rect(31,72,132,65,INK,22)+rect(48,89,27,23,'white',3)+rect(89,89,27,23,'white',3)+circle(66,141,12)+line('M157 135 H179',sw=7)))
info('I26','Camping and caravan site',inset(group(path('M100 20 L163 86 H37 Z')+path('M100 45 L131 86 H69 Z','white'),'translate(0 2)')+rect(40,105,121,43,INK,17)+circle(65,152,10)+rect(61,114,23,17,'white',2)+rect(99,114,23,17,'white',2)))
info('I27','Youth hostel',inset(path('M100 54 L153 99 H141 V154 H62 V99 H49 Z')+rect(89,111,25,43,'white')+path('M37 42 L16 83 H29 L11 113 H32 V155 H43 V113 H60 L43 83 H56 Z')))
info('I28','Harbour or ferry',inset(line('M100 61 V136 M67 91 H133 M48 114 Q100 170 152 114 M48 114 L47 134 M152 114 L153 134',sw=8)+circle(100,49,12,'none',INK,6)+path('M26 166 H174 L157 184 H43 Z')),'Anchor symbol is clear, but the exact service label must be confirmed.')
info('I29','Spanner service symbol',inset(path('M92 63 L72 54 V43 L126 36 V51 L108 59 V113 Q121 135 109 162 H93 Q81 134 92 113 Z')+rect(70,72,62,9)), 'The small original resembles a spanner; service meaning and silhouette need a clearer reference.')

def board(code,label,art,w=320,h=200,bg=GREEN,note=''):
    outline=rect(2,2,w-4,h-4,'white',12)+rect(6,6,w-12,h-12,bg,10)+f'<rect x="12" y="12" width="{w-24}" height="{h-24}" rx="7" fill="none" stroke="white" stroke-width="2"/>'
    add(code,label,'Directions',outline+art,SRC2,note,width=w,height=h)

board('D01','Taveta A23 advance direction',text('Taveta',x=26,y=43,size=28,fill='white',anchor='start')+text('A 23',x=26,y=75,size=25,fill='#f3d56b',anchor='start')+path('M218 157 V49 L207 36 L196 49 V91 L161 65 L146 80 L196 120 V157 Z','white')+text('1 km',x=164,y=182,size=25,fill='white'))
board('D02','Eldoret A104 and Njoro C56',text('Eldoret',x=23,y=44,size=29,fill='white',anchor='start')+text('A 104',x=159,y=44,size=26,fill='#f3d56b',anchor='start')+text('Njoro',x=25,y=121,size=27,fill='white',anchor='start')+text('C 56',x=25,y=152,size=25,fill='#f3d56b',anchor='start')+path('M240 180 V78 L228 60 L215 78 V137 L159 110 L148 129 L215 164 V180 Z','white'),w=290,h=220)
board('D03','Nakuru Elementaita and Ol Kalou',text('Nakuru',x=160,y=38,size=25,fill='white')+text('A 104',x=160,y=62,size=20,fill='#f3d56b')+path('M150 168 V80 H168 V108 H277 V124 H168 V168 Z M150 108 H38 V124 H150 Z','white')+text('Elementaita',x=30,y=151,size=19,fill='white',anchor='start')+text('D 320',x=30,y=175,size=19,fill='white',anchor='start')+text('Ol Kalou',x=203,y=151,size=20,fill='white',anchor='start')+text('C 69',x=203,y=175,size=19,fill='white',anchor='start'))
board('D04','Nakuru and Thika roundabout',text('Nakuru A 104',x=160,y=37,size=23,fill='white')+circle(150,104,32,'none','white',12)+path('M144 68 V48 H156 V68 M119 98 H63 V110 H119 M144 140 V176 H156 V140 M177 114 L222 145 L230 135 L184 104 Z','white')+text('Thika',x=242,y=164,size=24,fill='white')+text('(A 2)',x=242,y=187,size=20,fill='#f3d56b'))
board('D05','Garissa A3 roundabout',circle(140,92,30,'none','white',12)+path('M111 85 H51 V99 H111 M133 122 V175 H147 V122 M170 85 H229 V99 H170 M119 67 V34 H131 V63 M140 62 V34 H152 V64 M160 69 V34 H172 V77 Z','white')+text('Garissa',x=239,y=144,size=25,fill='white')+text('A 3',x=239,y=173,size=24,fill='#f3d56b'))

def white_board(code,label,art,w=320,h=200,note=''):
    add(code,label,'Directions',rect(4,4,w-8,h-8,'white',10)+f'<rect x="9" y="9" width="{w-18}" height="{h-18}" rx="8" fill="none" stroke="{INK}" stroke-width="5"/>'+art,SRC2,note,width=w,height=h)

white_board('D06','Kitale Kongoni and Kipsain',text('Kitale C 51',x=160,y=36,size=25)+path('M150 157 V52 H167 V83 H272 V100 H167 V157 Z M150 83 H46 V100 H150 Z')+text('Kongoni',x=73,y=134,size=22)+text('D 342',x=73,y=161,size=21)+text('Kipsain',x=240,y=134,size=22)+text('D 342',x=240,y=161,size=21))
white_board('D07','Bungoma Eldoret and Malaba',text('Bungoma C 33',x=160,y=36,size=25)+path('M151 155 V52 H168 V83 H271 L286 92 L271 101 H168 V155 Z M151 83 H48 V101 H151 Z')+text('Eldoret',x=77,y=135,size=22)+text('A104',x=77,y=163,size=21)+text('Malaba',x=241,y=135,size=22)+text('A104',x=241,y=163,size=21))
white_board('D08','Kongoni D323 junction',text('Kongoni',x=97,y=113,size=26)+text('D 323',x=97,y=145,size=24)+path('M238 48 H257 V157 H238 V85 H125 V67 H238 Z'))
board('D09','Nanyuki and Nyeri direction',text('Nanyuki',x=34,y=46,size=25,fill='white',anchor='start')+text('A 2',x=34,y=72,size=20,fill='#f3d56b',anchor='start')+text('Nyeri',x=34,y=110,size=25,fill='white',anchor='start')+text('(B 5)',x=34,y=137,size=20,fill='#f3d56b',anchor='start')+path('M228 35 L277 86 L228 137 H206 L255 86 L206 35 Z','white'),h=170,note='Small place and route text is uncertain in the photograph; all text on this board needs checking.')
board('D10','Malindi B8 direction',text('Malindi',x=170,y=70,size=34,fill='white')+text('B 8',x=170,y=112,size=27,fill='#f3d56b')+group(arrow('white'),'translate(3 8) scale(.65) rotate(-35 100 100)'),h=150)

def finger(code,label,rows,left=False,bg='white',note=''):
    fg=INK if bg=='white' else 'white'
    art=path('M9 9 H267 L310 70 L267 131 H9 Z',bg,fg,5)+path('M254 26 L285 70 L254 114','none',fg,9)
    for i,s in enumerate(rows): art+=text(s,x=139,y=(68 if len(rows)==1 else 55+i*36),size=28 if len(s)<16 else 23,fill=fg)
    if left:
        art=path('M53 9 H311 V131 H53 L10 70 Z',bg,fg,5)+path('M66 26 L35 70 L66 114','none',fg,9)
        for i,s in enumerate(rows): art+=text(s,x=185,y=(79 if len(rows)==1 else 58+i*36),size=28 if len(s)<16 else 23,fill=fg)
    add(code,label,'Directions',art,SRC2,note,width=320,height=140)
finger('D11','Ainabkoi C56 direction',['Ainabkoi','C 56'])
finger('D12','Kaiboi 40 km C37 direction',['Kaiboi 40 km','C 37'],left=True,note='The small direction arrow and place spelling should be checked against the original sign.')
white_board('D13','Kitale Kongoni and Kipsain route list',text('↑ Kitale C 51',x=160,y=52,size=28)+text('← Kongoni D 342',x=160,y=103,size=26)+text('Kipsain D 342 →',x=160,y=153,size=26))
board('D14','Sagana Nyeri and Nanyuki distances',text('Sagana   53 km',x=160,y=53,size=25,fill='white')+text('(Nyeri)   103 km',x=160,y=98,size=25,fill='white')+text('Nanyuki 145 km',x=160,y=143,size=25,fill='white'),h=180,note='Distances and place names are transcribed from a very small board; verify all three lines.')
board('D15','A3 route marker',text('A 3',y=133,size=78,fill='#f3d56b'),w=200)
board('D16','R route marker green',text('R',y=139,size=102,fill='white'),w=200)
white_board('D17','C33 Myanga and Mungatsi distances',text('C 33',x=160,y=48,size=27)+text('Myanga   8 km',x=160,y=99,size=28)+text('Mungatsi 32 km',x=160,y=145,size=27),note='Place spelling and distances need verification against a higher resolution source.')
white_board('D18','C60 route marker',text('C 60',y=126,size=58),w=200)
white_board('D19','R route marker white',text('R',y=139,size=102),w=200)
white_board('D20','ELD50 location marker',rect(22,38,276,122)+text('ELD 50',x=160,y=119,size=66,fill='white'))
finger('D21','Airport 2 direction',['Airport 2'],left=True,note='The numeral 2 is visible; the unit is not shown. Aircraft pictogram included separately below.')
# Add the small aircraft pictogram without converting any text into a bitmap.
airport=OUT/'d21-airport-2-direction.svg'
airport.write_text(airport.read_text().replace('</svg>',group(plane(),'translate(250 43) scale(.25) rotate(-90 100 100)')+'</svg>'))
finger('D22','Nairobi Hospital direction',['Nairobi','Hospital'])
finger('D23','Free car park direction',['Free','Car Park'])
finger('D24','Toilets direction',['Toilets'],left=True)
white_board('D25','Mombasa place name',text('MOMBASA',x=160,y=85,size=39),h=140)

for code,label in [('S01','Mbagathi Ridge'),('S02','Moi Avenue'),('S03','Kindaruma Lane')]:
    white_board(code,label+' street name',text(label.upper(),x=220,y=71,size=32),w=440,h=110)

def crossbuck(y=0): return group(path('M22 37 L100 71 L178 37 L189 58 L127 87 L189 116 L178 137 L100 103 L22 137 L11 116 L73 87 L11 58 Z','white',RED,6),f'translate(0 {y})')
add('W33','Single track railway crossing','Warning',crossbuck(12),SRC2)
add('W34','Multiple track railway crossing','Warning',group(crossbuck()+crossbuck(85),'translate(17 -7) scale(.83)'),SRC2)
add('S04','Red and white hazard marker','Hazard markers',rect(6,26,188,148,'white',5)+path('M16 72 L16 40 L48 40 Z M184 72 L184 40 L152 40 Z M16 124 L16 92 L68 40 L94 40 L94 46 Z M184 124 L184 92 L132 40 L106 40 L106 46 Z M16 144 L94 66 L94 98 L32 160 L16 160 Z M184 144 L106 66 L106 98 L168 160 L184 160 Z M94 118 L94 150 L84 160 L52 160 Z M106 118 L106 150 L116 160 L148 160 Z',RED),SRC2)
def chevrons(right=False):
    s=rect(5,51,190,98,'#f2bf42')
    for x in [15,70,125]: s+=path(f'M{x+37} 54 L{x+7} 100 L{x+37} 146 H{x+19} L{x-11} 100 L{x+19} 54 Z')
    return group(s,'translate(200 0) scale(-1 1)') if right else s
add('W35A','Chevron alignment left','Hazard markers',chevrons(),SRC2)
add('W35B','Chevron alignment right','Hazard markers',chevrons(True),SRC2)
add('W36','Hazard marker upward chevrons','Hazard markers',rect(45,8,110,184,'#f2bf42')+path('M48 75 L100 23 L152 75 V104 L100 52 L48 104 Z M48 139 L100 87 L152 139 V168 L100 116 L48 168 Z'),SRC2)
add('W37','Hazard marker diagonal stripes','Hazard markers',rect(45,8,110,184,'#f2bf42')+path('M48 8 H76 L152 84 V115 L48 11 Z M48 50 L152 154 V185 L48 81 Z M48 120 L120 192 H89 L48 151 Z'),SRC2)
panel_art = []
for code,label,art in [
    ('A01','Direction right',group(arrow(),'rotate(90 100 100)')),
    ('A02','Direction both ways',group(arrow(),'translate(0 20) scale(.8) rotate(-90 100 100)')+group(arrow(),'translate(40 20) scale(.8) rotate(90 100 100)')),
    ('A03','Direction left',group(arrow(),'rotate(-90 100 100)')),
    ('A04','Distance 15 m',text('15m',y=83,size=36)+line('M44 124 H156',sw=7)+path('M35 124 L55 110 V138 Z M165 124 L145 110 V138 Z')),
]:
    panel_art.append(rect(7,37,186,126,'white',3)+path('M7 37 H193 V163 H7 Z','none',INK,3)+group(art,'translate(20 20) scale(.8)'))

combined_panels = ''.join(group(art, f'translate({(i % 2) * 200} {(i // 2) * 180})') for i, art in enumerate(panel_art))
add('AP01','Additional panels','Supplementary plates',combined_panels,note='Combined right arrow, both-way arrow, left arrow, and 15 m distance panels at the user request. Classification remains for review.',width=400,height=360)

# Preview is a static local review artifact. Labels edited here can be exported as JSON.
(ROOT/'manifest.json').write_text(json.dumps(items,indent=2,ensure_ascii=False)+'\n')
DATA=json.dumps(items,ensure_ascii=False).replace('</','<\\/')
PAGE='''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Road signs — SVG review library</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f2f5f7;color:#152534;font:16px system-ui,sans-serif}header{padding:36px 5vw 24px;background:#112b36;color:white}h1{font-size:32px;margin:0 0 12px}p{max-width:850px;line-height:1.55}header p{color:#bfd1da}nav{display:flex;flex-wrap:wrap;gap:12px;padding:20px 5vw;background:white;position:sticky;top:0;z-index:2;border-bottom:1px solid #dce3e8}input,select,button{font:inherit;border:1px solid #bac8d1;border-radius:7px;padding:10px 12px}button{cursor:pointer;background:#0b6487;color:white;border:none}#search{flex:1;min-width:180px}#count{padding:14px 5vw;color:#4f626e}main{padding:0 5vw 40px;display:grid;grid-template-columns:repeat(auto-fill,minmax(235px,1fr));gap:20px}article{background:white;border:1px solid #dce3e8;border-radius:12px;padding:18px;display:flex;flex-direction:column;gap:10px}article img{width:100%;height:170px;object-fit:contain;margin-bottom:8px}article input{width:100%;font-size:14px;font-weight:600}small{font-size:12px;color:#637986}a{color:#07628a;font-size:13px}details{font-size:12px;color:#566a78;line-height:1.5}footer{padding:20px 5vw 40px;color:#566a78}.badge{font-size:11px;background:#fff2cc;color:#79601d;border-radius:4px;padding:4px 6px;align-self:flex-start}.tools{display:flex;gap:10px;align-items:center}
</style>
<header><h1>Road sign SVG library</h1><p>Individual vector redraws from your two road-sign poster photos and the separate blue U-turn sign. Search, filter, edit labels, and export the updated catalog. These are photo-derived drafts; every sign remains marked for verification.</p></header>
<nav><input id="search" placeholder="Search labels or IDs" aria-label="Search signs"><select id="category" aria-label="Category"><option value="">All categories</option></select><button id="export">Export labels JSON</button><button id="import">Import labels JSON</button><input id="importFile" type="file" accept=".json,application/json" hidden><button id="reset">Reset labels</button></nav><div id="count" role="status"></div><main id="grid"></main><footer>SVG artwork has transparent outer backgrounds. White sign faces are intentional. Text remains editable SVG text. Label edits are stored in this browser when storage is available; use Export labels JSON to save them to a file.</footer>
<script src="label-rules.js"></script>
<script>
const original=__DATA__;
let records=structuredClone(original);let storageOK=true;
// Saved labels are authoritative: never reapply naming rules on refresh.
try{
  const raw=localStorage.getItem('drive-test-sign-labels-v1');
  const saved=JSON.parse(raw||'{}');
  if(!localStorage.getItem('drive-test-ferry-name-restored-v1')){
    if(raw) localStorage.setItem('drive-test-labels-before-ferry-restore-v1',raw);
    if(saved['i28-harbour-or-ferry']==='Harbour or ferry') saved['i28-harbour-or-ferry']='Ferry service';
    if(raw) localStorage.setItem('drive-test-sign-labels-v1',JSON.stringify(saved));
    localStorage.setItem('drive-test-ferry-name-restored-v1','1');
  }
  restoreExportedNames(saved);
  records.forEach(r=>{if(typeof saved[r.id]==='string')r.label=saved[r.id]});
}catch(e){storageOK=false}

const grid=document.querySelector('#grid'),search=document.querySelector('#search'),category=document.querySelector('#category');
[...new Set(records.map(r=>r.category))].forEach(c=>{const o=document.createElement('option');o.value=c;o.textContent=c;category.append(o)});
function save(){try{localStorage.setItem('drive-test-sign-labels-v1',JSON.stringify(Object.fromEntries(records.map(r=>[r.id,r.label]))))}catch(e){storageOK=false;document.querySelector('#count').textContent+=' — Browser storage unavailable; export JSON to save labels.'}}
function render(){grid.replaceChildren();const q=search.value.toLowerCase();const shown=records.filter(r=>(!category.value||r.category===category.value)&&`${r.id} ${r.label}`.toLowerCase().includes(q));document.querySelector('#count').textContent=`${shown.length} of ${records.length} signs`+(storageOK?'':' — Export JSON to save labels.');for(const r of shown){const card=document.createElement('article');const img=document.createElement('img');img.src=r.svg;img.alt=r.label;img.loading='lazy';const meta=document.createElement('small');meta.textContent=`${r.code} · ${r.category}`;const input=document.createElement('input');input.value=r.label;input.setAttribute('aria-label',`Label for ${r.code}`);input.addEventListener('input',()=>{r.label=input.value;img.alt=r.label;save()});const badge=document.createElement('span');badge.className='badge';badge.textContent='Needs verification';const link=document.createElement('a');link.href=r.svg;link.download=r.id+'.svg';link.textContent='Download SVG';const detail=document.createElement('details');const summary=document.createElement('summary');summary.textContent='Source and notes';const note=document.createElement('p');note.textContent=r.source+' — '+r.notes;detail.append(summary,note);card.append(img,meta,input,badge,link,detail);grid.append(card)}}
search.addEventListener('input',render);category.addEventListener('change',render);
document.querySelector('#export').onclick=()=>{const blob=new Blob([JSON.stringify(records,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='sign-labels.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};

document.querySelector('#import').onclick=()=>document.querySelector('#importFile').click();
document.querySelector('#importFile').onchange=async(event)=>{
  const file=event.target.files[0];if(!file)return;
  try{
    const imported=JSON.parse(await file.text());
    if(!Array.isArray(imported))throw new Error('Expected an exported JSON list.');
    const labels=new Map();const ids=new Set(records.map(r=>r.id));
    for(const r of imported){const label=r.label??r.name;
      if(!ids.has(r.id)||labels.has(r.id)||typeof label!=='string'||!label.trim())throw new Error('Invalid name, unknown sign, or duplicate ID in the file.');
      labels.set(r.id,label);
    }
    if(!labels.size)throw new Error('No labels found.');
    if(!confirm(`Restore ${labels.size} labels from this file? Matching labels will be replaced.`))return;
    try{localStorage.setItem('drive-test-labels-before-import-v1',JSON.stringify(Object.fromEntries(records.map(r=>[r.id,r.label]))))}catch(e){throw new Error('Cannot back up existing labels in this browser. Export them before restoring in another browser.');}
    records.forEach(r=>{if(labels.has(r.id))r.label=labels.get(r.id)});save();render();
  }catch(error){alert('Import failed: '+error.message)}finally{event.target.value=''}
};

document.querySelector('#reset').onclick=()=>{if(confirm('Reset all edited labels to their original values?')){records=structuredClone(original);save();render()}};render();
</script></html>'''
(ROOT/'index.html').write_text(PAGE.replace('__DATA__',DATA))
with zipfile.ZipFile(ROOT/'road-signs-svg.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in [ROOT/'index.html',ROOT/'manifest.json',ROOT/'build_signs.py',ROOT/'label_rules.py',ROOT/'label-rules.js',ROOT/'catalog-labels.json',*[ROOT/r['svg'] for r in items]]:
        z.write(p,p.relative_to(ROOT))
    z.write(ROOT.parent/'README.md', 'README.md')
print(f'Generated {len(items)} SVG assets in {OUT}')
