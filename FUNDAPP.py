#################### base ####################

# Importing
import pandas as pd
from PIL import Image
import requests
from io import BytesIO

# Parsing
import tiingo as tiingo
from tiingo import TiingoClient
import yfinance as yf

# Visuals
from matplotlib.backends.backend_agg import RendererAgg
_lock = RendererAgg.lock
import matplotlib.pyplot as plt
import matplotlib.dates as dts
import mplcyberpunk

# Streamlit
import streamlit as st

# TIINGO API setup
TIINGO_API_KEY = "c5effc453b818a3236c1d8636fd954344a14ddb9"
config = {
    'api_key': TIINGO_API_KEY,
    'session': True
}
client = TiingoClient(config)

# Navigation 
dow30 = ['AXP', 'AMGN', 'AAPL', 'BA', 'CAT', 'CSCO', 'CVX', 'GS', 'HD',
         'HON', 'IBM', 'INTC', 'JNJ', 'KO', 'JPM', 'MCD', 'MMM', 'MRK',
         'MSFT','NKE', 'PG', 'TRV', 'UNH', 'CRM', 'VZ', 'V', 'WBA',
         'WMT', 'DIS', 'DOW']
incomeStatemententry = ['revenue',
                     'costRev',
                     'grossProfit',
                     'rnd',
                     'sga',
                     'opinc',
                     'opex',
                     'ebit',
                     'ebitda',
                     'intexp',
                     'taxExp',
                     'netinc']
balanceSheetentry = ['cashAndEq',
                    'investmentsCurrent',
                 'acctRec',
                 'inventory',
                 'assetsCurrent',
                 'ppeq',
                  'assetsNonCurrent',
                  'totalAssets',
                 'debtCurrent',
                 'debtNonCurrent',
                  'liabilitiesCurrent',
                 'liabilitiesNonCurrent',
                 'totalLiabilities',
                 'equity']
cashFlowentry= ['depamor',
              'sbcomp',
             'ncfo',
             'capex',
              'businessAcqDisposals',
             'ncfi',
             'payDiv',
              'issrepayEquity',
             'issrepayDebt',
              'investmentsAcqDisposals',
              'ncff',
              'ncfx', 'ncf'
             ]
shares = ['sharesBasic', 'shareswaDil', 'shareswa']

#################### interface ####################

# Sidebar
ticker = st.sidebar.selectbox('Компании из Промышленного индекса Доу Джонса:', dow30)
response = requests.get(yf.Ticker(ticker).info['logo_url'])
img = Image.open(BytesIO(response.content))
st.sidebar.image(img)
st.sidebar.title('Abount')
st.sidebar.write(yf.Ticker(ticker).info['longBusinessSummary'])

# Main
st.header(yf.Ticker(ticker).info['longName'])
st.table(pd.DataFrame.from_dict({'Exchange':[yf.Ticker(ticker).info['exchange']],
          'Industry':[yf.Ticker(ticker).info['industry']],
          'Last Close':[yf.Ticker(ticker).info['previousClose']]},
                                orient='index', columns = ['']))

#################### get data ####################

fs = pd.DataFrame(client.get_fundamentals_statements(ticker)).set_index('date').sort_index()
fs_type = ['overview', 'incomeStatement', 'cashFlow', 'balanceSheet']
fsA = fs[fs['quarter'] == 0]
fsQ = fs[fs['quarter'] > 0]
fsQ_index = fsQ.index
fsA_index = fsA.index

# QUATERLY STATEMENTS
l01 = []
for i in fsQ.iloc[:, 0]:
        x = pd.DataFrame(i['overview']).set_index('dataCode')
        l01.append(x)
overview = pd.concat(l01, axis = 1, ignore_index=False)
overview.columns = fsQ_index
l02 = []
for i in fsQ.iloc[:, 0]:
        x = pd.DataFrame(i['incomeStatement']).set_index('dataCode')
        l02.append(x)
incomeStatement = pd.concat(l02, axis = 1, ignore_index=False)
incomeStatement.columns = fsQ_index
l03 = []
for i in fsQ.iloc[:, 0]:
        x = pd.DataFrame(i['cashFlow']).set_index('dataCode')
        l03.append(x)
cashFlow = pd.concat(l03, axis = 1, ignore_index=False)
cashFlow.columns = fsQ_index
l04 = []
for i in fsQ.iloc[:, 0]:
        x = pd.DataFrame(i['balanceSheet']).set_index('dataCode')
        l04.append(x)
