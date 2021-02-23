#!/usr/bin/env python
import tkinter as tk
from tkinter import filedialog
import csv
from neo4j import GraphDatabase, basic_auth
import time

uri = "bolt://localhost"
driver = GraphDatabase.driver(uri, auth=("<username>", "<password>"),encrypted=False)


def add_pname(tx, row):
	operation = row[3].replace(" ","_")
	tx.run("MERGE (a:Process {processName: $pname, pid:$pid}) ",pname=row[1], pid=row[2])
	tx.run("MERGE (b:Path {path: $path}) ",path=row[4])
	tx.run("MERGE (a:Process {processName: $pname, pid:$pid})"
		"MERGE (b:Path {path: $path})"
		"MERGE (a)-[:"+operation+" {result:$result, detail:$detail}]->(b)",
		pname=row[1], pid=row[2], path=row[4], result=row[5], detail=row[6])


def main():
	root = tk.Tk().withdraw()
	#root.withdraw()
	f = filedialog.askopenfilename()
	with open(f) as file:
		csv_reader = csv.reader(file, delimiter=',')
		line_count = 0
		for row in csv_reader:
			if line_count == 0:
				print(f'Column names are {", ".join(row)}')
				line_count += 1
			else:
				driver.session().write_transaction(add_pname, row)
				line_count += 1

start_time = time.time()
main()
print("Completed in --- %s seconds ---" % (time.time() - start_time))
