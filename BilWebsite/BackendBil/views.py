from django.shortcuts import render
import re
import pdfplumber
import pandas as pd
import os
from django.db import IntegrityError
import logging
from decimal import Decimal

from django.http import HttpResponse
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from .models import BankStatement
from .models import Bank,System,DailyReportBankStatement,BankAccount
from django.db.models import Q
from datetime import date, datetime
from django.db import connection
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from datetime import datetime
from openpyxl.styles import NamedStyle
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
import openpyxl

pattern_lms = r'\b\d{9}\b'

pattern_pf = r'^(\d{5,})\s*-\s*(.*)' 
pattern_insurance = r'^\d{9}+$'
rr_pattern = re.compile(r':(\d+)/')
record_pattern = re.compile(r'\d{2}-[A-Z]{3}-\d{2}')
description_pattern = re.compile(r'(?<=\d{2}-[A-Z]{3}-\d{2})(?!.*\b\d{3}[A-Z]+\d{10,}|\d{16}\b).*')
pattern_reference = re.compile(r'\b\d{3}[A-Za-z]+\d+|\d{16}\b')
instrument_pattern = re.compile(r'(?<![-/#,&\d])\b\d{6}\b(?![-/#,&\d]| [A-Z])')
pattern_amount = re.compile(r'\d{1,3}(?:,\d{3})*\.\d{2}')
cheque_cleared = re.compile(r'(#|NO|[.])\s*(\d{6})')
in_house = re.compile(r'(?:-)\s*(\d{6})')
Incoming_fund_transfer = re.compile(r'(?:RRN-|RRN\s*-)\s*(\d+)')
bank_number_regex = re.compile(r'STATEMENT OF ACCOUNT FOR\s*[:]*\s*(\d{6,})')
Bob_Bank_number_regex = re.compile(r'ACCOUNT NO.\s*[:]*\s*(\d{6,})')
date_style = NamedStyle(name="date_style", number_format="YYYY-MM-DD")
logger = logging.getLogger(__name__)
def clean_cell(cell):
    if cell is not None:
        return cell.replace('\n', ' ').strip()
    return cell
cursor = connection.cursor()

def index(request):
    
    return render(request, 'home.html')
def user(request):
    
    return render(request, 'userpage.html')
