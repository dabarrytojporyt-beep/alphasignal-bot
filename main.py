"""
AlphaSignal Discord Bot
- Auto scans 500+ stocks every 2 hours
- MACD BUY: line ABOVE signal on Daily + Weekly + Monthly
- MACD SHORT: line BELOW signal on all 3 timeframes
- Real-time prices
- Full server setup with !setup
- Ticket system for payments
- Private channels per member
- 24/7 via Flask keepalive
"""

import discord
from discord.ext import commands, tasks
import yfinance as yf
import pandas as pd
import numpy as np
import asyncio
import os
import datetime
from threading import Thread
from flask import Flask

# ── KEEP ALIVE ────────────────────────────────────────
app = Flask('')
@app.route('/')
def home():
    return "AlphaSignal alive!"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()

# ── CONFIG ────────────────────────────────────────────
TOKEN = os.environ.get('DISCORD_TOKEN', '')
CHANNEL_ID = int(os.environ.get('DISCORD_CHANNEL_ID', '0'))

# ── TICKERS ───────────────────────────────────────────
TICKERS = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B","JPM","V",
    "UNH","XOM","JNJ","WMT","MA","PG","HD","CVX","MRK","ABBV",
    "PEP","KO","BAC","COST","AVGO","TMO","MCD","NFLX","CRM","LIN",
    "ACN","AMD","TXN","DHR","NEE","ADBE","ORCL","PM","SCHW","AMGN",
    "INTC","QCOM","IBM","GE","BA","CAT","HON","GS","MS","BLK",
    "SBUX","NKE","DIS","PYPL","ISRG","MDT","GILD","MMC","PLD","SPGI",
    "LOW","ELV","SYK","CB","ZTS","NOW","ADP","MDLZ","REGN","BKNG",
    "MO","SO","DUK","BMY","INTU","PNC","USB","TGT","CI","APD",
    "ITW","DE","GD","RTX","LMT","NOC","ETN","EMR","MMM","SHW",
    "ECL","ROP","FDX","UPS","CSX","NSC","UNP","CARR","OTIS","TT",
    "CTAS","FAST","PAYX","AJG","AON","MET","PRU","AFL","ALL","TRV",
    "WFC","C","FITB","KEY","RF","MTB","CFG","HBAN","ZION","CMA",
    "F","GM","STLA","TM","HMC","RIVN","LCID","NIO","LI","XPEV",
    "SNAP","PINS","TWTR","RBLX","U","DKNG","PENN","MGM","LVS","WYNN",
    "MAR","HLT","IHG","H","RCL","CCL","NCLH","AAL","DAL","UAL",
    "LUV","ALK","JBLU","BA","SPR","HWM","TDG","AXON","TRMB","GNRC",
    "ENPH","FSLR","SEDG","RUN","PLUG","BLDP","NKLA","HYLN","FSR","RIDE",
    "COIN","MSTR","RIOT","MARA","HUT","BITF","CLSK","IREN","WULF","BTBT",
    "SQ","AFRM","UPST","SOFI","LC","OPEN","OPENDOOR","HOOD","CLOV","ROOT",
    "ROKU","TTD","MGNI","IAS","DV","PUBM","APPS","RAMP","CRTO","ZETA",
    "SHOP","WIX","BIGC","GLOB","MELI","SE","GRAB","GOJEK","CPNG","BABA",
    "JD","PDD","BIDU","NTES","TCEHY","TME","BILI","IQ","DOYU","HUYA",
    "TSM","ASML","AMAT","LRCX","KLAC","MCHP","SWKS","QRVO","MPWR","ENTG",
    "ONTO","ACLS","FORM","ICHR","CCMP","UCTT","MKSI","BRKS","CAMT","COHU",
    "SMCI","PSTG","NTAP","STX","WDC","SEAGATE","NTNX","PEGA","HUBS","DDOG",
    "NET","CFLT","MDB","ESTC","SPLK","SUMO","NCNO","ALRM","QLYS","TENB",
    "CYBR","S","CRWD","ZS","OKTA","PING","SAIL","VRNT","OSPN","SCWX",
    "PANW","FTNT","CHKP","SAIC","LDOS","BAH","CACI","MAXR","HII","KTOS",
    "PLTR","BBAI","GFAI","SOUN","AITX","BFLY","OUST","LIDR","AEVA","MVIS",
    "LAZR","VLDR","INVZ","INDI","MBLY","PLUS","AI","BIGBEAR","IDAI","MCLD",
    "TWLO","ZM","DOCU","BOX","DOMO","ALTR","ATVI","EA","TTWO","ZNGA",
    "GLUU","PLTK","SKLZ","MTCH","BMBL","GRND","BUMBLE","HIMS","SMAR","APPF",
    "PCTY","PAYC","WK","VEEV","CDAY","NCR","WEX","FLYW","PAY","REPAY",
    "EVTC","PAYA","PRTH","SKYW","RPAY","FOUR","LSPD","TOST","PAR","BRSH",
    "MKTX","VIRT","HOOD","SCHW","IBKR","LPLA","RJF","SF","PIPR","MC",
    "LAZ","EVR","PJT","MOELIS","HLNE","STEP","BLUE","EDIT","CRSP","NTLA",
    "BEAM","VERVE","PRME","GRPH","ARCT","MRNA","BNTX","NVAX","SGEN","EXAS",
    "NTRA","ILMN","PACB","ONEM","ACAD","SAGE","INVA","PRGO","ENDP","MNK",
    "AGN","JAZZ","HZNP","ALNY","IONS","RARE","FOLD","FGEN","BMRN","SRPT",
    "ARWR","MDGL","AKRO","VKTX","RPRX","VCNX","RAPT","IMVT","JANUX","KYMR",
    "DVAX","HOOK","BCDA","PRCT","ATRS","TVTX","TGTX","RVMD","KRTX","ERAS",
    "XOM","CVX","COP","EOG","PXD","DVN","HES","MRO","APA","OXY",
    "PSX","VLO","MPC","DK","PARR","CLMT","CAPL","PBFX","CVRR","ALDW",
    "HAL","SLB","BKR","FTI","NOV","HP","LBRT","ACDC","NINE","WTTR",
    "NEE","AES","D","DUK","EXC","SRE","PCG","ED","ES","EIX",
    "AWK","WTRG","YORW","MSEX","ARTNA","GWRS","SJW","CTWS","CCWC","ARIS",
    "O","NNN","WPC","STAG","VICI","GLPI","GAMING","MPW","SBAC","CCI",
    "AMT","EQIX","DLR","IRM","CONE","QTS","COR","REXR","COLD","PSA",
    "EXR","CUBE","LSI","NSA","SSS","JYNT","SELF","STOR","FCPT","GTY",
    "SPG","MAC","SKT","CBL","WPG","PEI","ALX","SL","ROIC","KITE",
    "VNO","SLG","BXP","KRC","HPP","DEA","OFC","COPT","ESRT","CLNC",
    "AMH","INVH","NVR","PHM","DHI","LEN","MDC","MHO","TMHC","TOL",
    "KBH","BZH","LGIH","SKY","CVCO","UCP","GRBK","SMITH","JELD","PGTI",
    "AWI","USG","DOOR","FBHS","MAS","TREX","AZEK","FTDR","BECN","BLDR",
    "SUM","MLM","VMC","CRH","EXP","GMS","IBP","DFIN","UFP","UFPI",
]

