#!/usr/bin/python

import re
import pysphere

def mor_to_name(host_mor, esx_hosts):
	'''Convert esx host's object id to name.'''
	for mor, name in esx_hosts.iteritems():
		if mor == host_mor:
			return name

def clusters_hosts(vm_hosts):
	'''Create a dict referencing esx hosts with their cluster.'''
	cluster_host = {}
	for host in vm_hosts:
		server = pysphere.VIServer()
		server.connect(host, host_user, host_pass)
		
		clusters = server.get_clusters()
		for c_mor, cluster in clusters.iteritems():
			hosts = server.get_hosts(from_mor=c_mor)
			for h_mor, host in hosts.iteritems():
				cluster_host[host] = cluster
		server.disconnect()

	return cluster_host #{host:cluster}

def datastores(vm_hosts):
	'''Create a dict referencing datastore ids with their name'''
	datastores = {}
	for host in vm_hosts:
		server = pysphere.VIServer()
		server.connect(host, host_user, host_pass)

		all_datastores = server.get_datastores()
		for mor, name in all_datastores.iteritems():
			datastores[mor] = name
		server.disconnect()

	return datastores

def connect(vm_host):
	'''Connect to the esx server and return the session.'''
	server = pysphere.VIServer()
	server.connect(vm_host, host_user, host_pass)
	
	return server

def get_data(props, ds_re, cluster_host, esx_hosts, datastore_names):
	vm_info = {}

	for obj in props:
		vmname = None
		os = None
		ip = None
		nics = None
		disks = None
		datastore = None
		cpu = None
		memory = None
		esx_host = None
		annotation = None
		cluster = None
		disk_datastore = None
	
		for prop in obj.PropSet:
			if prop.Name == 'config.name':
				vmname = prop.Val
			elif prop.Name == 'config.guestFullName':
				os = prop.Val
			elif prop.Name == 'guest.ipAddress':
				ip = prop.Val
			elif prop.Name == 'summary.config.numCpu':
				cpu = prop.Val
			elif prop.Name == 'summary.config.memorySizeMB':
				memory = prop.Val
			elif prop.Name == 'config.annotation':
				annotation = prop.Val
			elif prop.Name == 'summary.config.vmPathName':
				datastore = re.match(ds_re, prop.Val).group('ds')
			elif prop.Name == 'runtime.host':
				host_mor = prop.Val
				esx_host = mor_to_name(host_mor, esx_hosts)
				try:
					cluster = cluster_host[esx_host]
				except:
					cluster = None
				esx_host = esx_host.rstrip('.domain.tld')
			elif prop.Name == 'guest.net':
				nics = []
				for nic in getattr(prop.Val, 'GuestNicInfo',[]):
					nics.append(getattr(nic, '_ipAddress', ''))
			elif prop.Name == 'guest.disk':
				disks = []
				for disk in getattr(prop.Val, 'GuestDiskInfo', []):
					path = getattr(disk, '_diskPath', '')
					capacity = getattr(disk, '_capacity', 0)
					free = getattr(disk, '_freeSpace', 0)
					disks.append((path, capacity, free))
			elif prop.Name == 'storage.perDatastoreUsage':
				disk_datastore = ''
				for datastore in getattr(prop.Val, 'VirtualMachineUsageOnDatastore', []):
					disk_datastore += datastore_names[getattr(datastore, '_datastore', '')] + '; '

		vm_info[obj.Obj] = {'vmname':vmname, 'os':os, 'ip':ip, 'nics':nics, 'disks':disks, 
							'datastore':datastore, 'cpu':cpu, 'memory':memory, 'esx_host':esx_host, 
							'annotation':annotation, 'cluster':cluster, 'disk_datastore':disk_datastore}

	return vm_info

def get_all_data():

	vm_hosts = ['host1.domain.tld', 'host2.domain.tld']
	host_user = 'username'
	host_pass = 'password'
	
	ran_clusters_and_datastores = False

	for vm_host in vm_hosts:
		server = connect(vm_host)
		esx_hosts = server.get_hosts() # dict of esx hosts object id:name
	
		properties = ['config.name', 'config.guestFullName', 'guest.ipAddress', 'guest.net', 'guest.disk', 
				'summary.config.numCpu', 'summary.config.memorySizeMB', 'summary.config.vmPathName', 
				'runtime.host', 'config.annotation', 'storage.perDatastoreUsage']

		props = server._retrieve_properties_traversal(property_names=properties, obj_type='VirtualMachine')

		ds_re = re.compile('\[(?P<ds>.+)\].+\.vmx') # datastore name

		if not ran_clusters_and_datastores:
			cluster_host = clusters_hosts(vm_hosts)
			datastore_names = datastores(vm_hosts)
			ran_clusters_and_datastores = True

		vm_info = get_data(props, ds_re, cluster_host, esx_hosts, datastore_names)
		server.disconnect()
		return vm_info 

