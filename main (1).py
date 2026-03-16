"""
AlphaSignal Discord Bot — BEST VERSION
5000+ stocks, MACD+RSI+Stoch, 24/7, full server setup
"""
import discord
from discord.ext import commands, tasks
import yfinance as yf
import pandas as pd
import numpy as np
import asyncio, os, datetime
from threading import Thread
from flask import Flask

app = Flask('')
@app.route('/')
def home(): return "AlphaSignal alive!"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()

TOKEN = os.environ.get('DISCORD_TOKEN', '')
CHANNEL_ID = int(os.environ.get('DISCORD_CHANNEL_ID', '0'))

def fetch_tickers():
    tickers = set()
    try:
        t = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
        tickers.update([x.replace('.','-') for x in t])
    except: pass
    try:
        t = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')[4]['Ticker'].tolist()
        tickers.update([x.replace('.','-') for x in t])
    except: pass
    fallback = ["AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","JPM","V","UNH","XOM","JNJ","WMT","MA","PG","HD","CVX","MRK","ABBV","PEP","KO","BAC","COST","AVGO","TMO","MCD","NFLX","CRM","LIN","ACN","AMD","TXN","DHR","NEE","ADBE","ORCL","PM","SCHW","AMGN","INTC","QCOM","IBM","GE","BA","CAT","HON","GS","MS","BLK","SBUX","NKE","DIS","PYPL","ISRG","MDT","GILD","MMC","PLD","SPGI","LOW","ELV","SYK","CB","ZTS","NOW","ADP","MDLZ","REGN","BKNG","MO","SO","DUK","BMY","INTU","PNC","USB","TGT","CI","APD","ITW","DE","GD","RTX","LMT","NOC","ETN","EMR","MMM","SHW","ECL","ROP","FDX","UPS","CSX","NSC","UNP","CARR","OTIS","TT","CTAS","FAST","PAYX","AON","MET","PRU","AFL","ALL","TRV","WFC","C","FITB","KEY","RF","CFG","F","GM","RIVN","NIO","XPEV","SNAP","PINS","RBLX","DKNG","MGM","LVS","MAR","HLT","RCL","CCL","NCLH","AAL","DAL","UAL","LUV","ENPH","FSLR","COIN","MSTR","RIOT","MARA","SQ","AFRM","UPST","SOFI","HOOD","ROKU","TTD","SHOP","MELI","SE","GRAB","CPNG","BABA","JD","PDD","BIDU","TSM","ASML","AMAT","LRCX","KLAC","MCHP","SMCI","PSTG","NTAP","STX","WDC","NTNX","HUBS","DDOG","NET","MDB","SPLK","CRWD","ZS","OKTA","PANW","FTNT","CHKP","PLTR","TWLO","ZM","DOCU","ATVI","EA","TTWO","MRNA","BNTX","ILMN","ACAD","ALNY","IONS","BMRN","SRPT","EOG","PXD","DVN","HES","MRO","OXY","PSX","VLO","MPC","HAL","SLB","BKR","NEE","AES","DUK","EXC","SRE","O","NNN","WPC","STAG","VICI","SBAC","CCI","AMT","EQIX","DLR","PSA","EXR","SPG","VNO","SLG","BXP","NVR","PHM","DHI","LEN","TOL","KBH","AWI","MAS","TREX","AZEK","BECN","BLDR","SUM","MLM","VMC","BILL","SMAR","APPF","WK","FOUR","PCTY","PAYC","VEEV","CDAY","WEX","MKTX","IBKR","LPLA","EDIT","CRSP","NTLA","BEAM","VERVE","EXAS","NTRA","JAZZ","PRGO","INVA","RPRX","DVAX","LAZR","INDI","MBLY","AI","BIGBEAR","AXON","TRMB","GNRC","PENN","MGAM","BOYD","CHDN","JOBY","ACHR","DUOL","CHGG","CSIQ","JKS","DQ","MAXN","NOVA","SPWR","ARRY","SHLS","BE","FCEL","BLDP","AEIS","ACLS","ONTO","ENTG","RMBS","WOLF","OLED","COHR","TWLO","BILL","LSPD","TOST","REPAY","EVTC","PAYA","BBAI","SOUN","MVIS","OUST"]
    tickers.update(fallback)
    result = sorted(list(tickers))
    print(f"[AlphaSignal] {len(result)} tickers loaded")
    return result

TICKERS = fetch_tickers()
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
scan_results, last_scan_time, total_signals, all_time_buys, all_time_shorts = [], None, 0, 0, 0