balanceSheet = pd.concat(l04, axis = 1, ignore_index=False)
balanceSheet.columns = fsQ_index

# consolidated QUATERLY STATEMENTS DataFrame
fsQcons = pd.concat([overview, incomeStatement, cashFlow, balanceSheet], axis = 0)
fsQcons.columns = pd.to_datetime(fsQcons.columns)

# Suplimentary calc
netMargin = fsQcons.loc['netinc'] / fsQcons.loc['revenue']
ebitda = fsQcons.loc['ebitda']
ebitda12m = ebitda.rolling(window = 4).sum()
eps = fsQcons.loc['eps']
eps12m = eps.rolling(window = 4).sum()
div = fsQcons.loc['payDiv']
div12m = div.rolling(window = 4).sum()
if (yf.Ticker(ticker).info['sector'] == 'Financial Services'):
    net_debt = 0
else:
    net_debt = fsQcons.loc['debtCurrent'] + fsQcons.loc['debtNonCurrent'] - fsQcons.loc['cashAndEq'] - fsQcons.loc['investmentsCurrent']
net_debt_ebitda = net_debt / ebitda12m
payout = fsQcons.loc['payDiv'] / fsQcons.loc['netinc']
multiples = pd.DataFrame(client.get_fundamentals_daily(ticker)).set_index('date').dropna()
multiples.index = pd.to_datetime(multiples.index, format = '%Y-%m-%d')

#################### plotting ####################

plt.style.use("cyberpunk")
fmt_quaterly = dts.MonthLocator(interval=3)

# Market Cap
fig, ax = plt.subplots()
ax.plot(multiples['marketCap'] / 10**9,
        color = 'blue')
ax.set_title('Market Cap',fontsize='x-large', fontweight='light')
ax.set_ylabel('bn USD',fontsize='large', fontweight='light')
ax.xaxis.set_major_locator(fmt_quaterly)
ax.annotate("{:.2f}млрд".format(multiples['marketCap'][-1] / 10**9),
            (fsQcons.columns[-1], multiples['marketCap'][-1] / 10**9),
            textcoords="offset pixels",
            xytext=(180,20),
            ha='center')
mplcyberpunk.add_glow_effects()
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.pyplot(fig)

# Analyst raiting
analysts_data = yf.Ticker(ticker).recommendations.drop_duplicates(subset = 'Firm', keep = 'last').sort_index()[['Firm', 'To Grade']]
analysts_data = analysts_data.loc[analysts_data.index > '2020']
analysts_data.index = analysts_data.index.strftime(date_format = '%d/%m/%Y')
analysts_data = analysts_data.rename(columns = {'Firm':'Инвестиционная компания','To Grade':'Оценка'})
analysts_data.index = analysts_data.index.rename('Дата')
anr = analysts_data.pivot_table(index = 'Оценка', aggfunc = 'size')
anr = pd.DataFrame(anr.rename(''))

st.header('Рейтинг аналитиков')
st.dataframe(analysts_data)
st.dataframe(anr)

# Inst holders
inst = yf.Ticker(ticker).institutional_holders.dropna().set_index('Holder').sort_values(['% Out'], ascending = False)['% Out']*100

st.header('Крупнейшие держатели')
st.table(inst)

# Revenue
fig, ax = plt.subplots()
ax.plot(fsQcons.columns,
        fsQcons.loc['revenue'] / 10**6,
        marker = 's',
        color = 'yellow')
