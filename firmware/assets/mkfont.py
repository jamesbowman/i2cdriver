#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import struct
import random

def rand(n):
    return random.randrange(n)

def as565(im):
    """ Return RGB565 of im """
    (r,g,b) = [np.array(c).astype(np.uint16) for c in im.split()]
    def s(x, n):
        return x * (2 ** n - 1) / 255
    return (s(b, 5) << 11) | (s(g, 6) << 5) | s(r, 5)

def c3(rgb):
    return (16 * (0xf & (rgb >> 8)),
            16 * (0xf & (rgb >> 4)),
            16 * (0xf & (rgb >> 0)))

font2 = ImageFont.truetype("IBMPlexSans-SemiBold.otf", 13)
fontSP = ImageFont.truetype("pf_ronda_seven_bold.ttf", 8)

def pad2(s):
    if len(s) % 2:
        s.append(s[0])
    return s

def rfont2(c):
    im = Image.new("L", (128, 160))
    dr = ImageDraw.Draw(im)
    dr.text((10,40), c, font=font2, fill=255)
    # im.save("out.png")
    extents = im.getbbox()
    assert 10 <= extents[0]
    assert 45 <= extents[1]
    if c in "0123456789":
        extents = (0, 0, 10 + 8, 45 + 9)
    im = im.crop((10, 45) + extents[2:])
    (w,h) = im.size
    nyb = pad2((np.array(im).astype(int).flatten() * 15 / 255).tolist())
    return [w,h] + nyb

def rf(c, font):
    im = Image.new("L", (128, 160))
    dr = ImageDraw.Draw(im)
    dr.text((10,40), c, font=font, fill=255)
    # im.save("out.png")
    extents = im.getbbox()
    im = im.crop(extents)
    (w,h) = im.size
    nyb = (np.array(im).astype(int).flatten() * 15 / 255).tolist()
    return [w,h] + nyb

fs = open("../font.fs", "wt")
fb = 0

if __name__ == '__main__':
    fs.write('here constant tplan\n')
    fs.write('%d , %d , $%x%x , $%x , ," %s"\n' % (60, 0, 0xf, 0xf, 0xf, "V"))
    fb += 5 + len("V")
    # fs.write("[ %d ]\n" % fb)
    fs.write('%d , %d , $%x%x , $%x , ," %s"\n' % (108, 0, 0xf, 0xf, 0xf, "mA"))
    fb += 5 + len("mA")
    # fs.write("[ %d ]\n" % fb)

    fs.write('0 ,\n')
    fb += 1
    # im.save("out.png")

uniq = "".join(sorted(set("0123456789.mAVDMCS")))
f2 = sum([rfont2(c) for c in uniq], [])
print "font2 %s takes %d bytes" % (uniq, len(f2) / 2)
def nybbles(nn):
    s = len(nn)
    assert s % 2 == 0
    b = ["$%x%x ," % tuple(nn[i:i+2]) for i in range(0, s, 2)]
    return b
fs.write('here constant font\n')
for c in uniq:
    bb = nybbles(rfont2(c))
    print >>fs, "'%s' , " % c, " ".join(bb)
    fb += 1 + len(bb)

# See http://angband.pl/font/tinyfont.html
fs.write("\nhere constant micro\n")
if 1:
    tiny = Image.open("hex4x5.png").convert("L")
    for i in range(16):
        x = 5 * i
        im = tiny.crop((x, 0, x + 4, 5))
        rim = im.transpose(Image.ROTATE_90)
        ch = ((np.array(rim)).flatten() * 15.99 / 255).astype(np.uint8).tolist()
        fs.write(" ".join(nybbles(ch)) + "\n")
        fb += len(ch) / 2

if 1:
    # Image.open("arrow.png").transpose(Image.FLIP_LEFT_RIGHT).save("larrow.png")
    for n in ("symbol-s", "symbol-p", "symbol-b", "arrow", "larrow", "dot", "label-sda", "label-scl"):
        im = Image.open(n + ".png").convert("L")
        if n.startswith("label-"):
            im = im.point([0] + 254 * [64] + [255])
        rim = im.transpose(Image.ROTATE_90)
        (w,h) = rim.size
        ch = [w,h] + pad2(((np.array(rim)).flatten() * 15.99 / 255).astype(np.uint8).tolist())
        fs.write("here constant %s \n" % n)
        fs.write(" ".join(nybbles(ch)) + "\n")
        fb += len(ch) / 2

if 1:
    w = 72
    gpng = "plasma.png"
    grad = Image.open(gpng).convert("RGB").resize((w, 1), Image.BILINEAR).load()
    fs.write("\nHERE constant grad\n")
    for x in range(w):
        (r,g,b) = grad[x,0]
        r = (r * 15) // 255
        g = (g * 15) // 255
        b = (b * 15) // 255
        fs.write('$%x%x , $%x ,\n' % (r, g, b))
    fb += 2 * w

fs.close()

fs = open("../fontsize.fs", "wt")
fs.write("&%d constant FONTDATA_SIZE\n" % fb)
fs.close()