# ── BOT SETUP ─────────────────────────────────────────
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

scan_results = []
last_scan_time = None
total_signals_sent = 0
all_time_buys = 0
all_time_shorts = 0

# ── MACD CALCULATION ──────────────────────────────────
def calc_macd(closes):
    if len(closes) < 35:
        return None
    s = pd.Series(closes)
    ema12 = s.ewm(span=12, adjust=False).mean()
    ema26 = s.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    # Check last 3 candles for crossover
    for i in range(-1, -4, -1):
        if macd.iloc[i] > signal.iloc[i]:
            return "BUY"
        elif macd.iloc[i] < signal.iloc[i]:
            return "SHORT"
    return "HOLD"

def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return 50
    s = pd.Series(closes)
    delta = s.diff()
    gain = delta.where(delta > 0, 0).ewm(com=period-1, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(com=period-1, adjust=False).mean()
    rs = gain / (loss + 1e-9)
    return float(100 - (100 / (1 + rs.iloc[-1])))

def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        # Real-time price
        info = stock.fast_info
        price = info.last_price
        if not price or price <= 0:
            return None

        # Daily data
        d = stock.history(interval='1d', period='1y')
        if len(d) < 35:
            return None
        d_signal = calc_macd(d['Close'].tolist())

        # Weekly data
        w = stock.history(interval='1wk', period='3y')
        if len(w) < 35:
            return None
        w_signal = calc_macd(w['Close'].tolist())

        # Monthly data
        m = stock.history(interval='1mo', period='10y')
        if len(m) < 35:
            return None
        m_signal = calc_macd(m['Close'].tolist())

        # RSI
        rsi = calc_rsi(d['Close'].tolist())

        # Volume
        avg_vol = d['Volume'].tail(20).mean()
        cur_vol = d['Volume'].iloc[-1]
        vol_ratio = cur_vol / avg_vol if avg_vol > 0 else 1

        # All 3 must agree
        if d_signal == "BUY" and w_signal == "BUY" and m_signal == "BUY":
            if rsi < 70:  # not overbought
                signal = "STRONG BUY"
            else:
                signal = "BUY"
        elif d_signal == "SHORT" and w_signal == "SHORT" and m_signal == "SHORT":
            if rsi > 30:  # not oversold
                signal = "STRONG SHORT"
            else:
                signal = "SHORT"
        else:
            return None  # No signal

        return {
            'ticker': ticker,
            'signal': signal,
            'price': price,
            'rsi': rsi,
            'vol_ratio': vol_ratio,
            'd_signal': d_signal,
            'w_signal': w_signal,
            'm_signal': m_signal,
        }
    except Exception:
        return None

# ── CHANNEL HELPERS ───────────────────────────────────
def find_channel(guild, name):
    name_clean = name.replace('・', '').replace('📡', '').replace('🏆', '').replace('📈', '').replace('🆓', '').strip()
    for ch in guild.channels:
        ch_clean = ch.name.replace('・', '').replace('📡', '').replace('🏆', '').replace('📈', '').replace('🆓', '').strip()
        if name_clean.lower() in ch_clean.lower():
            return ch
    return None

def is_command_channel(channel):
    allowed = ['commands', 'analysis-', 'ticket-', 'admin-commands', 'bot-commands']
    return any(a in channel.name.lower() for a in allowed)

# ── SIGNAL EMBED ──────────────────────────────────────
def make_signal_embed(result):
    is_buy = 'BUY' in result['signal']
    color = discord.Color.green() if is_buy else discord.Color.red()
    emoji = '🟢' if is_buy else '🔴'
    embed = discord.Embed(
        title=f"{emoji} {result['signal']} — {result['ticker']}",
        color=color,
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="💰 Price", value=f"${result['price']:.2f}", inline=True)
    embed.add_field(name="📊 RSI", value=f"{result['rsi']:.1f}", inline=True)
    embed.add_field(name="📦 Volume", value=f"{result['vol_ratio']:.1f}x avg", inline=True)
    embed.add_field(name="📅 Daily MACD", value=f"{'✅ BUY' if result['d_signal']=='BUY' else '🔴 SHORT' if result['d_signal']=='SHORT' else '⚪ HOLD'}", inline=True)
    embed.add_field(name="📅 Weekly MACD", value=f"{'✅ BUY' if result['w_signal']=='BUY' else '🔴 SHORT' if result['w_signal']=='SHORT' else '⚪ HOLD'}", inline=True)
    embed.add_field(name="📅 Monthly MACD", value=f"{'✅ BUY' if result['m_signal']=='BUY' else '🔴 SHORT' if result['m_signal']=='SHORT' else '⚪ HOLD'}", inline=True)
    embed.set_footer(text="AlphaSignal Pro — Not financial advice")
    return embed

# ── AUTO SCAN TASK ────────────────────────────────────
@tasks.loop(hours=2)
async def auto_scan():
    global scan_results, last_scan_time, total_signals_sent, all_time_buys, all_time_shorts
    guild = discord.utils.find(lambda g: True, bot.guilds)
    if not guild:
        return

    signal_ch = find_channel(guild, 'signal-feed')
    free_ch = find_channel(guild, 'free-signals')
    summary_ch = find_channel(guild, 'scan-summaries')

    buys, shorts, results = [], [], []
    print(f"[AlphaSignal] Starting scan of {len(TICKERS)} tickers...")

    for i, ticker in enumerate(TICKERS):
        if i % 50 == 0:
            print(f"[AlphaSignal] Scanning {i}/{len(TICKERS)}...")
            await asyncio.sleep(0)
        result = await asyncio.get_event_loop().run_in_executor(None, get_stock_data, ticker)
        if result:
            results.append(result)
            if 'BUY' in result['signal']:
                buys.append(result)
                all_time_buys += 1
            else:
                shorts.append(result)
                all_time_shorts += 1

    scan_results = results
    last_scan_time = datetime.datetime.utcnow()
    total_signals_sent += len(results)

    # Post signals to premium channel
    if signal_ch:
        for r in results:
            embed = make_signal_embed(r)
            await signal_ch.send(embed=embed)
            await asyncio.sleep(0.5)

    # Post 2 best to free channel
    if free_ch and results:
        await free_ch.send(f"📊 **Free Signal Preview** — {len(results)} signals found this scan. Showing 2:")
        for r in results[:2]:
            embed = make_signal_embed(r)
            await free_ch.send(embed=embed)

    # Post summary
    if summary_ch:
        embed = discord.Embed(
            title="📈 Scan Summary",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="✅ Total Scanned", value=str(len(TICKERS)), inline=True)
        embed.add_field(name="🟢 BUY Signals", value=str(len(buys)), inline=True)
        embed.add_field(name="🔴 SHORT Signals", value=str(len(shorts)), inline=True)
        if buys:
            top = ', '.join([f"**{r['ticker']}**" for r in buys[:5]])
            embed.add_field(name="🏆 Top Buys", value=top, inline=False)
        if shorts:
            top = ', '.join([f"**{r['ticker']}**" for r in shorts[:5]])
            embed.add_field(name="📉 Top Shorts", value=top, inline=False)
        embed.set_footer(text="AlphaSignal Pro — Not financial advice")
        await summary_ch.send(embed=embed)

    print(f"[AlphaSignal] Scan done. {len(buys)} buys, {len(shorts)} shorts.")

# ── COMMANDS ──────────────────────────────────────────
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if not is_command_channel(message.channel):
        if message.content.startswith('!'):
            return  # silently ignore commands outside command channels
    await bot.process_commands(message)

@bot.command(name='help')
async def cmd_help(ctx):
    premium = discord.utils.get(ctx.guild.roles, name="Premium")
    is_premium = premium in ctx.author.roles if premium else False
    embed = discord.Embed(title="📡 AlphaSignal Commands", color=discord.Color.blue())
    embed.add_field(name="🆓 Free Commands", value="""
`!help` — Show this menu
`!stock AAPL` — Analyze any stock
`!market` — Overall market sentiment
`!ping` — Bot latency
`!price` — Premium pricing
`!schedule` — Next scan time
""", inline=False)
    if is_premium:
        embed.add_field(name="💎 Premium Commands", value="""
`!scan` — Run full scan now
`!scan TSLA` — Scan one ticker
`!top` — Top 10 signals from last scan
`!top buys` — Top buys only
`!top shorts` — Top shorts only
`!status` — Bot status
`!stats` — All-time statistics
`!compare TSLA AAPL` — Compare two stocks
`!watchlist add TSLA` — Add to watchlist
`!watchlist show` — Show your watchlist
""", inline=False)
    embed.set_footer(text="AlphaSignal Pro — Not financial advice")
    await ctx.send(embed=embed)

@bot.command(name='scan')
@commands.has_role('Premium')
async def cmd_scan(ctx, ticker=None):
    if ticker:
        msg = await ctx.send(f"🔍 Scanning **{ticker.upper()}**...")
        result = await asyncio.get_event_loop().run_in_executor(None, get_stock_data, ticker.upper())
        if result:
            embed = make_signal_embed(result)
            await msg.edit(content="", embed=embed)
        else:
            await msg.edit(content=f"⚪ No signal for **{ticker.upper()}** — MACD timeframes don't all agree.")
    else:
        msg = await ctx.send(f"⚡ Starting full scan of {len(TICKERS)} stocks...")
        await auto_scan()
        await msg.edit(content=f"✅ Scan complete! Check **signal-feed** for results.")

@bot.command(name='stock')
async def cmd_stock(ctx, ticker=None):
    if not ticker:
        await ctx.send("Usage: `!stock AAPL`")
        return
    msg = await ctx.send(f"🔍 Analyzing **{ticker.upper()}**...")
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.fast_info
        price = info.last_price
        d = stock.history(interval='1d', period='1y')
        w = stock.history(interval='1wk', period='3y')
        m = stock.history(interval='1mo', period='10y')
        d_sig = calc_macd(d['Close'].tolist()) if len(d) >= 35 else 'N/A'
        w_sig = calc_macd(w['Close'].tolist()) if len(w) >= 35 else 'N/A'
        m_sig = calc_macd(m['Close'].tolist()) if len(m) >= 35 else 'N/A'
        rsi = calc_rsi(d['Close'].tolist()) if len(d) >= 15 else 50

        def sig_emoji(s):
            return '✅' if s == 'BUY' else '🔴' if s == 'SHORT' else '⚪'

        if d_sig == 'BUY' and w_sig == 'BUY' and m_sig == 'BUY':
            overall = '🟢 STRONG BUY'
            color = discord.Color.green()
        elif d_sig == 'SHORT' and w_sig == 'SHORT' and m_sig == 'SHORT':
            overall = '🔴 STRONG SHORT'
            color = discord.Color.red()
        else:
            overall = '⚪ MIXED / HOLD'
            color = discord.Color.greyple()

        embed = discord.Embed(title=f"📊 {ticker.upper()} Analysis", color=color)
        embed.add_field(name="💰 Price", value=f"${price:.2f}" if price else "N/A", inline=True)
        embed.add_field(name="📊 RSI", value=f"{rsi:.1f}", inline=True)
        embed.add_field(name="🎯 Signal", value=overall, inline=True)
        embed.add_field(name=f"{sig_emoji(d_sig)} Daily MACD", value=d_sig, inline=True)
        embed.add_field(name=f"{sig_emoji(w_sig)} Weekly MACD", value=w_sig, inline=True)
        embed.add_field(name=f"{sig_emoji(m_sig)} Monthly MACD", value=m_sig, inline=True)
        embed.set_footer(text="AlphaSignal Pro — Not financial advice")
        await msg.edit(content="", embed=embed)
    except Exception as e:
        await msg.edit(content=f"❌ Error fetching {ticker.upper()}: {str(e)}")

@bot.command(name='top')
@commands.has_role('Premium')
async def cmd_top(ctx, filter_type=None):
    if not scan_results:
        await ctx.send("No scan results yet. Run `!scan` first!")
        return
    results = scan_results
    if filter_type == 'buys':
        results = [r for r in results if 'BUY' in r['signal']]
    elif filter_type == 'shorts':
        results = [r for r in results if 'SHORT' in r['signal']]
    top10 = results[:10]
    embed = discord.Embed(title="🏆 Top Signals", color=discord.Color.gold())
    for r in top10:
        emoji = '🟢' if 'BUY' in r['signal'] else '🔴'
        embed.add_field(
            name=f"{emoji} {r['ticker']}",
            value=f"${r['price']:.2f} | RSI: {r['rsi']:.0f} | {r['signal']}",
            inline=False
        )
    embed.set_footer(text="AlphaSignal Pro — Not financial advice")
    await ctx.send(embed=embed)

@bot.command(name='status')
@commands.has_role('Premium')
async def cmd_status(ctx):
    next_scan = "In progress" if auto_scan.is_running() else "Not running"
    embed = discord.Embed(title="📡 AlphaSignal Status", color=discord.Color.blue())
    embed.add_field(name="🤖 Bot", value="Online ✅", inline=True)
    embed.add_field(name="📦 Tickers", value=str(len(TICKERS)), inline=True)
    embed.add_field(name="🔄 Scan Interval", value="Every 2 hours", inline=True)
    embed.add_field(name="🕐 Last Scan", value=str(last_scan_time)[:16] if last_scan_time else "Not yet", inline=True)
    embed.add_field(name="📊 Signals This Session", value=str(total_signals_sent), inline=True)
    embed.set_footer(text="AlphaSignal Pro — Not financial advice")
    await ctx.send(embed=embed)

@bot.command(name='stats')
@commands.has_role('Premium')
async def cmd_stats(ctx):
    embed = discord.Embed(title="📊 AlphaSignal All-Time Stats", color=discord.Color.purple())
    embed.add_field(name="🟢 Total BUY Signals", value=str(all_time_buys), inline=True)
    embed.add_field(name="🔴 Total SHORT Signals", value=str(all_time_shorts), inline=True)
    embed.add_field(name="📦 Stocks Watched", value=str(len(TICKERS)), inline=True)
    embed.set_footer(text="AlphaSignal Pro — Not financial advice")
    await ctx.send(embed=embed)

@bot.command(name='market')
async def cmd_market(ctx):
    msg = await ctx.send("📊 Checking market...")
    try:
        results = []
        for spy_ticker in ['SPY', 'QQQ', 'IWM']:
            r = await asyncio.get_event_loop().run_in_executor(None, get_stock_data, spy_ticker)
            if r:
                results.append(r)
        embed = discord.Embed(title="🌍 Market Sentiment", color=discord.Color.blue())
        for r in results:
            emoji = '🟢' if 'BUY' in r['signal'] else '🔴' if 'SHORT' in r['signal'] else '⚪'
            embed.add_field(name=f"{emoji} {r['ticker']}", value=f"${r['price']:.2f} — {r['signal']}", inline=True)
        if not results:
            embed.description = "⚪ Market data unavailable right now."
        embed.set_footer(text="AlphaSignal Pro — Not financial advice")
        await msg.edit(content="", embed=embed)
    except Exception as e:
        await msg.edit(content=f"❌ Error: {str(e)}")

@bot.command(name='price')
async def cmd_price(ctx):
    embed = discord.Embed(title="💎 AlphaSignal Premium", color=discord.Color.gold())
    embed.add_field(name="🆓 Free Tier", value="• 2 signals per day\n• !stock command\n• !market command", inline=True)
    embed.add_field(name="💎 Premium — $15/month", value="• Every signal in real-time\n• All commands\n• Private analysis channel\n• Top picks & summaries", inline=True)
    embed.add_field(name="💳 Payment Methods", value="PayPal • CashApp • Crypto (USDT)", inline=False)
    embed.add_field(name="🎫 How to Buy", value="Open a ticket in **#open-ticket** and send payment proof. Admin will verify and unlock Premium instantly.", inline=False)
    embed.set_footer(text="AlphaSignal Pro — Not financial advice")
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def cmd_ping(ctx):
    await ctx.send(f"🏓 Pong! Latency: **{round(bot.latency * 1000)}ms**")

@bot.command(name='schedule')
async def cmd_schedule(ctx):
    if last_scan_time:
        next_scan = last_scan_time + datetime.timedelta(hours=2)
        await ctx.send(f"⏰ Last scan: **{str(last_scan_time)[:16]}** UTC\nNext scan: **{str(next_scan)[:16]}** UTC")
    else:
        await ctx.send("⏰ First scan will run in **2 hours** after bot starts.")

@bot.command(name='compare')
async def cmd_compare(ctx, t1=None, t2=None):
    if not t1 or not t2:
        await ctx.send("Usage: `!compare AAPL TSLA`")
        return
    msg = await ctx.send(f"🔍 Comparing **{t1.upper()}** vs **{t2.upper()}**...")
    r1 = await asyncio.get_event_loop().run_in_executor(None, get_stock_data, t1.upper())
    r2 = await asyncio.get_event_loop().run_in_executor(None, get_stock_data, t2.upper())

    def fmt(r, t):
        if not r:
            return f"**{t}**: No signal / no data"
        e = '🟢' if 'BUY' in r['signal'] else '🔴'
        return f"{e} **{t}**: ${r['price']:.2f} | {r['signal']} | RSI {r['rsi']:.0f}"

    embed = discord.Embed(title=f"⚔️ {t1.upper()} vs {t2.upper()}", color=discord.Color.orange())
    embed.add_field(name=t1.upper(), value=fmt(r1, t1.upper()), inline=False)
    embed.add_field(name=t2.upper(), value=fmt(r2, t2.upper()), inline=False)
    embed.set_footer(text="AlphaSignal Pro — Not financial advice")
    await msg.edit(content="", embed=embed)

# ── WATCHLIST (per user, stored in memory) ────────────
watchlists = {}

@bot.command(name='watchlist')
async def cmd_watchlist(ctx, action=None, ticker=None):
    uid = ctx.author.id
    if uid not in watchlists:
        watchlists[uid] = []
    if action == 'add' and ticker:
        if ticker.upper() not in watchlists[uid]:
            watchlists[uid].append(ticker.upper())
        await ctx.send(f"✅ Added **{ticker.upper()}** to your watchlist.")
    elif action == 'remove' and ticker:
        watchlists[uid] = [t for t in watchlists[uid] if t != ticker.upper()]
        await ctx.send(f"🗑️ Removed **{ticker.upper()}** from your watchlist.")
    elif action == 'show':
        if watchlists[uid]:
            await ctx.send(f"📋 Your watchlist: **{', '.join(watchlists[uid])}**")
        else:
            await ctx.send("Your watchlist is empty. Use `!watchlist add AAPL`")
    else:
        await ctx.send("Usage: `!watchlist add AAPL` / `!watchlist remove AAPL` / `!watchlist show`")

# ── TICKET SYSTEM ─────────────────────────────────────
class TicketButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='🎫 Open Ticket', style=discord.ButtonStyle.green, custom_id='open_ticket')
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user
        existing = discord.utils.get(guild.channels, name=f'ticket-{member.name.lower()}')
        if existing:
            await interaction.response.send_message(f"You already have an open ticket: {existing.mention}", ephemeral=True)
            return
        admin_role = discord.utils.get(guild.roles, name='Admin')
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        support_cat = discord.utils.get(guild.categories, name='🎫 SUPPORT')
        channel = await guild.create_text_channel(
            f'ticket-{member.name.lower()}',
            overwrites=overwrites,
            category=support_cat
        )
        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=f"Welcome {member.mention}!\n\nTo get **Premium access** send payment and share your receipt here.\n\n💳 **Payment Options:**\n• PayPal: `paypal.me/alphasignal`\n• CashApp: `$alphasignal`\n• Crypto USDT: DM admin for wallet\n\n💎 **Price:** $15/month\n\nOnce payment is confirmed an admin will type `!addpremium` to unlock your access instantly.",
            color=discord.Color.gold()
        )
        embed.set_footer(text="An admin will be with you shortly.")
        await channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

