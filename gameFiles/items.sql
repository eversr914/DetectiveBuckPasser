/**items.sql**/

insert into items values(0, 'Bottle', 'An empty bottle, like the one that biker beat you with last week at the End Zone', 0.1, 1,0);
insert into items values(1, 'Whiskey', 'Old Crow, best bourbon in the $5 price range', 0.5, 1,500);
insert into items values(2, 'Foot in the boot', 'An old foot in a boot', 7, 1,0);
insert into items values(3, 'Cocaine', 'Just enough blow to mess make this a drug squad issue', 0.1, 1, 4000);
insert into items values(4, 'Rent Money', "Wad of greasy $1's", 1, 1,3700);
insert into items values(100, 'Money', 'Not backed by gold',.01,1, 1);

/**inventory**/
insert into inventory values(0, 0, 100);
insert into inventory values(0, 1, 2);
insert into inventory values(0, 100, 1000);
