from functions_file import *
# https://pypi.org/project/schedule/
import schedule, warnings, discord, vlc
from statistics import mean
from discord import Webhook, RequestsWebhookAdapter
warnings.simplefilter(action = "ignore", category = RuntimeWarning)

# Webhook settings
url_wb = os.environ.get('DISCORD_WH')
webhook = Webhook.from_url(url_wb, adapter=RequestsWebhookAdapter())

def rsi_job():
	# Only when internet is available
	df = coin_data_function('BTC', start=datetime(2017, 1, 1),
									end = datetime.now(), tf='1W')

	# RSI
	df['RSI'] = RSI(df['Close'])

	# Alarm
	limit = 29
	rsi_value = df['RSI'].iloc[-1]
	btc_close = df['Close'].iloc[-1]
	buy_price = btc_close*0.985
	sl = buy_price*0.90

	if rsi_value < limit:
		webhook.send(file=discord.File('take_my_money.jpeg'))
		webhook.send(f":dollar: BTC price: {btc_close}\n:fire: RSI value: {rsi_value:.2f}\n:money_mouth: Limit order (-1.5%) at {buy_price:.0f}\n:skull_crossbones: Stop loss (10%) at {sl:.0f}\n:dart: Target:   :waning_crescent_moon::dizzy:")
		p = vlc.MediaPlayer("rsi_song.mp3")
		p.play()

	currentDT = datetime.now()
	print (str(currentDT))
	print('BTC Price:', df['Close'].iloc[-1])
	print(f"RSI: {rsi_value:.2f}")
	print('\n')

schedule.every(20).seconds.do(rsi_job)

while True:
	schedule.run_pending()