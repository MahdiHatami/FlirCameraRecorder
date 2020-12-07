# Flir camera recorder

## Installation

###
1. install FLIR SDK https://www.flir.eu/products/spinnaker-sdk/
2. install PySpin from installed folder (use .whl file to pip install)


## Image manipulation

### crop
    r3 = image.crop((641, 0, 960, 300))
    prediction = k_model.predict(r3)
    r4 = image.crop((0, 300, 320, 600))
    prediction = k_model.predict(r4)
    r5 = image.crop((321, 301, 641, 600))
    prediction = k_model.predict(r5)
    r6 = image.crop((641, 301, 960, 600))
    prediction = k_model.predict(r6)

### resize
    image = image.resize((960, 600))

