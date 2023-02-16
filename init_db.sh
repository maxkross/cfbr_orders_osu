#!/bin bash

sqlite3 files/cfbrisk.db <<EOF

BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS region (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS territory (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    region INTEGER,
    FOREIGN KEY (region)
        REFERENCES region (id)
);

CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    day INTEGER NOT NULL,
    territory INTEGER NOT NULL,
    tier INTEGER,
    quota INTEGER,
    FOREIGN KEY (territory)
        REFERENCES territory (id)
);
CREATE UNIQUE INDEX plans_for_day_and_territory ON plans (season, day, territory, tier);

CREATE TABLE IF NOT EXISTS enemy_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER,
    day INTEGER,
    team TEXT NOT NULL UNIQUE,
    territory INTEGER NOT NULL,
    FOREIGN KEY (territory)
        REFERENCES territory (id)
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER,
    day INTEGER,
    user TEXT NOT NULL,
    territory INTEGER NOT NULL,
    stars INTEGER,
    accepted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (territory)
        REFERENCES territory (id)
);
CREATE UNIQUE INDEX orders_for_day_and_user ON orders (season, day, user);

CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER,
    day INTEGER,
    user TEXT NOT NULL,
    territory INTEGER,
    stars INTEGER,
    rank INTEGER,
    FOREIGN KEY (territory)
        REFERENCES territory (id)
);
CREATE UNIQUE INDEX offer_user_rank ON offers (season, day, user, rank);

INSERT INTO region VALUES(0,"Unplaced");
INSERT INTO region VALUES(1,"Pacific Northwest");
INSERT INTO region VALUES(2,"Northern Lights");
INSERT INTO region VALUES(3,"Canadian Shield");
INSERT INTO region VALUES(4,"Mid-Atlantic");
INSERT INTO region VALUES(5,"East  Appalachia");
INSERT INTO region VALUES(6,"Rust Belt");
INSERT INTO region VALUES(7,"Great Lakes");
INSERT INTO region VALUES(8,"Corn Belt");
INSERT INTO region VALUES(9,"California");
INSERT INTO region VALUES(10,"Rockies");
INSERT INTO region VALUES(11,"Flint Hills");
INSERT INTO region VALUES(12,"Sun Belt");
INSERT INTO region VALUES(13,"Republic of Texas");
INSERT INTO region VALUES(14,"Mississippi River");
INSERT INTO region VALUES(15,"West Appalachia");
INSERT INTO region VALUES(16,"Carolinas");
INSERT INTO region VALUES(17,"Georgia and Florida Railway");
INSERT INTO region VALUES(18,"Gulf States");
INSERT INTO region VALUES(19,"Mexico");
INSERT INTO region VALUES(20,"Caribbean");
INSERT INTO region VALUES(21,"Midwest");
INSERT INTO region VALUES(22,"Chaos");

