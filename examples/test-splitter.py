from saucebrush.filters import Splitter, PhoneNumberCleaner, FieldMerger, FieldAdder
from saucebrush.emitters import DebugEmitter
import operator
import saucebrush

data = [{'person': {'firstname': 'James', 'lastname': 'Turk'},
         'phones': [{'phone': '222-222-2222'}, {'phone': '(202) 333-3321'}]
       }]

namemerger = FieldMerger({'name': ('firstname', 'lastname')}, lambda x,y: ' '.join((x,y)))
phonecleaner = PhoneNumberCleaner(('phone',))
splitter = Splitter({'person':[namemerger], 'phones':[phonecleaner]})
ider = FieldAdder('id', [1,2,3,4,5])

saucebrush.run_recipe(data, [ider, splitter, DebugEmitter()])
