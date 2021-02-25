import tabula
import pandas as pd
import sys, os
from io import StringIO
import pdfplumber

class Pdf_Table_Extraction():

    def __init__(self, pdf) -> None:
        self.target_pdf = pdf
        self.elimination_periods = ['30', '60', '90', '180', '365', '730']
        
    def _split_drop_columns(self, table):
        self.raw_header=['Issue Age']
        drop_list = []
        
        colIndex = 1
        while colIndex < len(table.columns):   
            # Split and Expand                             
            if " " in str(table.iloc[1, colIndex]):              
                table = pd.concat([
                    table[table.columns[0:colIndex]],
                    table.iloc[:,colIndex].str.split(expand=True),
                    table[table.columns[colIndex+1:len(table.columns)]],
                ],axis=1)                    
            # Read Header
            if not pd.isna(table.iloc[0, colIndex]):
                self.raw_header.append(table.iloc[0, colIndex])  
            # Columns To Be Dropped
            if pd.isna(table.iloc[1, colIndex]):
                drop_list.append(colIndex)  
            else:
                try:
                    float(table.iloc[1, colIndex])
                except: 
                    drop_list.append(colIndex)
                
            colIndex += 1

        table = table.drop(table.columns[drop_list], axis = 1)        
        return table

    def _fix_column_header(self, table):         
        new_header = ['Issue Age']        
        col_width = len(table.columns)

        for index in range(1, max(col_width - 2, 4) ):
            new_header.append(self.elimination_periods[index-1])
                
        counter = len(new_header) - col_width        
        while counter < 0:            
            new_header.append(self.raw_header[counter])        
            counter += 1
        
        table.columns = new_header   
        table = table.drop([0], axis = 0) # drop first row 

        return table
    
    def extract_table(self, target_page):  
        orig_err = sys.stderr
        sys.stderr = StringIO()
        # process pdf start
        table = tabula.read_pdf(self.target_pdf, pages = target_page)[0]        
        table = self._split_drop_columns(table)
        table = self._fix_column_header(table)
        # process pdf end
        sys.stderr = orig_err       
        
        # print(table.head(1))
        return table.reset_index(drop=True)

    def extract_meta_data(self, target_page):
        page = pdfplumber.open(self.target_pdf).pages[target_page-1]            
        lines = page.extract_text().splitlines()           
        result = f'{lines[3]}~{lines[7]}'        
        return result

if __name__ == '__main__':
    pte = Pdf_Table_Extraction('./Mutual of Omaha Filed Disability Policy - Rate Filing_20191029.pdf')

    for p in range(7,72):
        table_name = pte.extract_meta_data(p)
        clean_table = pte.extract_table(p)         
        print(f'Page {p}: {table_name}')

        file_path = f'./Data/{table_name}.csv'
        if not os.path.isfile(file_path):
            clean_table.to_csv(file_path)
        else: # append without header            
            clean_table.to_csv(file_path, mode='a', header=False)

 