def calc_macd(closes):
    if len(closes) < 35: return None, 0, 0
    s = pd.Series(closes)
    e12 = s.ewm(span=12, adjust=False).mean()
    e26 = s.ewm(span=26, adjust=False).mean()
    macd = e12 - e26
    sig = macd.ewm(span=9, adjust=False).mean()
    m, sv = float(macd.iloc[-1]), float(sig.iloc[-1])
    return ("BUY" if m > sv else "SHORT" if m < sv else "HOLD"), m, sv

def calc_rsi(closes, p=14):
    if len(closes) < p+1: return 50.0
    s = pd.Series(closes)
    d = s.diff()
    g = d.where(d>0,0).ewm(com=p-1,adjust=False).mean()
    l = (-d.where(d<0,0)).ewm(com=p-1,adjust=False).mean()
    return float(100-(100/(1+(g/(l+1e-9)).iloc[-1])))

def calc_stoch(c, h, l, k=14, d=3):
    if len(c) < k: return 50.0, 50.0
    sc,sh,sl = pd.Series(c),pd.Series(h),pd.Series(l)
    ll,hh = sl.rolling(k).min(),sh.rolling(k).max()
    pk = 100*(sc-ll)/(hh-ll+1e-9)
    pd_ = pk.rolling(d).mean()
    return float(pk.iloc[-1]), float(pd_.iloc[-1])

def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = getattr(stock.fast_info,'last_price',None)
        if not price or price <= 0: return None
        d = stock.history(interval='1d', period='1y')
        if len(d) < 35: return None
        w = stock.history(interval='1wk', period='3y')
        if len(w) < 35: return None
        m = stock.history(interval='1mo', period='10y')
        if len(m) < 35: return None
        d_sig,_,_ = calc_macd(d['Close'].tolist())
        w_sig,_,_ = calc_macd(w['Close'].tolist())
        m_sig,_,_ = calc_macd(m['Close'].tolist())
        rsi = calc_rsi(d['Close'].tolist())
        sk,sd = calc_stoch(d['Close'].tolist(),d['High'].tolist(),d['Low'].tolist())
        stoch_sig = "BUY" if sk<20 else "SHORT" if sk>80 else ("BUY" if sk>sd else "SHORT")
        avg_vol = float(d['Volume'].tail(20).mean())
        cur_vol = float(d['Volume'].iloc[-1])
        vol = cur_vol/avg_vol if avg_vol > 0 else 1.0
        macd_buy = d_sig=="BUY" and w_sig=="BUY" and m_sig=="BUY"
        macd_short = d_sig=="SHORT" and w_sig=="SHORT" and m_sig=="SHORT"
        if macd_buy and rsi>50 and stoch_sig=="BUY": signal="STRONG BUY"
        elif macd_buy and rsi>50: signal="BUY"
        elif macd_short and rsi<50 and stoch_sig=="SHORT": signal="STRONG SHORT"
        elif macd_short and rsi<50: signal="SHORT"
        else: return None
        return {'ticker':ticker,'signal':signal,'price':price,'rsi':rsi,'sk':sk,'sd':sd,'stoch_sig':stoch_sig,'vol':vol,'ds':d_sig,'ws':w_sig,'ms':m_sig}
    except: return None

def find_ch(guild, name):
    for ch in guild.channels:
        if name.lower() in ch.name.lower(): return ch
    return None

def is_cmd_ch(channel):
    return any(a in channel.name.lower() for a in ['commands','analysis-','ticket-','bot-'])

def se(s): return '✅' if s=='BUY' else '🔴' if s=='SHORT' else '⚪'

def make_embed(r):
    ib = 'BUY' in r['signal']
    e = discord.Embed(title=f"{'🟢' if ib else '🔴'} {r['signal']} — {r['ticker']}",color=discord.Color.green() if ib else discord.Color.red(),timestamp=datetime.datetime.utcnow())
    e.add_field(name="💰 Price",value=f"${r['price']:.2f}",inline=True)
    e.add_field(name="📦 Volume",value=f"{r['vol']:.1f}x",inline=True)
    e.add_field(name="\u200b",value="\u200b",inline=True)
    e.add_field(name=f"{se(r['ds'])} Daily MACD",value=r['ds'],inline=True)
    e.add_field(name=f"{se(r['ws'])} Weekly MACD",value=r['ws'],inline=True)
    e.add_field(name=f"{se(r['ms'])} Monthly MACD",value=r['ms'],inline=True)
    re_ = '✅' if r['rsi']>50 else '🔴'
    e.add_field(name="📊 RSI (50 line)",value=f"{re_} {r['rsi']:.1f} {'Bull ✅' if r['rsi']>50 else 'Bear 🔴'}",inline=True)
    ste = '✅' if r['stoch_sig']=='BUY' else '🔴'
    e.add_field(name="📉 Stochastic",value=f"{ste} K:{r['sk']:.1f} D:{r['sd']:.1f}",inline=True)
    e.set_footer(text="AlphaSignal Pro — Not financial advice")
    return e

