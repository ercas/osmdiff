#!/usr/bin/env python3

from lxml import etree
import copy
import os
import shapely.geometry

def blank_way(way):
    new = etree.Element("way")
    for item in way.items():
        new.set(item[0], item[1])
    for child in way.getchildren():
        if (child.tag != "nd"):
            way.append(child)
    return new

def subtract(osm, poly, output_file = None):
    """ Subtract one OSM XML file's contents from another OSM XML file

    Args:
        osm: The path to the main OSM XML file.
        subtract_osm: The polygon to be subtracted from osm.
        output_file: The path to write the difference OSM XML to.
    """
    tree = etree.parse(osm)
    root = tree.getroot()
    unique_id = -1

    remove = {}
    orig_num = tree.xpath("count(//*)")

    # Remove nodes inside the polygon
    for node in root.findall(".//node"):
        if (poly.contains(shapely.geometry.Point(
            float(node.get("lon")),
            float(node.get("lat"))
        ))):
            remove[node.get("id")] = node.tag
            root.remove(node)

    # For ways: remove references to deleted nodes
    for way in root.findall(".//way"):
        if (int(way.get("id")) > 0):
            removing = False
            appending = []

            nodes = way.findall(".//nd")
            new_way = blank_way(way)

            # Remove ways with no nodes
            if (nodes == 0):
                root.remove(way)

            # Attempt to split other ways if possible
            # TODO: fix

    if (output_file is None):
        tree.write("%s-poly.osm" % osm.rstrip(".osm"))
    else:
        tree.write(output_file)

    print("Removed %d elements" % (orig_num - tree.xpath("count(//*)")))

def subtract_multi(osm, polygons, output_file = None):
    """ Wraper for multiple subtractions

    Args:
        osm: The path to the OSM XML file.
        polygons: An array of shapely polygons to be subtracted from osm.
        output_file: The path to write the difference OSM XML to.
    """

    tempfile = None

    for polygon in polygons:
        if (tempfile is None):
            tempfile = "temp%d.osm" % hash(osm)
            subtract(osm, polygon, tempfile)
        else:
            subtract(tempfile, polygon, tempfile)

    if (output_file is None):
        os.rename(tempfile, "%s-poly-multi.osm" % osm.rstrip(".osm"))
    else:
        os.renamve(tempfile, output_file)

if (__name__ == "__main__"):
    poly = shapely.geometry.box(-70.8983396, 42.5174601, -70.8937657, 42.5201496)
    subtract("map.osm", poly)
