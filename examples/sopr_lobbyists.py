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
        FieldRemover(['govt_entities', 'affiliated_orgs']),
        Flattener(['issues', 'lobbyists']),
        FieldCopier({'issues.filing_id': 'filing.id',
                     'client.filing_id': 'filing.id',
                     'lobbyists.filing_id': 'filing.id',
                     'registrant.filing_id': 'filing.id'}),
        saucebrush.filters.Splitter({
          'client':[FieldRemover(['state_or_local_gov', 'status']),
                    NameCleaner(['contact_name']),
                    FieldRenamer({'raw_contact_name': 'contact_name'}),
                    DjangoModelEmitter(DJ_SETTINGS, DJ_APPLABEL, 'client')
                    ],
          'filing':[FieldRemover(['affiliated_orgs_url']),
                    DateCleaner(['filing_date'], from_format='%Y-%m-%dT00:00:00', to_format='%Y-%m-%d'),
                    DjangoModelEmitter(DJ_SETTINGS, DJ_APPLABEL, 'filing')
                    ],
          'issues':[DjangoModelEmitter(DJ_SETTINGS, DJ_APPLABEL, 'issue')],
          'lobbyists':[FieldRemover(['indicator', 'status']),
                       NameCleaner(['name']),
                       FieldRenamer({'raw_name': 'name'}),
                       Unique(),
                       DjangoModelEmitter(DJ_SETTINGS, DJ_APPLABEL, 'lobbyist')
                       ],
          'registrant':[NameCleaner(['name']),
                        FieldRenamer({'raw_name': 'name'}),
                        DjangoModelEmitter(DJ_SETTINGS, DJ_APPLABEL, 'registrant')
                        ],
        }),
    )
    
if __name__ == '__main__':
    import sys
    for fname in sys.argv[1:]:
        print 'processing', fname
        process_sopr_filing(fname)