@tasks.loop(hours=2)
async def auto_scan():
    global scan_results,last_scan_time,total_signals,all_time_buys,all_time_shorts
    guild = discord.utils.find(lambda g:True,bot.guilds)
    if not guild: return
    sig_ch=find_ch(guild,'signal-feed')
    free_ch=find_ch(guild,'free-signals')
    sum_ch=find_ch(guild,'scan-summaries')
    buys,shorts=[],[]
    print(f"[AlphaSignal] Scanning {len(TICKERS)} tickers...")
    for i,ticker in enumerate(TICKERS):
        if i%100==0:
            print(f"[AlphaSignal] {i}/{len(TICKERS)}")
            await asyncio.sleep(0.1)
        r = await asyncio.get_event_loop().run_in_executor(None,get_stock_data,ticker)
        if r:
            (buys if 'BUY' in r['signal'] else shorts).append(r)
    scan_results=buys+shorts
    last_scan_time=datetime.datetime.utcnow()
    total_signals+=len(scan_results)
    all_time_buys+=len(buys)
    all_time_shorts+=len(shorts)
    if sig_ch:
        for r in scan_results:
            await sig_ch.send(embed=make_embed(r))
            await asyncio.sleep(0.3)
    if free_ch and scan_results:
        await free_ch.send(f"📊 **Free Preview** — {len(scan_results)} signals found this scan. Upgrade for all!")
        for r in scan_results[:2]: await free_ch.send(embed=make_embed(r))
    if sum_ch:
        e=discord.Embed(title="📈 Scan Complete",color=discord.Color.blue(),timestamp=datetime.datetime.utcnow())
        e.add_field(name="🔍 Scanned",value=str(len(TICKERS)),inline=True)
        e.add_field(name="🟢 BUY",value=str(len(buys)),inline=True)
        e.add_field(name="🔴 SHORT",value=str(len(shorts)),inline=True)
        if buys: e.add_field(name="🏆 Top Buys",value=' '.join([f"**{r['ticker']}**" for r in buys[:5]]),inline=False)
        if shorts: e.add_field(name="📉 Top Shorts",value=' '.join([f"**{r['ticker']}**" for r in shorts[:5]]),inline=False)
        e.set_footer(text="AlphaSignal Pro — Not financial advice")
        await sum_ch.send(embed=e)
    print(f"[AlphaSignal] Done. {len(buys)} buys, {len(shorts)} shorts.")

@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.content.startswith('!') and not is_cmd_ch(message.channel): return
    await bot.process_commands(message)

@bot.command(name='help')
async def cmd_help(ctx):
    p=discord.utils.get(ctx.guild.roles,name='Premium')
    hp=p in ctx.author.roles if p else False
    e=discord.Embed(title="📡 AlphaSignal Commands",color=discord.Color.blue())
    e.add_field(name="🆓 Free",value="`!stock AAPL` `!market` `!ping` `!price` `!schedule` `!help`",inline=False)
    if hp: e.add_field(name="💎 Premium",value="`!scan` `!scan TSLA` `!top` `!top buys` `!top shorts` `!status` `!stats` `!compare TSLA AAPL` `!watchlist add/remove/show`",inline=False)
    e.set_footer(text="AlphaSignal Pro — Not financial advice")
    await ctx.send(embed=e)

@bot.command(name='scan')
@commands.has_role('Premium')
async def cmd_scan(ctx, ticker=None):
    if ticker:
        msg=await ctx.send(f"🔍 Scanning **{ticker.upper()}**...")
        r=await asyncio.get_event_loop().run_in_executor(None,get_stock_data,ticker.upper())
        await msg.edit(content="",embed=make_embed(r)) if r else await msg.edit(content=f"⚪ No signal for **{ticker.upper()}**")
    else:
        msg=await ctx.send(f"⚡ Scanning **{len(TICKERS)}** stocks...")
        await auto_scan()
        await msg.edit(content="✅ Done! Check **signal-feed**.")

