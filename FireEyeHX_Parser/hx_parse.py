#!/usr/bin/env python
import tkinter as tk
from tkinter import filedialog
from zipfile import ZipFile
import os
import xml.etree.ElementTree as etree
from neo4j import GraphDatabase, basic_auth
import time

uri = "bolt://localhost"
driver = GraphDatabase.driver(uri, auth=("<username>", "<password>"),encrypted=False)



#Adds the IP addresses to the database
#Ignores IP 127.0.0.1 because that would relate machines that are not actually related
def add_ip(tx, ip):
    if(ip == "127.0.0.1"):
        return
    else:
        tx.run("MERGE (a:IP_Address {ip: $ip}) ",ip=ip)


#Adds a relationship from Network Events
#I removed LocalPort and PID to reduce the number of relationship events created
def add_relation(tx, localip, remoteip, remotePort, localPort, pid, process):
    if(localip == "127.0.0.1" or remoteip == "127.0.0.7"):
        return
    else:
        tx.run("MERGE (a:IP_Address {ip: $localip})"
            "MERGE (b:IP_Address {ip: $remoteip})"
            "MERGE (a)-[:Connects_to {remote_port:$remotePort, process:$process}]->(b)",
            localip=localip, remoteip=remoteip, remotePort=remotePort, process=process)


#Add machine name to the database
def add_machine(tx, machine):
    tx.run("MERGE (a:Machine {machine: $machine}) ", machine=machine)


#Creates a relationship between the Machine and the IPs associated with the machine
#Ignores IP 127.0.0.1 because that would relate machines that are not actually related
def add_ip_to_machine(tx, machine, ip):
    if(ip == "127.0.0.1"):
        return
    else:
        tx.run("MERGE (a:Machine {machine: $machine})"
            "MERGE (b:IP_Address {ip: $ip})"
            "MERGE (a)-[:Has_IP]->(b)",
            machine=machine, ip=ip)




#Adds the machine name and relates it to the IP address
def sysinfoParse(file):
    print("\nUseful commands")
    for event, element in etree.iterparse(file, events=('start','end')):
        if(event == "start" and element.tag == "machine"):
                machine = element.text
                driver.session().write_transaction(add_machine, machine)
                print("MATCH (a:Machine {machine:'"+machine+"'}) RETURN a")
        elif(event == "start" and element.tag == "OS"):
            try:
                os = element.text
            except:
                os = "NA"
        elif(event == "start" and element.tag == "ipAddress"):
                ip = element.text
                driver.session().write_transaction(add_ip, ip)
                driver.session().write_transaction(add_ip_to_machine, machine, ip)
                print("MATCH (a:IP_Address {ip:'"+ip+"'}) RETURN a")



#Parses and inputs IPs into neo4j and creates relationships
def parseNetwork(file):
    count = 0
    for event, element in etree.iterparse(file, events=('start','end')):
        if(event == 'start' and element.tag == 'eventItem'):
            try:
                eventType = element[1].text
            except:
                eventType = None
            if(eventType == 'ipv4NetworkEvent'):
                count +=1
                try:
                    remoteIP = element[2][0][1].text
                except:
                    remoteIP = "NA"
                try:
                    remotePort = element[2][1][1].text
                except:
                    remotePort = "NA"
                try:
                    localIP = element[2][2][1].text
                except:
                    localIP = "NA"
                try:
                    localPort = element[2][3][1].text
                except:
                    localPort = "NA"
                try:
                    pid = element[2][5][1].text
                except:
                    pid = "NA"
                try:
                    process = element[2][6][1].text
                except:
                    process = "NA"

                try:
                    driver.session().write_transaction(add_ip, remoteIP)
                    driver.session().write_transaction(add_ip, localIP)
                    driver.session().write_transaction(add_relation, localIP,remoteIP, remotePort, localPort, pid, process)
                except:
                    continue
        element.clear()




#Check Each file with the MANS file and return the Generator
def checkGenerator(file):
    for event, element in etree.iterparse(file, events=('start','end')):
        if(event == 'start' and element.tag == 'itemList'):
            return element.attrib['generator']
        elif(event == 'start' and element.tag == 'IssueList'):
            return 'Issues List'


#Shows Cypher Query Syntax:
def showSyntax():
    print("Display a specific machine name:")
    print("MATCH (a:Machine {machine:'<hostname>'}) RETURN a")
    print("\n")
    print("Find shortest path between 2 objects")
    print("MATCH (a:Machine {machine:'<machine>'}),(b:IP_Address {ip:'<ip address>'}), p = shortestPath((a)-[*]-(b)) RETURN p")
    print("\n")
    print("Find all connections from an IP address by a specific process")
    print("MATCH p=(a:IP_Address {ip:'<ip address>'})-[:Connects_to {process:'<process name>'}]-() RETURN p")




#Allows users to choose what they would like to do
def userInput():
    choice ='0'
    while choice =='0':
        print("What would you like to do?")
        print("1. Add Network Events to a graph")
        print("2. Add Process Events to a graph - Option Unavailable currently")
        print("3. Show basic Cypher Query syntax")
        print("4. Quit")
        choice = input("Please make a choice (1, 2, 3, 4): ")
        if choice == "4":
            quit()
        elif choice == "3":
            showSyntax()
        elif choice == "2":
            print("Choose the MANS file")
            return 2
        elif choice == "1":
            return 1
        else:
            print("Please select 1,2,3, or 4")



def main():
    root = tk.Tk().withdraw()
    #root.withdraw()
    f = filedialog.askopenfilename()
    userChoice = userInput()
    # Open the MANS (zipped) file
    with ZipFile(f, 'r') as zipObj:
        for name in zipObj.namelist():
            if(not name.endswith(".json") and not name.endswith(".xml")):
                file = zipObj.open(name)
                generator = checkGenerator(file)
                file = zipObj.open(name)
                if(generator == 'stateagentinspector'):
                    if(userChoice == 1):
                        print("Parsing Network Events....Please wait. This may take a few minutes")
                        parseNetwork(file)
                    else:
                        continue
                if(generator == 'sysinfo'):
                    sysinfoParse(file)



start_time = time.time()
main()
print("Completed in --- %s seconds ---" % (time.time() - start_time))
