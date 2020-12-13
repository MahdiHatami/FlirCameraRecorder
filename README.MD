# Flir camera recorder

## Installation

###
1. install FLIR SDK https://www.flir.eu/products/spinnaker-sdk/
2. install PySpin from installed folder (use .whl file to pip install)


## Image preparation

### resize
    image = image.resize((960, 600))

### Slice image
    r1 = rimage.crop((0, 0, 320, 300))
    r2 = rimage.crop((321, 0, 640, 300))
    r3 = image.crop((641, 0, 960, 300))
    r4 = image.crop((0, 300, 320, 600))
    r5 = image.crop((321, 301, 641, 600))
    r6 = image.crop((641, 301, 960, 600))