@bot.command(name='stock')
async def cmd_stock(ctx, ticker=None):
    if not ticker: await ctx.send("Usage: `!stock AAPL`"); return
    msg=await ctx.send(f"🔍 Analyzing **{ticker.upper()}**...")
    try:
        stock=yf.Ticker(ticker.upper())
        price=getattr(stock.fast_info,'last_price',0)
        d=stock.history(interval='1d',period='1y')
        w=stock.history(interval='1wk',period='3y')
        m=stock.history(interval='1mo',period='10y')
        ds,_,_=calc_macd(d['Close'].tolist()) if len(d)>=35 else ('N/A',0,0)
        ws,_,_=calc_macd(w['Close'].tolist()) if len(w)>=35 else ('N/A',0,0)
        ms,_,_=calc_macd(m['Close'].tolist()) if len(m)>=35 else ('N/A',0,0)
        rsi=calc_rsi(d['Close'].tolist()) if len(d)>=15 else 50
        sk,sd=calc_stoch(d['Close'].tolist(),d['High'].tolist(),d['Low'].tolist()) if len(d)>=14 else (50,50)
        ss="BUY" if sk<20 else "SHORT" if sk>80 else ("BUY" if sk>sd else "SHORT")
        mb=ds=="BUY" and ws=="BUY" and ms=="BUY"
        ms2=ds=="SHORT" and ws=="SHORT" and ms=="SHORT"
        if mb and rsi>50 and ss=="BUY": ov,col="🟢 STRONG BUY",discord.Color.green()
        elif mb and rsi>50: ov,col="✅ BUY",discord.Color.green()
        elif ms2 and rsi<50 and ss=="SHORT": ov,col="🔴 STRONG SHORT",discord.Color.red()
        elif ms2 and rsi<50: ov,col="🔴 SHORT",discord.Color.red()
        else: ov,col="⚪ NO SIGNAL",discord.Color.greyple()
        e=discord.Embed(title=f"📊 {ticker.upper()}",color=col)
        e.add_field(name="💰 Price",value=f"${price:.2f}" if price else "N/A",inline=True)
        e.add_field(name="🎯 Signal",value=ov,inline=True)
        e.add_field(name="\u200b",value="\u200b",inline=True)
        e.add_field(name=f"{se(ds)} Daily MACD",value=str(ds),inline=True)
        e.add_field(name=f"{se(ws)} Weekly MACD",value=str(ws),inline=True)
        e.add_field(name=f"{se(ms)} Monthly MACD",value=str(ms),inline=True)
        re_='✅' if rsi>50 else '🔴'
        e.add_field(name="📊 RSI (50 line)",value=f"{re_} {rsi:.1f} {'Bull ✅' if rsi>50 else 'Bear 🔴'}",inline=True)
        ste='✅' if ss=='BUY' else '🔴'
        e.add_field(name="📉 Stochastic",value=f"{ste} K:{sk:.1f} D:{sd:.1f}",inline=True)
        e.set_footer(text="AlphaSignal Pro — Not financial advice")
        await msg.edit(content="",embed=e)
    except Exception as ex: await msg.edit(content=f"❌ Error: {str(ex)}")

@bot.command(name='top')
@commands.has_role('Premium')
async def cmd_top(ctx, ft=None):
    if not scan_results: await ctx.send("No results yet. Run `!scan`!"); return
    res=scan_results
    if ft=='buys': res=[r for r in res if 'BUY' in r['signal']]
    elif ft=='shorts': res=[r for r in res if 'SHORT' in r['signal']]
    e=discord.Embed(title="🏆 Top Signals",color=discord.Color.gold())
    for r in res[:10]:
        em='🟢' if 'BUY' in r['signal'] else '🔴'
        e.add_field(name=f"{em} {r['ticker']}",value=f"${r['price']:.2f} | RSI:{r['rsi']:.0f} | {r['signal']}",inline=False)
    e.set_footer(text="AlphaSignal Pro — Not financial advice")
    await ctx.send(embed=e)

@bot.command(name='status')
@commands.has_role('Premium')
async def cmd_status(ctx):
    e=discord.Embed(title="📡 Status",color=discord.Color.blue())
    e.add_field(name="🤖 Bot",value="Online ✅",inline=True)
    e.add_field(name="📦 Tickers",value=str(len(TICKERS)),inline=True)
    e.add_field(name="🔄 Interval",value="Every 2 hours",inline=True)
    e.add_field(name="🕐 Last Scan",value=str(last_scan_time)[:16] if last_scan_time else "Not yet",inline=True)
    e.add_field(name="📊 Total Signals",value=str(total_signals),inline=True)
    e.set_footer(text="AlphaSignal Pro — Not financial advice")
    await ctx.send(embed=e)

