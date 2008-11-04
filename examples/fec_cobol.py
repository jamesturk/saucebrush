from saucebrush.sources import FixedWidthFileSource
from saucebrush.filters import FieldModifier, FieldRemover
from saucebrush.emitters import SqliteEmitter, SqlDumpEmitter
from saucebrush import run_recipe

CM_FIELDS = [('id',9),('name',90),('treasurer',38),('street_1',34),
             ('street_2',34),('city',18),('state',2),('zipcode',5),
             ('designation',1),('type',1),('party',3),('filing_frequency',1),
             ('interest_group_category',1),('connected_org_name',38),
             ('candidate_id',9)]

# party_1 and party_3 become party and party_2
CN_FIELDS = [('id',9), ('name',38), ('party',3), ('fillerA',3), ('party_2',3),
             ('seat_status',1), ('fillerB',1), ('status',1), ('street_1',34),
             ('street_2',34), ('city',18), ('state',2), ('zipcode',5),
             ('committee_id', 9), ('election_year',2), ('district', 2)]

# Combines year field (split in data for no apparent reason)
INDIV_FIELDS = [('filer_id',9), ('amendment',1), ('report_type', 3),
                ('primary_general',1), ('microfilm_loc',11),
                ('transaction_type',3), ('name',34), ('city',18), ('state', 2),
                ('zipcode', 5), ('occupation', 35), ('month', 2), ('day', 2),
                ('year',4), ('amount',7), ('other_id',9),
                ('fec_record_number',7)]

# Combines year field (split in data for no apparent reason)
PAS2_FIELDS = [('id',9), ('amendment',1), ('report_type', 3),
               ('primary_general',1), ('microfilm_loc',11),
               ('transaction_type',3), ('month', 2), ('day', 2),
               ('year',4), ('amount',7), ('other_id',9), ('candidate_id',9),
               ('fec_record_number', 7)]


def fix_cobol_number(number):
    mapping = {']':'0', 'j':'1', 'k':'2', 'l':'3', 'm':'4', 'n':'5', 'o':'6', 'p':'7', 'q':'8', 'r':'9'}
    number = number.lstrip('0')
    if not number:
        number = '0'
    elif number[-1] in mapping.keys():
        number = '-' + number[0:-1] + mapping[number[-1]]
    return number

def process_fec_year(year):
    # committees
    source = FixedWidthFileSource(open('%s/foiacm.dta' % year), CM_FIELDS)
    #sqlite = SqliteOutput('fec%s.sqlite' % year, 'committee', [f[0] for f in CM_FIELDS if f[0] != 'filler'])
    emit_mysql = SqlDumpEmitter(open('fec%s.sql' % year,'a'), 'committee', [f[0] for f in CM_FIELDS if f[0] != 'filler'])
    run_recipe(source, emit_mysql)

    # candidate
    source = FixedWidthFileSource(open('%s/foiacn.dta' % year), CN_FIELDS)
    fieldremover = FieldRemover(('fillerA', 'fillerB'))
    #sqlite = SqliteOutput('fec%s.sqlite' % year, 'candidate', [f[0] for f in CN_FIELDS if f[0] != 'filler'])
    emit_mysql = SqlDumpEmitter(open('fec%s.sql' % year,'a'), 'candidate', [f[0] for f in CN_FIELDS if not f[0].startswith('filler')])
    run_recipe(source, fieldremover, emit_mysql)

    # contributions
    source = FixedWidthFileSource(open('%s/itcont.dta' % year), INDIV_FIELDS)
    decobolizer = FieldModifier(('amount', ), fix_cobol_number)
    #sqlite = SqliteOutput('fec%s.sqlite' % year, 'contribution', [f[0] for f in INDIV_FIELDS if f[0] != 'filler'])
    emit_mysql = SqlDumpEmitter(open('fec%s.sql' % year,'a'), 'contribution', [f[0] for f in INDIV_FIELDS if f[0] != 'filler'])
    run_recipe(source, decobolizer, emit_mysql)

if __name__=='__main__':
    process_fec_year(2008)
    #for year in [2000,2002,2004,2006,2008]:
    #    process_fec_year(year)
