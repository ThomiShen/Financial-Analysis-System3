import akshare as ak

stock_profit_forecast_ths_df = ak.stock_profit_forecast_ths(symbol="600519", indicator="预测年报每股收益")
print(stock_profit_forecast_ths_df)


import akshare as ak

stock_board_concept_name_ths_df = ak.stock_board_concept_name_ths()
print(stock_board_concept_name_ths_df)