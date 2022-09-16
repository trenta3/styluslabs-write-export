#!/usr/bin/env python3
import io, re, gzip
import xml.etree.ElementTree as ET
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas

# TODO: Add ability to show title, author, description, etc. in html body
# TODO: Add ability to export in the form of simple html slides (slide number, left and right arrows)
# TODO: Add ability to add footer and header to html pages directly from other files

__VERSION__ = "0.0.0"

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
    pages = write_root.findall("svg[@class='write-page']", namespaces)
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
        outcontent.setCreator(f"StylusLabs Write Export Script {__VERSION__}")
        if title is not None:
            outcontent.setTitle(title)
        if author is not None:
            outcontent.setAuthor(author)
        if description is not None:
            outcontent.setSubject(description)
    # Now iterate over each page doing necessary conversions
    for idx, page in enumerate(pages):
        # Get current page width and height (typically in pixels)
        pgwidth, pgheight = int(page.get("width")[:-2]), int(page.get("height")[:-2])
        pagelinks = []
        pagebookmarks = []
        for element in page.findall(".//path[@id][@class='bookmark']", namespaces):
            bookmark = {}
            bookmark["key"] = element.get("id")
            posmatch = re.search(r"translate\(([0-9\.]+),([0-9\.]+)\)", element.get("transform"))
            if not posmatch:
                raise Exception(f"Position matching for bookmark {ET.tostring(element).decode('utf-8')} failed")
            bookmark["top"] = pgheight - float(posmatch.group(1))
            bookmark["left"] = float(posmatch.group(2))
            pagebookmarks.append(bookmark)
        for element in page.findall(".//a[@xlink:href]", namespaces):
            link = {}
            # Change xlink references to real html links
            element.attrib["href"] = element.get("{" + namespaces['xlink'] + "}href")
            link["href"] = element.attrib["href"]
            if element.get("target") is not None:
                # Change external links to open in blank pages
                element.attrib["target"] = "_blank"
                link["target"] = element.attrib["target"]
            linkRect = element.find("rect", namespaces)
            rectx, recty, rectw, recth = (float(linkRect.get("x")), float(linkRect.get("y")),
                                          float(linkRect.get("width")), float(linkRect.get("height")))
            link["rect"] = (rectx, pgheight - recty, rectx + rectw, pgheight - (recty + recth))
            pagelinks.append(link)
        if format == "html":
            outcontent += ET.tostring(page).decode("UTF-8")
        elif format == "pdf":
            rlpage = svg2rlg(io.BytesIO(ET.tostring(page)))
            # Set the page sizes for the current page
            outcontent.setPageSize((pgwidth, pgheight))
            renderPDF.draw(rlpage, outcontent, x=0, y=0)
            # Add the current page bookmarks
            for bookmark in pagebookmarks:
                outcontent.bookmarkHorizontalAbsolute(bookmark["key"], top=bookmark["top"], fit="Fit")
            # Now we add the links using canvas elements
            for link in pagelinks:
                if link["href"].startswith("#"):
                    outcontent.linkRect("", link["href"][1:], Rect=link["rect"])
                else:
                    outcontent.linkURL(link["href"], rect=link["rect"], relative=1)
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
