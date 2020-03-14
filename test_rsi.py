from functions_file import *
# https://pypi.org/project/schedule/

def rsi_job():
	# Only when internet is available
	df = coin_data_function('BTC', start=datetime(2017, 1, 1),
									end = datetime.now(), tf='1W')

	# RSI
	df['RSI'] = RSI(df['Close'])

	# To Excel
	name ='BTC data.xlsx'
	df.to_excel(name, index =  False)

def test_rsi():
	excel_file = 'BTC data.xlsx'
	df = pd.read_excel(excel_file)

	# Change at will
	df['Close'].iloc[-1] = 3907

	# RSI
	df['RSI'] = RSI(df['Close'])

	print(df.tail())


rsi_job()
test_rsi()