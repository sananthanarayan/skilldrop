"""Valid binary seeds for the fuzz targets that read Office and Outlook files (RFC-0062).

A fuzzer starting from a file that fails the first header check never reaches the parser
behind it, so these build small but genuine files, with the standard library only:

  outlook_msg()  an Outlook .msg (Compound File Binary, version 3): subject, sender, body, sent
                 time, one recipient and one attachment, as Outlook lays them out
  docx(), xlsx(), pptx()   minimal Office Open XML packages; each takes its main XML part, so a
                           target can fuzz that part inside an otherwise valid package
"""
import io
import struct
import zipfile

END, FREE, FATSECT, NOSTREAM = 0xFFFFFFFE, 0xFFFFFFFF, 0xFFFFFFFD, 0xFFFFFFFF
SS, MSS = 512, 64


def _utf16(s):
    return s.encode("utf-16-le")


def _props(header, entries):
    """A __properties_version1.0 stream: a header, then 16-byte fixed-size property records."""
    out = bytearray(header)
    for pid, ptype, value in entries:
        out += struct.pack("<IIQ", (pid << 16) | ptype, 6, value)
    return bytes(out)


def outlook_msg(subject="Quarterly figures", body="Hello,\r\nthe figures are attached.\r\nThanks", sender="Avery Example",
                address="avery@example.com", to="Robin Example", to_address="robin@example.com"):
    filetime = 133_000_000_000_000_000  # 2022-06-18, as 100 ns ticks since 1601
    # (name, kind, data or children) — kind 1 is a storage, 2 a stream
    tree = [
        ("__substg1.0_0037001F", 2, _utf16(subject)),
        ("__substg1.0_1000001F", 2, _utf16(body)),
        ("__substg1.0_0C1A001F", 2, _utf16(sender)),
        ("__substg1.0_0C1F001F", 2, _utf16(address)),
        ("__properties_version1.0", 2, _props(b"\x00" * 32, [(0x0039, 0x0040, filetime)])),
        ("__recip_version1.0_#00000000", 1, [
            ("__substg1.0_3001001F", 2, _utf16(to)),
            ("__substg1.0_3003001F", 2, _utf16(to_address)),
            ("__properties_version1.0", 2, _props(b"\x00" * 8, [(0x0C15, 0x0003, 1)])),
        ]),
        ("__attach_version1.0_#00000000", 1, [
            ("__substg1.0_3707001F", 2, _utf16("figures.csv")),
            ("__substg1.0_37010102", 2, b"region,total\nnorth,12\n"),
        ]),
    ]

    entries = [{"name": "Root Entry", "kind": 5, "data": b"", "child": NOSTREAM, "right": NOSTREAM}]

    def add(items):
        first, prev = None, None
        for name, kind, payload in items:
            idx = len(entries)
            entries.append({"name": name, "kind": kind, "data": payload if kind == 2 else b"",
                            "child": NOSTREAM, "right": NOSTREAM})
            if kind == 1:
                entries[idx]["child"] = add(payload)
            if prev is None:
                first = idx
            else:
                entries[prev]["right"] = idx  # siblings chained to the right; the reader walks left and right
            prev = idx
        return first if first is not None else NOSTREAM

    entries[0]["child"] = add(tree)

    # every stream is under the 4096-byte cutoff, so all live in the mini stream
    mini, minifat = bytearray(), []
    for e in entries:
        if e["kind"] == 2:
            e["start"], e["size"] = len(mini) // MSS, len(e["data"])
            n = max(1, -(-len(e["data"]) // MSS))
            minifat += [len(mini) // MSS + k + 1 for k in range(n - 1)] + [END]
            mini += e["data"].ljust(n * MSS, b"\x00")
        else:
            e["start"], e["size"] = (0 if e["kind"] == 1 else END), 0

    n_dir = -(-len(entries) * 128 // SS)
    n_mini = -(-len(mini) // SS)
    # sector 0: FAT; then directory, then the mini FAT, then the mini stream's sectors
    dir_start, minifat_start, ministream_start = 1, 1 + n_dir, 2 + n_dir
    fat = [FATSECT]
    fat += [dir_start + k + 1 for k in range(n_dir - 1)] + [END]
    fat += [END]
    fat += [ministream_start + k + 1 for k in range(n_mini - 1)] + [END]
    fat += [FREE] * (SS // 4 - len(fat))
    entries[0]["start"], entries[0]["size"] = ministream_start, len(mini)

    def dirent(e):
        name = _utf16(e["name"]) + b"\x00\x00"
        raw = bytearray(128)
        raw[:len(name)] = name
        struct.pack_into("<HBB", raw, 64, len(name), e["kind"], 1)
        struct.pack_into("<III", raw, 68, NOSTREAM, e["right"], e["child"])
        struct.pack_into("<II", raw, 116, e["start"], e["size"])
        return bytes(raw)

    directory = b"".join(dirent(e) for e in entries).ljust(n_dir * SS, b"\x00")
    mfat = struct.pack("<%dI" % len(minifat), *minifat).ljust(SS, b"\xff")
    header = bytearray(SS)
    header[0:8] = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"
    struct.pack_into("<HHHHH", header, 24, 0x003E, 3, 0xFFFE, 9, 6)
    struct.pack_into("<IIIIIIIII", header, 40, 0, 1, dir_start, 0, 4096, minifat_start, 1, END, 0)
    struct.pack_into("<109I", header, 76, 0, *([FREE] * 108))
    body_sectors = struct.pack("<%dI" % (SS // 4), *fat) + directory + mfat + bytes(mini).ljust(n_mini * SS, b"\x00")
    return bytes(header) + body_sectors


def _zip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, text in files.items():
            z.writestr(name, text)
    return buf.getvalue()


CT = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' \
     '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>' \
     '<Default Extension="xml" ContentType="application/xml"/>%s</Types>'
W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def docx(document=None):
    doc = document if document is not None else DOCX_XML
    return _zip({"[Content_Types].xml": CT % '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>',
                 "_rels/.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
                 "word/document.xml": doc})


DOCX_XML = ('<?xml version="1.0" encoding="UTF-8"?><w:document %s><w:body>'
            '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Release notes</w:t></w:r></w:p>'
            '<w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Fixed</w:t></w:r><w:r><w:t xml:space="preserve"> the importer.</w:t></w:r></w:p>'
            '<w:tbl><w:tr><w:tc><w:p><w:r><w:t>Area</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Count</w:t></w:r></w:p></w:tc></w:tr>'
            '<w:tr><w:tc><w:p><w:r><w:t>Billing</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>3</w:t></w:r></w:p></w:tc></w:tr></w:tbl>'
           '</w:body></w:document>') % W


XLSX_NS = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
XLSX_XML = ('<?xml version="1.0"?><worksheet %s><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="inlineStr"><is><t>Total</t></is></c></row>'
            '<row r="2"><c r="A2" t="s"><v>1</v></c><c r="B2"><v>12.5</v></c><c r="C2" t="b"><v>1</v></c><c r="D2" s="1"><v>45000</v></c></row>'
            '<row r="4"><c r="AB4" t="str"><f>A2&amp;B2</f><v>North12.5</v></c></row></sheetData>'
            '<mergeCells count="1"><mergeCell ref="A1:B1"/></mergeCells></worksheet>') % XLSX_NS


def xlsx(sheet=None):
    ns = XLSX_NS
    return _zip({"[Content_Types].xml": CT % '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
                 "_rels/.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
                 "xl/workbook.xml": '<?xml version="1.0"?><workbook %s><sheets><sheet name="Totals" sheetId="1" r:id="rId1"/></sheets></workbook>' % ns,
                 "xl/_rels/workbook.xml.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/></Relationships>',
                 "xl/sharedStrings.xml": '<?xml version="1.0"?><sst %s count="2" uniqueCount="2"><si><t>Region</t></si><si><t>North</t></si></sst>' % ns,
                 "xl/worksheets/sheet1.xml": sheet if sheet is not None else XLSX_XML})


PPTX_NS = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
PPTX_XML = ('<?xml version="1.0"?><p:sld %s><p:cSld><p:spTree><p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr/><p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr><p:txBody><a:p><a:r><a:t>Q3 review</a:t></a:r></a:p></p:txBody></p:sp>'
            '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Body"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:txBody><a:p><a:pPr lvl="1"/><a:r><a:t>Revenue up 4%%</a:t></a:r></a:p></p:txBody></p:sp>'
            '<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="4" name="Table"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr><a:graphic><a:graphicData><a:tbl>'
            '<a:tr><a:tc><a:txBody><a:p><a:r><a:t>Region</a:t></a:r></a:p></a:txBody></a:tc><a:tc gridSpan="2"><a:txBody><a:p><a:r><a:t>Total</a:t></a:r></a:p></a:txBody></a:tc></a:tr>'
            '</a:tbl></a:graphicData></a:graphic></p:graphicFrame></p:spTree></p:cSld></p:sld>') % PPTX_NS


def pptx(slide=None):
    p = PPTX_NS
    return _zip({"[Content_Types].xml": CT % '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>',
                 "_rels/.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>',
                 "ppt/presentation.xml": '<?xml version="1.0"?><p:presentation %s><p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst></p:presentation>' % p,
                 "ppt/_rels/presentation.xml.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/></Relationships>',
                 "ppt/slides/slide1.xml": slide if slide is not None else PPTX_XML})
