from flask import Flask, render_template, request,redirect,url_for
app = Flask(__name__)
from flask_session import Session
import pandas as pd
import os
from docx import Document
from cut import StockInfoExtractor
import akshare as ak
import zhifu
from datetime import datetime
from kline_visualization import StockKLinePlotter
from flask import session
import PyPDF2
from timian  import BigTimian_20,BigTimian_5, DataFetcher,SZZS
from search import Search
from test import chat_with_spark
from flask import jsonify
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = '123456'
app.config['SESSION_TYPE'] = 'filesystem'  # 使用文件系统来存储session数据
app.config['SESSION_FILE_DIR'] = 'static/flask_session/'  # session文件的存储路径
Session(app)
#PDF处理
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    return text
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        word_file=request.files['docxFile']
        if word_file:
            # 保存文件到指定的上传文件夹
            filename = os.path.join(app.config['UPLOAD_FOLDER'], word_file.filename)
            word_file.save(filename)
            # 读取文件的名称
            file_name = word_file.filename
            start_time = file_name.split("-")[0]
            # Save start_date in the session
            session['start_date'] = start_time
            content=""
            if filename.endswith('.docx'):
                # 处理 Word 文件
                doc=Document(word_file)
                fullText = []
                for para in doc.paragraphs:
                    fullText.append(para.text)
                content = '\n'.join(fullText)
            elif filename.endswith('.pdf'):
                content=extract_text_from_pdf(filename)
            cut=StockInfoExtractor()
            result=cut.get_stock_details(content)
            # 将股票按照行业分类
            industry_dict = {}
            for stock in result:
                industry = stock[2]
                if industry not in industry_dict:
                    industry_dict[industry] = []
                industry_dict[industry].append(stock)
            session['content'] = industry_dict
            return render_template('zhifudaima.html', content=industry_dict )
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')
@app.route('/visualization',methods=['GET', 'POST'])
def visualization():
    if request.method == 'POST':
        selected_stocks = request.form.getlist('selected_stocks')
        stock_set=[]
        # Get start_date from the session
        start_date = session.get('start_date', None)
        for stock in selected_stocks:
            big_timian_20 = BigTimian_20(stock)
            bigtimian_score_20=big_timian_20.get_combined_data()
            big_timian_5 = BigTimian_5(stock)
            bigtimian_score_5=big_timian_5.get_combined_data()
            zhifudaima_info = zhifu.zhifu_info(stock)
            ################平均5和20计算
            # hangye=zhifudaima_info["business"]
            # fetcher = DataFetcher(hangye)
            # pingjun_5, pingjun_20 = fetcher.fetch_data()
            ################平均5和20计算  ################平均5和20计算  ################平均5和20计算
            # 将所有的 Series 对象转换为 list
            for key, value in zhifudaima_info.items():
                if isinstance(value, pd.Series):
                    zhifudaima_info[key] = value.tolist()
            ssss=StockKLinePlotter()
            img =ssss.get_k_line_plot_base64_start(stock, start_date)
            stock_set.append([zhifudaima_info,img,bigtimian_score_20,bigtimian_score_5])

        # Store the stock_set in the session
        session['stock_set'] = stock_set
        # Redirect to the same route with GET method
        return redirect(url_for('visualization'))

    # For demonstration, just pass the list of selected stocks to the template
    # Render the template using data from the session
    selected_stocks = session.get('stock_set', [])
    return render_template('visualization.html', selected_stocks=selected_stocks)

@app.route('/information')
def information():
    huilv = ak.fx_spot_quote().loc[0][2]
    return render_template('information.html',huilv=huilv)

@app.route('/trend')
def trend():
    concept = ak.stock_board_concept_name_ths()
    return render_template('trend.html',concept=concept.head(20))

@app.route('/search', methods=['GET', 'POST'])
def search():
    query=request.args.get('query')
    search=Search(query)
    query=search.process_input()
    s_timian_20 = BigTimian_20(query["代码"])
    s_score_20 = s_timian_20.get_combined_data()
    s_timian_5 = BigTimian_5(query["代码"])
    s_score_5 = s_timian_5.get_combined_data()
    df=SZZS.szzs(query["代码"])
    # df的DataFrame
    df = df.sort_values(by='日期')
    # 将数据转化为列表
    zs=[]
    gegu=[]
    dates = df["日期"].tolist()
    closing_prices = df["收盘价"].tolist()
    volumes = df["成交量"].tolist()
    zs.append(dates)
    zs.append(closing_prices)
    zs.append(volumes)
    df2=SZZS.gegu(query["代码"])
    # df的DataFrame
    df2 = df2.sort_values(by='日期')
    # 将数据转化为列表
    # 直接转换日期列
    df2["日期"] = df2["日期"].apply(lambda date: datetime.strftime(date,"%Y-%m-%d"))
    dates2 = df2["日期"].tolist()
    closing_prices2 = df2["收盘"].tolist()
    volumes2 = df2["换手率"].tolist()
    gegu.append(dates2)
    gegu.append(closing_prices2)
    gegu.append(volumes2)
    timian_30=[]
    df3= SZZS.timian_30(query["代码"])
    df3 = df3.sort_values(by='日期')
    dates3 = df3["日期"].tolist()
    value3 = df3["计分"].tolist()
    timian_30.append(dates3)
    timian_30.append(value3)
    return render_template('search.html',round=round,query=query,score_20=s_score_20,score_5=s_score_5,zs=zs,gegu=gegu,timian_30=timian_30)


@app.route('/zhifudaima', methods=['GET', 'POST'])

def result():
    content = session.get('content', {})  # 从 session 中获取 content，如果没有则默认为空字典
    return render_template('zhifudaima.html', content=content)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'GET':
        return render_template('chat.html')
    elif request.method == 'POST':
        user_message = request.form.get('message')
        reply = chat_with_spark(user_message)
        return jsonify(reply=reply)

@app.route('/zhifudaima_detail/<zhifudaima_code>',methods=['GET', 'POST'])
def zhifudaima_detail(zhifudaima_code):
    #股票代码查找股票的详细信息
    zhifudaima_info = zhifu.zhifu_info(zhifudaima_code)
    return render_template('zhifudaima_detail.html', zhifudaima_info=zhifudaima_info)

if __name__ == '__main__':
    app.run(debug=True)



