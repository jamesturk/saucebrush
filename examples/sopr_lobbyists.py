"""
    Import SOPR lobbyist filings using lobbyists.py
    (http://github.com/dhess/lobbyists/tree/master)
    
"""
import saucebrush
from saucebrush.filters import *
from saucebrush.emitters import DjangoModelEmitter, DebugEmitter
import lobbyists

def process_sopr_filing(sopr_xml_file):
    from sunlightapi import settings as DJ_SETTINGS
    DJ_APPLABEL = 'lobbyists'
    
    saucebrush.run_recipe(lobbyists.parse_filings(sopr_xml_file),
        # flatten non-list dictionaries & clean up some fields
        DictFlattener(['filing', 'client', 'registrant']),
        FieldRemover(['govt_entities', 'affiliated_orgs', 'foreign_entities',
                      'client_state_or_local_gov', 'client_status',
                      'filing_affiliated_orgs_url']),
        FieldRenamer({'filing_date': 'filing_filing_date'}),
        
        # process names & dates
        FieldAdder('client_contact_name', ''),
        FieldAdder('registrant_name', ''),
        NameCleaner('client_contact_name', prefix='client_', nomatch_name='client_raw_contact_name'),
        NameCleaner('registrant_name', prefix='registrant_', nomatch_name='registrant_raw_name'),
        FieldModifier('filing_date', lambda x: x.split('.')[0]),
        DateCleaner('filing_date', from_format='%Y-%m-%dT%H:%M:%S', to_format='%Y-%m-%d'),
        
        # flatten lists
        Flattener(['issues', 'lobbyists']),
        FieldCopier({'issues.filing_id': 'filing_id',
                     'lobbyists.filing_id': 'filing_id'}),
        
        # handle lists
        saucebrush.filters.Splitter({
          'issues':[DjangoModelEmitter(DJ_SETTINGS, DJ_APPLABEL, 'issue')],
          'lobbyists':[FieldRemover(['indicator', 'status']),
                       NameCleaner(['name']),
                       FieldRenamer({'raw_name': 'name'}),
                       Unique(),    # remove some duplicate lobbyists on a form
                       DjangoModelEmitter(DJ_SETTINGS, DJ_APPLABEL, 'lobbyist')
                       ],
        }),
        FieldRemover(['issues', 'lobbyists']),
        DjangoModelEmitter(DJ_SETTINGS, DJ_APPLABEL, 'filing')
    )
    
if __name__ == '__main__':
    import sys
    for fname in sys.argv[1:]:
        print 'processing', fname
        process_sopr_filing(fname)