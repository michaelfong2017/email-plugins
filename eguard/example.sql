-- SQLite

-- select all table names
SELECT name FROM sqlite_master WHERE type='table';

-- select address from known sender / junk sender demo
select * from 'cs@michaelfong.co_known_sender';
select * from junk_sender;

-- delete address from known sender demo 
delete from 'cs@michaelfong.co_known_sender' where address = 'cs@michaelfong.co';
delete from junk_sender where address = 'cs@michaelfong.co';

-- insert address into known sender demo
insert into 'cs@michaelfong.co_known_sender' values('cs@michaelfong.co');
insert into junk_sender values('cs@michaelfong.co');