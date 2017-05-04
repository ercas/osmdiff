#!/usr/bin/env python3

from shapely import geometry
from lxml import etree
import copy
import os

unique_id = -1

def clone_way_no_nodes(way):
    global unique_id # TODO: use a class to localize
    new = copy.copy(way)
    for ref in new.findall(".//nd"):
        new.remove(ref)
    new.set("id", str(unique_id))
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

    remove = set()
    orig_num = tree.xpath("count(//*)")

    # Remove nodes inside the polygon
    for node in root.findall(".//node"):
        if (poly.contains(geometry.Point(
            float(node.get("lon")),
            float(node.get("lat"))
        ))):
            _id = node.get("id")
            print("Removing node %s" % _id)
            remove.add(_id)
            root.remove(node)

    # For ways: remove references to deleted nodes
    for way in root.findall(".//way"):
        # Ignore ways that were added as a result of splits
        if (int(way.get("id")) > 0):
            nodes = way.findall(".//nd")

            # Remove ways with no nodes
            if (nodes == 0):
                root.remove(way)

            # Attempt to split other ways if possible
            else:
                new_ways = []
                copying = True
                blank = True

                new_way = clone_way_no_nodes(way)
                for node in nodes:
                    ref = node.get("ref")

                    if (ref in remove):
                        copying = False
                        if (blank == False):
                            new_ways.append(new_way)
                            new_way = clone_way_no_nodes(way)
                            blank = True
                    else:
                        copying = True

                    if (copying):
                        new_way.append(copy.copy(node))
                        blank = False

                # Append the final segment
                new_ways.append(new_way)

                # If a split was made (segments > 1), remove the original way
                # and append the new segments
                if (len(new_ways) > 1):
                    print("Splitting way %s into %d segments" % (
                        way.get("id"), len(new_ways))
                    )
                    root.remove(way)
                    for new_way in new_ways:
                        root.append(new_way)

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
    #poly = geometry.box(-70.8983396, 42.5174601, -70.8937657, 42.5201496)
    poly = geometry.Polygon([
        (-70.8974461, 42.5171513),
        (-70.8937868, 42.5184048),
        (-70.8982679, 42.5204092)
    ])
    subtract("map.osm", poly)
