import pandas as pd
import datetime
import requests
import sched
import time
import json

# 用來產生網頁的函式
def html_template(html_table):
  return f'''
    <!DOCTYPE html>
    <html>
      <head>
        <link rel="stylesheet" href="main.css" />
        <style>
        * {{
            box-sizing: border-box;
            -webkit-box-sizing: border-box;
            -moz-box-sizing: border-box;
          }}
          body {{
            font-family: Helvetica;
            -webkit-font-smoothing: antialiased;
            background: rgba( 71, 147, 227, 1);
          }}
          h2 {{
            text-align: center;
            font-size: 30px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: white;
            padding: 30px 0;
          }}

          /* Table Styles */
          .table-wrapper {{
            margin: 10px 70px 70px;
            box-shadow: 0px 35px 50px rgba( 0, 0, 0, 0.2 );
          }}

          .fl-table {{
            border-radius: 5px;
            font-size: 12px;
            font-weight: normal;
            border: none;
            border-collapse: collapse;
            width: 100%;
            max-width: 100%;
            white-space: nowrap;
            background-color: white;
          }}

          .fl-table td, .fl-table th {{
            text-align: center;
            padding: 8px;
          }}

          .fl-table td {{
            border-right: 1px solid #f8f8f8;
            font-size: 12px;
          }}

          .fl-table thead th {{
            color: #ffffff;
            background: #4FC3A1;
          }}

          .fl-table thead th:nth-child(odd) {{
            color: #ffffff;
            background: #324960;
          }}

          .fl-table tr:nth-child(even) {{
            background: #F8F8F8;
          }}

          /* Responsive */
          @media (max-width: 767px) {{
              .fl-table {{
                display: block;
                width: 100%;
              }}
              .table-wrapper:before {{
                content: "Scroll horizontally >";
                display: block;
                text-align: right;
                font-size: 11px;
                color: white;
                padding: 0 0 10px;
              }}
              .fl-table thead, .fl-table tbody, .fl-table thead th {{
                display: block;
              }}
              .fl-table thead th:last-child {{
                border-bottom: none;
              }}
              .fl-table thead {{
                float: left;
              }}
              .fl-table tbody {{
                width: auto;
                position: relative;
                overflow-x: auto;
              }}
              .fl-table td, .fl-table th {{
                padding: 20px .625em .625em .625em;
                height: 60px;
                vertical-align: middle;
                box-sizing: border-box;
                overflow-x: hidden;
                overflow-y: auto;
                width: 120px;
                font-size: 13px;
                text-overflow: ellipsis;
              }}
              .fl-table thead th {{
                text-align: left;
                border-bottom: 1px solid #f7f7f9;
              }}
              .fl-table tbody tr {{
                display: table-cell;
              }}
              .fl-table tbody tr:nth-child(odd) {{
                background: none;
              }}
              .fl-table tr:nth-child(even) {{
                background: transparent;
              }}
              .fl-table tr td:nth-child(odd) {{
                background: #F8F8F8;
                border-right: 1px solid #E6E4E4;
              }}
              .fl-table tr td:nth-child(even) {{
                border-right: 1px solid #E6E4E4;
              }}
              .fl-table tbody td {{
                display: block;
                text-align: center;
              }}
          }}
        </style>
      </head>
      
      <body>
        <h2>我的最新股票資訊</h2>
        <div class="table-wrapper">
        <table class="fl-table">
          <thead>
          <tr>
            <th>股票代號</th>
            <th>公司簡稱</th>
            <th>成交價</th>
            <th>成交量</th>
            <th>累積成交量</th>
            <th>開盤價</th>
            <th>最高價</th>
            <th>最低價</th>
            <th>昨收價</th>
            <th>漲跌百分比</th>
            <th>資料更新時間</th>
          </tr>
          </thead>
          <tbody>
            {html_table}
          <tbody>
        </table>
        </div>
      </body>
    </html>
    '''

# 打算要取得的股票代碼
stock_list_tse = ['0050', '0056', '2330', '2317', '1216']
stock_list_otc = ['6547', '6180']
    
# 組合API需要的股票清單字串
stock_list1 = '|'.join('tse_{}.tw'.format(stock) for stock in stock_list_tse) 

# 6字頭的股票參數不一樣
stock_list2 = '|'.join('otc_{}.tw'.format(stock) for stock in stock_list_otc) 
stock_list = stock_list1 + '|' + stock_list2
print(stock_list)

#　組合完整的URL
query_url = f'http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={stock_list}'

# 呼叫股票資訊API
response = requests.get(query_url)

# 判斷該API呼叫是否成功
if response.status_code != 200:
  raise Exception('取得股票資訊失敗.')
else:
  print(response.text)

# 將回傳的JSON格式資料轉成Python的dictionary
data = json.loads(response.text)

# 過濾出有用到的欄位
columns = ['c','n','z','tv','v','o','h','l','y', 'tlong']
df = pd.DataFrame(data['msgArray'], columns=columns)
df.columns = ['股票代號','公司簡稱','成交價','成交量','累積成交量','開盤價','最高價','最低價','昨收價', '資料更新時間']

# 自行新增漲跌百分比欄位
df.insert(9, "漲跌百分比", 0.0) 

# 用來計算漲跌百分比的函式
def count_per(x):
  if isinstance(x[0], int) == False:
    x[0] = 0.0
  
  result = (x[0] - float(x[1])) / float(x[1]) * 100

  return pd.Series(['-' if x[0] == 0.0 else x[0], x[1], '-' if result == -100 else result])

# 填入每支股票的漲跌百分比
df[['成交價', '昨收價', '漲跌百分比']] = df[['成交價', '昨收價', '漲跌百分比']].apply(count_per, axis=1)

# 紀錄更新時間
def time2str(t):
  print(t)
  t = int(t) / 1000 + 8 * 60 * 60. # UTC時間加8小時為台灣時間
  
  return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))

# 把API回傳的秒數時間轉成容易閱讀的格式
df['資料更新時間'] = df['資料更新時間'].apply(time2str)

# 將每筆股票資訊組合成HTML的Table格式資料
html_table = ''
for index, row in df.iterrows():
  html_table += '<tr>\n'
  html_table += '<td>' + '</td>\n<td>'.join(row) + '</td>'
  html_table += '\n</tr>'

# 將產生的網頁寫入檔案
with open('index.html', 'w') as src:
  src.write(html_template(html_table))

# 上傳index.html到雲端
import ftplib
session = ftplib.FTP('files.000webhost.com','web16800000','3939889.')
file = open('index.html','rb')
session.storbinary('STOR /public_html/index.html', file)
file.close()
session.quit()