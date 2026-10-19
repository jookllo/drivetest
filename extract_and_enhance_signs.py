#!/usr/bin/env python3
"""
Road Signs Extraction, Clarification & Vectorization Pipeline
Extracts, rectifies, enhances, vectorizes (SVG), and catalogs every sign from
IMG-20261014-WA0089.jpg, IMG-20261014-WA0091.jpg, and IMG-20261014-WA0092.jpg.
"""

import os
import sys
import json
import base64
import csv
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

CATEGORIES = [
    "warning",
    "priority",
    "mandatory",
    "prohibitory",
    "information",
    "direction",
    "hazard_markers",
    "controls"
]

for cat in CATEGORIES:
    os.makedirs(f"assets/png/{cat}", exist_ok=True)
    os.makedirs(f"assets/svg/{cat}", exist_ok=True)

def enhance_image(im):
    """
    Cleans, contrast-balances, sharpens and upscales extracted sign crops.
    """
    im = im.convert("RGB")
    # Autocontrast with 1% cutoff removes gray wash while retaining colors
    c = ImageOps.autocontrast(im, cutoff=1)
    c = ImageEnhance.Color(c).enhance(1.2)
    c = ImageEnhance.Sharpness(c).enhance(1.25)

    # 2.5x upscale with Lanczos
    target_w = max(int(c.width * 2.5), 180)
    target_h = max(int(c.height * 2.5), 180)
    c = c.resize((target_w, target_h), Image.Resampling.LANCZOS)
    c = c.filter(ImageFilter.UnsharpMask(radius=1.5, percent=120, threshold=2))
    return c

def generate_svg(enhanced_pil, sign_info):
    """
    Generates a crisp SVG with vector outer geometry and embedded high-res image.
    """
    w, h = enhanced_pil.size
    category = sign_info.get("category", "")
    code = sign_info.get("code", "")

    buffer = BytesIO()
    enhanced_pil.save(buffer, format="PNG")
    b64_png = base64.b64encode(buffer.getvalue()).decode("utf-8")
    data_uri = f"data:image/png;base64,{b64_png}"

    view_w, view_h = 300, 300
    if w != h:
        view_h = max(200, int(300 * (h / w)))

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {view_w} {view_h}" width="{view_w}" height="{view_h}">')
    svg.append('  <defs>')
    svg.append('    <filter id="subtle-shadow" x="-5%" y="-5%" width="110%" height="110%">')
    svg.append('      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.15"/>')
    svg.append('    </filter>')
    svg.append('  </defs>')

    if category == "warning":
        svg.append('  <!-- Warning Sign Outer Triangle -->')
        svg.append('  <polygon points="150,18 282,258 18,258" rx="8" fill="#FFFFFF" stroke="#D32F2F" stroke-width="26" stroke-linejoin="round" filter="url(#subtle-shadow)"/>')
        svg.append(f'  <image href="{data_uri}" x="35" y="45" width="230" height="205" preserveAspectRatio="xMidYMid meet" />')

    elif category == "prohibitory":
        svg.append('  <!-- Prohibitory Sign Outer Ring -->')
        svg.append('  <circle cx="150" cy="150" r="132" fill="#FFFFFF" stroke="#D32F2F" stroke-width="26" filter="url(#subtle-shadow)"/>')
        svg.append(f'  <image href="{data_uri}" x="40" y="40" width="220" height="220" preserveAspectRatio="xMidYMid meet" />')

    elif category == "mandatory":
        svg.append('  <!-- Mandatory Sign Blue Circle -->')
        svg.append('  <circle cx="150" cy="150" r="135" fill="#0D47A1" stroke="#FFFFFF" stroke-width="6" filter="url(#subtle-shadow)"/>')
        svg.append(f'  <image href="{data_uri}" x="35" y="35" width="230" height="230" preserveAspectRatio="xMidYMid meet" />')

    elif category == "priority":
        if "stop" in sign_info.get("id", "").lower():
            pts = "88,15 212,15 285,88 285,212 212,285 88,285 15,212 15,88"
            svg.append(f'  <polygon points="{pts}" fill="#C62828" stroke="#FFFFFF" stroke-width="6" filter="url(#subtle-shadow)"/>')
            svg.append(f'  <image href="{data_uri}" x="35" y="35" width="230" height="230" preserveAspectRatio="xMidYMid meet" />')
        else:
            svg.append('  <polygon points="150,282 282,42 18,42" fill="#FFFFFF" stroke="#D32F2F" stroke-width="26" stroke-linejoin="round" filter="url(#subtle-shadow)"/>')
            svg.append(f'  <image href="{data_uri}" x="35" y="45" width="230" height="205" preserveAspectRatio="xMidYMid meet" />')

    elif category == "information":
        svg.append(f'  <rect x="15" y="15" width="{view_w-30}" height="{view_h-30}" rx="16" fill="#1565C0" stroke="#FFFFFF" stroke-width="6" filter="url(#subtle-shadow)"/>')
        svg.append(f'  <image href="{data_uri}" x="25" y="25" width="{view_w-50}" height="{view_h-50}" preserveAspectRatio="xMidYMid meet" />')

    elif category == "direction":
        svg.append(f'  <rect x="15" y="15" width="{view_w-30}" height="{view_h-30}" rx="12" fill="#1B5E20" stroke="#FFFFFF" stroke-width="6" filter="url(#subtle-shadow)"/>')
        svg.append(f'  <image href="{data_uri}" x="25" y="25" width="{view_w-50}" height="{view_h-50}" preserveAspectRatio="xMidYMid meet" />')

    else:
        svg.append(f'  <rect x="5" y="5" width="{view_w-10}" height="{view_h-10}" rx="8" fill="#FFFFFF" stroke="#E0E0E0" stroke-width="2" filter="url(#subtle-shadow)"/>')
        svg.append(f'  <image href="{data_uri}" x="10" y="10" width="{view_w-20}" height="{view_h-20}" preserveAspectRatio="xMidYMid meet" />')

    if code:
        svg.append('  <g id="code-badge">')
        svg.append(f'    <rect x="{view_w - 75}" y="12" width="62" height="24" rx="4" fill="#000000" fill-opacity="0.65"/>')
        svg.append(f'    <text x="{view_w - 44}" y="28" fill="#FFFFFF" font-family="system-ui, sans-serif" font-size="12" font-weight="bold" text-anchor="middle">{code}</text>')
        svg.append('  </g>')

    svg.append('</svg>')
    return "\n".join(svg)

