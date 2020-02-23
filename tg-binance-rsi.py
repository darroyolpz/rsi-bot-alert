from functions_file import *
import schedule, warnings, logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
warnings.simplefilter(action = "ignore", category = RuntimeWarning)

# Create an environment variable and get the token
TG_TOKEN = os.environ.get('TG_TOKEN_BINANCE_BOT')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

#---------------------------------------------------------------------------#
# Telegram function
def tg_call(update, context):
	# Send a message when the command /start is triggered 
	update.message.reply_text("Hello mate! Let me start checking")

	# Job function
	def job():
		coins = ['BTC', 'ETH', 'BNB', 'LTC']

		for coin in coins:
			# Only when internet is available
			df = coin_data_function(coin, start=datetime(2017, 1, 1),
											end = datetime.now(), tf='1W')

			# Drop the columns we don't need
			cols = ['Volume', 'Number of trades', 'Buy volume']
			df = df.drop(cols, axis=1)
			df['Coin'] = coin

			# RSI
			df['RSI'] = RSI(df['Close'])

			# Buy
			df['Buy'] = 0
			limit = 30
			df.loc[df['RSI'] < limit, 'Buy'] = 1

			# Export to Excel
			name = coin + ' hourly data.xlsx'
			df.to_excel(name, index =  False)

			# Data
			rsi = float(df['RSI'].iloc[-1])
			price = float(df['Close'].iloc[-1])
			buy = df['Buy'].iloc[-1]

			currentDT = datetime.now()
			print (str(currentDT))
			print(coin, 'Price:', price)
			print('RSI:', rsi)
			print('\n')

			# RSI message
			if buy == 1:
				update.message.reply_text(f"RSI Alert on {coin} \nPrice: {price} \nRSI: {rsi:.1f}")

	# Schedule job
	cols = ["00:59", "04:59", "08:59", "12:59", "16:59", "20:59"]

	for col in cols:
		schedule.every().day.at(col).do(job)

	while True:
		schedule.run_pending()

#---------------------------------------------------------------------------#
# Main function
def main():

	# Create the updater
	updater = Updater(TG_TOKEN, use_context=True)

	# Get the dispatcher to register handlers
	dp = updater.dispatcher

	# Start the loop with /start
	dp.add_handler(CommandHandler("start", tg_call))

	# Start the Bot
	updater.start_polling()
	updater.idle() # killall python3.7 to kill the app

#---------------------------------------------------------------------------#
# Start - Check if this file is run directly by python or it is imported
if __name__ == '__main__':
	main()