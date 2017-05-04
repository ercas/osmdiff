#!/usr/bin/env python3

from lxml import etree
import os

def subtract(main_osm, subtract_osm, output_file = None):
    """ Subtract one OSM XML file's contents from another OSM XML file

    Args:
        main_osm: The path to the main OSM XML file.
        subtract_osm: The path to the OSM XML file to be subtracted from
            main_osm.
        output_file: The path to write the difference OSM XML to.
    """
    main = etree.parse(main_osm)
    mainroot = main.getroot()
    subtract = etree.parse(subtract_osm)

    remove = {}
    orig_num = main.xpath("count(//*)")

    for element in subtract.getroot().getchildren():
        if ("id" in element.keys()):
            remove[element.get("id")] = element.tag
    for element in mainroot.getchildren():
        if ("id" in element.keys()):

            # Remove elements with intersecting IDs
            _id = element.get("id")
            if (_id in remove):
                if (element.tag == remove[_id]):
                    mainroot.remove(element)

            # For all ways: remove nodes that were previously removed
            elif (element.tag == "way"):
                for node in element.getchildren():
                    if (node.tag == "nd"):
                        ref = node.get("ref")
                        if (ref in remove):
                            element.remove(node)

    if (output_file is None):
        main.write("%s-%s" % (main_osm, subtract_osm))
    else:
        main.write(output_file)

def subtract_multi(main_osm, subtract_osm_array, output_file = None):
    """ Wraper for multiple subtractions

    Args:
        main_osm: The path to the main OSM XML file.
        subtract_osm_array: An array of paths to OSM XML files to be subtracted
            from the main OSM XML file, in order of subtraction.
        output_file: The path to write the difference OSM XML to.
    """
    tempfile = None
    for subtract_osm in subtract_osm_array:
        if (tempfile is None):
            tempfile = "temp%d.osm" % hash(main_osm)
            subtract(main_osm, subtract_osm, tempfile)
        else:
            subtract(tempfile, subtract_osm, tempfile)
    if (output_file is None):
        os.rename(tempfile, "%s-%s" % (main_osm, "-".join(subtract_osm_array)))
    else:
        os.renamve(tempfile, output_file)

if (__name__ == "__main__"):
    subtract("map.osm", "map_sub.osm")
    subtract_multi("map.osm", ["map_sub.osm", "map_sub2.osm"])
