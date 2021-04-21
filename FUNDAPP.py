
################## Importing libraries ##################

# Base
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
# Parsing
from tiingo import TiingoClient
import yfinance as yf
# Visuals
import plotly.graph_objs as go
# Streamlit
import streamlit as st

################## Data ##################

# TIINGO API setup
TIINGO_API_KEY = "c5effc453b818a3236c1d8636fd954344a14ddb9"
config = {
    'api_key': TIINGO_API_KEY,
    'session': True
}
client = TiingoClient(config)
# DOW30
dow30 = ['AXP', 'AMGN', 'AAPL', 'BA', 'CAT', 'CSCO', 'CVX', 'GS', 'HD',
         'HON', 'IBM', 'INTC', 'JNJ', 'KO', 'JPM', 'MCD', 'MMM', 'MRK',
         'MSFT','NKE', 'PG', 'TRV', 'UNH', 'CRM', 'VZ', 'V', 'WBA',
         'WMT', 'DIS', 'DOW']
# Tags
incomeStatemententryfull = ['revenue',
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
incomeStatemententryoutflow = ['costRev',
                               'opex',
                               'intexp','taxExp']
incomeStatemententryinflow = ['revenue',
                     'ebitda',
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
cf = ['ncfo', 'ncfi', 'ncff', 'ncf']
growth = ['revenueQoQ', 'epsQoQ']
shares = ['sharesBasic', 'shareswaDil', 'shareswa']
ticker = st.sidebar.selectbox(st.heder('DOW30'), dow30)

# Analyst Data
analysts_data = yf.Ticker(ticker).recommendations.drop_duplicates(subset = 'Firm', keep = 'last').sort_index()[['Firm', 'To Grade']]
analysts_data = analysts_data.loc[analysts_data.index > '2020']
analysts_data.index = analysts_data.index.strftime(date_format = '%d/%m/%Y')
analysts_data = analysts_data.rename(columns = {'Firm':'Инвестиционная компания','To Grade':'Оценка'})
analysts_data.index = analysts_data.index.rename('Дата')
anr = analysts_data.pivot_table(index = 'Оценка', aggfunc = 'size')
anr = pd.DataFrame(anr.rename('')).sort_values('', ascending=False)
inst = yf.Ticker(ticker).institutional_holders.dropna().set_index('Holder').sort_values(['% Out'], ascending = False)['% Out']
# Get Financials
fs = pd.DataFrame(client.get_fundamentals_statements(ticker)).set_index('date').sort_index()
fs_type = ['overview', 'incomeStatement', 'cashFlow', 'balanceSheet']
fsA = fs[fs['quarter'] == 0]
fsQ = fs[fs['quarter'] > 0]
fsQ_index = fsQ.index
fsA_index = fsA.index
# To quaterly statements
# overview DataFrame
l01 = []
for i in fsQ.iloc[:, 0]:
        x = pd.DataFrame(i['overview']).set_index('dataCode')
        l01.append(x)
overview = pd.concat(l01, axis = 1, ignore_index=False)
overview.columns = fsQ_index
# incomeStatement DataFrame
l02 = []
for i in fsQ.iloc[:, 0]:
        x = pd.DataFrame(i['incomeStatement']).set_index('dataCode')
        l02.append(x)
incomeStatement = pd.concat(l02, axis = 1, ignore_index=False)
incomeStatement.columns = fsQ_index
# cashFlow DataFrame
l03 = []
for i in fsQ.iloc[:, 0]:
        x = pd.DataFrame(i['cashFlow']).set_index('dataCode')
        l03.append(x)
cashFlow = pd.concat(l03, axis = 1, ignore_index=False)
cashFlow.columns = fsQ_index
# balanceSheet DataFrame
l04 = []
for i in fsQ.iloc[:, 0]:
        x = pd.DataFrame(i['balanceSheet']).set_index('dataCode')
        l04.append(x)
balanceSheet = pd.concat(l04, axis = 1, ignore_index=False)
balanceSheet.columns = fsQ_index
# consolidated
fsQcons = pd.concat([overview, incomeStatement, cashFlow, balanceSheet], axis = 0)
fsQcons.columns = pd.to_datetime(fsQcons.columns)
# Additional
# 12M rolling
ebitda = fsQcons.loc['ebitda']
ebitda12m = ebitda.rolling(window = 4).sum()
eps = fsQcons.loc['eps']
eps12m = eps.rolling(window = 4).sum()
div = fsQcons.loc['payDiv']
div12m = div.rolling(window = 4).sum()
# Debt
if (yf.Ticker(ticker).info['sector'] == 'Financial Services'):
    net_debt = fsQcons.loc['totalAssets'] - fsQcons.loc['cashAndEq']
else:
    net_debt = fsQcons.loc['debtCurrent'] + fsQcons.loc['debtNonCurrent'] - fsQcons.loc['cashAndEq'] - fsQcons.loc['investmentsCurrent']
# Net Debt / 12M rolling EBITDA
net_debt_ebitda = net_debt / ebitda12m
net_debt_ebitda = net_debt_ebitda.dropna()
# Payout
payout = - fsQcons.loc['payDiv'] / fsQcons.loc['netinc'] * 100
# Multiples and Valuation
multiples = pd.DataFrame(client.get_fundamentals_daily(ticker)).set_index('date').dropna()
multiples.index = pd.to_datetime(multiples.index, format = '%Y-%m-%d')
ebitda12m.index = pd.to_datetime(ebitda12m.index).tz_localize('Etc/UCT')
div12m.index = pd.to_datetime(div12m.index).tz_localize('Etc/UCT')
divs_and_val = pd.concat([multiples[['marketCap','enterpriseVal']], ebitda12m, -div12m], axis = 1, ignore_index=False).dropna() / 10**6
divs_and_val['evebitda'] = divs_and_val['enterpriseVal'] / divs_and_val['ebitda']
divs_and_val['divyield'] = divs_and_val['payDiv'] / divs_and_val['marketCap'] * 100

################## App ##################

# Sidebar
response = requests.get(yf.Ticker(ticker).info['logo_url'])
img = Image.open(BytesIO(response.content))
st.sidebar.image(img)
st.sidebar.header('About')
st.sidebar.write(yf.Ticker(ticker).info['longBusinessSummary'])
# Page
st.title(yf.Ticker(ticker).info['longName'])
data = analysts_data
fig = go.Figure(data=[go.Table(header=dict(values=['Date', 'Investment Company', 'Recommendation'], line_color= 'white',
                                           fill_color='rgb(8, 81, 156)', font=dict(family='Arial', color='white', size=15)),
                 cells=dict(values=[
                     list(data.index),
                     list(data.iloc[:,0]),
                     list(data.iloc[:,1])
                 ],  line_color= 'white', fill_color='white' , font=dict(family='Arial', color='rgb(8, 81, 156)', size=15)))
                     ])
st.header('Analysts Recommendation')
st.plotly_chart(fig)

data = anr
fig = go.Figure(data=[go.Table(header=dict(values=['Recommendation', 'Number'], line_color= 'white',
                                           fill_color='rgb(8, 81, 156)', font=dict(family='Arial', color='white', size=15)),
                 cells=dict(values=[
                     list(data.index),
                     list(data.iloc[:,0])
                 ],  line_color= 'white', fill_color='white' , font=dict(family='Arial', color='rgb(8, 81, 156)', size=15)))
                     ])
st.plotly_chart(fig)

data = inst*100
fig = go.Figure(data=[go.Table(header=dict(values=['Holder', '% Out'], line_color= 'white',
                                           fill_color='rgb(8, 81, 156)', font=dict(family='Arial', color='white', size=15)),
                 cells=dict(values=[
                     list(data.index),
                     list(data)
                 ],  line_color= 'white', fill_color='white' , font=dict(family='Arial', color='rgb(8, 81, 156)', size=15)))
                     ])
st.header('Top Holders')
st.plotly_chart(fig)

title = 'Market Cap & Enterprise Value'
labels = ['MC', 'EV']
colors = ['rgb(115,115,115)', 'rgb(49,130,189)']

mode_size = [8, 12]
line_size = [2, 4]

data = multiples[['marketCap', 'enterpriseVal']]

fig = go.Figure()

for i in range(len(data.columns)):
    fig.add_trace(go.Scatter(x=data.index, y=data.iloc[:,i], mode='lines',
                             line = dict(color=colors[i], width=line_size[i], shape='spline'),
                             name=labels[i], hoverlabel = dict(bgcolor = colors[i], font = dict(family='Arial', size=15, color='white'),
                                         align = 'left', namelength = 0), hoverinfo = 'y',
                            ))
    fig.add_trace(go.Scatter(x=[data.index[0], data.index[-1]],
                              y=[data.iloc[:,i][0], data.iloc[:,i][-1]],
                              mode='markers', marker=dict(color=colors[i], size=mode_size[i]),
                             hoverlabel = dict(bgcolor = colors[i], font = dict(family='Arial', size=15, color='white'),
                                         align = 'left', namelength = 0), hoverinfo = 'none'
                            ))
    fig.add_annotation(x=0.05, y=data.iloc[:,i][0], xref='paper', xanchor='right', yanchor='middle',
                       text=labels[i], font=dict(family='Arial', size=16), showarrow =False)
    fig.add_annotation(x=0.95, y=data.iloc[:,i][-1], xref='paper',
                                  xanchor='left', yanchor='middle',
                                  text='{:.2f}B'.format(data.iloc[:,i][-1] / 10**9),
                                  font=dict(family='Arial', size=16), showarrow =False)

fig.update_layout(xaxis=dict(showline=True, showgrid=False, showticklabels=True, linecolor='rgb(204, 204, 204)',
                             linewidth=2, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                  yaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=False), showlegend=False,
                  plot_bgcolor='white', title = dict(x = 0.5, text = title, font = dict(family='Arial', size=28, color='black')))
st.header('Fundamentals')
st.plotly_chart(fig)

title = 'Income Statement: Income Entries'
labels = ['Revenue', 'EBITDA', 'Net Income']
colors = ['rgb(36,36,36)', 'rgb(115,115,115)', 'rgb(49,130,189)']


mode_size = [8, 8, 12]
line_size = [2, 2, 4]

data = fsQcons.loc[incomeStatemententryinflow]

fig = go.Figure()

for i in range(len(data.index)):
    fig.add_trace(go.Scatter(x=data.columns, y=data.iloc[i], mode='lines',
                             line = dict(color=colors[i], width=line_size[i], shape='spline'),
                             name=labels[i], hoverlabel = dict(bgcolor = colors[i], font = dict(family='Arial', size=15, color='white'),
                                         align = 'left', namelength = 0), hoverinfo = 'y',
                            ))
    fig.add_trace(go.Scatter(x=[data.columns[0], data.columns[-1]],
                              y=[data.iloc[i][0], data.iloc[i][-1]],
                              mode='markers', marker=dict(color=colors[i], size=mode_size[i]),
                             hoverlabel = dict(bgcolor = colors[i], font = dict(family='Arial', size=15, color='white'),
                                         align = 'left', namelength = 0), hoverinfo = 'none'
                            ))
    fig.add_annotation(x=0.05, y=data.iloc[i][0], xref='paper', xanchor='right', yanchor='middle',
                       text=labels[i], font=dict(family='Arial', size=16), showarrow =False)
    fig.add_annotation(x=0.95, y=data.iloc[i][-1], xref='paper',
                                  xanchor='left', yanchor='middle',
                                  text='{:.2f}B'.format(data.iloc[i][-1] / 10**9),
                                  font=dict(family='Arial', size=16), showarrow =False)

fig.update_layout(xaxis=dict(showline=True, showgrid=False, showticklabels=True, linecolor='rgb(204, 204, 204)',
                             linewidth=2, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                  yaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=False), showlegend=False,
                  plot_bgcolor='white', title = dict(x = 0.5, text = title, font = dict(family='Arial', size=28, color='black')))
st.plotly_chart(fig)

title = 'Income Statement: Expenses'
labels = ['Cost of Revenue', 'OPEX', 'Interest', 'Tax']
colors = ['rgb(49,130,189)', 'rgb(189,189,189)', 'rgb(36,36,36)', 'rgb(115,115,115)']


mode_size = [12, 8, 8, 8]
line_size = [4, 2, 2, 2]

data = fsQcons.loc[incomeStatemententryoutflow]

fig = go.Figure()

for i in range(len(data.index)):
    fig.add_trace(go.Scatter(x=data.columns, y=data.iloc[i], mode='lines',
                             line = dict(color=colors[i], width=line_size[i], shape='spline'),
                             name=labels[i], hoverlabel = dict(bgcolor = colors[i],
                                                               font = dict(family='Arial', size=15, color='white'),
                                                               align = 'left', namelength = 0), hoverinfo = 'y'))
    fig.add_trace(go.Scatter(x=[data.columns[0], data.columns[-1]],
                              y=[data.iloc[i][0], data.iloc[i][-1]],
                              mode='markers', marker=dict(color=colors[i], size=mode_size[i]),
                             hoverlabel = dict(bgcolor = colors[i], font = dict(family='Arial', size=15, color='white'),
                                         align = 'left', namelength = 0), hoverinfo = 'none'
                            ))
    fig.add_annotation(x=0.05, y=data.iloc[i][0], xref='paper', xanchor='right', yanchor='middle',
                       text=labels[i], font=dict(family='Arial', size=16), showarrow =False)
    fig.add_annotation(x=0.95, y=data.iloc[i][-1], xref='paper',
                                  xanchor='left', yanchor='middle',
                                  text='{:.2f}B'.format(data.iloc[i][-1] / 10**9),
                                  font=dict(family='Arial', size=16), showarrow =False)

fig.update_layout(xaxis=dict(showline=True, showgrid=False, showticklabels=True, linecolor='rgb(204, 204, 204)',
                             linewidth=2, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                  yaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=False), showlegend=False,
                  plot_bgcolor='white', title = dict(x = 0.5, text = title, font = dict(family='Arial', size=28, color='black')))
st.plotly_chart(fig)

title = 'Cash Flow'
labels = ['Operating', 'Investing', 'Financing', 'Net']
colors = ['rgb(189,189,189)', 'rgb(36,36,36)', 'rgb(115,115,115)', 'rgb(49,130,189)']


mode_size = [8, 8, 8, 12]
line_size = [2, 2, 2, 4]

data = fsQcons.loc[cf]

fig = go.Figure()

for i in range(len(data.index)):
    fig.add_trace(go.Scatter(x=data.columns, y=data.iloc[i], mode='lines',
                             line = dict(color=colors[i], width=line_size[i], shape='spline'),
                             name=labels[i], hoverlabel = dict(bgcolor = colors[i], font = dict(family='Arial', size=15, color='white'),
                                         align = 'left', namelength = 0), hoverinfo = 'y',
                            ))
    fig.add_trace(go.Scatter(x=[data.columns[0], data.columns[-1]],
                              y=[data.iloc[i][0], data.iloc[i][-1]],
                              mode='markers', marker=dict(color=colors[i], size=mode_size[i]),
                             hoverlabel = dict(bgcolor = colors[i], font = dict(family='Arial', size=15, color='white'),
                                         align = 'left', namelength = 0), hoverinfo = 'none'
                            ))
    fig.add_annotation(x=0.05, y=data.iloc[i][0], xref='paper', xanchor='right', yanchor='middle',
                       text=labels[i], font=dict(family='Arial', size=16), showarrow =False)
    fig.add_annotation(x=0.95, y=data.iloc[i][-1], xref='paper',
                                  xanchor='left', yanchor='middle',
                                  text='{:.2f}B'.format(data.iloc[i][-1] / 10**9),
                                  font=dict(family='Arial', size=16), showarrow =False)

fig.update_layout(xaxis=dict(showline=True, showgrid=False, showticklabels=True, linecolor='rgb(204, 204, 204)',
                             linewidth=2, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                  yaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=False), showlegend=False,
                  plot_bgcolor='white', title = dict(x = 0.5, text = title, font = dict(family='Arial', size=28, color='black')))
st.plotly_chart(fig)

title = 'Growth'
labels = ['Revenue', 'Earnings']
colors = ['rgb(49,130,189)', 'rgb(189,189,189)']


mode_size = [12, 8]
line_size = [4, 2]

data = fsQcons.loc[growth]

fig = go.Figure()

for i in range(len(data.index)):
    fig.add_trace(go.Scatter(x=data.columns, y=data.iloc[i], mode='lines',
                             line = dict(color=colors[i], width=line_size[i], shape='spline'),
                             name=labels[i], hoverlabel = dict(bgcolor = colors[i],
                                                               font = dict(family='Arial', size=15, color='white'),
                                                               align = 'left', namelength = 0), hoverinfo = 'y'))
    fig.add_trace(go.Scatter(x=[data.columns[0], data.columns[-1]],
                              y=[data.iloc[i][0], data.iloc[i][-1]],
                              mode='markers', marker=dict(color=colors[i], size=mode_size[i]),
                             hoverlabel = dict(bgcolor = colors[i], font = dict(family='Arial', size=15, color='white'),
                                         align = 'left', namelength = 0), hoverinfo = 'none'
                            ))
    fig.add_annotation(x=0.05, y=data.iloc[i][0], xref='paper', xanchor='right', yanchor='middle',
                       text=labels[i], font=dict(family='Arial', size=16), showarrow =False)
    fig.add_annotation(x=0.95, y=data.iloc[i][-1], xref='paper',
                                  xanchor='left', yanchor='middle',
                                  text='{:.2f}%'.format(data.iloc[i][-1]*100),
                                  font=dict(family='Arial', size=16), showarrow =False)

fig.update_layout(xaxis=dict(showline=True, showgrid=False, showticklabels=True, linecolor='rgb(204, 204, 204)',
                             linewidth=2, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                  yaxis=dict(showgrid=False, zeroline=True, showline=False, showticklabels=False), showlegend=False,
                  plot_bgcolor='white', title = dict(x = 0.5, text = title, font = dict(family='Arial', size=28, color='black')))
st.plotly_chart(fig)

title = 'Shares Info'
labels = ['Basic', 'Dilluted', 'Weighted Avg']
colors = ['rgb(36,36,36)', 'rgb(115,115,115)', 'rgb(49,130,189)']


mode_size = [8, 8, 12]
line_size = [2, 2, 4]

data = fsQcons.loc[shares]

fig = go.Figure()

for i in range(len(data.index)):
    fig.add_trace(go.Scatter(x=data.columns, y=data.iloc[i], mode='lines',
                             line = dict(color=colors[i], width=line_size[i], shape='spline'),
                             name=labels[i], hoverlabel = dict(bgcolor = colors[i], font = dict(family='Arial', size=15, color='white'),
                                         align = 'left', namelength = 0), hoverinfo = 'y',
                            ))
    fig.add_trace(go.Scatter(x=[data.columns[0], data.columns[-1]],
                              y=[data.iloc[i][0], data.iloc[i][-1]],
                              mode='markers', marker=dict(color=colors[i], size=mode_size[i]),
                             hoverlabel = dict(bgcolor = colors[i], font = dict(family='Arial', size=15, color='white'),
                                         align = 'left', namelength = 0), hoverinfo = 'none'
                            ))
    fig.add_annotation(x=0.05, y=data.iloc[i][0], xref='paper', xanchor='right', yanchor='middle',
                       text=labels[i], font=dict(family='Arial', size=16), showarrow =False)
    fig.add_annotation(x=0.95, y=data.iloc[i][-1], xref='paper',
                                  xanchor='left', yanchor='middle',
                                  text='{:.0f}M'.format(data.iloc[i][-1] / 10**6),
                                  font=dict(family='Arial', size=16), showarrow =False)

fig.update_layout(xaxis=dict(showline=True, showgrid=False, showticklabels=True, linecolor='rgb(204, 204, 204)',
                             linewidth=2, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                  yaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=False), showlegend=False,
                  plot_bgcolor='white', title = dict(x = 0.5, text = title, font = dict(family='Arial', size=28, color='black')))
st.plotly_chart(fig)

title = 'Earnings per Share'
colors = 'rgb(49,130,189)'

data = fsQcons.loc['eps']

fig = go.Figure()
fig.add_trace(go.Bar(x = data.index, y = data.values, marker_color = colors,
                     hoverlabel = dict(bgcolor = colors, font = dict(family='Arial', size=15, color='white'),
                                       align = 'left', namelength = 0), hoverinfo = 'y'))
fig.update_layout(xaxis=dict(showticklabels=True, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                  yaxis=dict(showgrid=False, showline=False, showticklabels=False), showlegend=False,
                  plot_bgcolor='white', title = dict(x = 0.5, text = title, font = dict(family='Arial', size=28, color='black')))

st.plotly_chart(fig)

title = 'Dividends and Equity Operations'
labels = ['Dividends', 'Buyback and Issuance']
colors = ['rgb(49,130,189)', 'rgb(115,115,115)']

data = -fsQcons.loc[['payDiv', 'issrepayEquity']] / 10 ** 9

fig = go.Figure(data=[
    go.Bar(x=data.columns, y=data.iloc[0], name=labels[0], marker_color=colors[0],
           hoverlabel=dict(bgcolor=colors[0], font=dict(family='Arial', size=15, color='white'),
                           align='left', namelength=0), hoverinfo='y'),
    go.Bar(x=data.columns, y=data.iloc[1], name=labels[1], marker_color=colors[1],
           hoverlabel=dict(bgcolor=colors[1], font=dict(family='Arial', size=15, color='white'),
                           align='left', namelength=0), hoverinfo='y')])

fig.update_layout(barmode='group')
fig.update_layout(
    xaxis=dict(showticklabels=True, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
    yaxis=dict(showgrid=False, showline=False, showticklabels=False), showlegend=True,
    plot_bgcolor='white',
    title=dict(x=0.5, text=title, font=dict(family='Arial', size=28, color='black')),
    legend=dict(x=0, y=1.0))
st.plotly_chart(fig)

title = 'Dividend Payout'
colors = 'rgb(49,130,189)'

data = payout

fig = go.Figure()
fig.add_trace(go.Bar(x = data.index, y = data.values, marker_color = colors,
                     hoverlabel = dict(bgcolor = colors, font = dict(family='Arial', size=15, color='white'),
                                       align = 'left', namelength = 0), hoverinfo = 'y'))
fig.update_layout(xaxis=dict(showticklabels=True, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                  yaxis=dict(showgrid=False, showline=False, showticklabels=False), showlegend=False,
                  plot_bgcolor='white', title = dict(x = 0.5, text = title, font = dict(family='Arial', size=28, color='black')))

st.plotly_chart(fig)

title = 'Dividend Yield'
colors = 'rgb(49,130,189)'

data = divs_and_val['divyield']

fig = go.Figure()
fig.add_trace(go.Bar(x = data.index, y = data.values, marker_color = colors,
                     hoverlabel = dict(bgcolor = colors, font = dict(family='Arial', size=15, color='white'),
                                       align = 'left', namelength = 0), hoverinfo = 'y'))
fig.update_layout(xaxis=dict(showticklabels=True, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                  yaxis=dict(showgrid=False, showline=False, showticklabels=False), showlegend=False,
                  plot_bgcolor='white', title = dict(x = 0.5, text = title, font = dict(family='Arial', size=28, color='black')))

st.plotly_chart(fig)

title = 'Return'
labels = ['ROA', 'ROE']
colors = ['rgb(49,130,189)', 'rgb(189,189,189)']


mode_size = [12, 8]
line_size = [4, 2]

data = fsQcons.loc[['roa', 'roe']]

fig = go.Figure()

for i in range(len(data.index)):
    fig.add_trace(go.Scatter(x=data.columns, y=data.iloc[i], mode='lines',
                             line = dict(color=colors[i], width=line_size[i], shape='spline'),
                             name=labels[i], hoverlabel = dict(bgcolor = colors[i],
                                                               font = dict(family='Arial', size=15, color='white'),
                                                               align = 'left', namelength = 0), hoverinfo = 'y'))
    fig.add_trace(go.Scatter(x=[data.columns[0], data.columns[-1]],
                              y=[data.iloc[i][0], data.iloc[i][-1]],
                              mode='markers', marker=dict(color=colors[i], size=mode_size[i]),
                             hoverlabel = dict(bgcolor = colors[i], font = dict(family='Arial', size=15, color='white'),
                                         align = 'left', namelength = 0), hoverinfo = 'none'
                            ))
    fig.add_annotation(x=0.05, y=data.iloc[i][0], xref='paper', xanchor='right', yanchor='middle',
                       text=labels[i], font=dict(family='Arial', size=16), showarrow =False)
    fig.add_annotation(x=0.95, y=data.iloc[i][-1], xref='paper',
                                  xanchor='left', yanchor='middle',
                                  text='{:.2f}%'.format(data.iloc[i][-1]*100),
                                  font=dict(family='Arial', size=16), showarrow =False)

fig.update_layout(xaxis=dict(showline=True, showgrid=False, showticklabels=True, linecolor='rgb(204, 204, 204)',
                             linewidth=2, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                  yaxis=dict(showgrid=False, zeroline=True, showline=False, showticklabels=False), showlegend=False,
                  plot_bgcolor='white', title = dict(x = 0.5, text = title, font = dict(family='Arial', size=28, color='black')))
st.plotly_chart(fig)

title = 'Net Debt'
colors = 'rgb(49,130,189)'

data = net_debt

fig = go.Figure()
fig.add_trace(go.Bar(x = data.index, y = data.values, marker_color = colors,
                     hoverlabel = dict(bgcolor = colors, font = dict(family='Arial', size=15, color='white'),
                                       align = 'left', namelength = 0), hoverinfo = 'y'))
fig.update_layout(xaxis=dict(showticklabels=True, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                  yaxis=dict(showgrid=False, showline=False, showticklabels=False), showlegend=False,
                  plot_bgcolor='white', title = dict(x = 0.5, text = title, font = dict(family='Arial', size=28, color='black')))

st.plotly_chart(fig)

title = 'Net Debt / 12M EBITDA'
colors = 'rgb(49,130,189)'

data = net_debt_ebitda

fig = go.Figure()
fig.add_trace(go.Bar(x = data.index, y = data.values, marker_color = colors,
                     hoverlabel = dict(bgcolor = colors, font = dict(family='Arial', size=15, color='white'),
                                       align = 'left', namelength = 0), hoverinfo = 'y'))
fig.update_layout(xaxis=dict(showticklabels=True, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                  yaxis=dict(showgrid=False, showline=False, showticklabels=False), showlegend=False,
                  plot_bgcolor='white', title = dict(x = 0.5, text = title, font = dict(family='Arial', size=28, color='black')))

st.plotly_chart(fig)

title = 'PB & PE'
labels = ['PB', 'PE']
colors = ['rgb(115,115,115)', 'rgb(49,130,189)']


mode_size = [8, 12]
line_size = [2, 4]

data = multiples[['pbRatio', 'peRatio']]

fig = go.Figure()

for i in range(len(data.columns)):
    fig.add_trace(go.Scatter(x=data.index, y=data.iloc[:,i], mode='lines',
                             line = dict(color=colors[i], width=line_size[i], shape='spline'),
                             name=labels[i], hoverlabel = dict(bgcolor = colors[i], font = dict(family='Arial', size=15, color='white'),
                                         align = 'left', namelength = 0), hoverinfo = 'y',
                            ))
    fig.add_trace(go.Scatter(x=[data.index[0], data.index[-1]],
                              y=[data.iloc[:,i][0], data.iloc[:,i][-1]],
                              mode='markers', marker=dict(color=colors[i], size=mode_size[i]),
                             hoverlabel = dict(bgcolor = colors[i], font = dict(family='Arial', size=15, color='white'),
                                         align = 'left', namelength = 0), hoverinfo = 'none'
                            ))
    fig.add_annotation(x=0.05, y=data.iloc[:,i][0], xref='paper', xanchor='right', yanchor='middle',
                       text=labels[i], font=dict(family='Arial', size=16), showarrow =False)
    fig.add_annotation(x=0.95, y=data.iloc[:,i][-1], xref='paper',
                                  xanchor='left', yanchor='middle',
                                  text='{:.2f}X'.format(data.iloc[:,i][-1]),
                                  font=dict(family='Arial', size=16), showarrow =False)

fig.update_layout(xaxis=dict(showline=True, showgrid=False, showticklabels=True, linecolor='rgb(204, 204, 204)',
                             linewidth=2, ticks='outside', tickfont=dict(family='Arial', size=12, color='rgb(82, 82, 82)')),
                  yaxis=dict(showgrid=False, zeroline=False, showline=False, showticklabels=False), showlegend=False,
                  plot_bgcolor='white', title = dict(x = 0.5, text = title, font = dict(family='Arial', size=28, color='black')))
st.plotly_chart(fig)