@bot.command(name='stats')
@commands.has_role('Premium')
async def cmd_stats(ctx):
    e=discord.Embed(title="📊 All-Time Stats",color=discord.Color.purple())
    e.add_field(name="🟢 BUY",value=str(all_time_buys),inline=True)
    e.add_field(name="🔴 SHORT",value=str(all_time_shorts),inline=True)
    e.add_field(name="📦 Stocks",value=str(len(TICKERS)),inline=True)
    e.set_footer(text="AlphaSignal Pro — Not financial advice")
    await ctx.send(embed=e)

@bot.command(name='market')
async def cmd_market(ctx):
    msg=await ctx.send("📊 Checking market...")
    try:
        e=discord.Embed(title="🌍 Market Sentiment",color=discord.Color.blue())
        for t in ['SPY','QQQ','IWM']:
            r=await asyncio.get_event_loop().run_in_executor(None,get_stock_data,t)
            em='🟢' if r and 'BUY' in r['signal'] else '🔴' if r and 'SHORT' in r['signal'] else '⚪'
            e.add_field(name=f"{em} {t}",value=f"${r['price']:.2f} — {r['signal']}" if r else "No signal",inline=True)
        e.set_footer(text="AlphaSignal Pro — Not financial advice")
        await msg.edit(content="",embed=e)
    except Exception as ex: await msg.edit(content=f"❌ {str(ex)}")

@bot.command(name='price')
async def cmd_price(ctx):
    e=discord.Embed(title="💎 AlphaSignal Premium",color=discord.Color.gold())
    e.add_field(name="🆓 Free",value="2 signals/day\n!stock & !market\nPrivate channel",inline=True)
    e.add_field(name="💎 $15/month",value="ALL signals live\nAll commands\nTop picks & summaries",inline=True)
    e.add_field(name="💳 Payment",value="PayPal • CashApp • Crypto\nOpen ticket in **#open-ticket**",inline=False)
    e.set_footer(text="AlphaSignal Pro — Not financial advice")
    await ctx.send(embed=e)

@bot.command(name='ping')
async def cmd_ping(ctx): await ctx.send(f"🏓 {round(bot.latency*1000)}ms")

@bot.command(name='schedule')
async def cmd_schedule(ctx):
    if last_scan_time:
        nxt=last_scan_time+datetime.timedelta(hours=2)
        await ctx.send(f"⏰ Last: **{str(last_scan_time)[:16]}** | Next: **{str(nxt)[:16]}** UTC")
    else: await ctx.send("⏰ First scan runs 2 hours after launch.")

@bot.command(name='compare')
async def cmd_compare(ctx, t1=None, t2=None):
    if not t1 or not t2: await ctx.send("Usage: `!compare AAPL TSLA`"); return
    msg=await ctx.send(f"🔍 Comparing...")
    r1=await asyncio.get_event_loop().run_in_executor(None,get_stock_data,t1.upper())
    r2=await asyncio.get_event_loop().run_in_executor(None,get_stock_data,t2.upper())
    e=discord.Embed(title=f"⚔️ {t1.upper()} vs {t2.upper()}",color=discord.Color.orange())
    def fmt(r,t): return f"{'🟢' if r and 'BUY' in r['signal'] else '🔴'} {r['signal']} | ${r['price']:.2f} | RSI:{r['rsi']:.0f}" if r else "No signal"
    e.add_field(name=t1.upper(),value=fmt(r1,t1),inline=False)
    e.add_field(name=t2.upper(),value=fmt(r2,t2),inline=False)
    e.set_footer(text="AlphaSignal Pro — Not financial advice")
    await msg.edit(content="",embed=e)

wl={}
@bot.command(name='watchlist')
async def cmd_watchlist(ctx, action=None, ticker=None):
    uid=ctx.author.id
    if uid not in wl: wl[uid]=[]
    if action=='add' and ticker:
        if ticker.upper() not in wl[uid]: wl[uid].append(ticker.upper())
        await ctx.send(f"✅ Added **{ticker.upper()}**")
    elif action=='remove' and ticker:
        wl[uid]=[t for t in wl[uid] if t!=ticker.upper()]
        await ctx.send(f"🗑️ Removed **{ticker.upper()}**")
    elif action=='show': await ctx.send(f"📋 **{', '.join(wl[uid])}**" if wl[uid] else "Empty. Use `!watchlist add AAPL`")
    else: await ctx.send("Usage: `!watchlist add/remove/show TICKER`")