def main():
    print("Loading source images...")
    im91 = Image.open("IMG-20261014-WA0091.jpg")
    im92 = Image.open("IMG-20261014-WA0092.jpg")
    im89 = Image.open("IMG-20261014-WA0089.jpg")

    print("Rectifying perspective for WA0091 and WA0092...")
    corners91 = (42, 36, 30, 882, 1585, 882, 1585, 80)
    rec91 = im91.transform((1600, 900), Image.Transform.QUAD, data=corners91, resample=Image.Resampling.BICUBIC)

    corners92 = (0, 35, 0, 890, 1235, 875, 1220, 50)
    rec92 = im92.transform((1250, 900), Image.Transform.QUAD, data=corners92, resample=Image.Resampling.BICUBIC)

    metadata_list = []

    # =========================================================
    # 1. BOARD 1: WA0091 - Accurately Calibrated Grid
    # =========================================================
    cols_x91 = [
        (75, 190),    # Col 0: W.1 .. W.7
        (190, 305),   # Col 1: W.8 .. W.13b
        (305, 420),   # Col 2: W.14 .. W.20
        (420, 535),   # Col 3: W.21 .. W.27
        (535, 650),   # Col 4: W.28a .. R.1 (STOP)
        (650, 760),   # Col 5: R.2 (Give way), M.1 .. M.4
        (760, 870),   # Col 6: M.5, M.7 .. M.10
        (870, 980),   # Col 7: M.11, P.1 .. P.6
        (980, 1090),  # Col 8: P.7 .. P.13
        (1090, 1200), # Col 9: P.14 .. P.20
        (1200, 1310), # Col 10: P.21 .. P.26
        (1310, 1420), # Col 11: P.27 .. P.32
    ]

    rows_y91 = [
        (25, 135),    # Row 0
        (135, 247),   # Row 1
        (247, 360),   # Row 2
        (360, 472),   # Row 3
        (472, 585),   # Row 4
        (585, 697),   # Row 5
        (697, 810),   # Row 6
    ]

    board91_definitions = {
        # Col 0 - Warning Signs
        (0, 0): {"id": "w01_bend_left", "code": "W.1", "name": "Sharp Bend to the Left", "category": "warning", "meaning": "Warns of a sharp bend to the left ahead. Slow down and maintain lane discipline."},
        (0, 1): {"id": "w02_bend_right", "code": "W.2", "name": "Sharp Bend to the Right", "category": "warning", "meaning": "Warns of a sharp bend to the right ahead. Reduce speed and prepare to steer."},
        (0, 2): {"id": "w03_double_bend_right", "code": "W.3", "name": "Double Bend (First to Right)", "category": "warning", "meaning": "A series of sharp bends, the first to the right. Reduce speed appropriately."},
        (0, 3): {"id": "w04_double_bend_left", "code": "W.4", "name": "Double Bend (First to Left)", "category": "warning", "meaning": "A series of sharp bends, the first to the left. Drive cautiously."},
        (0, 4): {"id": "w05_steep_hill_downwards", "code": "W.5", "name": "Steep Hill Downwards", "category": "warning", "meaning": "Steep descent ahead. Select a lower gear to assist engine braking."},
        (0, 5): {"id": "w06_steep_hill_upwards", "code": "W.6", "name": "Steep Hill Upwards", "category": "warning", "meaning": "Steep ascent ahead. Shift to an appropriate lower gear."},
        (0, 6): {"id": "w07_road_narrows_both_sides", "code": "W.7", "name": "Road Narrows from Both Sides", "category": "warning", "meaning": "The carriageway narrows from both sides. Watch for oncoming vehicles."},

        # Col 1 - Road Narrows & Surface Conditions
        (1, 0): {"id": "w08_road_narrows_right", "code": "W.8", "name": "Road Narrows from Right", "category": "warning", "meaning": "The road narrows ahead on the right-hand side."},
        (1, 1): {"id": "w09_road_narrows_left", "code": "W.9", "name": "Road Narrows from Left", "category": "warning", "meaning": "The road narrows ahead on the left-hand side."},
        (1, 2): {"id": "w10_river_bank_quayside", "code": "W.10", "name": "River Bank or Quayside Ahead", "category": "warning", "meaning": "Road leads onto a quay, river bank, or unfenced body of water."},
        (1, 3): {"id": "w11_uneven_road", "code": "W.11", "name": "Uneven Road Surface", "category": "warning", "meaning": "Bumpy, irregular, or uneven road surface ahead."},
        (1, 4): {"id": "w12_speed_bump_hump", "code": "W.12", "name": "Speed Bump / Hump Ahead", "category": "warning", "meaning": "A raised bump or traffic calming hump ahead. Slow down to avoid vehicle damage."},
        (1, 5): {"id": "w13a_dip_riverbed", "code": "W.13a", "name": "Severe Dip / Riverbed", "category": "warning", "meaning": "A sharp depression or dip in the road surface ahead."},
        (1, 6): {"id": "w13b_culvert_drift", "code": "W.13b", "name": "Culvert / Low-Water Drift", "category": "warning", "meaning": "Drift or culvert prone to flash flooding across the roadway."},

        # Col 2 - Crossings & Surface Hazards
        (2, 0): {"id": "w14_slippery_road", "code": "W.14", "name": "Slippery Road Surface Ahead", "category": "warning", "meaning": "Road ahead may be unusually slippery under wet or muddy conditions."},
        (2, 1): {"id": "w15_loose_surface_gravel", "code": "W.15", "name": "Loose Surface Material / Gravel", "category": "warning", "meaning": "Loose gravel or stone chippings on the road surface. Risk of skidding."},
        (2, 2): {"id": "w16_falling_rocks", "code": "W.16", "name": "Danger of Falling Rocks", "category": "warning", "meaning": "Danger from falling or fallen rocks on the carriageway."},
        (2, 3): {"id": "w17_pedestrian_crossing_ahead", "code": "W.17", "name": "Pedestrian Crossing Ahead", "category": "warning", "meaning": "Zebra or marked pedestrian crossing ahead. Yield to pedestrians."},
        (2, 4): {"id": "w18_children_crossing", "code": "W.18", "name": "Children Crossing / School Zone", "category": "warning", "meaning": "School or playground nearby. Watch for children crossing suddenly."},
        (2, 5): {"id": "w19_cyclists_ahead", "code": "W.19", "name": "Cyclists Ahead", "category": "warning", "meaning": "Cyclists frequent this road or cycle route crosses ahead."},
        (2, 6): {"id": "w20_cattle_crossing", "code": "W.20", "name": "Cattle Crossing Ahead", "category": "warning", "meaning": "Domestic cattle or farm livestock likely on or crossing the road."},

        # Col 3 - General Hazards & Aviation
        (3, 0): {"id": "w21_wild_animals", "code": "W.21", "name": "Wild Animals Crossing", "category": "warning", "meaning": "National park or game corridor ahead. Wild animals may cross unexpectedly."},
        (3, 1): {"id": "w22_road_works_ahead", "code": "W.22", "name": "Road Works Ahead", "category": "warning", "meaning": "Construction, maintenance, or workers ahead on or beside the road."},
        (3, 2): {"id": "w23_traffic_lights_ahead", "code": "W.23", "name": "Traffic Light Signals Ahead", "category": "warning", "meaning": "Junction controlled by traffic light signals ahead. Prepare to stop if red."},
        (3, 3): {"id": "w24_low_flying_aircraft", "code": "W.24", "name": "Low Flying Aircraft Ahead", "category": "warning", "meaning": "Road passes near airport runway. Low-flying planes or sudden noise possible."},
        (3, 4): {"id": "w25_two_way_traffic", "code": "W.25", "name": "Two-Way Traffic Ahead", "category": "warning", "meaning": "Road ahead carries two-way traffic instead of one-way."},
        (3, 5): {"id": "w26_general_danger", "code": "W.26", "name": "General Hazard / Other Danger", "category": "warning", "meaning": "Hazard ahead not covered by other specific signs. Proceed with caution."},
        (3, 6): {"id": "w27_railway_cross_ahead", "code": "W.27", "name": "Railway Level Crossing Hazard", "category": "warning", "meaning": "Level crossing ahead. Prepare to give way to trains."},

        # Col 4 - Junctions, Rail & STOP
        (4, 0): {"id": "w28a_junction_crossroad", "code": "W.28a", "name": "Crossroad Ahead (Priority Road)", "category": "warning", "meaning": "Crossroads ahead with side roads having to yield to you."},
        (4, 1): {"id": "w28b_side_road_right", "code": "W.28b", "name": "Side Road Junction on Right", "category": "warning", "meaning": "Side road intersects from the right ahead."},
        (4, 2): {"id": "w29_side_road_left", "code": "W.29", "name": "Side Road Junction on Left", "category": "warning", "meaning": "Side road intersects from the left ahead."},
        (4, 3): {"id": "w30_roundabout_ahead", "code": "W.30", "name": "Roundabout Ahead", "category": "warning", "meaning": "Traffic circle / roundabout ahead. Yield to traffic already in the circle."},
        (4, 4): {"id": "w31_level_crossing_barrier", "code": "W.31", "name": "Railway Crossing with Gates / Barrier", "category": "warning", "meaning": "Railway level crossing equipped with gates or automatic barriers ahead."},
        (4, 5): {"id": "w32_level_crossing_no_barrier", "code": "W.32", "name": "Railway Crossing without Gates / Barrier", "category": "warning", "meaning": "Open railway level crossing ahead without gates. Stop, look, and listen."},
        (4, 6): {"id": "r01_stop", "code": "R.1", "name": "STOP Sign", "category": "priority", "meaning": "Come to a complete stop before the stop line and give way to all traffic."},

        # Col 5 - Priority & Mandatory Movements
        (5, 0): {"id": "r02_give_way", "code": "R.2", "name": "GIVE WAY / Yield", "category": "priority", "meaning": "Give way to all vehicles travelling on the major road ahead."},
        (5, 1): {"id": "m01_turn_left", "code": "M.1", "name": "Turn Left Mandatory", "category": "mandatory", "meaning": "Vehicles must turn to the left at the next intersection."},
        (5, 2): {"id": "m02_ahead_only", "code": "M.2", "name": "Proceed Straight Ahead Only", "category": "mandatory", "meaning": "Mandatory direction: proceed straight ahead only; turning prohibited."},
        (5, 5): {"id": "m03_turn_right_ahead", "code": "M.3", "name": "Turn Right Ahead", "category": "mandatory", "meaning": "Vehicles must turn right ahead."},
        (5, 6): {"id": "m04_turn_left_ahead", "code": "M.4", "name": "Turn Left Ahead", "category": "mandatory", "meaning": "Vehicles must turn left ahead."},

        # Col 6 - Mandatory Paths & Speed
        (6, 0): {"id": "m05_pass_left", "code": "M.5", "name": "Pass to the Left", "category": "mandatory", "meaning": "Pass obstacle or island to the left-hand side."},
        (6, 1): {"id": "m07_cycle_track", "code": "M.7", "name": "Compulsory Track for Cyclists", "category": "mandatory", "meaning": "Designated path for pedal cycles; cyclists must use this track."},
        (6, 2): {"id": "m08_pedestrian_path", "code": "M.8", "name": "Compulsory Pedestrian Footpath", "category": "mandatory", "meaning": "Designated footpath reserved exclusively for pedestrians."},
        (6, 5): {"id": "m09_cattle_track", "code": "M.9", "name": "Compulsory Track for Cattle", "category": "mandatory", "meaning": "Designated route for herded cattle or farm livestock."},
        (6, 6): {"id": "m10_minimum_speed_30", "code": "M.10", "name": "Compulsory Minimum Speed 30 km/h", "category": "mandatory", "meaning": "Vehicles must travel at least 30 km/h unless road conditions prevent it."},

        # Col 7 - Prohibitions on Entry & Road Use
        (7, 0): {"id": "m11_end_minimum_speed_30", "code": "M.11", "name": "End of Minimum Speed 30 km/h", "category": "mandatory", "meaning": "Compulsory minimum speed restriction ends here."},
        (7, 1): {"id": "p01_no_entry", "code": "P.1", "name": "No Entry for All Vehicles", "category": "prohibitory", "meaning": "No vehicular traffic permitted past this point in this direction."},
        (7, 2): {"id": "p02_road_closed", "code": "P.2", "name": "Road Closed to All Vehicles", "category": "prohibitory", "meaning": "Road closed in both directions to all vehicular traffic."},
        (7, 3): {"id": "p03_no_motor_vehicles", "code": "P.3", "name": "No Entry for Motor Vehicles with >2 Wheels", "category": "prohibitory", "meaning": "Cars, vans, and multi-track motor vehicles prohibited."},
        (7, 4): {"id": "p04_no_motorcycles", "code": "P.4", "name": "No Entry for Motorcycles", "category": "prohibitory", "meaning": "Motorcycles and mopeds prohibited from entering."},
        (7, 5): {"id": "p05_no_bicycles", "code": "P.5", "name": "No Entry for Pedal Bicycles", "category": "prohibitory", "meaning": "Pedal bicycles prohibited on this carriageway."},
        (7, 6): {"id": "p06_no_pedestrians", "code": "P.6", "name": "No Pedestrians Allowed", "category": "prohibitory", "meaning": "Pedestrians prohibited (e.g. motorways or restricted tunnels)."},

        # Col 8 - Vehicle Type Restrictions & Width
        (8, 0): {"id": "p07_no_animal_drawn", "code": "P.7", "name": "No Animal-Drawn Vehicles", "category": "prohibitory", "meaning": "Carts and carriages pulled by horses, donkeys, or oxen prohibited."},
        (8, 1): {"id": "p08_no_handcarts", "code": "P.8", "name": "No Handcarts (Mkokoteni)", "category": "prohibitory", "meaning": "Hand-pushed carts (mkokoteni) prohibited from entering."},
        (8, 2): {"id": "p09_no_tractors", "code": "P.9", "name": "No Agricultural / Farm Vehicles", "category": "prohibitory", "meaning": "Tractors and slow-moving farm machinery prohibited."},
        (8, 3): {"id": "p10_no_trucks", "code": "P.10", "name": "No Heavy Commercial Vehicles / Trucks", "category": "prohibitory", "meaning": "Lorries, trucks, and heavy commercial vehicles prohibited."},
        (8, 4): {"id": "p11_no_buses", "code": "P.11", "name": "No Buses / Passenger Coaches", "category": "prohibitory", "meaning": "Public buses and coaches prohibited."},
        (8, 5): {"id": "p12_no_trailers", "code": "P.12", "name": "No Motor Vehicles Towing Trailers", "category": "prohibitory", "meaning": "Vehicles drawing a trailer or caravan prohibited."},
        (8, 6): {"id": "p13_width_limit_2m", "code": "P.13", "name": "Maximum Width Limit 2m", "category": "prohibitory", "meaning": "No entry for vehicles exceeding 2 meters in overall width."},

        # Col 9 - Dimension Limits & Distance
        (9, 0): {"id": "p14_height_limit_3_5m", "code": "P.14", "name": "Maximum Height Limit 3.5m", "category": "prohibitory", "meaning": "No entry for vehicles exceeding 3.5 meters in height (low bridge/overhead cables)."},
        (9, 1): {"id": "p15_weight_limit_5t", "code": "P.15", "name": "Maximum Weight Limit 5 Tonnes", "category": "prohibitory", "meaning": "No entry for vehicles exceeding 5 tonnes maximum laden weight."},
        (9, 2): {"id": "p16_axle_limit_2t", "code": "P.16", "name": "Maximum Axle Weight Limit 2 Tonnes", "category": "prohibitory", "meaning": "Vehicles exceeding 2 tonnes per axle prohibited."},
        (9, 3): {"id": "p17_length_limit_10m", "code": "P.17", "name": "Maximum Length Limit 10m", "category": "prohibitory", "meaning": "No entry for vehicles or combinations exceeding 10 meters in length."},
        (9, 4): {"id": "p18_min_distance_70m", "code": "P.18", "name": "Minimum Following Distance 70m", "category": "prohibitory", "meaning": "Maintain a minimum distance of at least 70 meters from the vehicle ahead."},
        (9, 5): {"id": "p19_no_right_turn", "code": "P.19", "name": "No Right Turn", "category": "prohibitory", "meaning": "Turning to the right is prohibited at this junction."},
        (9, 6): {"id": "p20_stop_children", "code": "P.20", "name": "Stop - Children Crossing (School Warden)", "category": "prohibitory", "meaning": "Drivers must stop when signal is displayed by school traffic warden."},

        # Col 10 - Maneuver & Speed Restrictions
        (10, 0): {"id": "p21_no_u_turn", "code": "P.21", "name": "No U-Turn", "category": "prohibitory", "meaning": "Making a U-turn (turning around 180 degrees) is prohibited."},
        (10, 1): {"id": "p22_no_overtaking", "code": "P.22", "name": "Overtaking Prohibited", "category": "prohibitory", "meaning": "Passing or overtaking other motor vehicles is strictly prohibited."},
        (10, 2): {"id": "p23_no_overtaking_trucks", "code": "P.23", "name": "Overtaking by Goods Vehicles Prohibited", "category": "prohibitory", "meaning": "Heavy goods vehicles (>3.5t) prohibited from overtaking."},
        (10, 3): {"id": "p24_speed_limit_50", "code": "P.24", "name": "Maximum Speed Limit 50 km/h", "category": "prohibitory", "meaning": "Do not exceed 50 km/h (standard urban speed limit in Kenya)."},
        (10, 4): {"id": "p25_no_hooting", "code": "P.25", "name": "No Hooting / Sounding of Horns", "category": "prohibitory", "meaning": "Use of audible warning devices (horns) is prohibited (near hospitals/schools)."},
        (10, 5): {"id": "p26_no_left_turn", "code": "P.26", "name": "No Left Turn", "category": "prohibitory", "meaning": "Turning to the left is prohibited at this junction."},

        # Col 11 - Priority, De-restriction & Parking
        (11, 0): {"id": "p27_two_way_traffic_circle", "code": "P.27", "name": "Two-Way Traffic Priority", "category": "prohibitory", "meaning": "Red arrow has priority over black arrow; opposing traffic must yield."},
        (11, 1): {"id": "p28_end_all_restrictions", "code": "P.28", "name": "End of All Local Prohibitions", "category": "prohibitory", "meaning": "End of all previously imposed local speed and overtaking restrictions."},
        (11, 2): {"id": "p29_end_speed_limit_40", "code": "P.29", "name": "End of Speed Limit 40 km/h", "category": "prohibitory", "meaning": "Speed limit of 40 km/h no longer applies."},
        (11, 3): {"id": "p30_no_parking", "code": "P.30", "name": "No Parking", "category": "prohibitory", "meaning": "Parking is prohibited; brief stopping to pick up or set down passengers allowed."},
        (11, 4): {"id": "p31_no_stopping", "code": "P.31", "name": "No Stopping (Clearway)", "category": "prohibitory", "meaning": "Stopping and parking prohibited at all times for any reason."},
        (11, 5): {"id": "p32_controlled_parking_zone", "code": "P.32", "name": "Controlled Parking Zone", "category": "prohibitory", "meaning": "Entry to controlled parking zone where specific meter/time rules apply."},
    }

    print("Extracting calibrated signs from Board 1 (WA0091)...")
    for (col_idx, row_idx), sign_info in board91_definitions.items():
        x1, x2 = cols_x91[col_idx]
        y1, y2 = rows_y91[row_idx]
        crop = rec91.crop((x1, y1, x2, y2))
        enhanced = enhance_image(crop)

        cat = sign_info["category"]
        sid = sign_info["id"]

        png_path = f"assets/png/{cat}/{sid}.png"
        svg_path = f"assets/svg/{cat}/{sid}.svg"

        enhanced.save(png_path, "PNG")
        svg_content = generate_svg(enhanced, sign_info)
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

        sign_entry = {
            "id": sid,
            "code": sign_info["code"],
            "name": sign_info["name"],
            "category": cat,
            "meaning": sign_info["meaning"],
            "quiz_question": f"What does the road sign '{sign_info['name']}' indicate?",
            "quiz_answer": sign_info["meaning"],
            "png_path": png_path,
            "svg_path": svg_path
        }
        metadata_list.append(sign_entry)

    # =========================================================
    # 2. BOARD 2: WA0092 - Accurately Calibrated Signs
    # =========================================================
    board92_items = [
        # Direction Signs (Green)
        {"id": "dir_taveta_a23", "code": "DIR.1", "name": "Taveta A23 Direction Sign", "category": "direction",
         "bbox": (230, 20, 370, 140), "meaning": "Advance direction sign to Taveta via route A23 (1 km)."},
        {"id": "dir_bungoma_c33", "code": "DIR.2", "name": "Bungoma C33 / Eldoret / Malaba Direction Sign", "category": "direction",
         "bbox": (440, 15, 620, 135), "meaning": "Direction sign showing routes to Eldoret, Malaba, and Bungoma (C33 / A104)."},
        {"id": "dir_eldoret_a104", "code": "DIR.3", "name": "Eldoret A104 / Njoro C56 Route Sign", "category": "direction",
         "bbox": (190, 160, 390, 405), "meaning": "Route indicator pointing ahead to Eldoret (A104) and left branch to Njoro (C56)."},
        {"id": "dir_nakuru_a104", "code": "DIR.4", "name": "Nakuru A104 / Elmenteita / Ol Kalou Sign", "category": "direction",
         "bbox": (190, 425, 395, 555), "meaning": "Direction sign at junction for Nakuru (A104), Elmenteita (D320), and Ol Kalou (C69)."},
        {"id": "dir_nakuru_thika_roundabout", "code": "DIR.5", "name": "Roundabout Direction: Nakuru A104 / Thika A2", "category": "direction",
         "bbox": (190, 565, 395, 705), "meaning": "Roundabout layout sign guiding traffic towards Nakuru (A104) or Thika (A2)."},
        {"id": "dir_garissa_a3", "code": "DIR.6", "name": "Roundabout Direction: Garissa A3 / Ainabkoi", "category": "direction",
         "bbox": (190, 715, 395, 855), "meaning": "Roundabout guidance sign for Garissa (A3) and Ainabkoi (C56)."},
        {"id": "dir_kitale_c51", "code": "DIR.7", "name": "Kitale C51 / Kongoni / Kipsain Crossroads Sign", "category": "direction",
         "bbox": (180, 855, 390, 980), "meaning": "Major crossroad guidance for Kitale (C51), Kongoni (D342), and Kipsain."},

        # Information Signs Column 1 (x: 635 to 745)
        {"id": "info_toilets", "code": "I.1", "name": "Public Toilets / Restroom", "category": "information",
         "bbox": (635, 10, 745, 75), "meaning": "Indicates availability of public restroom / toilet facilities."},
        {"id": "info_parking", "code": "I.2", "name": "Parking Area (P)", "category": "information",
         "bbox": (635, 80, 745, 205), "meaning": "Designated area where parking is permitted."},
        {"id": "info_parking_500m", "code": "I.3", "name": "Parking Area Ahead (500m)", "category": "information",
         "bbox": (635, 215, 745, 275), "meaning": "Advance information that parking is available 500 meters ahead."},
        {"id": "info_pedestrian_crossing", "code": "I.4", "name": "Marked Pedestrian Crossing", "category": "information",
         "bbox": (635, 285, 745, 415), "meaning": "Location of marked pedestrian crossing."},
        {"id": "info_hospital", "code": "I.5", "name": "Hospital (H)", "category": "information",
         "bbox": (630, 425, 740, 555), "meaning": "Hospital or medical facility ahead. Avoid making unnecessary noise."},
        {"id": "info_one_way_straight", "code": "I.6", "name": "One-Way Road (Straight Ahead)", "category": "information",
         "bbox": (635, 570, 745, 630), "meaning": "One-way street ahead; all traffic travels in the indicated direction."},
        {"id": "info_one_way_left", "code": "I.7", "name": "One-Way Road (Left Direction)", "category": "information",
         "bbox": (635, 645, 745, 705), "meaning": "Traffic on this crossing roadway travels one-way to the left."},
        {"id": "info_cul_de_sac", "code": "I.8", "name": "No Through Road (Cul-de-sac)", "category": "information",
         "bbox": (630, 720, 740, 840), "meaning": "Road has no exit ahead; dead end street."},
        {"id": "info_cycle_path", "code": "I.9", "name": "Cycle Route / Path", "category": "information",
         "bbox": (630, 855, 740, 975), "meaning": "Information indicating designated bicycle route."},

        # Column 2 (x: 745 to 855)
        {"id": "info_in", "code": "I.10", "name": "Vehicular Entrance (IN)", "category": "information",
         "bbox": (745, 10, 855, 70), "meaning": "Vehicular entrance to premises or one-way entrance."},
        {"id": "info_out", "code": "I.11", "name": "Vehicular Exit (OUT)", "category": "information",
         "bbox": (745, 75, 855, 135), "meaning": "Vehicular exit from premises."},
        {"id": "info_no_entry_text", "code": "I.12", "name": "NO ENTRY Sign", "category": "information",
         "bbox": (745, 140, 855, 205), "meaning": "Text notification indicating no entry allowed."},
        {"id": "info_no_exit_text", "code": "I.13", "name": "NO EXIT Sign", "category": "information",
         "bbox": (745, 215, 855, 275), "meaning": "Text notification indicating no exit."},
        {"id": "info_taxi_rank", "code": "I.14", "name": "Taxi Rank / Stand", "category": "information",
         "bbox": (745, 280, 855, 345), "meaning": "Designated rank or parking space for licensed taxis."},
        {"id": "info_bus_stop", "code": "I.15", "name": "Bus Stop", "category": "information",
         "bbox": (745, 350, 855, 415), "meaning": "Designated stopping point for passenger buses."},
        {"id": "info_priority_oncoming", "code": "I.16", "name": "Priority Over Oncoming Vehicles", "category": "information",
         "bbox": (740, 430, 855, 555), "meaning": "You have right of way over oncoming vehicles at narrowed road sections."},
        {"id": "info_first_aid", "code": "I.17", "name": "First Aid Post (+)", "category": "information",
         "bbox": (745, 720, 855, 840), "meaning": "Location of a first aid station or emergency medical post."},
        {"id": "info_breakdown_service", "code": "I.18", "name": "Breakdown / Repair Service", "category": "information",
         "bbox": (745, 855, 855, 975), "meaning": "Vehicle breakdown assistance and mechanical workshop available."},

        # Services Column 3 (x: 855 to 965)
        {"id": "info_telephone", "code": "I.19", "name": "Public Telephone Facility", "category": "information",
         "bbox": (855, 20, 965, 135), "meaning": "Public telephone available for motorists."},
        {"id": "info_petrol_station", "code": "I.20", "name": "Petrol / Filling Station", "category": "information",
         "bbox": (855, 145, 965, 265), "meaning": "Motor fuel and filling station ahead."},
        {"id": "info_hotel_motel", "code": "I.21", "name": "Hotel / Motel / Lodging", "category": "information",
         "bbox": (855, 285, 965, 410), "meaning": "Hotel, motel, or overnight accommodation ahead."},
        {"id": "info_restaurant", "code": "I.22", "name": "Restaurant / Food Facility", "category": "information",
         "bbox": (855, 430, 965, 555), "meaning": "Restaurant or full meal dining services available."},
        {"id": "info_refreshments_cafe", "code": "I.23", "name": "Cafeteria / Refreshments", "category": "information",
         "bbox": (855, 575, 965, 695), "meaning": "Light refreshments, coffee, or tea facility."},
        {"id": "info_picnic_site", "code": "I.24", "name": "Picnic Site", "category": "information",
         "bbox": (855, 715, 965, 840), "meaning": "Designated picnic and rest area for motorists."},

        # Camping & Hazard Markers Column 4 (x: 965 to 1180)
        {"id": "info_camping_site", "code": "I.25", "name": "Camping Site (Tents)", "category": "information",
         "bbox": (965, 20, 1070, 135), "meaning": "Designated tent camping grounds ahead."},
        {"id": "info_caravan_site", "code": "I.26", "name": "Caravan Site", "category": "information",
         "bbox": (965, 145, 1070, 265), "meaning": "Designated trailer caravan park ahead."},
        {"id": "info_camping_and_caravan", "code": "I.27", "name": "Camping and Caravan Park", "category": "information",
         "bbox": (965, 285, 1070, 410), "meaning": "Facilities for both tents and caravans available."},
        {"id": "hazard_single_crossbuck", "code": "H.1", "name": "Railway Level Crossing (Single Track)", "category": "hazard_markers",
         "bbox": (965, 570, 1180, 690), "meaning": "Single railway track crossing at grade. Crossbuck marker."},
        {"id": "hazard_double_crossbuck", "code": "H.2", "name": "Railway Level Crossing (Two or More Tracks)", "category": "hazard_markers",
         "bbox": (965, 705, 1180, 845), "meaning": "Multiple railway tracks crossing at grade. Crossbuck marker."},
        {"id": "hazard_chevrons_sharp_curve", "code": "H.3", "name": "Sharp Deviation Chevrons", "category": "hazard_markers",
         "bbox": (965, 855, 1075, 980), "meaning": "Delineation chevrons highlighting sudden sharp change of route direction."},

        # Column 5: Facilities & Street Names (x: 1070 to 1210)
        {"id": "info_youth_hostel", "code": "I.28", "name": "Youth Hostel / Rest Accommodation", "category": "information",
         "bbox": (1075, 20, 1180, 135), "meaning": "Youth hostel or low-cost accommodation."},
        {"id": "info_port_ferry", "code": "I.29", "name": "Port / Harbour / Ferry (Anchor)", "category": "information",
         "bbox": (1075, 145, 1180, 265), "meaning": "Ferry terminal, seaport, or inland boat harbour ahead."},
        {"id": "warning_danger_hazard_triangle", "code": "W.33", "name": "Hazard Danger Ahead (Red Triangle)", "category": "warning",
         "bbox": (1075, 275, 1180, 410), "meaning": "Danger ahead marker symbol."},
        {"id": "info_street_names", "code": "I.30", "name": "Street Name Signboards (Mbagathi Ridge, Moi Ave)", "category": "information",
         "bbox": (965, 430, 1180, 555), "meaning": "City street name and avenue naming markers."},
    ]

    print("Extracting calibrated signs from Board 2 (WA0092)...")
    for item in board92_items:
        x1, y1, x2, y2 = item["bbox"]
        x1 = max(0, min(x1, rec92.width - 10))
        x2 = max(x1 + 10, min(x2, rec92.width))
        y1 = max(0, min(y1, rec92.height - 10))
        y2 = max(y1 + 10, min(y2, rec92.height))

        crop = rec92.crop((x1, y1, x2, y2))
        enhanced = enhance_image(crop)

        cat = item["category"]
        sid = item["id"]

        png_path = f"assets/png/{cat}/{sid}.png"
        svg_path = f"assets/svg/{cat}/{sid}.svg"

        enhanced.save(png_path, "PNG")
        svg_content = generate_svg(enhanced, item)
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

        sign_entry = {
            "id": sid,
            "code": item["code"],
            "name": item["name"],
            "category": cat,
            "meaning": item["meaning"],
            "quiz_question": f"What does the road sign '{item['name']}' indicate?",
            "quiz_answer": item["meaning"],
            "png_path": png_path,
            "svg_path": svg_path
        }
        metadata_list.append(sign_entry)

    # =========================================================
    # 3. CONTROLS & SIDE WALL (WA0089 & WA0092 wall)
    # =========================================================
    print("Extracting controls diagrams (WA0089) and wall displays...")
    # Steering Wheel Hand Positions
    steering_crop = im89.crop((40, 80, 860, 1260))
    steering_enh = enhance_image(steering_crop)
    steering_entry = {
        "id": "steering_wheel_hand_positions",
        "code": "CTRL.1",
        "name": "Steering Wheel Hand Positions (Clock Method)",
        "category": "controls",
        "meaning": "Recommended driving hand positions: 'Best' is 9 and 3 o'clock (or 10 and 2 o'clock). 'Normal' is 8 and 4 o'clock. 'Danger' is one hand at 12 o'clock or holding bottom spokes.",
        "quiz_question": "What is the recommended hand position on the steering wheel?",
        "quiz_answer": "9 and 3 o'clock position (or 10 and 2 o'clock) provides optimal vehicle control and airbag safety."
    }
    steering_png = "assets/png/controls/steering_wheel_hand_positions.png"
    steering_svg = "assets/svg/controls/steering_wheel_hand_positions.svg"
    steering_enh.save(steering_png, "PNG")
    with open(steering_svg, "w", encoding="utf-8") as f:
        f.write(generate_svg(steering_enh, steering_entry))
    steering_entry["png_path"] = steering_png
    steering_entry["svg_path"] = steering_svg
    metadata_list.append(steering_entry)

    # Footbrake and clutch controls
    foot_crop = im89.crop((200, 1290, 860, 1580))
    foot_enh = enhance_image(foot_crop)
    foot_entry = {
        "id": "footbrake_and_clutch_pedals",
        "code": "CTRL.2",
        "name": "Footbrake and Clutch Operation",
        "category": "controls",
        "meaning": "Correct pedal operation: Firmly press the brake pedal with your right foot, and smoothly press the clutch pedal fully to the floor with your left foot.",
        "quiz_question": "Which foot operates the brake pedal in a manual vehicle?",
        "quiz_answer": "The right foot operates both the accelerator and footbrake pedals; the left foot operates the clutch only."
    }
    foot_png = "assets/png/controls/footbrake_and_clutch_pedals.png"
    foot_svg = "assets/svg/controls/footbrake_and_clutch_pedals.svg"
    foot_enh.save(foot_png, "PNG")
    with open(foot_svg, "w", encoding="utf-8") as f:
        f.write(generate_svg(foot_enh, foot_entry))
    foot_entry["png_path"] = foot_png
    foot_entry["svg_path"] = foot_svg
    metadata_list.append(foot_entry)

    # Mandatory U-turn on wall from WA0092
    u_turn_crop = im92.crop((1240, 140, 1420, 390))
    u_turn_enh = enhance_image(u_turn_crop)
    uturn_entry = {
        "id": "m12_mandatory_u_turn",
        "code": "M.12",
        "name": "Mandatory U-Turn Ahead",
        "category": "mandatory",
        "meaning": "Mandatory U-turn ahead: Vehicles must execute a U-turn at this designated loop.",
        "quiz_question": "What does a circular blue sign with a curved 180-degree white arrow mean?",
        "quiz_answer": "It is a mandatory sign directing drivers to perform a U-turn."
    }
    uturn_png = "assets/png/mandatory/m12_mandatory_u_turn.png"
    uturn_svg = "assets/svg/mandatory/m12_mandatory_u_turn.svg"
    u_turn_enh.save(uturn_png, "PNG")
    with open(uturn_svg, "w", encoding="utf-8") as f:
        f.write(generate_svg(u_turn_enh, uturn_entry))
    uturn_entry["png_path"] = uturn_png
    uturn_entry["svg_path"] = uturn_svg
    metadata_list.append(uturn_entry)

    # Traffic Police Hand Signals on wall from WA0092
    police_crop = im92.crop((1420, 390, 1600, 610))
    police_enh = enhance_image(police_crop)
    police_entry = {
        "id": "ctrl_traffic_police_signals",
        "code": "CTRL.3",
        "name": "Traffic Police Officer Arm Signals",
        "category": "controls",
        "meaning": "Signals given by police officers directing traffic: arm raised vertically means stop traffic approaching from front and behind; arm extended horizontally means stop vehicles approaching from direction shown.",
        "quiz_question": "When a traffic police officer extends an arm horizontally towards your vehicle, what should you do?",
        "quiz_answer": "You must stop before reaching the officer."
    }
    police_png = "assets/png/controls/ctrl_traffic_police_signals.png"
    police_svg = "assets/svg/controls/ctrl_traffic_police_signals.svg"
    police_enh.save(police_png, "PNG")
    with open(police_svg, "w", encoding="utf-8") as f:
        f.write(generate_svg(police_enh, police_entry))
    police_entry["png_path"] = police_png
    police_entry["svg_path"] = police_svg
    metadata_list.append(police_entry)

    print(f"Total extracted and enhanced signs: {len(metadata_list)}")
    print("Writing signs_metadata.json...")
    with open("signs_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, indent=2, ensure_ascii=False)

    print("Writing signs_labels.csv...")
    with open("signs_labels.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Code", "Name", "Category", "Meaning", "PNG Path", "SVG Path", "Quiz Question", "Quiz Answer"])
        for item in metadata_list:
            writer.writerow([
                item["id"],
                item["code"],
                item["name"],
                item["category"],
                item["meaning"],
                item["png_path"],
                item["svg_path"],
                item["quiz_question"],
                item["quiz_answer"]
            ])

    print("Extraction and cataloging pipeline completed successfully!")

if __name__ == "__main__":
    main()