def uploadBankStatement(request):
    folder='my_folder/' 
    
    if request.method == 'POST':
        system_name = request.POST.get('system_name')
        system_namer = request.POST.get('system_name_drop_down')
        bank_name = request.POST.get('bank_name')
        bank_namer = request.POST.get('bank_name_drop_down')
      
        Bank_data= None
        System_data=None
        try:
            Bank_data = Bank.objects.get(Q(name=bank_name) | Q(name=bank_namer))
            System_data = System.objects.get(Q(name=system_name)| Q(name=system_namer))
            print(System_data)

        except System.DoesNotExist:
            print("theerer")
            return render(request, 'uploaddailyreport.html', {'error': 'No such system present'})
        except Bank.DoesNotExist:
            print("theerer")
            return render(request, 'uploaddailyreport.html', {'error': 'No such bank name present'})
        except:
            messages.error(request,"No data  present")
            return render(request,'uploadbankstatement.html')
       
      
        uploaded_file = request.FILES.get('file') or request.FILES.get('file_drop')
        print(Bank_data)
       
        
        if uploaded_file:
            fs = FileSystemStorage(location=folder)
            filename = fs.save(uploaded_file.name, uploaded_file)
    

            file_path = fs.path(filename)
        else:
       
            messages.error(request,"Please Upload the file please")
            return render(request, 'uploadbankstatement.html', {'error': 'Please upload the file'})
        
        if bank_name=='Bank of Bhutan' or bank_namer=="Bank of Bhutan":
            Bob_Bank_number = None
           
            if os.path.exists(file_path):

                pdf = pdfplumber.open(file_path)  # Use the absolute path to open the file
                data_save = False
                clean_data = []
                for page in pdf.pages:
                    raw_text = page.extract_text()
                    if raw_text:
        # Split text by lines and then combine lines based on record boundaries
                        lines = raw_text.split('\n')
                        for Line in lines:
                            bank_number = Bob_Bank_number_regex.search(Line)
                            if bank_number is not None:
                                Bob_Bank_number=bank_number.group(1)
                                

                    count_table = page.extract_table()
                    cleaned_table = [[clean_cell(cell) for cell in row] for row in count_table]
                    df = pd.DataFrame(cleaned_table[1:], columns=cleaned_table[0])
                    df = df.drop('VALUE DATE', axis=1)
                    for index, row in df.iterrows():
                        particulars = row.get('PARTICULARS', '')
                        if particulars and not particulars.endswith('88888'):
                            match_data = rr_pattern.search(particulars)
                            if match_data:
                                df.at[index, 'PARTICULARS'] = match_data.group(1)
                            else:
                                df.at[index, 'PARTICULARS'] = ''


                        else:
                            df.at[index, 'PARTICULARS'] = ''
                    data_dicts = df.to_dict(orient='records')
                    clean_data.extend(data_dicts)
                  
                for record in clean_data:
                    try:
                        date = datetime.strptime(record['POST DATE'], '%d/%m/%Y')
                    except ValueError:
                        print(f"Skipping record with invalid date: {record['POST DATE']}")
                        continue
                    journal_number = record.get('journal_number', '').strip() or None
                    balance = float(record['BALANCE'].replace(',', '')) if record['BALANCE'] else None
                    balance = round(balance, 2) if balance is not None else None
                    


                    # if not BankStatement.objects.filter(
                    # date=date,
                    # journal_number=journal_number).exists():
                    try:
                 
                            BankStatement.objects.create(
                            date = date,
                            journal_number=record['JOURNAL NUMBER'],
                            rr_number= record['PARTICULARS'] if record['PARTICULARS'] else None,
                            debit=float(record['DEBIT'].replace(',', '')) if record['DEBIT'] else None,
                            credit = float(record['CREDIT'].replace(',', '')) if record['CREDIT'] else None,
                            instrument_number= record['CHEQUE NO/ REFERENCE'] if record['CHEQUE NO/ REFERENCE'] else None,
                            balance=balance,
                            bank_name=Bank_data,
                            bank_account_number= Bob_Bank_number,
                            system_name=System_data,

                            )
                    except IntegrityError:
                            pass
                            # logger.warning(f"Duplicate entry found for date: {date} and journal number: {journal_number}.")

                            
                                
                    data_save= True
                if data_save:
                    print("The data are saved perfectly")
                    messages.success(request, "The data are saved perfectly")
                else:
                 messages.error(request, "No valid data to save")
            else:
                print("Failed to save data")

        elif bank_name=='Bhutan National Bank' or bank_namer=="Bhutan National Bank":
            if os.path.exists(file_path):
                pdf = pdfplumber.open(file_path)
                BankStatementSave = False
                Bank_Number = None
                combined_lines = []
                current_record = []
                formatted_transactions = []
                for page in pdf.pages:
                    raw_text = page.extract_text()
                    if raw_text:
                        lines = raw_text.split('\n')
                        for line in lines:
                            line = line.strip()
            
            # Search for bank number
                            bank_number = bank_number_regex.search(line)
                            if bank_number is not None:
                                Bank_Number = bank_number.group(1)
                
                            if record_pattern.match(line):
                                if current_record:
                                    combined_lines.append(' '.join(current_record).strip())
                                current_record = [line]
                            else:
                                current_record.append(line)
                        if current_record:
                            combined_lines.append(' '.join(current_record).strip())
                            current_record = []
                formatted_records = []
                for record in combined_lines:
                    if not record_pattern.match(record):
                        if formatted_records:
                            formatted_records[-1] += ' ' + record
                        else:
                            formatted_records.append(record)
                    else:
                        formatted_records.append(record)
                
                for record in formatted_records:
                    date_match = record_pattern.search(record)
                    date = date_match.group() if date_match else ''
                    description_match = description_pattern.search(record)
                    description = description_match.group() if description_match else ''
                    if description.strip().startswith("CHEQUE CLEARED"):
                        cheque_number = cheque_cleared.search(description)   
                        if cheque_number:
                            transaction_number = cheque_number.group(2)
                            transaction_status = "CHEQUE CLEARED"

                        else:
                            transaction_number = None
                            transaction_status = None

                    elif description.strip().startswith("In-House"):
                        inhouse_pattern = in_house.search(description)   
                        if inhouse_pattern:
                            transaction_number = inhouse_pattern.group(1)
                            transaction_status= "IN-House Cheque"
                        else:
                            transaction_number = None
                            transaction_status = None
                    elif description.strip().startswith("Incoming Fund Transfer"):
                        Incoming = Incoming_fund_transfer.search(description)   
                        if Incoming:
                            transaction_number = Incoming.group(1)
                            transaction_status = "INCOMING FUND TRANSFER"
                        else:
                            transaction_number = None
                            transaction_status = None
                    elif description.strip().startswith("Incoming Payment via"):
                        Incoming = Incoming_fund_transfer.search(description)   
                        if Incoming:
                            transaction_number = Incoming.group(1)
                            transaction_status = "Incoming Payment via"
                        else:
                            transaction_number = None
                            transaction_status = None
                    else:
                        transaction_number = None
                        transaction_status = None
                    references = pattern_reference.findall(record)
                    reference = references[0] if references else ' '
                    instrument_match = instrument_pattern.search(record)
                    instrument = instrument_match.group() if instrument_match else ' '
                    amounts = pattern_amount.findall(record)
                    credit_balance = amounts[0] if len(amounts) > 0 else ''
                    balance = amounts[1] if len(amounts) > 1 else ''
                    formatted_transactions.append({
                            "Date": date,
                            "Description": description,
                            "Reference": reference,
                            "CheckNo_InstrumentNo": instrument,
                            "Amount": credit_balance,
                            "Balance": balance,
                            "TransactionNumber": transaction_number,
                            "Transaction_status": transaction_status
                        })

                    
                formatted_transactions = formatted_transactions[2:]
                
                for record in formatted_transactions:
                    try:
                        date = datetime.strptime(record['Date'], '%d-%b-%y')
                        BankStatement.objects.create(
                            date=date,
                            journal_number= record['TransactionNumber'] if record['TransactionNumber'] else None,
                            rr_number= record['Description'] if record['Description'] else None,
                            instrument_number=record['CheckNo_InstrumentNo'] if record['CheckNo_InstrumentNo'] else None,
                            reference_no= record['Reference'] if record['Reference'] else None,
                            transaction_type=record['Transaction_status'] if record['Transaction_status'] else None,
                            credit=float(record['Amount'].replace(',', '')),
                            balance=float(record['Balance'].replace(',', '')),
                            bank_name=Bank_data,
                            bank_account_number=Bank_Number,
                            system_name=System_data,)
                        BankStatementSave = True
                    except IntegrityError as e:
                            logger.warning(f"IntegrityError: {e}. Record with date {date} and journal number {journal_number} already exists.")
                    except ValueError as e:
                        print(f"Error parsing date: {e}")
                       
                    
                            
                if BankStatementSave:
                    print("The data are saved perfectly")
                    messages.success(request, "The data are saved perfectly")
                else:
                    messages.error(request, "No valid data to save")

        else:
            messages.error(request, "Please Enter the  require details")             
                            
        



    return render(request, 'uploadbankstatement.html')

