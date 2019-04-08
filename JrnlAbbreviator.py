# Fetch journal title abbreviation from web archive
# Derek Fujimoto
# Apr 2019

import warnings,requests,os
import pandas as pd
from bs4 import BeautifulSoup
from multiprocessing import Pool
from tqdm import tqdm

# patch the warnings class for nice output
def _warning(message,category=UserWarning,filename='',lineno=-1,file=None,line=None):
    print('%s:'%category.__name__,message)
warnings.showwarning = _warning

try:
    import pyperclip
except (ImportError,ModuleNotFoundError):
    warnings.warn('Warning: install pyperclip for convert_clipboard')

__doc__=\
"""
# Constructor
JnrlAbbreviator(nproc)    
    nproc: number of processors to initialize with (aftwards runs only as serial)
  
# Functions
convert(jname)
    Convert a single entry, returns abbreviation. 
    If input is abbreviation, returns that abbreviation
    
    jname: name of journal (string)
      
    Output
      abbreviation (string)

convet_clipboard()
    Fetches journal name from clipboard, and places abbreviation back on clipboard. 
  
convert_bibfile(filename,inplace=False)
    Search bibtext ".bib" file for journal entries and write a new file with the abbreviations. 
    
    filename: path to file to read
    inplace:  overwrite input file. Otherwise makes a copy with suffix "_jabbr "in the same directory
"""


# =========================================================================== #
class JrnlAbbreviator(object):
    
    url_base = 'http://images.webofknowledge.com/images/help/WOS/%s_abrvjt.html'
    
    replace_char = ('{','}','"',',','\\','=')
    journ_versions = ('journal','Journal','JOURNAL')
    
    # ======================================================================= #
    def __init__(self,nproc=1):
        """
            nproc = number of processors to use in initialization
        """
        
        # make list of letters
        letter_list = ['0-9']+[chr(i) for i in range(ord('A'),ord('Z')+1)]
        
        # build data structures
        if nproc > 1:
            p = Pool(nproc)
            try:
                df_list = tqdm(p.imap_unordered(self._fetch,letter_list),
                               desc='Building abbreviation list (n=%d)'%nproc,
                                leave=False,total=27)
            finally:
                p.close()
        else:
            df_list = tqdm(map(self._fetch,letter_list),
                           desc='Building abbreviation list',leave=False,
                           total=27)
        
        # make final data strucutre
        self.df = pd.concat(df_list,axis='index')
        
        # make nice abbreviations 
        self.df = self.df.str.title().str.split().str.join('. ')+'.'

    # ======================================================================= #
    def _fetch(self,letter):
        """Get series for indexing single letter"""

        # get url
        url = self.url_base%letter
        
        # get text data
        html=requests.get(url).text
        soup = BeautifulSoup(html,'lxml')
        
        # kill all script and style elements 
        for script in soup(["script", "style"]): 
            script.extract() 
        
        # get text lines
        lines = soup.get_text().splitlines()
        
        # remove header
        lines = lines[lines.index('Journal List')+1:]
        
        # drop blank lines 
        lines = list(filter(None,lines))
        
        # remove solo entries
        lines = [lines[i] for i in range(len(lines)-1) 
                    if not (lines[i][:1]!='\t' and lines[i+1][:1]!='\t')]
        
        # split into keys and abbreviations
        keys = [lines[i] for i in range(0,len(lines)-1,2)]
        abbr = (lines[i+1] for i in range(0,len(lines)-1,2))
            
        # get pandas series
        return pd.Series(abbr,index=keys)
        
    # ======================================================================= #
    def convert(self,jname):
        """
            Convert a single entry, returns abbreviation. 
            If input is abbreviation, returns that abbreviation
        """
        
        jupper = jname.upper()
        
        # replace initial "THE"
        if jupper[:3] == 'THE':  jupper = jupper[4:]
                
        # some sub journals listed with dashes
        if jupper not in self.df.index:
            jupper = jupper.replace(': ','-')
            
        # fetch abbreviation
        try:
            abbrev = self.df[jupper]
        
        # check if already in abbreviations list
        except KeyError:
            jname2 = jupper.replace('.','').title()
            jname2 = '. '.join(jname2.split())+'.'
            if jname2 in self.df.values:
                abbrev = jname2
            else:
                raise KeyError('"%s" not found in index or '%jname+\
                               'abbreviations lists')
        
        return abbrev

    # ======================================================================= #
    def convert_clipboard(self):
        """Convert based on clipboard and place back on clipboard"""
        pyperclip.copy(self.convert(pyperclip.paste()))
            
    # ======================================================================= #
    def convert_bibfile(self,filename,inplace=False):
        """Convert based on bibtex file. Writes new bibtex file"""
        
        # get file
        with open(filename,'r') as fid:
            lines = fid.readlines()
        
        # modify journal lines
        for i,line in enumerate(lines): 
            
            # check if journal line
            if any([j in line for j in self.journ_versions]):
                
                # get journal name 
                jname = line.translate({ord(s):'' for s in self.replace_char}).strip()
                jname = jname[7:].strip()
                
                # try to convert
                try:
                    abbrev = self.convert(jname)
                except KeyError:
                    warnings.warn('"%s" not found in index or '%jname+\
                                  'abbreviations lists (line %d)' % (i+1),
                                  RuntimeWarning)
                    continue
                
                # if in index, replace
                lines[i] = 'journal = {%s},\n'%abbrev
            
        # get output filename
        if inplace:
            filename2 = filename
        else:
            filename2 = os.path.splitext(filename)[0]+'_jabbr.bib'
            
        # write to file
        with open(filename2,'w') as fid:
            for l in lines:
                fid.write(l)
