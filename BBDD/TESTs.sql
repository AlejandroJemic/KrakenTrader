select count (*) from BalanceHistory;
select count (*) from TradesCondensation;

select julianday(max(Time)) - julianday(min(time)) from BalanceHistory; -- 2017-10-11 23:43:07.913669 - 2017-12-02 20:55:55.970539

select count(*) from TradesCondensation; --86288
select max(time) from TradesCondensation; --2017-12-04 16:12:30.066263

select count(*) from BalanceHistory; -- 86287
select max(time) from BalanceHistory; --2017-12-04 16:12:30.066263

select * from BalanceHistory  where time not in (select Time from TradesCondensation);
--delete  from BalanceHistory  where time not in (select Time from TradesCondensation);
--select * from BalanceHistory where time >= '2017-12-18 01:20:45' and Time <= '2017-12-18 01:30:45';

select OpeningTypeID, sum(deltaCH) as suma, count(*) as cantidad from MyTrades  group by OpeningTypeID
select openTime, deltaCH from MyTrades  where OpeningTypeID = 6 order by deltaCH desc;

select bh.* from MyTrades as mt
left outer join BalanceHistory  as bh on (bh.time = mt.openTime);
--delete from MyTrades where id = 47