ax.set_title('Выручка',fontsize='x-large', fontweight='light')
ax.set_ylabel('млн долл',fontsize='large', fontweight='light')
ax.annotate("${:.2f}".format(fsQcons.loc['revenue'][-1] / 10**6),
            (fsQcons.columns[-1],fsQcons.loc['revenue'][-1] / 10**6),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
mplcyberpunk.add_glow_effects()
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.header('Профиль роста: Выручка')
st.pyplot(fig)

# Revenue QoQ
fig, ax = plt.subplots()
ax.plot(fsQcons.columns,
        fsQcons.loc['revenueQoQ']*100,
        marker = 's',
        color = 'yellow')
ax.set_title('Динамика выручки г/г',fontsize='x-large', fontweight='light')
ax.set_ylabel('Изменение, %',fontsize='large', fontweight='light')
ax.annotate("{:.2f}%".format(fsQcons.loc['revenueQoQ'][-1]*100),
            (fsQcons.columns[-1],fsQcons.loc['revenueQoQ'][-1]*100),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
mplcyberpunk.add_glow_effects()
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.pyplot(fig)

# EBITDA
fig, ax = plt.subplots()
ax.plot(fsQcons.columns,
        fsQcons.loc['ebitda'] / 10**6,
        marker = 's',
        color = 'yellow')
ax.set_title('EBITDA',fontsize='x-large', fontweight='light')
ax.set_ylabel('млн долл',fontsize='large', fontweight='light')
ax.annotate("${:.2f}".format(fsQcons.loc['ebitda'][-1] / 10**6),
            (fsQcons.columns[-1],fsQcons.loc['ebitda'][-1] / 10**6),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
mplcyberpunk.add_glow_effects()
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.header('Профиль роста: EBITDA')
st.pyplot(fig)

# Earnings
fig, ax = plt.subplots()
ax.plot(fsQcons.columns,
        fsQcons.loc['netinc'] / 10**6,
        marker = 's',
        color = 'yellow')
ax.set_title('Чистая прибыль',fontsize='x-large', fontweight='light')
ax.set_ylabel('млн долл',fontsize='large', fontweight='light')
ax.annotate("${:.2f}".format(fsQcons.loc['netinc'][-1] / 10**6),
            (fsQcons.columns[-1],fsQcons.loc['netinc'][-1] / 10**6),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
mplcyberpunk.add_glow_effects()
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.header('Профиль роста: Прибыль')
st.pyplot(fig)

fig, ax = plt.subplots()
ax.plot(fsQcons.columns,
        fsQcons.loc['eps'],
        marker = 's',
        color = 'yellow')
ax.set_title('Прибыль на акцию',fontsize='x-large', fontweight='light')
ax.set_ylabel('долл на акцию',fontsize='large', fontweight='light')
ax.annotate("${:.0f}".format(fsQcons.loc['eps'][-1]),
            (fsQcons.columns[-1],fsQcons.loc['eps'][-1]),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
mplcyberpunk.add_glow_effects()
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.pyplot(fig)

fig, ax = plt.subplots()
ax.plot(fsQcons.columns,
        fsQcons.loc['epsQoQ']*100,
        marker = 's',
        color = 'yellow')
ax.set_title('Динамика прибыли на акцию г/г',fontsize='x-large', fontweight='light')
ax.set_ylabel('Изменение, %',fontsize='large', fontweight='light')
ax.annotate("{:.2f}%".format(fsQcons.loc['epsQoQ'][-1]*100),
            (fsQcons.columns[-1],fsQcons.loc['epsQoQ'][-1]*100),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
mplcyberpunk.add_glow_effects()
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.pyplot(fig)

# Debt
if (yf.Ticker(ticker).info['sector'] == 'Financial Services'):
    fig, ax = plt.subplots()
else:
    fig, ax = plt.subplots()
    ax.bar(fsQcons.columns,
           net_debt / 10 ** 6,
           width=60,
           color='yellow')
    ax.set_title('Чистый долг', fontsize='x-large', fontweight='light')
    ax.set_ylabel('млн долл', fontsize='large', fontweight='light')
    ax.xaxis_date()
    ax.annotate("${:.2f}".format(net_debt[-1] / 10 ** 6),
                (fsQcons.columns[-1], net_debt[-1] / 10 ** 6),
                textcoords="offset pixels",
                xytext=(0, 10),
                ha='center')
    plt.xticks(rotation='vertical')
    plt.grid(False)
    st.header('Финансовое положение: Долг')
    st.pyplot(fig)

# Debt / EBITDA
if (yf.Ticker(ticker).info['sector'] == 'Financial Services'):
    fig, ax = plt.subplots()
else:
    fig, ax = plt.subplots()
    ax.bar(fsQcons.columns,
       net_debt_ebitda,
       width = 60,
       color = 'yellow')
    ax.set_title('Чистый долг / 12M EBITDA',fontsize='x-large', fontweight='light')
    ax.set_ylabel('коэффициент X',fontsize='large', fontweight='light')
    ax.annotate("{:.2f}X".format(net_debt_ebitda[-1]),
            (fsQcons.columns[-1],net_debt_ebitda[-1]),
            textcoords="offset pixels",
            xytext=(0,10),
            ha='center')
    plt.xticks(rotation = 'vertical')
    plt.grid(False)
    st.pyplot(fig)

# CF
plt.plot(fsQcons.loc['ncfo'] / 10**6, color = 'white',  linestyle = ':')
plt.plot(fsQcons.loc['ncfi'] / 10**6, color = 'red', linestyle = ':')
plt.plot(fsQcons.loc['ncff'] / 10**6, color = 'magenta', linestyle = ':')
plt.plot(fsQcons.loc['freeCashFlow'] / 10**6, color = 'yellow', marker = 's')
plt.title('Денежный поток',fontsize='x-large', fontweight='light')
plt.ylabel('млн долл',fontsize='large', fontweight='light')
plt.legend(['Денежный поток от операций',
            'Инвестиционный денежный поток',
            'Финансовый денежный поток',
            'Чистый денежный поток'])
plt.annotate("${:.2f}".format(fsQcons.loc['freeCashFlow'][-1] / 10**6),
            (fsQcons.columns[-1],fsQcons.loc['freeCashFlow'][-1] / 10**6),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.header('Операционная составляющая: Денежный поток')
st.pyplot(fig)

# Suplimentary calc
ebitda12m.index = pd.to_datetime(ebitda12m.index).tz_localize('Etc/UCT')
div12m.index = pd.to_datetime(div12m.index).tz_localize('Etc/UCT')
divs_and_val = pd.concat([multiples[['marketCap','enterpriseVal']], ebitda12m, -div12m], axis = 1, ignore_index=False).dropna() / 10**6
divs_and_val['evebitda'] = divs_and_val['enterpriseVal'] / divs_and_val['ebitda']
divs_and_val['divyield'] = divs_and_val['payDiv'] / divs_and_val['marketCap']

# Margin
fig, (ax1, ax2) = plt.subplots(2, 1)
fig.suptitle('Маржинальность', fontsize='x-large', fontweight='light')
ax1.plot(fsQcons.loc['grossMargin']*100, color = 'yellow',  marker = 's')
ax2.plot(netMargin*100, color = 'yellow', marker = 's')
ax1.set(title = "Валовая маржа",
        ylabel = "%")
ax1.axes.xaxis.set_visible(False)
ax2.set(title = "Маржа по чистой прибыли",
       xlabel = " ",
       ylabel = "%")
ax1.annotate("{:.2f}%".format(fsQcons.loc['grossMargin'][-1]*100),
            (fsQcons.columns[-1],fsQcons.loc['grossMargin'][-1]*100),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
ax2.annotate("{:.2f}%".format(netMargin[-1]*100),
            (fsQcons.columns[-1],netMargin[-1]*100),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
plt.xticks(rotation = 'vertical')
ax1.grid(False)
ax2.grid(False)

st.header('Операционная составляющая: Маржинальность')
st.pyplot(fig)

# Yield and share info
fig, ax = plt.subplots()
ax.bar(fsQcons.columns,
       -fsQcons.loc['payDiv'] / 10**6,
       width = 60,
       color = 'yellow')
ax.set_title('Дивиденды',fontsize='x-large', fontweight='light')
ax.set_ylabel('млн долл',fontsize='large', fontweight='light')
ax.annotate("${:.2f}".format(-fsQcons.loc['payDiv'][-1] / 10**6),
            (fsQcons.columns[-1],-fsQcons.loc['payDiv'][-1] / 10**6),
            textcoords="offset pixels",
            xytext=(0,10),
            ha='center')
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.header('Доходность акционера')
st.pyplot(fig)

fig, ax = plt.subplots()
ax.bar(fsQcons.columns,
       -fsQcons.loc['issrepayEquity'] / 10**6,
       width = 60,
       color = 'yellow')
ax.set_title('Выкуп и выпуск акций',fontsize='x-large', fontweight='light')
ax.set_ylabel('млн долл',fontsize='large', fontweight='light')
ax.annotate("${:.2f}".format(-fsQcons.loc['issrepayEquity'][-1] / 10**6),
            (fsQcons.columns[-1],-fsQcons.loc['issrepayEquity'][-1] / 10**6),
            textcoords="offset pixels",
            xytext=(0,10),
            ha='center')
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.pyplot(fig)

fig, ax = plt.subplots()
ax.plot(divs_and_val.index,
        divs_and_val['divyield']*100,
        marker = 's',
        color = 'yellow')
ax.set_title('Дивидендная доходность за 12М',fontsize='x-large', fontweight='light')
ax.set_ylabel('Доходность, %',fontsize='large', fontweight='light')
ax.annotate("{:.2f}%".format(divs_and_val['divyield'][-1]*100),
            (divs_and_val.index[-1],divs_and_val['divyield'][-1]*100),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
mplcyberpunk.add_glow_effects()
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.pyplot(fig)

# payout
fig, ax = plt.subplots()
ax.plot(payout.index,
        -payout*100,
        marker = 's',
        color = 'yellow')
ax.set_title('Запас прочности:\nдивиденды и выкуп к чистой прибыли',fontsize='x-large', fontweight='light')
ax.set_ylabel('%',fontsize='large', fontweight='light')
ax.annotate("{:.2f}%".format(-payout[-1]*100),
            (fsQcons.columns[-1],-payout[-1]*100),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
mplcyberpunk.add_glow_effects()
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.pyplot(fig)

plt.plot(fsQcons.loc['sharesBasic'] / 10**6, color = 'yellow',  marker = 's')
plt.plot(fsQcons.loc['shareswaDil'] / 10**6, color = 'red', linestyle = ':')
plt.plot(fsQcons.loc['shareswa'] / 10**6, color = 'magenta', linestyle = ':')
plt.title('Количество акций в обращении',fontsize='x-large', fontweight='light')
plt.ylabel('млн шт',fontsize='large', fontweight='light')
plt.legend(['Число акций обыкновенных',
            'Число акций разводненное',
            'Число акций средневзвешенное'])
plt.annotate("{:.0f}млн шт".format(fsQcons.loc['sharesBasic'][-1] / 10**6),
            (fsQcons.columns[-1],fsQcons.loc['sharesBasic'][-1] / 10**6),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.pyplot(fig)

fig, (ax1, ax2) = plt.subplots(2, 1)
fig.suptitle('Доходность', fontsize='x-large', fontweight='light')
ax1.plot(fsQcons.loc['roa']*100, color = 'yellow',  marker = 's')
ax2.plot(fsQcons.loc['roe']*100, color = 'yellow', marker = 's')
ax1.set(title = "ROA",
        ylabel = "%")
ax1.axes.xaxis.set_visible(False)
ax2.set(title = "ROE",
       xlabel = " ",
       ylabel = "%")
ax1.annotate("{:.2f}%".format(fsQcons.loc['roa'][-1]*100),
            (fsQcons.columns[-1],fsQcons.loc['roa'][-1]*100),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
ax2.annotate("{:.2f}%".format(fsQcons.loc['roe'][-1]*100),
            (fsQcons.columns[-1],fsQcons.loc['roe'][-1]*100),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
plt.xticks(rotation = 'vertical')
ax1.grid(False)
ax2.grid(False)

st.pyplot(fig)

# P / E
fig, ax = plt.subplots()
ax.plot(multiples['peRatio'],
        color = 'yellow')
ax.set_title('P / E',fontsize='x-large', fontweight='light')
ax.xaxis.set_major_locator(fmt_quaterly)
ax.annotate("{:.2f}X".format(multiples['peRatio'][-1]),
            (fsQcons.columns[-1], multiples['peRatio'][-1]),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
mplcyberpunk.add_glow_effects()
plt.xticks(rotation = 'vertical')
plt.grid(False)
st.header('Оценка')
st.pyplot(fig)

# P / B
fig, ax = plt.subplots()
ax.plot(multiples['pbRatio'],
        color = 'yellow')
ax.set_title('P / B',fontsize='x-large', fontweight='light')
ax.xaxis.set_major_locator(fmt_quaterly)
ax.annotate("{:.2f}X".format(multiples['pbRatio'][-1]),
            (fsQcons.columns[-1], multiples['pbRatio'][-1]),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='center')
mplcyberpunk.add_glow_effects()
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.pyplot(fig)

# 1YPEG
fig, ax = plt.subplots()
ax.plot(multiples['trailingPEG1Y'],
        color = 'yellow')
ax.set_title('Trailing PEG1Y',fontsize='x-large', fontweight='light')
ax.xaxis.set_major_locator(fmt_quaterly)
ax.annotate("{:.2f}X".format(multiples['trailingPEG1Y'][-1]),
            (fsQcons.columns[-1], multiples['trailingPEG1Y'][-1]),
            textcoords="offset pixels",
            xytext=(100,20),
            ha='left')
plt.xticks(rotation = 'vertical')
plt.grid(False)

st.pyplot(fig)
