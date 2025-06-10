from MRclass import MeanReversion

# add: 
# - stop loss (if z goes up in 2 ticks, close, z does down in 2 ticks close) 
# - regime identification

mr = MeanReversion(ticker="SPY", window=30, alo=50)
mr.run() 