@bot.command(name='closeticket')
@commands.has_role('Admin')
async def cmd_closeticket(ctx):
    if 'ticket-' in ctx.channel.name:
        await ctx.send("🔒 Closing ticket in 5 seconds...")
        await asyncio.sleep(5)
        await ctx.channel.delete()
    else:
        await ctx.send("❌ This is not a ticket channel.")

# ── MEMBER JOIN ───────────────────────────────────────
@bot.event
async def on_member_join(member):
    guild = member.guild
    free_role = discord.utils.get(guild.roles, name='Free Member')
    if free_role:
        await member.add_roles(free_role)
    # Create private analysis channel
    analysis_cat = discord.utils.get(guild.categories, name='🤖 PERSONAL ANALYSIS')
    if analysis_cat:
        admin_role = discord.utils.get(guild.roles, name='Admin')
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        channel = await guild.create_text_channel(
            f'analysis-{member.name.lower()}',
            overwrites=overwrites,
            category=analysis_cat
        )
        embed = discord.Embed(
            title=f"👋 Welcome {member.display_name}!",
            description="This is your **private analysis channel** — only you and admins can see this.\n\nUse any command here:\n`!stock AAPL` — analyze any stock\n`!market` — market sentiment\n`!price` — get Premium\n`!help` — all commands",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed)

