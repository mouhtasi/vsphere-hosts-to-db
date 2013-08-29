DROP TABLE IF EXISTS vm_host;

CREATE TABLE vm_host (
	vm varchar(50) NOT NULL,
	esx_host varchar(50) NOT NULL,
	ip varchar(30),
	vmcluster varchar(50),
	annotation varchar(255),
	nics varchar(255),
	disks varchar(255),
	datastore varchar(50),
	memory smallint unsigned,
	os varchar(50),
	cpu smallint unsigned,
	disk_datastore varchar(100)
);
