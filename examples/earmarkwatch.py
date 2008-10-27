from saucebrush.sources import CSVSource
from saucebrush.outputs import CSVOutput, DebugOutput

def merge_columns(datasource, mapping, merge_func):
    for rowdata in datasource:
        for to_col,from_cols in mapping.iteritems():
            values = [rowdata.pop(col, None) for col in from_cols]
            rowdata[to_col] = reduce(merge_func, values)
        yield rowdata

def add_column(datasource, column_name, column_value):
    if callable(column_value):
        for rowdata in datasource:
            rowdata[column_name] = column_value()
    else:
        for rowdata in datasource:
            rowdata[column_name] = column_value

def legislators_to_ids(datasource):
    for rowdata in datasource:
        names = rowdata['members'].split('; ')
        parties = rowdata['parties'].split('; ')
        states = rowdata['states'].split('; ')
        if not len(names) == len(parties) == len(states):
            raise Exception('line %d: len(names)=%d, len(parties)=%d, len(states)=%d' % (rowdata['row'], len(names), len(parties), len(states)))
        members = zip(names, parties, states)
        for name, party, state in members:
            pass

def main():
    import sys
    filename = sys.argv[1]

    column_names = ['house_amount', 'senate_amount', 'conference_amount',
                    'budget_request', 'request_letter', 'description', 'benficiary',
                    'address', 'city', 'county', 'state', 'zipcode', 'bill',
                    'bill_section', 'bill_subsection', 'project_heading',
                    'house_members', 'house_parties', 'house_states',
                    'senate_members', 'senate_parties', 'senate_states',
                    'presidential', 'undisclosed', 'intended_recipient', 'notes']

    output_names = ['appropriated', 'budget_request', 'request_letter',
                    'description', 'benficiary',
                    'address', 'city', 'county', 'state', 'zipcode', 'bill',
                    'bill_section', 'bill_subsection', 'project_heading',
                    'members', 'parties', 'states',
                    'presidential', 'undisclosed', 'intended_recipient', 'notes']

    data = CSVSource(open(filename), column_names, 1)
    data = merge_columns(data, {'appropriated': ['house_amount', 'senate_amount', 'conference_amount'],
                                'members': ['house_members', 'senate_members'],
                                'parties': ['house_parties', 'senate_parties'],
                                'states': ['house_states', 'senate_states']},
                         lambda x,y: x or y)

    output = CSVOutput(open('brushed.'+filename,'w'), output_names)

    for item in data:
        output.write(item)

if __name__=='__main__':
    main()
