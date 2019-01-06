kill $(ps aux | grep runCtaTrading | awk '{print $2}');
date=`date "+%Y%m%d"`
touch log/trading/eth/$date.log;/root/anaconda2/bin/python -u runCtaTrading.py OKEX_eth.json &>>log/trading/eth/$date.log &
touch log/trading/dy/$date.log;/root/anaconda2/bin/python -u runCtaTrading.py OKEX_dy.json &>>log/trading/dy/$date.log &