def uploaddailyreport(request):
    folder='dailyreport/'
    if request.method == 'POST':

        system_name = request.POST.get('system_name')
        system_namer = request.POST.get('system_name_drop_down')
       
        
        
        try:
            System_data = System.objects.get(Q(name=system_name)| Q(name=system_namer))
            print(System_data)

        except System.DoesNotExist:
            messages.error(request, "No such system name are  present")
            return render(request, 'uploaddailyreport.html', {'error': 'No such bank name present'})
        except Exception as e:
            print(e)
            return render(request, 'uploaddailyreport.html', {'error': f'Error retrieving data: {e}'})
        uploaded_file = request.FILES.get('file') or request.FILES.get('file_drop')
        print(uploaded_file)
        if uploaded_file:
            print("hsgfsh")
            fs = FileSystemStorage(location=folder)
            filename = fs.save(uploaded_file.name, uploaded_file)
    

            file_path = fs.path(filename)
            pdf_extension=file_path.endswith(".pdf")
            excel_extension = file_path.endswith(".xlsx")

            print(pdf_extension,excel_extension)

        else:
       
            print("Please upload the file")
            return render(request, 'uploadbankstatement.html', {'error': 'Please upload the file'})
        try:
            if system_name=='PF':
                if os.path.exists(file_path):
                    
                    
                    if pdf_extension:  
                        pdf = pdfplumber.open(file_path)  
                        clean_data = []
                        BankStatement = False
                        for page in pdf.pages:
                            count_table = page.extract_table()
    
                            if count_table is None:
                                continue  # Skip to the next page if no table is found

                            cleaned_table = []
                            for row in count_table:
                                clean_row = []
                                for cell in row:
                                    if cell is None:
                                        clean_row.append('')  # Handle None cells if necessary
                                    else:
                                        cleaned_cell = clean_cell(cell)
                                        clean_row.append(cleaned_cell)
                                cleaned_table.append(clean_row)


                            df = pd.DataFrame(cleaned_table[1:], columns=cleaned_table[0])
    
  
                            columns_to_drop = ['Sl.No', 'MOU Date', 'Branch']
                            for col in columns_to_drop:
                                if col in df.columns:
                                    df = df.drop(col, axis=1)
       
                            data_dicts = df.to_dict(orient='records')

                            clean_data.extend(data_dicts)
                            try:
                                for record  in data_dicts:
                                    if not DailyReportBankStatement.objects.filter(voucher_no=record['Voucher No']).exists():
                
                                        DailyReportBankStatement.objects.create(
                                            tran_date= record['Voucher Date'] if record['Voucher Date'] else  None,
                                            voucher_no= record['Voucher No'] if record['Voucher No'] else  None,
                                            customer_name= record['Organization'] if record['Organization'] else  None,
                                            ref_number = record['Company A/c No'] if record['Company A/c No'] else None,
                                            tran_mode= record['Trans. Mode'] if record['Trans. Mode'] else  None,
                                            instrument_number= record['Inst No'] if record['Inst No'] else  None,
                                            instrument_date= record['Cheque date'] if record['Cheque date'] else  None,
                                            bank_name = record['Bank Name'] if record['Bank Name'] else  None,
                                            cheque_amount=float(record.get('Cheque Amount', '0').replace(',', '')),
                                            cash_amount=float(record['Cash Amount'].replace(',', '')) if record['Cash Amount'] else  None,
                                            system_name=System_data,
        
                                        )
                                    BankStatement = True
                            except Exception as e:
                                print(f"There was a problem uploading the data: {e}")
                                continue
                    elif excel_extension:
                        account_number = None
                        wb = openpyxl.load_workbook(file_path)
                        ws = wb.active

                        first_sheet = wb.worksheets[0]
                        for row in first_sheet.iter_rows():
                            for cell in row:
                                match=re.search(pattern_pf,str(cell.value))
                                if match:  # Check if the regex pattern matches
                                        account_number = match.group(1)
                                        print(f"Account Number: {account_number}")
                        clean_data = []
                        for row in ws.iter_rows():
                            for cell in row:
                                for cell in row:
                                    if not cell.border.left.style:
                                        try:
                                            cell.value = None
                                        except:
                                            continue
                        df = pd.DataFrame(ws.values).dropna(how='all', axis=0).dropna(how='all', axis=1).reset_index(drop=True) # load into pandas, drop empty rows and columns
                        df = df.T.set_index(0).T
                        date_format = '%Y-%m-%d'
                        df['Instrument Date'] = pd.to_datetime(df['Instrument Date'],format=date_format, errors='coerce').dt.date
                        df['Instrument Date'] = df['Instrument Date'].apply(lambda x: x if pd.notna(x) else None)




                        data_dicts = df.to_dict(orient='records')
                   
                        try:
                            for record  in data_dicts:
                                if not DailyReportBankStatement.objects.filter(voucher_no=record['Voucher No']).exists():

                                    DailyReportBankStatement.objects.create(
                                        tran_date= record['Trans.Date'].strftime('%Y-%m-%d') if record['Trans.Date'] else  None,
                                        voucher_no= record['Voucher No'] if record['Voucher No'] else  None,
                                        instrument_number= record['Instrument No'] if record['Instrument No'] else  None,
                                        instrument_date= record['Instrument Date'] if record['Instrument Date'] else  None,
                                        credit_amount=float(record['Cr Amount']) if record['Cr Amount'] else  0, 
                                        debit_amount=float(record['Dr Amount']) if record['Dr Amount'] else  0,
                                        system_name=System_data,
                                        bank_account_number=account_number
        
                                 )
                                BankStatement = True
                        except Exception as e:
                            print(f"There was a problem uploading the data: {e}")
                    else:
                        print("No such extension")  

            elif system_name == 'Insurance':
                if os.path.exists(file_path):
                    wb = openpyxl.load_workbook(file_path)
                    ws = wb.active
                    first_sheet = wb.worksheets[0]
                    account_number= None
                    for row in first_sheet.iter_rows():
                        for cell in row:
                            if not cell.border.left.style:
                                match=re.search(pattern_insurance,str(cell.value))
                                if match:  # Check if the regex pattern matches
                                    account_number = match.group()
                                    print(f"Account Number: {account_number}")
                    clean_data = []
                    for row in ws.iter_rows():
                        for cell in row:
                            for cell in row:
                                if not cell.border.left.style:
                                    try:
                                        cell.value = None
                                    except:
                                        continue
                    df = pd.DataFrame(ws.values).dropna(how='all', axis=0).dropna(how='all', axis=1).reset_index(drop=True) # load into pandas, drop empty rows and columns
                    df = df.T.set_index(0).T
                    date_format = '%Y-%m-%d'
                    df['Instrument Date'] = pd.to_datetime(df['Instrument Date'],format=date_format, errors='coerce').dt.date
                    df['Instrument Date'] = df['Instrument Date'].apply(lambda x: x if pd.notna(x) else None)




                    data_dicts = df.to_dict(orient='records')
                   
                    try:
                        for record  in data_dicts:
                            date_str = record.get('Date')
                            if date_str:
                                try:
                                    date_obj = datetime.strptime(date_str, '%d-%b-%Y')  # Adjust format if needed
                                    formatted_date = date_obj.strftime('%Y-%m-%d')
                                except ValueError:
                                    formatted_date = None
                            else:
                                formatted_date = None
                            if not DailyReportBankStatement.objects.filter(voucher_no=record['Voucher No']).exists():

                                DailyReportBankStatement.objects.create(
                                    tran_date=formatted_date,
                                    voucher_no= record['Voucher No'] if record['Voucher No'] else  None,
                                    instrument_number= record['Instrument No'] if record['Instrument No'] else  None,
                                    instrument_date= record['Instrument Date'] if record['Instrument Date'] else  None,
                                    credit_amount=float(record['Cr Amount']) if record['Cr Amount'] else  0, 
                                    debit_amount=float(record['Dr Amount']) if record['Dr Amount'] else  0,
                                    system_name=System_data,
                                    bank_account_number=account_number
        
                                )
                            BankStatement = True
                    except Exception as e:
                        print(f"There was a problem uploading the data: {e}")
            elif system_name == 'LMS':
                if os.path.exists(file_path):
                    wb = openpyxl.load_workbook(file_path)
                    ws = wb.active
                    first_sheet = wb.worksheets[0]
                    account_number=None
                    excel_data = pd.read_excel(file_path, sheet_name=None)
                    sheet_data = excel_data['Sheet1']

                    combined_text = " ".join(sheet_data.iloc[2:5].fillna('').apply(lambda row: ' '.join(row.values.astype(str)), axis=1))
                    matches = re.search(pattern_lms, combined_text)
                    if matches:
                        account_number=matches.group()
                        print(account_number)
                    clean_data = []
                    for row in ws.iter_rows():
                        for cell in row:
                            for cell in row:
                                if not cell.border.left.style:
                                    try:
                                        cell.value = None
                                    except:
                                        continue
                    df = pd.DataFrame(ws.values).dropna(how='all', axis=0).dropna(how='all', axis=1).reset_index(drop=True) # load into pandas, drop empty rows and columns
                    df = df.T.set_index(0).T
               


                    data_dicts = df.to_dict(orient='records')
                    # print(data_dicts)
                   
                    try:
                        for record  in data_dicts:
                            if not DailyReportBankStatement.objects.filter(voucher_no=record['Voucher No']).exists():

                                DailyReportBankStatement.objects.create(
                                    tran_date= record['Voucher Date'].strftime('%Y-%d-%m') if record['Voucher Date'] else  None,
                                    voucher_no= record['Voucher No'] if record['Voucher No'] else  None,
                                    instrument_number= record['Cheque/ Account No'] if record['Cheque/ Account No'] else  None,
                                    credit_amount=float(record['Cr Amount']) if record['Cr Amount'] else  0, 
                                    debit_amount=float(record['Dr Amount']) if record['Dr Amount'] else  0,
                                    system_name=System_data,
                                    bank_account_number=account_number
        
                                )
                            BankStatement = True
                    except Exception as e:
                        print(f"There was a problem uploading the data: {e}")


            if BankStatement:
                print("The data are saved perfectly")
                messages.success(request, "The data are saved perfectly")
                return render(request, 'uploaddailyreport.html')
            else:
                messages.error(request, "No valid data to save")       
        except:
            messages.error(request, "No valid data to save")   
       
    return render(request, 'uploaddailyreport.html')

