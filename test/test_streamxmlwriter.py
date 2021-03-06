#!/usr/bin/env python
"""Test suite for Stream XML Writer module"""

# Copyright (c) 2009-2010 Filip Salomonsson
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import unittest
from io import BytesIO
import sys
from streamxmlwriter import *

def writer_and_output(*args, **kwargs):
    out = BytesIO()
    return XMLWriter(out, *args, **kwargs), out


class XMLWriterTestCase(unittest.TestCase):
    def testSingleElement(self):
        w, out = writer_and_output()
        w.start("foo")
        w.end()
        self.assertEqual(out.getvalue(), b"<foo />")

    def testTextData(self):
        w, out = writer_and_output()
        w.start("foo")
        w.data("bar")
        w.end()
        self.assertEqual(out.getvalue(), b"<foo>bar</foo>")

    def testSingleAttribute(self):
        w, out = writer_and_output()
        w.start("foo", {"bar": "baz"})
        w.end()
        self.assertEqual(out.getvalue(), b"<foo bar=\"baz\" />")

    def testSortedAttributes(self):
        w, out = writer_and_output()
        w.start("foo", {"bar": "bar", "baz": "baz"})
        w.end()
        self.assertEqual(out.getvalue(), b"<foo bar=\"bar\" baz=\"baz\" />")

    def testUnsortedAttributes(self):
        w, out = writer_and_output(sort=False)
        w.start("foo", (("baz", "baz"), ("bar", "bar")))
        w.end()
        self.assertEqual(out.getvalue(), b"<foo baz=\"baz\" bar=\"bar\" />")

    def testEscapeAttributes(self):
        w, out = writer_and_output()
        w.start("foo", {"bar": "<>&\""})
        w.end()
        self.assertEqual(out.getvalue(), b"<foo bar=\"&lt;>&amp;&quot;\" />")

    def testEscapeCharacterData(self):
        w, out = writer_and_output()
        w.start("foo")
        w.data("<>&")
        w.end()
        self.assertEqual(out.getvalue(), b"<foo>&lt;&gt;&amp;</foo>")

    def testFileEncoding(self):
        w1, out1 = writer_and_output()
        w2, out2 = writer_and_output(encoding="us-ascii")
        w3, out3 = writer_and_output(encoding="iso-8859-1")
        w4, out4 = writer_and_output(encoding="utf-8")
        for w in (w1, w2, w3, w4):
            w.start("foo")
            if (sys.hexversion >= 0x030000F0):
              eval('w.data("\xe5\xe4\xf6\u2603\u2764")')
            else:
              eval('w.data(u"\xe5\xe4\xf6\u2603\u2764")')
            w.end()
        self.assertEqual(out1.getvalue(),
                         b"<foo>\xc3\xa5\xc3\xa4\xc3\xb6\xe2\x98\x83\xe2\x9d\xa4</foo>")
        self.assertEqual(out2.getvalue(),
                         b"<foo>&#229;&#228;&#246;&#9731;&#10084;</foo>")
        self.assertEqual(out3.getvalue(),
                         b"<?xml version='1.0' encoding='iso-8859-1'?>" \
                         b"<foo>\xe5\xe4\xf6&#9731;&#10084;</foo>")
        self.assertEqual(out4.getvalue(),
                         b"<foo>\xc3\xa5\xc3\xa4\xc3\xb6\xe2\x98\x83\xe2\x9d\xa4</foo>")

    def testClose(self):
        w, out = writer_and_output()
        w.start("a")
        w.start("b")
        w.close()
        self.assertEqual(out.getvalue(), b"<a><b /></a>")

    def testDeclarationLateDeclarationRaisesSyntaxError(self):
        w, out = writer_and_output()
        w.start("a")
        self.assertRaises(XMLSyntaxError, w.declaration)

    def testIgnoreDoubleDeclaration(self):
        w, out = writer_and_output()
        w.declaration()
        w.declaration()
        w.close()
        self.assertEqual(out.getvalue(),
                         b"<?xml version='1.0' encoding='utf-8'?>")

    def testAbbrevEmpty(self):
        w, out = writer_and_output(abbrev_empty=False)
        w.start("a")
        w.close()
        self.assertEqual(out.getvalue(), b"<a></a>")


    def testNamedEnd(self):
        w, out = writer_and_output()
        w.start("a")
        w.end("a")
        w.close()
        self.assertTrue(True)