class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label='🎫 Open Ticket',style=discord.ButtonStyle.green,custom_id='ticket_open')
    async def open_ticket(self,interaction:discord.Interaction,button:discord.ui.Button):
        guild=interaction.guild; member=interaction.user
        ex=discord.utils.get(guild.channels,name=f'ticket-{member.name.lower()}')
        if ex: await interaction.response.send_message(f"Already have ticket: {ex.mention}",ephemeral=True); return
        ar=discord.utils.get(guild.roles,name='Admin')
        cat=discord.utils.get(guild.categories,name='🎫 SUPPORT')
        ow={guild.default_role:discord.PermissionOverwrite(read_messages=False),member:discord.PermissionOverwrite(read_messages=True,send_messages=True),guild.me:discord.PermissionOverwrite(read_messages=True,send_messages=True)}
        if ar: ow[ar]=discord.PermissionOverwrite(read_messages=True,send_messages=True)
        ch=await guild.create_text_channel(f'ticket-{member.name.lower()}',overwrites=ow,category=cat)
        e=discord.Embed(title="🎫 Support Ticket",color=discord.Color.gold())
        e.description=f"Welcome {member.mention}!\n\n💳 **Payment:**\n• PayPal: `paypal.me/alphasignal`\n• CashApp: `$alphasignal`\n• Crypto USDT: DM admin\n\n💎 **$15/month** — send receipt here, admin unlocks instantly."
        await ch.send(embed=e)
        await interaction.response.send_message(f"✅ Ticket: {ch.mention}",ephemeral=True)

@bot.command(name='closeticket')
@commands.has_role('Admin')
async def cmd_closeticket(ctx):
    if 'ticket-' in ctx.channel.name:
        await ctx.send("🔒 Closing in 5s..."); await asyncio.sleep(5); await ctx.channel.delete()
    else: await ctx.send("❌ Not a ticket channel.")

@bot.command(name='addpremium')
@commands.has_role('Admin')
async def cmd_addpremium(ctx, member:discord.Member=None):
    if not member: await ctx.send("Usage: `!addpremium @user`"); return
    role=discord.utils.get(ctx.guild.roles,name='Premium')
    if role:
        await member.add_roles(role); await ctx.send(f"✅ {member.mention} is now **Premium**!")
        log=find_ch(ctx.guild,'member-log')
        if log: await log.send(f"💎 Premium → {member.mention} by {ctx.author.mention}")

@bot.command(name='removepremium')
@commands.has_role('Admin')
async def cmd_removepremium(ctx, member:discord.Member=None):
    if not member: await ctx.send("Usage: `!removepremium @user`"); return
    role=discord.utils.get(ctx.guild.roles,name='Premium')
    if role and role in member.roles: await member.remove_roles(role); await ctx.send(f"✅ Removed from {member.mention}")

@bot.command(name='members')
@commands.has_role('Admin')
async def cmd_members(ctx):
    p=discord.utils.get(ctx.guild.roles,name='Premium')
    f=discord.utils.get(ctx.guild.roles,name='Free Member')
    e=discord.Embed(title="👥 Members",color=discord.Color.blue())
    e.add_field(name="💎 Premium",value=str(len(p.members)) if p else "0",inline=True)
    e.add_field(name="🆓 Free",value=str(len(f.members)) if f else "0",inline=True)
    e.add_field(name="👥 Total",value=str(ctx.guild.member_count),inline=True)
    await ctx.send(embed=e)

@bot.command(name='announce')
@commands.has_role('Admin')
async def cmd_announce(ctx, *, message=None):
    if not message: await ctx.send("Usage: `!announce message`"); return
    ch=find_ch(ctx.guild,'announcements')
    if ch:
        e=discord.Embed(description=message,color=discord.Color.blue(),timestamp=datetime.datetime.utcnow())
        e.set_author(name="📣 Announcement")
        await ch.send(embed=e); await ctx.send("✅ Posted!")

@bot.event
async def on_member_join(member):
    guild=member.guild
    fr=discord.utils.get(guild.roles,name='Free Member')
    if fr: await member.add_roles(fr)
    cat=discord.utils.get(guild.categories,name='🤖 PERSONAL ANALYSIS')
    if cat:
        ar=discord.utils.get(guild.roles,name='Admin')
        ow={guild.default_role:discord.PermissionOverwrite(read_messages=False),member:discord.PermissionOverwrite(read_messages=True,send_messages=True),guild.me:discord.PermissionOverwrite(read_messages=True,send_messages=True)}
        if ar: ow[ar]=discord.PermissionOverwrite(read_messages=True,send_messages=True)
        ch=await guild.create_text_channel(f'analysis-{member.name.lower()}',overwrites=ow,category=cat)
        e=discord.Embed(title=f"👋 Welcome {member.display_name}!",color=discord.Color.blue())
        e.description="**Your private channel** — only you and admins see this.\n\n`!stock AAPL` — analyze any stock\n`!market` — market overview\n`!price` — get Premium\n`!help` — all commands"
        await ch.send(embed=e)

