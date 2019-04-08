# Contents

## `JnrlAbbreviator`

Find abbreviations for journal titles. 

```python
# Constructor
JnrlAbbreviator(nproc)    
"""
  nproc: number of processors to initialize with (aftwards runs only as serial)
"""
  
# Functions
convert(jname)
"""
  Convert a single entry, returns abbreviation. 
  If input is abbreviation, returns that abbreviation

  jname: name of journal (string)
"""

convet_clipboard()
"""
  Fetches journal name from clipboard, and places abbreviation back on clipboard. 
"""
  
convert_bibfile(filename,inplace=False)
"""
  Search bibtext ".bib" file for journal entries and write a new file with the abbreviations. 

  filename: path to file to read
  inplace:  overwrite input file. Otherwise makes a copy with suffix "_jabbr "in the same directory
"""
```
