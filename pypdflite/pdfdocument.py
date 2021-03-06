from pdfobjects.pdffont import PDFFont
from pdfobjects.pdfpage import PDFPage
from pdfobjects.pdfcolorscheme import PDFColorScheme
from pdfobjects.pdftext import PDFText
from pdfobjects.pdfcursor import PDFCursor
from pdfobjects.pdfline import PDFLine
from pdfobjects.pdfrectangle import PDFRectangle


class PDFDocument(object):
    """ The Document object is the base class that
        is used to add and manage the content of the
        pdf file.

        Document maintains lists of pages and other
        resources, provides for default selections,
        which can be changed through the convinence
        methods.

        Note that page and text objects do not maintain
        fonts themselves. If they must use them (for
        calculating widths or such), they must have
        the current font passed to them.

    """
    def __init__(self, session):
        "Sets up a standard default document."
        self.SS = session
        self.pages = []
        self.fonts = []               # array of used fonts
        self._setDefaults()

    def _setDefaults(self):
        self.setColorScheme()
        self._setDefaultFont()
        self.addPage()

    def setColorScheme(self, colorscheme=None):
        """ Default color object is black.

        """
        if colorscheme is None:
            self.colorscheme = PDFColorScheme()
        else:
            if isinstance(colorscheme, PDFColorScheme):
                self.colorscheme = colorscheme
            else:
                raise Exception("invalid color scheme")

    def _setDefaultFont(self):
        """ Internal method to set the
            initial default font. Change
            the font using setFont method.

        """
        self.font = PDFFont()
        self.font._setIndex()
        self.fonts.append(self.font)

    def addPage(self, page=None):
        """ May generate and add a PDFPage
            separately, or use this to generate
            a default page.

        """
        if page is None:
            self.page = PDFPage()
        else:
            self.page = page
        self.page._setIndex(len(self.pages))
        self.pages.append(self.page)
        currentfont = self.font
        self.setFont(font=currentfont)

    def getPage(self):
        "Returns reference to current page object."
        return self.page

    def setFont(self, family=None, style=None, size=None, font=None):
        """ Set the document font object, size given in points.
            If family, style, and/or size is given, generates
            a new Font object, checks to see if it is already
            in use, and selects it.

            May also use the font keyword to add an already
            instantiated PDFFont object.

        """

        if size is None:
            size = self.font.fontsize

        if font is not None:
            newfont = font
        else:
            newfont = PDFFont(family, style, size)

        #Test if font is already selected
        if not newfont._equals(self.font):
            #Test if used for the first time
            if newfont.fontkey not in self.fonts:
                i = len(self.fonts) + 1
                newfont._setIndex(i)
                self.fonts.append(newfont)

        #Select it
        self.font = newfont
        if(self.page.index > 0):
            self.SS._out('BT /F%d %.2f Tf ET' % (self.font.index, self.font.fontsize), self.page)
        else:
            del newfont

    def getFont(self):
        """ Get the current font object. Useful for storing
            in variables, and switching between styles.

        """
        return self.font

    def setFontSize(self, size):
        "Convinence method for just changing font size."
        if(self.font.fontsize == size):
            pass
        else:
            self.setFont(self.font.family, self.font.style, size)

    def _getOrientationChanges(self):
        """ Returns a list of the pages that have
            orientation changes.

        """
        self.orientation_changes = []
        for page in self.pages:
            if page.orientation_change is True:
                self.orientation_changes.append(page.index)
            else:
                pass
        return self.orientation_changes

    def _outputPages(self):
        """ Called by the PDFLite object to prompt creating
            the page objects.

        """
        if self.orientation_changes is None:
            self._getOrientationChanges()
        else:
            #Page
            for page in self.pages:
                self.SS._addObject()
                self.SS._out('<</Type /Page')
                self.SS._out('/Parent 1 0 R')
                if page in self.orientation_changes:
                    self.SS._out('/MediaBox [0 0 %.2f %.2f]' % (page.width, page.height))
                self.SS._out('/Resources 2 0 R')
                self.SS._out('/Contents %s 0 R>>' % len(self.SS.objects))
                self.SS._out('endobj')
                #Page content
                self.SS._addObject()
                if self.SS.compression is True:
                    textfilter = '/Filter /FlateDecode'
                    page._compress()
                else:
                    textfilter = ''
                self.SS._out('<< %s /Length %s >>' % (textfilter, len(page.buffer)))
                self.SS._putStream(page.buffer)
                self.SS._out('endobj')

    def _outputFonts(self):
        """ Called by the PDFLite object to prompt creating
            the font objects.

        """
        for font in self.fonts:
            obj = self.SS._addObject()
            font._setNumber(obj.id)
            self.SS._out('<</Type /Font')
            self.SS._out('/BaseFont /' + font.name)
            self.SS._out('/Subtype /Type1')
            if(font.name != 'Symbol' and font.name != 'ZapfDingbats'):
                self.SS._out('/Encoding /WinAnsiEncoding')
            self.SS._out('>>')
            self.SS._out('endobj')

    """ The following methods are the core ways to input content.

    """
    def addText(self, text):
        """ Input text, short or long. Writes in order, within the
            pre-defined page boundaries. Use addNewline as a return
            character. Sequential addText commands will print without
            additional whitespace.

            Currently all "left-justified", although that may change in
            future version.

        """
        text = PDFText(self.SS, self.page, self.font, self.colorscheme, text)

    def addNewline(self, number=1):
        """ Starts over again at the new line. If number is specified,
            it will leave multiple lines.
        """
        if isinstance(number, int):
            try:
                self.page.addNewline(self.font, number)
            except ValueError:
                self.addPage()
        else:
            raise TypeError("Number of newlines must be an integer.")

    def addIndent(self):
        """ Adds a standard tab of 4 spaces.
        """
        self.page.addIndent(self.font)

    def addLine(self, x1=None, y1=None, x2=None, y2=None, cursor1=None, cursor2=None):
        if cursor1 is not None:
            if cursor2 is not None:
                pass
        else:
            cursor1 = PDFCursor(x1, y1)
            cursor2 = PDFCursor(x2, y2)

        myline = PDFLine(self.SS, self.page, self.colorscheme, cursor1, cursor2)
        myline.draw()

    def drawHorizonalLine(self):
        endcursor = self.page.cursor.copy()
        endcursor.x = endcursor.xmax

        myline = PDFLine(self.SS, self.page, self.colorscheme, self.page.cursor, endcursor)
        myline.draw()

    def drawRectangle(self, x1=None, y1=None, x2=None, y2=None, width=None, height=None, cursor1=None, cursor2=None, style='S'):
        if cursor1 is not None:
            if cursor2 is not None:
                pass
            elif width is not None and height is not None:
                dims = PDFCursor(width, height)
                cursor2 = cursor1.add(dims)
            elif x2 is not None and y2 is not None:
                cursor2 = PDFCursor(x2, y2)
            else:
                raise Exception("Rectanlge not defined")
        else:
            if x1 is not None and y1 is not None:
                cursor1 = PDFCursor(x1, y1)
                if x2 is not None and y2 is not None:
                    cursor2 = PDFCursor(x2, y2)
                elif width is not None and height is not None:
                    dims = PDFCursor(width, height)
                    cursor2 = cursor1.add(dims)
                else:
                    raise Exception("Rectanlge not defined")
            else:
                raise Exception("Rectanlge not defined")

        rect = PDFRectangle(self.SS, self.page, self.colorscheme, cursor1, cursor2, size=1, style=style)
        rect.draw()

    def addTable(self, datalist, headerlist=None, cursor=None):
        pass