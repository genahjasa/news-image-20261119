"""news-image-20261119 -- one image that sums up Thursday 19 November 2026.

The collage in image.jpg is a newspaper front page with four panels:

* the first-ever Trump-Xi-Putin trilateral, meeting in Shenzhen on the
  sidelines of APEC to talk nuclear arms, Ukraine and Iran;
* the US-Iran exchange widening across the Gulf -- US jets hitting a
  missile site on Qeshm Island while Iran strikes back in Bahrain
  and Kuwait;
* the International Court of Justice delivering its judgment in
  The Gambia v. Myanmar, the Rohingya genocide case, in The Hague;
* Grand Theft Auto VI rolling out worldwide, opening at 99 on
  Metacritic and sending players back to Vice City.

The program itself is deliberately boring: it finds image.jpg next to
this file, proves it is a real 1024x1024 JPEG, and writes the exact
same bytes to /output/entry.png. No network, no randomness, no image
processing -- running it twice produces byte-identical output.
"""

import hashlib
import os
import sys

IMAGE_FILE = "image.jpg"
DESTINATION = "/output/entry.png"
WANTED_WIDTH = 1024
WANTED_HEIGHT = 1024
CHUNK = 65536

# Start-of-frame markers whose segments store width and height.
FRAME_MARKERS = frozenset((
    0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
    0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
))


def die(reason):
    """Report a problem on stderr and stop with a non-zero status."""
    print("error: %s" % reason, file=sys.stderr)
    return 1


def file_digest(path):
    """sha256 hex digest of a file, read in chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        while True:
            block = stream.read(CHUNK)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def jpeg_size(blob):
    """Extract (width, height) from JPEG bytes, or raise ValueError.

    Walks the marker segments after the SOI magic until a start-of-frame
    segment is reached; its payload holds precision, height, width.
    Markers without a length field (padding, restarts, SOI) are skipped
    two bytes at a time instead of being read as segments.
    """
    if len(blob) < 4:
        raise ValueError("file too short to be a JPEG")
    if blob[0] != 0xFF or blob[1] != 0xD8:
        raise ValueError("does not start with the JPEG SOI marker")

    pos = 2
    while pos + 4 <= len(blob):
        if blob[pos] != 0xFF:
            raise ValueError("bad marker prefix at byte %d" % pos)
        code = blob[pos + 1]
        if code == 0xFF:  # fill byte, step past it
            pos += 1
            continue
        if code == 0x00 or 0xD0 <= code <= 0xD9:
            pos += 2  # stuffed byte, restart, SOI or EOI: no length
            continue
        size = int.from_bytes(blob[pos + 2:pos + 4], "big")
        if size < 2 or pos + 2 + size > len(blob):
            raise ValueError("segment at byte %d runs past the file" % pos)
        if code in FRAME_MARKERS:
            height = int.from_bytes(blob[pos + 5:pos + 7], "big")
            width = int.from_bytes(blob[pos + 7:pos + 9], "big")
            if width == 0 or height == 0:
                raise ValueError("start-of-frame reports a zero dimension")
            return width, height
        pos += 2 + size
    raise ValueError("no start-of-frame segment found")


def run():
    base = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(base, IMAGE_FILE)

    if not os.path.isfile(source):
        return die("no %s beside main.py (%s)" % (IMAGE_FILE, source))

    try:
        with open(source, "rb") as stream:
            blob = stream.read()
    except OSError as exc:
        return die("cannot read %s: %s" % (IMAGE_FILE, exc))

    if len(blob) == 0:
        return die("%s is empty" % IMAGE_FILE)

    try:
        width, height = jpeg_size(blob)
    except ValueError as exc:
        return die("%s is not a valid JPEG: %s" % (IMAGE_FILE, exc))

    if (width, height) != (WANTED_WIDTH, WANTED_HEIGHT):
        return die("%s is %dx%d, wanted %dx%d"
                   % (IMAGE_FILE, width, height,
                      WANTED_WIDTH, WANTED_HEIGHT))

    out_dir = os.path.dirname(DESTINATION)
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        return die("cannot create %s: %s" % (out_dir, exc))

    try:
        with open(DESTINATION, "wb") as stream:
            stream.write(blob)
    except OSError as exc:
        return die("cannot write %s: %s" % (DESTINATION, exc))

    expected = hashlib.sha256(blob).hexdigest()
    try:
        actual = file_digest(DESTINATION)
    except OSError as exc:
        return die("cannot re-read %s: %s" % (DESTINATION, exc))
    if actual != expected:
        return die("verification failed: %s differs from %s"
                   % (DESTINATION, IMAGE_FILE))

    print("wrote %s: %d bytes, sha256 %s"
          % (DESTINATION, len(blob), expected))
    return 0


if __name__ == "__main__":
    sys.exit(run())
