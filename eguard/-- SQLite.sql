-- SQLite

-- select address from known sender / junk sender demo
select * from known_sender;
select * from junk_sender;

-- delete address from known sender demo 
delete from known_sender where address = 'pc@michaelfong.co';
delete from junk_sender where address = 'pc@michaelfong.co';

-- insert address into known sender demo
insert into known_sender values('pc@michaelfong.co');
insert into junk_sender values('pc@michaelfong.co');