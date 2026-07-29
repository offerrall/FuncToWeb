# Image with Pillow

Optional dependency: **Pillow**.

```bash
pip install pillow
```

`image.py` draws a square gradient with a frame and a label, and returns
the `PIL.Image.Image` object unchanged: FuncToWeb recognizes it as an image,
encodes it as a PNG, and sends it as a data URI inside an `image` output.

What it demonstrates:

* returning a Pillow image produces an `image` output, not the object's `str()`;
* FuncToWeb does not import Pillow: it detects Pillow because the example has
  already imported it, so the dependency lives only in this file;
* the color input uses the `Color` type.

Run it from the repository root:

```bash
python examples/outputs_optional/pillow/image.py
```
