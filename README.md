# StylusLabs Write Export
A simple python script to export Stylus Write `svgz` files to other formats with working links.
Currently implements exports to single comprehensive `html` files and to `pdf` files.

## Quick Start
```bash
# Install the needed dependencies
pip install -r requirements.txt
# Convert the example file into a single-page html
./styluslabs-write-export.py -i WriteSample.svgz -o WriteSample.html -f html
# Convert the example file into a pdf document
./styluslabs-write-export.py -i WriteSample.svgz -o WriteSample.pdf -f pdf
# See the available export options and metadata
./styluslabs-write-export.py -h
```