# ── REACTION ROLES ────────────────────────────────────
@bot.event
async def on_raw_reaction_add(payload):
    if str(payload.emoji) != '✅':
        return
    guild = bot.get_guild(payload.guild_id)
    if not guild:
        return
    channel = guild.get_channel(payload.channel_id)
    if channel and 'verify' in channel.name:
        member = guild.get_member(payload.user_id)
        if member and not member.bot:
            free_role = discord.utils.get(guild.roles, name='Free Member')
            if free_role:
                await member.add_roles(free_role)

# ── ADMIN COMMANDS ────────────────────────────────────
@bot.command(name='addpremium')
@commands.has_role('Admin')
async def cmd_addpremium(ctx, member: discord.Member = None):
    if not member:
        await ctx.send("Usage: `!addpremium @user`")
        return
    premium_role = discord.utils.get(ctx.guild.roles, name='Premium')
    if premium_role:
        await member.add_roles(premium_role)
        await ctx.send(f"✅ {member.mention} has been given **Premium** access!")
        log_ch = find_channel(ctx.guild, 'member-log')
        if log_ch:
            await log_ch.send(f"💎 **Premium granted** to {member.mention} by {ctx.author.mention} at {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")

@bot.command(name='removepremium')
@commands.has_role('Admin')
async def cmd_removepremium(ctx, member: discord.Member = None):
    if not member:
        await ctx.send("Usage: `!removepremium @user`")
        return
    premium_role = discord.utils.get(ctx.guild.roles, name='Premium')
    if premium_role and premium_role in member.roles:
        await member.remove_roles(premium_role)
        await ctx.send(f"✅ Removed **Premium** from {member.mention}")

