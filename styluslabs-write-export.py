#!/usr/bin/env python3
import io, gzip
import xml.etree.ElementTree as ET
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas

# TODO: Make links work when exporting to pdf
# TODO: Add title, author, description, etc. annotations to pdf informations
# TODO: Add ability to show title, author, description, etc. in html body
# TODO: Add ability to export in the form of simple html slides (slide number, left and right arrows)
# TODO: Add ability to add footer and header to html pages directly from other files

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
    if format == "html":
        outcontent = ""
        outcontent += "<!DOCTYPE html><html><head><meta charset='UTF-8'>"
        if title is not None:
            outcontent += f"<title>{title}</title>"
        if author is not None:
            outcontent += f"<meta name='author' content='{author}'>"
        if description is not None:
            outcontent += f"<meta name='description' content='{description}'>"
        if keywords is not None:
            outcontent += f"<meta name='keywords' content='{keywords}'>"
    elif format == "pdf":
        outcontent = canvas.Canvas(output)
    # Now iterate over each page doing necessary conversions
    for idx, page in enumerate(pages):
        # Get current page width and height (typically in pixels)
        pgwidth, pgheight = page.get("width"), page.get("height")
        for element in page.findall(".//a[@xlink:href]", namespaces=namespaces):
            # Change xlink references to real html links
            element.attrib["href"] = element.get("{" + namespaces['xlink'] + "}href")
            if element.get("target") is not None:
                # Change external links to open in blank pages
                element.attrib["target"] = "_blank"
        if format == "html":
            outcontent += ET.tostring(page).decode("UTF-8")
        elif format == "pdf":
            rlpage = svg2rlg(io.BytesIO(ET.tostring(page)))
            # Set the page sizes for the current page
            rlwidth, rlheight = int(pgwidth[:-2]), int(pgheight[:-2])
            outcontent.setPageSize((rlwidth, rlheight))
            renderPDF.draw(rlpage, outcontent, x=0, y=0)
            outcontent.showPage()
    # Add the final parts of the format
    if format == "html":
        outcontent += "</body></html>"
        # Write the translated content to the output file
        with open(output, "wb") as fout:
            fout.write(outcontent.encode("UTF-8"))
    elif format == "pdf":
        outcontent.save()


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
