import argparse
import csv
import pymongo
import pandas  # just for Chaja

def parse_arguments():
    parser = argparse.ArgumentParser(description='QA Report Parser and Reporter')
    parser.add_argument('--weekly-report', type=str, help='Path to the weekly QA CSV report')
    parser.add_argument('--db-dump', type=str, help='Path to the DB dump Excel file')
    parser.add_argument('--export-csv', action='store_true', help='Export CSV for user Kevin Chaja')
    parser.add_argument('--filter-db', type=str, help='Filter database by specific criteria: Armen, repeatable, blocker, date, mix')
    return parser.parse_args()

# Insert data into MongoDB without checking for duplicates
def insert_Data(collection, file_path):
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        # Find the document with the highest _id to ensure uniqueness and increment from there
        last_doc = collection.find_one(sort=[("_id", pymongo.DESCENDING)])
        next_id = last_doc['_id'] + 1 if last_doc else 1
        for row in reader:
            row['_id'] = next_id
            collection.insert_one(row)
            next_id += 1


def export_csv(data, filename):
    try:
        with open(filename, mode='w', newline='', encoding='utf-8-sig') as file:  # Note the encoding here
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        print(f"Exported data to {filename}")
    except Exception as e:
        print(f"Failed to export data to {filename}: {e}")

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
    filename_query = criteria
    if criteria.lower() == 'armen':
        query['Test Owner'] = {'$regex': 'Armen Levon(an|yan)', '$options': 'i'}
    elif criteria.lower() == 'repeatable':
        query['Repeatable?'] = 'Yes'
    elif criteria.lower() == 'blocker':
        query['Blocker?'] = 'Yes'
    elif criteria.lower() == 'date':
        query['Build #'] = {'$in': ['3/19/2024', '3/19']}
    elif criteria.lower() == 'mix':
        handle_mix_filter(collection1, collection2, criteria)
        return

    if query:
        documents1 = filter_documents(collection1, query)
        documents2 = filter_documents(collection2, query)
        display_documents(documents1 + documents2, filename_query)
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
    kevin_data = list(collection2.find({'Test Owner': 'Kevin Chaja'}))
    print(f"Kevin Chaja data: {kevin_data}")  # This will show the data being fetched
    if kevin_data:
        export_csv(kevin_data, 'kevin_chaja_report.csv')
    else:
        print("No data found for Kevin Chaja.")

