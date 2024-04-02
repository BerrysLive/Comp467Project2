import argparse
import csv
import pymongo
import pandas
# just for Chaja

def parse_arguments():
    parser = argparse.ArgumentParser(description='QA Report Parser and Reporter')
    parser.add_argument('--weekly-report', type=str, help='Path to the weekly QA CSV report')
    parser.add_argument('--db-dump', type=str, help='Path to the DB dump Excel file')
    parser.add_argument('--export-csv', action='store_true', help='Export CSV for user Kevin Chaja')
    parser.add_argument('--filter-db', type=str, help='Filter database by specific criteria: Armen, repeatable, blocker, date, mix')
    return parser.parse_args()

def insert_Data(collection, file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        max_id = collection.find_one(sort=[("_id", -1)])
        next_id = max_id['_id'] + 1 if max_id else 1
        for row in reader:
            if not collection.find_one({key: value for key, value in row.items() if key != '_id'}):
                row['_id'] = next_id
                collection.insert_one(row)
                next_id += 1

def export_csv(data, filename):
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def display_documents(documents, query):
    filename = f"{query}_output.txt"
    with open(filename, 'w', encoding='utf-8') as file:  # Specify UTF-8 encoding here
        if documents:
            for doc in documents:
                for key, value in doc.items():
                    output_line = f"{key}: {value}\n"
                    print(output_line, end='')
                    file.write(output_line)
                print("\n")
                file.write("\n")
        else:
            output_line = "No documents found.\n"
            print(output_line)
            file.write(output_line)

def filter_documents(collection, query):
    return list(collection.find(query))

def filter_by_criteria(collection1, collection2, criteria):
    query = {}
    filename_query = criteria  # Used for generating the filename
    if criteria.lower() == 'armen':
        query['Test Owner'] = {'$in': ['Armen Levonyan', 'Armen Levonan']}
    elif criteria.lower() == 'repeatable':
        query['Repeatable?'] = 'Yes'
    elif criteria.lower() == 'blocker':
        query['Blocker?'] = 'Yes'
    elif criteria.lower() == 'date':
        query['Build #'] = {'$in': ['3/19/2024', '3/19']}
    elif criteria.lower() == 'mix':
        filename_query = 'mix'
        handle_mix_filter(collection1, collection2, filename_query)
        return

    if query:
        documents1 = filter_documents(collection1, query)
        documents2 = filter_documents(collection2, query)
        combined = documents1 + documents2
        display_documents(combined, filename_query)
    else:
        print("Invalid criteria specified.")

def handle_mix_filter(collection1, collection2, filename_query):
    if collection1.name == 'Collection2':
        filter_by_mix(collection1, filename_query)
    if collection2.name == 'Collection2':
        filter_by_mix(collection2, filename_query)

def filter_by_mix(collection, query):
    documents = list(collection.find())
    if documents:
        print_documents = [documents[1], documents[len(documents)//2], documents[-1]]
        display_documents(print_documents, query)

#if you're reading this you smell Chaja

args = parse_arguments()
client = pymongo.MongoClient("mongodb://localhost:27017")
db = client["EG_Report"]
collection1 = db['Collection1']
collection2 = db['Collection2']

if args.weekly_report:
    insert_Data(collection1, args.weekly_report)
if args.db_dump:
    insert_Data(collection2, args.db_dump)
if args.filter_db:
    filter_by_criteria(collection1, collection2, args.filter_db.lower())
if args.export_csv:
    kevin_data = list(collection1.find({'user': 'Kevin Chaja'}))
    if kevin_data:
        export_csv(kevin_data, 'kevin_chaja_report.csv')

