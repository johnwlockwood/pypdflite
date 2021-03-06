import unittest
from pypdflite.pdfobjects.pdfpage import PDFPage


class PageTest(unittest.TestCase):
    def setUp(self):
        self.__class__.testclass = PDFPage()

    def testCore(self):
        result = self.testclass.pagesize[0]
        self.assertEqual(result, 612)
        result = self.testclass.pagesize[1]
        self.assertEqual(result, 792)
