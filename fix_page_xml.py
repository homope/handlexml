import argparse
from pathlib import Path

from lxml import etree as ET


TARGET_PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2019-07-15"


def get_page_namespace(root):
    namespace = root.nsmap.get(None)
    if namespace:
        return namespace

    if root.tag.startswith("{"):
        return root.tag[1:].split("}", 1)[0]

    return TARGET_PAGE_NS


def generate_baseline_from_coords(coords_string):
    points = [tuple(map(int, pair.split(","))) for pair in coords_string.split() if "," in pair]
    if len(points) < 2:
        return ""

    min_x = min(point[0] for point in points)
    max_x = max(point[0] for point in points)
    if min_x == max_x:
        return ""

    left_points = [point for point in points if point[0] <= min_x + (max_x - min_x) * 0.2]
    right_points = [point for point in points if point[0] >= max_x - (max_x - min_x) * 0.2]
    if not left_points or not right_points:
        return ""

    left_y = max(point[1] for point in left_points)
    right_y = max(point[1] for point in right_points)
    return f"{min_x},{left_y} {max_x},{right_y}"


def clamp_points(points):
    fixed_points = []
    for pair in points.split():
        if "," not in pair:
            continue
        x_str, y_str = pair.split(",", 1)
        try:
            x = max(0, int(round(float(x_str))))
            y = max(0, int(round(float(y_str))))
        except ValueError:
            continue
        fixed_points.append(f"{x},{y}")
    return " ".join(fixed_points)


def prepare_xml_for_kraken(xml_path, output_path):
    parser = ET.XMLParser(remove_blank_text=True)
    tree = ET.parse(str(xml_path), parser)
    root = tree.getroot()

    namespace = get_page_namespace(root)
    ns = {"pc": namespace}

    page_element = root.find(".//pc:Page", namespaces=ns)
    if page_element is not None and not page_element.get("imageFilename"):
        page_element.set("imageFilename", f"{Path(xml_path).stem}.jpg")

    for coords_element in root.xpath('.//pc:Coords', namespaces=ns):
        points = coords_element.get("points")
        if points:
            coords_element.set("points", clamp_points(points))

    for baseline_element in root.xpath('.//pc:Baseline', namespaces=ns):
        points = baseline_element.get("points")
        if points:
            baseline_element.set("points", clamp_points(points))

    for textline in root.xpath('.//pc:TextLine', namespaces=ns):
        coords = textline.find("pc:Coords", namespaces=ns)
        baseline = textline.find("pc:Baseline", namespaces=ns)

        if coords is not None and baseline is None:
            baseline_points = generate_baseline_from_coords(coords.get("points", ""))
            if baseline_points:
                new_baseline = ET.Element(f"{{{namespace}}}Baseline")
                new_baseline.set("points", baseline_points)
                textline.insert(textline.index(coords) + 1, new_baseline)

        if coords is not None and baseline is not None and textline.index(coords) > textline.index(baseline):
            textline.remove(coords)
            textline.insert(0, coords)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(output_path), encoding="utf-8", xml_declaration=True, pretty_print=True)


def batch_prepare(input_dir="data", output_dir="kraken_ready"):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    xml_files = sorted(input_path.glob("*.xml"))
    if not xml_files:
        print(f"Nem találhatók XML fájlok itt: {input_path}")
        return 0

    processed = 0
    for xml_file in xml_files:
        target_file = output_path / xml_file.name
        try:
            prepare_xml_for_kraken(xml_file, target_file)
            processed += 1
            print(f"[OK] {xml_file.name}")
        except Exception as exc:
            print(f"[HIBA] {xml_file.name}: {exc}")

    print(f"\nKész: {processed} XML fájl előkészítve ide: {output_path}")
    return processed


def main():
    parser = argparse.ArgumentParser(description="PAGE XML előkészítés Kraken feldolgozáshoz")
    parser.add_argument("-i", "--input", default="data", help="Forrás XML mappa")
    parser.add_argument("-o", "--output", default="kraken_ready", help="Kimeneti mappa")
    args = parser.parse_args()

    batch_prepare(args.input, args.output)


if __name__ == "__main__":
    main()