class PrettyPrintTestCase(unittest.TestCase):
    def testSimple(self):
        w, out = writer_and_output(pretty_print=True)
        w.start("a")
        w.start("b")
        w.data("foo")
        w.end()
        w.start("b")
        w.data("bar")
        w.end()
        w.start("b")
        w.start("c")
        w.close()
        self.assertEqual(out.getvalue(), b"<a>\n  <b>foo</b>\n  <b>bar</b>\n  <b>\n    <c />\n  </b>\n</a>")

    def testComment(self):
        w, out = writer_and_output(pretty_print=True)
        w.start("a")
        w.comment("comment")
        w.start("b")
        w.close()
        self.assertEqual(out.getvalue(),
                         b"<a>\n  <!--comment-->\n  <b />\n</a>")

    def testCommentBeforeRoot(self):
        w, out = writer_and_output(pretty_print=True)
        w.comment("comment")
        w.start("a")
        w.close()
        self.assertEqual(out.getvalue(),
                         b"<!--comment-->\n<a />")

    def testCommentAfterRoot(self):
        w, out = writer_and_output(pretty_print=True)
        w.start("a")
        w.end()
        w.comment("comment")
        w.close()
        self.assertEqual(out.getvalue(),
                         b"<a />\n<!--comment-->")

    def testPI(self):
        w, out = writer_and_output(pretty_print=True)
        w.start("a")
        w.pi("foo", "bar")
        w.start("b")
        w.close()
        self.assertEqual(out.getvalue(),
                         b"<a>\n  <?foo bar?>\n  <b />\n</a>")

    def testPIBeforeRoot(self):
        w, out = writer_and_output(pretty_print=True)
        w.pi("foo", "bar")
        w.start("a")
        w.close()
        self.assertEqual(out.getvalue(),
                         b"<?foo bar?>\n<a />")

    def testPIAfterRoot(self):
        w, out = writer_and_output(pretty_print=True)
        w.start("a")
        w.end()
        w.pi("foo", "bar")
        w.close()
        self.assertEqual(out.getvalue(),
                         b"<a />\n<?foo bar?>")


class NamespaceTestCase(unittest.TestCase):
    def testSimple(self):
        w, out = writer_and_output()
        w.start_ns("", "http://example.org/ns")
        w.start("{http://example.org/ns}foo")
        w.close()
        self.assertEqual(out.getvalue(),
                         b'<foo xmlns="http://example.org/ns" />')

    def testAttribute(self):
        w, out = writer_and_output()
        w.start_ns("a", "http://example.org/ns")
        w.start("foo", {"{http://example.org/ns}bar": "baz"})
        w.close()
        self.assertEqual(out.getvalue(),
                         b'<foo xmlns:a="http://example.org/ns" a:bar="baz" />')

    def testPrefixedElement(self):
        w, out = writer_and_output()
        w.start_ns("a", "http://example.org/ns")
        w.start("{http://example.org/ns}foo")
        w.close()
        self.assertEqual(out.getvalue(),
                         b'<a:foo xmlns:a="http://example.org/ns" />')

    def testDefaultUnbinding(self):
        w, out = writer_and_output()
        w.start_ns("", "http://example.org/ns")
        w.start("{http://example.org/ns}foo")
        w.start_ns("", "")
        w.start("foo")
        w.close()
        self.assertEqual(out.getvalue(),
                         b'<foo xmlns="http://example.org/ns">'
                         b'<foo xmlns="" /></foo>')

    def testPrefixRebinding(self):
        w, out = writer_and_output()
        w.start_ns("a", "http://example.org/ns")
        w.start("{http://example.org/ns}foo")
        w.start_ns("a", "http://example.org/ns2")
        w.start("{http://example.org/ns2}foo")
        w.close()
        self.assertEqual(out.getvalue(),
                         b'<a:foo xmlns:a="http://example.org/ns">'
                         b'<a:foo xmlns:a="http://example.org/ns2" />'
                         b'</a:foo>')

    def testAttributesSameLocalName(self):
        w, out = writer_and_output()
        w.start_ns("a", "http://example.org/ns1")
        w.start_ns("b", "http://example.org/ns2")
        w.start("foo")
        w.start("bar", {"{http://example.org/ns1}attr": "1",
                        "{http://example.org/ns2}attr": "2"})
        w.close()
        self.assertEquals(out.getvalue(),
                          b'<foo xmlns:a="http://example.org/ns1"'
                          b' xmlns:b="http://example.org/ns2">'
                          b'<bar a:attr="1" b:attr="2" />'
                          b'</foo>')

    def testAttributesSameLocalOnePrefixed(self):
        w, out = writer_and_output()
        w.start_ns("a", "http://example.org/ns")
        w.start("foo")
        w.start("bar", {"{http://example.org/ns}attr": "1",
                        "attr": "2"})
        w.close()
        self.assertEquals(out.getvalue(),
                          b'<foo xmlns:a="http://example.org/ns">'
                          b'<bar attr="2" a:attr="1" />'
                          b'</foo>')

    def testAttributesSameLocalOnePrefixedOneDefault(self):
        w, out = writer_and_output()
        w.start_ns("", "http://example.org/ns1")
        w.start_ns("a", "http://example.org/ns2")
        w.start("{http://example.org/ns1}foo")
        w.start("{http://example.org/ns1}bar",
                {"{http://example.org/ns1}attr": "1",
                 "{http://example.org/ns2}attr": "2"})
        w.close()
        self.assertEquals(out.getvalue(),
                          b'<foo xmlns="http://example.org/ns1"'
                          b' xmlns:a="http://example.org/ns2">'
                          b'<bar attr="1" a:attr="2" />'
                          b'</foo>')