INSERT INTO territory VALUES(1,"Colorado Springs",10);
INSERT INTO territory VALUES(2,"Akron",6);
INSERT INTO territory VALUES(3,"Tuscaloosa",18);
INSERT INTO territory VALUES(4,"Boone",16);
INSERT INTO territory VALUES(5,"Tucson",12);
INSERT INTO territory VALUES(6,"Tempe",12);
INSERT INTO territory VALUES(7,"Fayetteville",14);
INSERT INTO territory VALUES(8,"Jonesboro",14);
INSERT INTO territory VALUES(9,"West Point",4);
INSERT INTO territory VALUES(10,"Auburn",18);
INSERT INTO territory VALUES(11,"Muncie",21);
INSERT INTO territory VALUES(12,"Waco",13);
INSERT INTO territory VALUES(13,"Boise",1);
INSERT INTO territory VALUES(14,"Boston",3);
INSERT INTO territory VALUES(15,"Bowling Green",6);
INSERT INTO territory VALUES(16,"Buffalo",4);
INSERT INTO territory VALUES(17,"Provo",10);
INSERT INTO territory VALUES(18,"Berkeley",9);
INSERT INTO territory VALUES(19,"Mount Pleasant",7);
INSERT INTO territory VALUES(20,"Alaska",1);
INSERT INTO territory VALUES(21,"Charlotte",16);
INSERT INTO territory VALUES(22,"Cincinnati",6);
INSERT INTO territory VALUES(23,"Clemson",16);
INSERT INTO territory VALUES(24,"Myrtle Beach",16);
INSERT INTO territory VALUES(25,"Boulder",10);
INSERT INTO territory VALUES(26,"Fort Collins",10);
INSERT INTO territory VALUES(27,"Connecticut",3);
INSERT INTO territory VALUES(28,"Durham",16);
INSERT INTO territory VALUES(29,"Greenville",16);
INSERT INTO territory VALUES(30,"Ypsilanti",7);
INSERT INTO territory VALUES(31,"Gainesville",17);
INSERT INTO territory VALUES(32,"Boca Raton",17);
INSERT INTO territory VALUES(33,"University Park",17);
INSERT INTO territory VALUES(34,"Tallahassee",18);
INSERT INTO territory VALUES(35,"Fresno",9);
INSERT INTO territory VALUES(36,"Athens",17);
INSERT INTO territory VALUES(37,"Statesboro",17);
INSERT INTO territory VALUES(38,"South Atlanta",17);
INSERT INTO territory VALUES(39,"North Atlanta",17);
INSERT INTO territory VALUES(40,"Hawai'i",9);
INSERT INTO territory VALUES(41,"East Houston",13);
INSERT INTO territory VALUES(42,"Champaign",21);
INSERT INTO territory VALUES(43,"Bloomington",21);
INSERT INTO territory VALUES(44,"Iowa City",8);
INSERT INTO territory VALUES(45,"Ames",8);
INSERT INTO territory VALUES(46,"Lawrence",11);
INSERT INTO territory VALUES(47,"Manhattan",11);
INSERT INTO territory VALUES(48,"Cleveland",6);
INSERT INTO territory VALUES(49,"Lexington",15);
INSERT INTO territory VALUES(50,"Lynchburg",5);
INSERT INTO territory VALUES(51,"Lafayette",14);
INSERT INTO territory VALUES(52,"Monroe",14);
INSERT INTO territory VALUES(53,"Ruston",14);
INSERT INTO territory VALUES(54,"Louisville",15);
INSERT INTO territory VALUES(55,"Baton Rouge",14);
INSERT INTO territory VALUES(56,"Huntington",5);
INSERT INTO territory VALUES(57,"College Park",5);
INSERT INTO territory VALUES(58,"Memphis",15);
INSERT INTO territory VALUES(59,"Miami",17);
INSERT INTO territory VALUES(60,"Miami Valley",6);
INSERT INTO territory VALUES(61,"Ann Arbor",7);
INSERT INTO territory VALUES(62,"Lansing",7);
INSERT INTO territory VALUES(63,"Murfreesboro",15);
INSERT INTO territory VALUES(64,"Minnesota",8);
INSERT INTO territory VALUES(65,"Starkville",18);
INSERT INTO territory VALUES(66,"Missouri",11);
INSERT INTO territory VALUES(67,"Annapolis",4);
INSERT INTO territory VALUES(68,"Raleigh",16);
INSERT INTO territory VALUES(69,"Nebraska",8);
INSERT INTO territory VALUES(70,"Reno",10);
INSERT INTO territory VALUES(71,"Albuquerque",12);
INSERT INTO territory VALUES(72,"Las Cruces",12);
INSERT INTO territory VALUES(73,"Chapel Hill",16);
INSERT INTO territory VALUES(74,"DeKalb",21);
INSERT INTO territory VALUES(75,"Denton",13);
INSERT INTO territory VALUES(76,"Chicago",21);
INSERT INTO territory VALUES(77,"South Bend",21);
INSERT INTO territory VALUES(78,"Hocking Hills",6);
INSERT INTO territory VALUES(79,"Columbus",6);
INSERT INTO territory VALUES(80,"Norman",11);
INSERT INTO territory VALUES(81,"Stillwater",11);
INSERT INTO territory VALUES(82,"Norfolk",5);
INSERT INTO territory VALUES(83,"Oxford",18);
INSERT INTO territory VALUES(84,"Eugene",1);
INSERT INTO territory VALUES(85,"Corvallis",1);
INSERT INTO territory VALUES(86,"Happy Valley",4);
INSERT INTO territory VALUES(87,"Pittsburgh",4);
INSERT INTO territory VALUES(88,"West Lafayette",21);
INSERT INTO territory VALUES(89,"West Houston",13);
INSERT INTO territory VALUES(90,"New Jersey",4);
INSERT INTO territory VALUES(91,"San Diego",9);
INSERT INTO territory VALUES(92,"San Jose",9);
INSERT INTO territory VALUES(93,"Dallas",13);
INSERT INTO territory VALUES(94,"Mobile",18);
INSERT INTO territory VALUES(95,"Columbia",16);
INSERT INTO territory VALUES(96,"Hattiesburg",18);
INSERT INTO territory VALUES(97,"Tampa",17);
INSERT INTO territory VALUES(98,"Redwood",9);
INSERT INTO territory VALUES(99,"Syracuse",4);
INSERT INTO territory VALUES(100,"Fort Worth",13);
INSERT INTO territory VALUES(101,"Philadelphia",4);
INSERT INTO territory VALUES(102,"Knoxville",15);
INSERT INTO territory VALUES(103,"Austin",13);
INSERT INTO territory VALUES(104,"College Station",13);
INSERT INTO territory VALUES(105,"San Marcos",13);
INSERT INTO territory VALUES(106,"Lubbock",12);
INSERT INTO territory VALUES(107,"Toledo",6);
INSERT INTO territory VALUES(108,"Troy",18);
INSERT INTO territory VALUES(109,"New Orleans",14);
INSERT INTO territory VALUES(110,"Tulsa",11);
INSERT INTO territory VALUES(111,"Birmingham",18);
INSERT INTO territory VALUES(112,"Orlando",17);
INSERT INTO territory VALUES(113,"North Los Angeles",9);
INSERT INTO territory VALUES(114,"Amherst",3);
INSERT INTO territory VALUES(115,"Las Vegas",10);
INSERT INTO territory VALUES(116,"South Los Angeles",9);
INSERT INTO territory VALUES(117,"Salt Lake City",10);
INSERT INTO territory VALUES(118,"Logan",10);
INSERT INTO territory VALUES(119,"El Paso",12);
INSERT INTO territory VALUES(120,"San Antonio",13);
INSERT INTO territory VALUES(121,"Nashville",15);
INSERT INTO territory VALUES(122,"Charlottesville",5);
INSERT INTO territory VALUES(123,"Blacksburg",5);
INSERT INTO territory VALUES(124,"Winston-Salem",16);
INSERT INTO territory VALUES(125,"Seattle",1);
INSERT INTO territory VALUES(126,"Pullman",1);
INSERT INTO territory VALUES(127,"Western Kentucky",15);
INSERT INTO territory VALUES(128,"Kalamazoo",7);
INSERT INTO territory VALUES(129,"Morgantown",5);
INSERT INTO territory VALUES(130,"Wisconsin",7);
INSERT INTO territory VALUES(131,"Wyoming",8);
INSERT INTO territory VALUES(133,"Pampa",12);
INSERT INTO territory VALUES(134,"Manitoba",2);
INSERT INTO territory VALUES(135,"Saskatchewan",2);
INSERT INTO territory VALUES(136,"Alberta",2);
INSERT INTO territory VALUES(137,"British Columbia",1);
INSERT INTO territory VALUES(138,"Nunavut",2);
INSERT INTO territory VALUES(139,"Northwest Territories",2);
INSERT INTO territory VALUES(140,"Yukon",1);
INSERT INTO territory VALUES(141,"Thunder Bay",2);
INSERT INTO territory VALUES(143,"New Brunswick",3);
INSERT INTO territory VALUES(144,"Nova Scotia",3);
INSERT INTO territory VALUES(145,"Newfoundland",3);
INSERT INTO territory VALUES(146,"Prince Edward Island",3);
INSERT INTO territory VALUES(148,"Tabasco",20);
INSERT INTO territory VALUES(150,"Veracruz",19);
INSERT INTO territory VALUES(151,"Puebla",19);
INSERT INTO territory VALUES(156,"México",19);
INSERT INTO territory VALUES(158,"Baja California",9);
INSERT INTO territory VALUES(160,"Chihuahua",19);
INSERT INTO territory VALUES(162,"Tamaulipas",19);
INSERT INTO territory VALUES(163,"Nuevo León",19);
INSERT INTO territory VALUES(164,"Sinaloa",19);
INSERT INTO territory VALUES(166,"Jalisco",19);
INSERT INTO territory VALUES(167,"Belize",20);
INSERT INTO territory VALUES(170,"Zacatecas",19);
INSERT INTO territory VALUES(174,"Guerrero",19);
INSERT INTO territory VALUES(176,"Quintana Roo",20);
INSERT INTO territory VALUES(177,"Yucatán",20);
INSERT INTO territory VALUES(178,"Bahamas",20);
INSERT INTO territory VALUES(179,"Dominican Republic",20);
INSERT INTO territory VALUES(180,"Haiti",20);
INSERT INTO territory VALUES(181,"Puerto Rico",20);
INSERT INTO territory VALUES(182,"Cuba",20);
INSERT INTO territory VALUES(183,"Jamaica",20);
INSERT INTO territory VALUES(184,"Chiapas",20);
INSERT INTO territory VALUES(185,"Oaxaca",19);
INSERT INTO territory VALUES(186,"Bermuda",22);
INSERT INTO territory VALUES(187,"Guatemala",20);
INSERT INTO territory VALUES(188,"Springfield",11);
INSERT INTO territory VALUES(189,"Texarkana",14);
INSERT INTO territory VALUES(190,"Cariboo",1);
INSERT INTO territory VALUES(191,"Fort Mcmurray",2);
INSERT INTO territory VALUES(192,"Regina",2);
INSERT INTO territory VALUES(193,"Winnipeg",2);
INSERT INTO territory VALUES(194,"Moose River",2);
INSERT INTO territory VALUES(195,"Cote Nord",3);
INSERT INTO territory VALUES(196,"Toronto",7);
INSERT INTO territory VALUES(197,"Sault Ste Marie",7);
INSERT INTO territory VALUES(198,"Labrador",3);
INSERT INTO territory VALUES(199,"Sherbrooke",3);
INSERT INTO territory VALUES(200,"Montreal",3);
INSERT INTO territory VALUES(201,"Montana",8);
INSERT INTO territory VALUES(202,"Dakotas",8);
INSERT INTO territory VALUES(203,"Vancouver",1);
INSERT INTO territory VALUES(204,"Palo Alto",9);

COMMIT;

EOF