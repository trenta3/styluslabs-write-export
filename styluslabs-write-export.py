#!/usr/bin/env python3
import gzip
import xml.etree.ElementTree as ET

# TODO: Export to multi-page pdf using ReportLab and/or svglib
# TODO: Add ability to export in the form of simple html slides

namespaces = {
    "": "http://www.w3.org/2000/svg",
    "xlink": "http://www.w3.org/1999/xlink",
}

for ns, fullpath in namespaces.items():
    ET.register_namespace(ns, fullpath)

def convert_write_file(input, output, format="html", title=None, author=None, description=None, keywords=None):
    if input.endswith(".svgz"):
        content = gzip.open(input, "rb").read()
    elif input.endswith(".svg"):
        content = open(input, "rb").read()
    else:
        raise Exception(f"Unknown input file extensions for {input=}")
    # Search for Write root with id #write-document
    root = ET.fromstring(content.decode("utf-8"))
    write_root = root.find(".[@id='write-document']")
    if write_root is None:
        raise Exception(f"StylusLabs Write document root not found.\nEnsure the input file comes from Write!")
    # Collect all pages from the root
    pages = write_root.findall("svg[@class='write-page']", namespaces=namespaces)
    # Create the heading of the format
    outcontent = ""
    if format == "html":
        outcontent += "<!DOCTYPE html><html><head><meta charset='UTF-8'>"
        if title is not None:
            outcontent += f"<title>{title}</title>"
        if author is not None:
            outcontent += f"<meta name='author' content='{author}'>"
        if description is not None:
            outcontent += f"<meta name='description' content='{description}'>"
        if keywords is not None:
            outcontent += f"<meta name='keywords' content='{keywords}'>"
    # Now iterate over each page doing necessary conversions
    for idx, page in enumerate(pages):
        for element in page.findall(".//a[@xlink:href]", namespaces=namespaces):
            # Change xlink references to real html links
            element.attrib["href"] = element.get("{" + namespaces['xlink'] + "}href")
            if element.get("target") is not None:
                # Change external links to open in blank pages
                element.attrib["target"] = "_blank"
        outcontent += ET.tostring(page).decode("UTF-8")
    # Add the final parts of the format
    if format == "html":
        outcontent += "</body></html>"
    # Write the translated content to the output file
    with open(output, "wb") as fout:
        fout.write(outcontent.encode("UTF-8"))


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser("Converter from StylusLabs Write svgz to other formats")
    parser.add_argument("-i", "--input", type=str,
                        help="The input file path")
    parser.add_argument("-o", "--output", type=str,
                        help="The output file path")
    parser.add_argument("-f", "--format", type=str, default="html", const="html", nargs="?",
                        choices=["html", "pdf"],
                        help="The output format: html or pdf")
    parser.add_argument("-t", "--title", type=str, default=None,
                        help="The title to give to the document")
    parser.add_argument("-a", "--author", type=str, default=None,
                        help="The author of the document")
    parser.add_argument("-d", "--description", type=str, default=None,
                        help="A description to embed in the document")
    parser.add_argument("-k", "--keywords", type=str, default=None,
                        help="Comma separated keywords to embed in the document")
    args = parser.parse_args()
    convert_write_file(**vars(args))
