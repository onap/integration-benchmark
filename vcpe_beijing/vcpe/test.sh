#!/bin/bash
 
#开始时间
begin=$(date +%s)
 
count=$1
rsnum=$2
cishu=$(expr $count / $rsnum)
 
for ((i=0; i<$cishu;))
do
	start_num=$(expr $i \* $rsnum + 1)
	end_num=$(expr $start_num + $rsnum - 1)
	for j in `seq $start_num $end_num`
	do
		./echo.sh $j &
                sleep 0.01
	done
	wait
	i=$(expr $i + 1)
done
 
#结束时间
end=$(date +%s)
spend=$(expr $end - $begin)
echo "花费时间为$spend秒"
