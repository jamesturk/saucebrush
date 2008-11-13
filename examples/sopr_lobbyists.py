"""
    Import SOPR lobbyist filings using lobbyists.py
    (http://github.com/dhess/lobbyists/tree/master)
    
"""
import saucebrush
from saucebrush import utils
from saucebrush.filters import *
from saucebrush.emitters import DebugEmitter
import lobbyists

def process_sopr_filing(sopr_xml_file):
    
    saucebrush.run_recipe(lobbyists.parse_filings(sopr_xml_file),
                          FieldRemover(['govt_entities', 'affiliated_orgs']),
                          Flattener(['issues', 'lobbyists']),
                          saucebrush.filters.Splitter({
                            'client':[FieldRemover(['state_or_local_gov', 'status']), NameCleaner(['contact_name'])],
                            'filing':[FieldRemover(['affiliated_orgs_url'])],
                            'issues':[],
                            'lobbyists':[FieldRemover(['indicator', 'status']), NameCleaner(['name']), Unique()],
                            'registrant':[NameCleaner(['name'])],
                          }),
                          FieldCopier({'issues.filing_id': 'filing.id',
                                       'client.filing_id': 'filing.id',
                                       'lobbyists.filing_id': 'filing.id',
                                       'registrant.filing_id': 'filing.id'}),
                          DebugEmitter(open('test.out','w')),
    )
    
if __name__ == '__main__':
    process_sopr_filing('sample.xml')