class IterwriteTestCase(unittest.TestCase):
    def testBasic(self):
        from lxml import etree
        w, out = writer_and_output()
        xml = """\
<!--comment before--><?pi before?><foo xmlns="http://example.org/ns1">
  <?a pi?>
  <bar xmlns:b="http://example.org/ns2">
    <?pi inside?>some text
    <baz attr="1" b:attr="2" />
    oh dear<!--comment inside -->text here too
  </bar>
</foo><?pi after?><!--comment after-->"""
        xmlbytes = xml.encode('utf-8')
        events = ("start", "end", "start-ns", "end-ns", "pi", "comment")
        w.iterwrite(etree.iterparse(BytesIO(xmlbytes), events))
        w.close()
        self.assertEqual(out.getvalue(), xmlbytes)

    def testChunkedText(self):
        from lxml import etree
        for padding in (16382, 32755):
            padding = " " * padding
            w, out = writer_and_output()
            xml = "%s<doc><foo>hello</foo></doc>" % padding
            xmlbytes = xml.encode('utf-8')
            events = ("start", "end")
            w.iterwrite(etree.iterparse(BytesIO(xmlbytes), events))
            w.close()
            self.assertEqual(out.getvalue(), xml.strip().encode('utf-8'))


# from lxml import etree
# 
# rmt = etree.parse("test/xmlconf/eduni/namespaces/1.0/rmt-ns10.xml")
# 
# #<TEST RECOMMENDATION="NS1.0" SECTIONS="2" URI="001.xml" ID="rmt-ns10-001" TYPE="valid">
# def test_factory(uri, id):
#     def func(self):
#         doc = etree.parse(uri)
#         canonical = StringIO()
#         doc.write_c14n(canonical, with_comments=False)
#         # print
#         # print
#         # print uri
#         # print tostring(doc.getroot())
#         events = ("start", "end", "start-ns", "end-ns")
#         out = StringIO()
#         w = XMLWriter(out, encoding="utf-8")
#         for event, elem in etree.iterparse(uri, events):
#             if event == "start-ns":
#                 prefix, ns = elem
#                 w.start_ns(prefix, ns)
#             elif event == "end-ns":
#                 w.end_ns()
#             elif event == "start":
#                 w.start(elem.tag, elem.attrib)
#                 if elem.text:
#                     w.data(elem.text)
#             elif event == "end":
#                 w.end(elem.tag)
#                 if elem.tail:
#                     w.data(elem.tail)
#         w.close()
#         canonical2 = StringIO()
#         tree = etree.ElementTree(etree.XML(out.getvalue()))
#         tree.write_c14n(canonical2, with_comments=False)
#         self.assertEquals(canonical.getvalue(),
#                           canonical2.getvalue())
#     return func
# for test in rmt.xpath(".//TEST[@TYPE='valid' or @TYPE='invalid']"):
#     uri = "test/xmlconf/eduni/namespaces/1.0/" + test.get("URI")
#     id = "test_" + test.get("ID").replace("-", "_")
#     setattr(NamespaceTestCase, id, test_factory(uri, id))



if __name__ == "__main__":
    unittest.main()
