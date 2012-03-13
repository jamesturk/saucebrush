import re
import exceptions

class FECSource(object):

    SPLIT_CHAR = '\x1c'
    FORM_FIELDS = {
        'F56' : ['form_type', 'committee_id', 'transaction_id', 'entity_type',
                 'contributor_organization', 'contributor_lastname', 'contributor_firstname',
                 'contributor_middlename', 'contributor_prefix', 'contributor_suffix',
                 'contributor_street1', 'contributor_street2', 'contributor_city',
                 'contributor_state', 'contributor_zip', 'contributor_committee_id',
                 'date', 'amount', 'contributor_employer', 'contributor_occupation']
    }

    # use Regex to map forms to keys in FORM_FIELDS
    FORM_MAPPING = (
        ('F1(A|N)', 'F1'),
        ('F1S', 'F1S'),
        ('F1M(A|N)', 'F1M'),
        ('F2(A|N)', 'F2'),
        ('F2S', 'F2S'),
        ('F24', 'F24'),
        ('F3(N|A|T)', 'F3'),
        ('F3S', 'F3S'),
        ('F3ZT?', 'F3Z'),
        ('F3P(N|A|T)', 'F3P'),
        ('F3PS', 'F3PS'),
        ('F3P31AL', 'F3P31AL'),
        ('F3X(N|A|T)', 'F3X'),
        ('F4(N|A|T)', 'F4'),
        ('F5(N|A|T)', 'F5'),
        ('F56', 'F56'),
        ('F57', 'F57'),
        ('F6', 'F6'),
        ('F65', 'F65'),
        ('F7(N|A|T)', 'F7'),
        ('F76', 'F76'),
        ('F8(N|A|T)', 'F8'),
        ('F82', 'F82'),
        ('F83', 'F83'),
        ('F9(A|N)', 'F9'),
        ('F91', 'F91'),
        ('F92', 'F92'),
        ('F93', 'F93'),
        ('F94', 'F94'),
        ('F10', 'F10'),
        ('F105', 'F105'),
        ('F13(A|N)', 'F13'),
        ('F132', 'F132'),
        ('F133', 'F133'),
        ('F99', 'F99'),
        ('SA.+', 'SA'),
        ('SB.+', 'SB'),
        ('SC/.+', 'SC'),
        ('SC1/.+', 'SC1'),
        ('SC2/.+', 'SC2'),
        ('SD.+', 'SD'),
        ('SE', 'SE'),
        ('SF', 'SF'),
        ('H1', 'H1'),
        ('H2', 'H2'),
        ('H3', 'H3'),
        ('H4', 'H4'),
        ('H5', 'H5'),
        ('H6', 'H6'),
        ('SI', 'SI'),
        ('SL', 'SL'),
        ('TEXT', 'TEXT'),
    )

    # compile regexes with optional quotes
    FORM_MAPPING = dict( [(re.compile("(\")?%s(\")?" % pattern), form)
                        for pattern,form in FORM_MAPPING] )

    def __init__(self, filename):
        self.filename = filename
        self.fecfile = open(filename)
        self.header = self.fecfile.readline().split(self.SPLIT_CHAR)
        if self.header[0] != "HDR":
            print self.header
        #assert self.header[2].startswith("6.2"), self.header
        self._in_textblock = False

    @staticmethod
    def get_form_type(rectype):
        for type_re, type in FECSource.FORM_MAPPING.items():
            if type_re.match(rectype):
                return type

    def process_file(self):
        begintext = re.compile('\[BEGINTEXT\]', re.IGNORECASE)
        endtext = re.compile('\[ENDTEXT\]', re.IGNORECASE)
        in_textblock = False

        for line in self.fecfile:

            # get fields from line
            fields = line.split(self.SPLIT_CHAR)

            # handle the BEGINTEXT/ENDTEXT blocks
            if begintext.match(fields[0]):
                in_textblock = True
            elif begintext.match(fields[0]):
                in_textblock = False
            elif line != '\n' and not in_textblock:
                type = self.get_form_type(fields[0])
                if type in self.FORM_FIELDS:
                    yield dict(zip(self.FORM_FIELDS[type], fields))

    def __iter__(self):
        return self.process_file()
