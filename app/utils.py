from datetime import datetime, timedelta

def to_utc_minus_5(utc_dt):
    return utc_dt - timedelta(hours=5)


def parse_farmland_xml(xml_content):
    """
    Parses farmland.xml and returns a list of dictionaries with 'id' and 'area'.
    """
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml_content)
        farmlands = []
        # Support both <farmland ... /> and <farmlands><farmland ... /></farmlands>
        if root.tag == 'farmland':
            items = [root]
        else:
            items = root.findall('.//farmland')

        for item in items:
            f_id = item.get('id')
            area = item.get('area')
            if f_id and area:
                farmlands.append({
                    'id': f_id,
                    'area': float(area)
                })
        return farmlands
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return []