def generateReport(request):
    context = {}  
    account_numbers = BankAccount.objects.values_list('account_number','account_name')
    system = System.objects.values_list('id', 'name')
    #  AND dr.system_name_id = %s
    #  AND bbs.bank_account_number = %s
    # system_id,account_number

    # AND dr.system_name_id = %s
    # AND bbs.bank_account_number= %s
    context = {
        'account_numbers': account_numbers,
        'system':system
        }
    if request.method == 'POST':
        system_id = None
        startdate = request.POST.get('start_date')
        enddate = request.POST.get('end_date')
        account_number = request.POST.get('account_number')
        print(account_number)
        
        systemname = request.POST.get('typeofsystem')
       
        if systemname:
            try:
                system = System.objects.get(name=systemname)
                print(system)
                system_id = system.id
                print(system_id)
            except System.DoesNotExist:
        # Handle the case where the systemname does not exist in the database
                print(f"System with name '{systemname}' does not exist.")
        else:
    # No systemname provided, system_id remains None
            print("No system name provided.")

       

        if not startdate and enddate and account_number:
            messages.error(request,"Please select all the required fields please")
            return render(request, 'generateReport.html',context)
     
        
        try:
           
            
            if startdate > enddate:
                messages.error(request, "Start date cannot be after end date.")
                return render(request, 'generateReport.html', context)

            
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
            return render(request, 'generateReport.html', context)
        
        wb = Workbook()
        
        # Remove the default sheet
        wb.remove(wb.active)
        
        # Create sheets
        sheet1 = wb.create_sheet('Reconciliation Report')
        sheet2 = wb.create_sheet('FailedBank statement')
        sheet3 = wb.create_sheet('Failed reportDCR')

        try:
            query = """
            SELECT 
                    dr.id,
                    dr.tran_date,
                    dr.voucher_no,
                    dr.instrument_number,
                    dr.credit_amount,
                    dr.debit_amount,
                    sys.name,
                    bbs.journal_number,
                    bbs.reference_no,
                    bbs.instrument_number AS bbs_instrument_number,
                    bbs.debit,
                    bbs.credit,
                    bbs.bank_account_number,
                    dr.status
                FROM public."BackendBil_dailyreportbankstatement" dr
                LEFT JOIN public."BackendBil_system" sys ON dr.system_name_id = sys.id
                LEFT JOIN public."BackendBil_bankstatement" bbs ON 
                    sys.id = bbs.system_name_id and(
                    dr.instrument_number = bbs.journal_number 
                    OR dr.instrument_number = bbs.instrument_number 
                    OR dr.instrument_number = bbs.reference_no)
 
                WHERE dr.status = 'success' 
                AND dr.tran_date BETWEEN %s AND %s 
                   
                """
        
        except Exception as e:
            print('your error ',e)
            messages.error(request, "An error occurred while processing your request.")
            return render(request, 'generateReport.html',context)
        conditions = []
        params = [startdate, enddate]
        

        
        if system_id and system_id != 'Select System ID':
            conditions.append("dr.system_name_id = %s")
            params.append(system_id)
       
        
        if  account_number and account_number != 'Select Account Number':
            conditions.append("bbs.bank_account_number = %s AND  dr.bank_account_number=%s")
            params.append(account_number)  # Append the first account number
            params.append(account_number)  # Append the first account number
        print("Constructed Query:", query)
        print("Parameters:", params)
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        try:
                try:
                    reconciliation_report = DailyReportBankStatement.objects.raw(query,params)
                    print("heelo")
                    
                except Exception as e:
                    print(f"An error occurred: {str(e)}")
                    messages.error(request, f"An error occurred while processing your request: {str(e)}")
                    return render(request, 'generateReport.html', context)
                total_records = len(list(reconciliation_report))
                
                print(f"Total records retrieved: {total_records}")
                headers = [
                            'SL.No', 'Date', 'Voucher Number', 'DCR Instrument Number', 
                            'DCR credit_amount','DCR debit_amount' ,'System Name', 'Bank Statement instrument_number', 
                            'bankstatement_reference_no', 'bankstatement_journalnumber',
                            'bankstatement_credit', 'bankstatement_debit', 'Bank Number', 'status'
                ]
                for col_num, header in enumerate(headers, 1):
                    col_letter = get_column_letter(col_num)
                    sheet1[f'{col_letter}1'] = header
                for row_num, record in enumerate(reconciliation_report, 2):            
                    sheet1[f'A{row_num}'] = row_num - 1  # SL.No starts from 1
                    sheet1[f'B{row_num}'] = getattr(record, 'tran_date', None)
                    sheet1[f'C{row_num}'] = getattr(record, 'voucher_no', 'N/A')
                    sheet1[f'D{row_num}'] = getattr(record, 'instrument_number', 'N/A')
                    sheet1[f'E{row_num}'] = getattr(record, 'credit_amount', 'N/A')
                    sheet1[f'F{row_num}'] = getattr(record, 'debit_amount', 'N/A')
                    sheet1[f'G{row_num}'] = getattr(record, 'name', 'N/A')
                    sheet1[f'H{row_num}'] = getattr(record, 'instrument_number', 'N/A')
                    sheet1[f'I{row_num}'] = getattr(record, 'reference_no', 'N/A')
                    sheet1[f'J{row_num}'] = getattr(record, 'journal_number', 'N/A')
                    sheet1[f'K{row_num}'] = getattr(record, 'credit', 'N/A')
                    sheet1[f'L{row_num}'] = getattr(record, 'debit', 'N/A')
                    sheet1[f'M{row_num}'] = getattr(record, 'bank_account_number', 'N/A')
                    sheet1[f'N{row_num}'] = getattr(record, 'status', 'N/A')

        except Exception as e:
                print(f"An error occurred: {str(e)}")
                return HttpResponse(f"An error occurred: {str(e)}", status=500)
        try:
            query = """
                SELECT  
                dr.id, dr.tran_date, dr.voucher_no, dr.instrument_number,
						dr.credit_amount,
						dr.debit_amount, dr.status
                FROM public."BackendBil_dailyreportbankstatement" dr
                WHERE (dr.status = 'Failed' or dr.status='Pending')
                AND dr.tran_date BETWEEN %s AND %s
                
    
            """
        except Exception as e:
            messages.error(request, "An error occurred while processing your request.")
            return render(request, 'generateReport.html',context)
        
        conditions = []
        params = [startdate, enddate] 

        
        # if system_id and system_id != 'Select System ID':
        #     conditions.append("dr.system_name_id = %s")
        #     params.append(system_id)
       

        
        if  account_number and account_number != 'Select Account Number':
            conditions.append("dr.bank_account_number=%s")
            params.append(account_number) 
          
        
        if conditions:
            query += " AND " + " AND ".join(conditions)

        print("Constructed Query:", query)
        print("Parameters:", params)

        try:
                try:
                    reconciliation_report = DailyReportBankStatement.objects.raw(query,params)
                    print("world")
                except Exception as e:
                    print(f"An error occurred: {str(e)}")
                    messages.error(request, f"An error occurred while processing your request: {str(e)}")
                    return render(request, 'generateReport.html', context)
                total_records = len(list(reconciliation_report))
                headers = ['SL.No', 'Date', 'Voucher Number',  'DCR Instrument Number','credit_amount', 'debit_amount', 'status']
                for col_num, header in enumerate(headers, 1):
                    col_letter = get_column_letter(col_num)
                    sheet3[f'{col_letter}1'] = header
                for row_num, record in enumerate(reconciliation_report, 2):
                    sheet3[f'A{row_num}'] = row_num-1
                    sheet3[f'B{row_num}'] = getattr(record, 'tran_date', None)
                    sheet3[f'C{row_num}'] = getattr(record, 'voucher_no', 'N/A')
                    sheet3[f'D{row_num}'] = getattr(record, 'instrument_number', 'N/A')
                    sheet3[f'E{row_num}'] = getattr(record, 'credit_amount', 'N/A')
                    sheet3[f'F{row_num}'] = getattr(record, 'debit_amount', 'N/A')
                 
                    sheet3[f'G{row_num}'] = getattr(record, 'status', 'N/A')

        except Exception as e:
                print(f"An error occurred: {str(e)}")
                return HttpResponse(f"An error occurred: {str(e)}", status=500)
        
        try:
            query = """
                SELECT bbs.id,bbs.date,bbs.journal_number,bbs.instrument_number,bbs.reference_no,bbs.debit,bbs.credit,bbs.bank_account_number,bbs.status FROM public."BackendBil_bankstatement" bbs 
                WHERE bbs.status = 'Failed'
                AND bbs.date BETWEEN %s AND %s
            
         
                
                """
        except Exception as e:
            messages.error(request, "An error occurred while processing your request.")
            return render(request, 'generateReport.html',context)
        conditions = []
        params = [startdate, enddate]
        
        

        
        if system_id and system_id != 'Select System ID':
            conditions.append("bbs.system_name_id = %s")
            params.append(system_id)
        
        if account_number and account_number != 'Select Account Number':
            conditions.append("bbs.bank_account_number = %s ")
            params.append(account_number)
        
        if conditions:
            query += " AND " + " AND ".join(conditions)
        try:
                try:
                    reconciliation_report = DailyReportBankStatement.objects.raw(query,params)
                    print("How are you")
                except Exception as e:
                    print(f"An error occurred: {str(e)}")
                    messages.error(request, f"An error occurred while processing your request: {str(e)}")
                    return render(request, 'generateReport.html', context)
                total_records = len(list(reconciliation_report))
                headers = ['SL.No', 'Date', 'Journal Number', 'Instrument Number', 'Reference  Number', 'debit','credit','Bank Account Number', 'status']
                for col_num, header in enumerate(headers, 1):
                    col_letter = get_column_letter(col_num)
                    sheet2[f'{col_letter}1'] = header
                for row_num, record in enumerate(reconciliation_report, 2):
                    sheet2[f'A{row_num}'] = row_num-1
                    sheet2[f'B{row_num}'] = getattr(record, 'date', None)
                    sheet2[f'C{row_num}'] = getattr(record, 'journal_number', 'N/A')
                    sheet2[f'D{row_num}'] = getattr(record, 'instrument_number', 'N/A')
                    sheet2[f'E{row_num}'] = getattr(record, 'reference_no', 'N/A')
                    sheet2[f'F{row_num}'] = getattr(record, 'debit', 'N/A')
                    sheet2[f'G{row_num}'] = getattr(record, 'credit', 'N/A')
                    sheet2[f'H{row_num}'] = getattr(record, 'bank_account_number', 'N/A')
                    sheet2[f'I{row_num}'] = getattr(record, 'status', 'N/A')

        except Exception as e:
                print(f"An error occurred: {str(e)}")
                return HttpResponse(f"An error occurred: {str(e)}", status=500)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'reconciliation_report_{timestamp}.xlsx'
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Save the workbook to the response
        wb.save(response)

        return response
    
    return render(request, 'generateReport.html',context)