@bot.command(name='members')
@commands.has_role('Admin')
async def cmd_members(ctx):
    premium_role = discord.utils.get(ctx.guild.roles, name='Premium')
    free_role = discord.utils.get(ctx.guild.roles, name='Free Member')
    premium_count = len(premium_role.members) if premium_role else 0
    free_count = len(free_role.members) if free_role else 0
    embed = discord.Embed(title="👥 Member Stats", color=discord.Color.blue())
    embed.add_field(name="💎 Premium Members", value=str(premium_count), inline=True)
    embed.add_field(name="🆓 Free Members", value=str(free_count), inline=True)
    embed.add_field(name="👥 Total", value=str(ctx.guild.member_count), inline=True)
    await ctx.send(embed=embed)

@bot.command(name='announce')
@commands.has_role('Admin')
async def cmd_announce(ctx, *, message=None):
    if not message:
        await ctx.send("Usage: `!announce Your message here`")
        return
    ann_ch = find_channel(ctx.guild, 'announcements')
    if ann_ch:
        embed = discord.Embed(description=message, color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
        embed.set_author(name="📣 Announcement")
        embed.set_footer(text=f"Posted by {ctx.author.display_name}")
        await ann_ch.send(embed=embed)
        await ctx.send("✅ Announcement posted!")
    else:
        await ctx.send("❌ Could not find announcements channel.")

# ── SERVER SETUP ──────────────────────────────────────
@bot.command(name='setup')
@commands.has_role('Admin')
async def cmd_setup(ctx):
    guild = ctx.guild
    msg = await ctx.send("⚙️ Setting up AlphaSignal server... (this takes ~1 minute)")

    # Create roles
    roles_to_create = [
        ('Admin', discord.Color.red()),
        ('Premium', discord.Color.gold()),
        ('Moderator', discord.Color.blue()),
        ('Free Member', discord.Color.greyple()),
    ]
    for role_name, color in roles_to_create:
        if not discord.utils.get(guild.roles, name=role_name):
            await guild.create_role(name=role_name, color=color)

    free_role = discord.utils.get(guild.roles, name='Free Member')
    premium_role = discord.utils.get(guild.roles, name='Premium')
    admin_role = discord.utils.get(guild.roles, name='Admin')

    def ow_public():
        return {guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False)}

    def ow_premium_only():
        return {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            premium_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            admin_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

    def ow_free_chat():
        return {
            guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }

    # Category definitions
    categories = [
        ("🚀 START HERE", [
            ("👋・welcome", ow_public()),
            ("📜・rules", ow_public()),
            ("📣・announcements", ow_public()),
            ("✅・verify", ow_free_chat()),
            ("🎫・get-premium", ow_public()),
        ]),
        ("📚 EDUCATION", [
            ("📖・how-to-use", ow_public()),
            ("🧠・what-is-macd", ow_public()),
            ("❓・faq", ow_public()),
        ]),
        ("🆓 FREE MEMBERS", [
            ("🆓・free-signals", ow_public()),
            ("💬・free-chat", ow_free_chat()),
            ("🤖・free-commands", ow_free_chat()),
        ]),
        ("💎 PREMIUM ONLY", [
            ("📡・signal-feed", ow_premium_only()),
            ("🏆・top-picks", ow_premium_only()),
            ("📈・scan-summaries", ow_premium_only()),
            ("💬・premium-chat", ow_premium_only()),
            ("🤖・premium-commands", ow_premium_only()),
        ]),
        ("🤖 PERSONAL ANALYSIS", []),
        ("🎫 SUPPORT", [
            ("📩・open-ticket", ow_free_chat()),
        ]),
        ("🛡 ADMIN", [
            ("🔧・admin-commands", {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                admin_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }),
            ("📋・member-log", {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                admin_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            }),
        ]),
    ]

    for cat_name, channels in categories:
        cat = discord.utils.get(guild.categories, name=cat_name)
        if not cat:
            cat = await guild.create_category(cat_name)
        for ch_name, overwrites in channels:
            if not discord.utils.get(guild.channels, name=ch_name):
                await guild.create_text_channel(ch_name, category=cat, overwrites=overwrites)

    await asyncio.sleep(2)

    # Post content to channels
    welcome_ch = find_channel(guild, 'welcome')
    if welcome_ch:
        embed = discord.Embed(
            title="📈 Welcome to AlphaSignal",
            description="**The #1 Triple-Timeframe MACD Stock Scanner on Discord**\n\nWe scan **500+ stocks** every 2 hours across Daily, Weekly & Monthly timeframes.\nSignals only fire when **ALL 3 agree** — extremely high conviction.",
            color=discord.Color.green()
        )
        embed.add_field(name="🆓 Free Tier", value="• 2 signals per day\n• !stock command\n• !market command\n• Personal analysis channel", inline=True)
        embed.add_field(name="💎 Premium — $15/mo", value="• Every signal in real-time\n• All commands\n• Top picks & summaries\n• Priority support", inline=True)
        embed.add_field(name="🚀 Get Started", value="1️⃣ React ✅ in **#verify**\n2️⃣ Use `!help` in your private channel\n3️⃣ Open a ticket to upgrade to Premium", inline=False)
        embed.set_footer(text="AlphaSignal Pro — Not financial advice")
        await welcome_ch.send(embed=embed)

    rules_ch = find_channel(guild, 'rules')
    if rules_ch:
        embed = discord.Embed(title="📜 Server Rules", color=discord.Color.red())
        rules = [
            "Nothing posted here is financial advice. Always do your own research.",
            "No spamming or repeated messages.",
            "Do not share Premium signals outside this server.",
            "Treat all members with respect. Zero tolerance for harassment.",
            "No self promotion without admin permission.",
            "English only in public channels.",
            "No begging for Premium access.",
            "Keep bot commands in command channels only.",
            "No pump and dump discussion.",
            "Breaking rules = warning → kick → permanent ban."
        ]
        embed.description = '\n'.join([f"**{i+1}.** {r}" for i, r in enumerate(rules)])
        embed.set_footer(text="By staying in this server you agree to all rules.")
        await rules_ch.send(embed=embed)

    verify_ch = find_channel(guild, 'verify')
    if verify_ch:
        embed = discord.Embed(
            title="✅ Verify to Access the Server",
            description="React with ✅ below to confirm you have read the rules.\nYou will automatically receive the **Free Member** role and unlock the server.",
            color=discord.Color.green()
        )
        vmsg = await verify_ch.send(embed=embed)
        await vmsg.add_reaction('✅')

    get_prem_ch = find_channel(guild, 'get-premium')
    if get_prem_ch:
        embed = discord.Embed(title="💎 Upgrade to Premium", color=discord.Color.gold())
        embed.add_field(name="🆓 Free", value="2 signals/day\n!stock & !market\nPersonal channel", inline=True)
        embed.add_field(name="💎 Premium $15/mo", value="All signals live\nAll commands\nTop picks & summaries\nPriority support", inline=True)
        embed.add_field(name="How to Pay", value="Open a ticket in **#open-ticket** → send payment → admin verifies → instant access", inline=False)
        embed.set_footer(text="AlphaSignal Pro — Not financial advice")
        await get_prem_ch.send(embed=embed)

    how_ch = find_channel(guild, 'how-to-use')
    if how_ch:
        embed = discord.Embed(title="📖 How to Use AlphaSignal", color=discord.Color.blue())
        embed.add_field(name="🆓 Free Commands", value="`!stock AAPL` — Full analysis\n`!market` — Market sentiment\n`!ping` — Bot latency\n`!price` — Pricing info\n`!schedule` — Next scan time", inline=False)
        embed.add_field(name="💎 Premium Commands", value="`!scan` — Run full scan now\n`!scan TSLA` — Scan one stock\n`!top` — Top 10 signals\n`!compare TSLA AAPL` — Compare stocks\n`!watchlist add TSLA` — Personal watchlist\n`!status` — Bot status\n`!stats` — All-time stats", inline=False)
        embed.set_footer(text="AlphaSignal Pro — Not financial advice")
        await how_ch.send(embed=embed)

    ticket_ch = find_channel(guild, 'open-ticket')
    if ticket_ch:
        embed = discord.Embed(
            title="🎫 Open a Support Ticket",
            description="Click the button below to open a private ticket.\nUse tickets to:\n• Pay for Premium\n• Get support\n• Report issues",
            color=discord.Color.blue()
        )
        await ticket_ch.send(embed=embed, view=TicketButton())

    await msg.edit(content="✅ **AlphaSignal server setup complete!** All channels, roles and content have been created.")

# ── BOT READY ─────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"[AlphaSignal] Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching,
        name="500+ stocks | AlphaSignal"
    ))
    if not auto_scan.is_running():
        auto_scan.start()
    # Re-register ticket button view
    bot.add_view(TicketButton())

# ── RECONNECT ─────────────────────────────────────────
@bot.event
async def on_disconnect():
    print("[AlphaSignal] Disconnected. Reconnecting...")

bot.run(TOKEN, reconnect=True)
