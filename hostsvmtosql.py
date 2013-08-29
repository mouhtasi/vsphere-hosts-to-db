#!/usr/bin/python

import re
import pyodbc
import vsphere_fast
import pprint

def connect_db(server, database, username, password):
	'''Connect to the mysql db and return a cursor'''
	connection = pyodbc.connect('DRIVER={MySQL};SERVER=%s;DATABASE=%s;USER=%s;PASSWORD=%s'
								%(server, database, username, password))
	return connection, connection.cursor()

def data_into_db(cursor, data):
	for thing in data.values():
		vm = thing['vmname']
		annotation = thing['annotation']
		vmcluster = thing['cluster']
		cpu = thing['cpu']
		datastore = thing['datastore']
		disks = return_string_disks(thing['disks'])
		esx_host = thing['esx_host']
		ip = thing['ip']
		memory = thing['memory']
		nics = return_string_nics(thing['nics'])
		os = thing['os']
		disk_datastore = thing['disk_datastore']

		action = check_if_exists(cursor, vm)

		if action == 'insert':
			sql = "INSERT INTO vm_host(vm, esx_host, ip, vmcluster, annotation, nics, disks, datastore, memory, os, cpu, disk_datastore) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)" 
			cursor.execute(sql, vm, esx_host, ip, vmcluster, annotation, nics, disks, datastore, memory, os, cpu, disk_datastore)

		elif action == 'update':
		# delete vm then insert vm with new data
			cursor.execute("DELETE FROM vm_host WHERE vm='%s'" % vm)
			sql = "INSERT INTO vm_host(vm, esx_host, ip, vmcluster, annotation, nics, disks, datastore, memory, os, cpu, disk_datastore) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)" 
			cursor.execute(sql, vm, esx_host, ip, vmcluster, annotation, nics, disks, datastore, memory, os, cpu, disk_datastore)
	
def check_if_exists(cursor, vm):
	'''Check if the vm exists in the db already and return whether it should be inserted
		or updated'''
	cursor.execute("SELECT * FROM vm_host WHERE vm='%s'" % vm)
	if cursor.fetchone():
		action = 'update'
	else:
		action = 'insert'

	return action

def return_string_nics(nics):
	ips = ''
	for nic in nics:
		for ip in nic:
			if re.match(ipv4_re, ip):
				ips += ip + '; ' # '0.0.0.0;1.1.1.1'
	return ips

def return_string_disks(disks):
	line = ''
	for disk in disks:
		path, capacity, free = disk
		line += path + ': ' + str(decimal_or_whole(free/1024.0/1024/1024))
		line += 'GB of ' + str(decimal_or_whole(capacity/1024.0/1024/1024))
		line += 'GB free; '
	return line

def decimal_or_whole(num):
	if num < 1:
		rnum = round(num, 3)
	else:
		rnum = int(num)
	return rnum

if __name__ == '__main__':

	ipv4_re = re.compile('[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')

	### db info
	server = 'localhost'
	database = 'test'
	username = 'root'
	password = 'password'

	connection, cursor = connect_db(server, database, username, password)
	data = vsphere_fast.get_all_data()
	data_into_db(cursor, data)
	connection.commit()