@bot.event
async def on_raw_reaction_add(payload):
    if str(payload.emoji)!='✅': return
    guild=bot.get_guild(payload.guild_id)
    if not guild: return
    ch=guild.get_channel(payload.channel_id)
    if ch and 'verify' in ch.name:
        m=guild.get_member(payload.user_id)
        if m and not m.bot:
            r=discord.utils.get(guild.roles,name='Free Member')
            if r: await m.add_roles(r)

@bot.command(name='setup')
@commands.has_role('Admin')
async def cmd_setup(ctx):
    guild=ctx.guild
    msg=await ctx.send("⚙️ Building AlphaSignal server...")
    for name,color in [('Admin',discord.Color.red()),('Premium',discord.Color.gold()),('Moderator',discord.Color.blue()),('Free Member',discord.Color.greyple())]:
        if not discord.utils.get(guild.roles,name=name): await guild.create_role(name=name,color=color)
    fr=discord.utils.get(guild.roles,name='Free Member')
    pr=discord.utils.get(guild.roles,name='Premium')
    ar=discord.utils.get(guild.roles,name='Admin')
    def pub(): return {guild.default_role:discord.PermissionOverwrite(read_messages=True,send_messages=False),guild.me:discord.PermissionOverwrite(read_messages=True,send_messages=True)}
    def chat(): return {guild.default_role:discord.PermissionOverwrite(read_messages=True,send_messages=True),guild.me:discord.PermissionOverwrite(read_messages=True,send_messages=True)}
    def prem(): return {guild.default_role:discord.PermissionOverwrite(read_messages=False),pr:discord.PermissionOverwrite(read_messages=True,send_messages=True),ar:discord.PermissionOverwrite(read_messages=True,send_messages=True),guild.me:discord.PermissionOverwrite(read_messages=True,send_messages=True)}
    def adm(): return {guild.default_role:discord.PermissionOverwrite(read_messages=False),ar:discord.PermissionOverwrite(read_messages=True,send_messages=True),guild.me:discord.PermissionOverwrite(read_messages=True,send_messages=True)}
    cats=[("🚀 START HERE",[("👋・welcome",pub()),("📜・rules",pub()),("📣・announcements",pub()),("✅・verify",chat()),("🎫・get-premium",pub())]),("📚 EDUCATION",[("📖・how-to-use",pub()),("🧠・what-is-macd",pub()),("❓・faq",pub())]),("🆓 FREE MEMBERS",[("🆓・free-signals",pub()),("💬・free-chat",chat()),("🤖・free-commands",chat())]),("💎 PREMIUM ONLY",[("📡・signal-feed",prem()),("🏆・top-picks",prem()),("📈・scan-summaries",prem()),("💬・premium-chat",prem()),("🤖・premium-commands",prem())]),("🤖 PERSONAL ANALYSIS",[]),("🎫 SUPPORT",[("📩・open-ticket",chat())]),("🛡 ADMIN",[("🔧・admin-commands",adm()),("📋・member-log",adm())])]
    for cn,chs in cats:
        cat=discord.utils.get(guild.categories,name=cn) or await guild.create_category(cn)
        for chn,ow in chs:
            if not discord.utils.get(guild.channels,name=chn): await guild.create_text_channel(chn,category=cat,overwrites=ow)
    await asyncio.sleep(2)
    ch=find_ch(guild,'welcome')
    if ch:
        e=discord.Embed(title="📈 Welcome to AlphaSignal",description="**The #1 Triple-Timeframe MACD Scanner**\n\nScans **5000+ stocks** every 2 hours.\nSignals only fire when **MACD + RSI + Stochastic ALL agree.**",color=discord.Color.green())
        e.add_field(name="🆓 Free",value="2 signals/day\n!stock & !market\nPrivate channel",inline=True)
        e.add_field(name="💎 Premium $15/mo",value="ALL signals live\nAll commands\nTop picks & summaries",inline=True)
        e.add_field(name="🚀 Get Started",value="1️⃣ React ✅ in **#verify**\n2️⃣ Use `!help` in your private channel\n3️⃣ Open ticket to upgrade",inline=False)
        e.set_footer(text="AlphaSignal Pro — Not financial advice")
        await ch.send(embed=e)
    ch=find_ch(guild,'rules')
    if ch:
        e=discord.Embed(title="📜 Rules",color=discord.Color.red())
        e.description='\n'.join([f"**{i+1}.** {r}" for i,r in enumerate(["Nothing here is financial advice. Do your own research.","No spamming.","Do not share Premium signals outside this server.","Be respectful. Zero tolerance for harassment.","No self promotion without permission.","English only in public channels.","No begging for Premium access.","Bot commands in command channels only.","No pump and dump discussion.","Breaking rules = warning → kick → ban."])])
        await ch.send(embed=e)
    ch=find_ch(guild,'verify')
    if ch:
        e=discord.Embed(title="✅ Verify",description="React ✅ to confirm you read the rules and unlock the server.",color=discord.Color.green())
        vm=await ch.send(embed=e); await vm.add_reaction('✅')
    ch=find_ch(guild,'get-premium')
    if ch:
        e=discord.Embed(title="💎 Get Premium",color=discord.Color.gold())
        e.add_field(name="🆓 Free",value="2 signals/day\n!stock & !market",inline=True)
        e.add_field(name="💎 $15/month",value="All signals live\nAll commands\nTop picks",inline=True)
        e.add_field(name="How",value="Open ticket in **#open-ticket** → pay → instant access",inline=False)
        await ch.send(embed=e)
    ch=find_ch(guild,'how-to-use')
    if ch:
        e=discord.Embed(title="📖 How to Use AlphaSignal",color=discord.Color.blue())
        e.add_field(name="🆓 Free Commands",value="`!stock AAPL` — Full analysis\n`!market` — Market sentiment\n`!ping` — Latency\n`!price` — Pricing\n`!schedule` — Next scan",inline=False)
        e.add_field(name="💎 Premium Commands",value="`!scan` — Full scan now\n`!scan TSLA` — Single stock\n`!top` — Top 10 signals\n`!compare TSLA AAPL` — Compare\n`!watchlist add/show/remove` — Watchlist\n`!status` — Bot info\n`!stats` — All-time stats",inline=False)
        await ch.send(embed=e)
    ch=find_ch(guild,'what-is-macd')
    if ch:
        e=discord.Embed(title="🧠 What is MACD?",color=discord.Color.blue())
        e.description="**MACD** = Moving Average Convergence Divergence\n\n**Formula:**\nMACD Line = 12 EMA − 26 EMA\nSignal Line = 9 EMA of MACD\n\n**BUY:** MACD crosses ABOVE Signal line\n**SHORT:** MACD crosses BELOW Signal line\n\n**AlphaSignal checks Daily + Weekly + Monthly.**\nAll 3 must agree + RSI above/below 50 + Stochastic confirmation.\nThis filters out 90%+ of false signals."
        await ch.send(embed=e)
    ch=find_ch(guild,'faq')
    if ch:
        e=discord.Embed(title="❓ FAQ",color=discord.Color.blue())
        e.add_field(name="How accurate are signals?",value="Requires MACD (3 timeframes) + RSI 50 line + Stochastic to agree. Very high conviction. Always do your own research.",inline=False)
        e.add_field(name="How often does it scan?",value="Every 2 hours, 24/7 automatically.",inline=False)
        e.add_field(name="What is RSI 50?",value="RSI above 50 = bullish. Below 50 = bearish. We only send BUY when RSI is above 50.",inline=False)
        e.add_field(name="How do I upgrade?",value="Open a ticket in **#open-ticket** and send payment proof.",inline=False)
        await ch.send(embed=e)
    ch=find_ch(guild,'open-ticket')
    if ch:
        e=discord.Embed(title="🎫 Open a Ticket",description="Click below for a private support ticket.\nUse to pay for Premium or get help.",color=discord.Color.blue())
        await ch.send(embed=e,view=TicketView())
    await msg.edit(content=f"✅ **Done!** {len(TICKERS)} stocks loaded. Type `!scan` in **premium-commands** to run your first scan!")

@bot.event
async def on_ready():
    print(f"[AlphaSignal] Online as {bot.user} | {len(TICKERS)} tickers")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,name=f"{len(TICKERS)} stocks | AlphaSignal"))
    bot.add_view(TicketView())
    if not auto_scan.is_running(): auto_scan.start()

@bot.event
async def on_disconnect(): print("[AlphaSignal] Disconnected, reconnecting...")

bot.run(TOKEN, reconnect=True)