from django.db import connection

def startReconcilation(request):
    startdate = request.POST.get('start_date')
    enddate = request.POST.get('end_date')
    
    if startdate and enddate:
        startdate = datetime.strptime(startdate, '%Y-%m-%d').date()
        enddate = datetime.strptime(enddate, '%Y-%m-%d').date()

        success = 0
        Failed = 0
        
        with connection.cursor() as cursor:
            # Update DailyReportBankStatement based on matching criteria
            cursor.execute('''
                UPDATE public."BackendBil_dailyreportbankstatement" drbs
                SET status = CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM public."BackendBil_bankstatement" bs
                        WHERE 
                            (
                                bs.journal_number = drbs.instrument_number OR 
                                bs.instrument_number = drbs.instrument_number OR 
                                bs.reference_no = drbs.instrument_number
                                OR bs.rr_number =drbs.instrument_number
                            ) 
                            AND 
                            (
                                bs.debit = drbs.credit_amount OR 
                                bs.credit = drbs.debit_amount
                            )
                    )
                    THEN 'success'
                    ELSE 'Failed'
                END
                WHERE drbs.tran_date BETWEEN %s AND %s
            ''', [startdate, enddate])
            
            # Count the number of successful and failed updates in DailyReportBankStatement
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
                    SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) AS failed_count
                FROM public."BackendBil_dailyreportbankstatement"
                WHERE tran_date BETWEEN %s AND %s
            ''', [startdate, enddate])
            result = cursor.fetchone()
            success = result[0] or 0
            Failed = result[1] or 0
            
            # Update BankStatement based on matching criteria
            cursor.execute('''
                UPDATE public."BackendBil_bankstatement" bs
                SET status = CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM public."BackendBil_dailyreportbankstatement" drbs
                        WHERE 
                            (
                                drbs.instrument_number = bs.journal_number OR 
                                drbs.instrument_number = bs.instrument_number OR 
                                drbs.instrument_number = bs.reference_no OR
                                drbs.instrument_number = bs.rr_number 

                            ) 
                            AND 
                            (
                                drbs.debit_amount = bs.credit OR 
                                drbs.credit_amount = bs.debit
                            )
                    )
                    THEN 'success'
                    ELSE 'Failed'
                END
                WHERE bs.date BETWEEN %s AND %s
            ''', [startdate, enddate])
            
            # Count the number of successful and failed updates in BankStatement
            cursor.execute('''
                SELECT 
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
                    SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) AS failed_count
                FROM public."BackendBil_bankstatement"
                WHERE date BETWEEN %s AND %s
            ''', [startdate, enddate])
            result = cursor.fetchone()
            success += result[0] or 0
            Failed += result[1] or 0
        
        # Display success and failure messages
        if success > 0:
            messages.success(request, f"Reconciliation done for {success} records.")
        if Failed > 0:
            messages.error(request, f"Reconciliation failed for {Failed} records.")
        
        return render(request, 'Reconcialtion.html')
    
    else:
        messages.error(request, "Please enter the required date range.")
        return render(request, 'Reconcialtion.html')


from django.views.decorators.http import require_GET
from django.http import JsonResponse

@require_GET
def get_account_numbers(request):
    system_id = request.GET.get('system_id')
    system_no = System.objects.get(name=system_id)
    system_main_id=system_no.id
    accounts = BankAccount.objects.filter(system_name_id=system_main_id).values('account_name', 'account_number')
    return JsonResponse({'account_numbers': list(accounts)})