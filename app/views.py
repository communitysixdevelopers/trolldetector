# -*- coding: utf-8 -*-
from flask import request, render_template, make_response, jsonify, redirect, render_template_string
from app import app_web, MODEL, interpretation, get_question_answers, interpretation_short, \
    TABLE_INTERP_TOP, TABLE_INTERP, db, ApiInformation, User, UserHistory, login_required, login_user, current_user, logout_user
from datetime import datetime 

FLAG_TABLE_LINK = -3
LINK_COMMENT = ""

def get_simple_table(data):
    str_table = ""
    str_ = '''<head>
                <meta charset="utf-8">
                <link rel="stylesheet" type="text/css" href="../static/style_table.css"/>
            </head>
            <body>
                <center>
                <table border="1" class="table_prob">
                    <thead>
                        <tr style="text-align: left;">
                        <th></th>
                        <th>Key_api</th>
                        <th>Тариф</th>
                        <th>Осталось запросов вероятности</th>
                        <th>Осталось запросов вероятности по сслыке</th>
                        <th>Осталось запросов интерпретации</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table}
                    </tbody>
                </center>
            </body>
            '''
    for i, api in enumerate(data):
        str_table += "<tr><th>{}</th><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(i+1,api.api_key, api.tarif, api.counts_proba_left, api.counts_link_left, api.counts_interpr_left)
    return str_.format(table=str_table)

def get_table_history(data):
    str_table = ""
    str_ = '''<head>
                <meta charset="utf-8">
                <link rel="stylesheet" type="text/css" href="../../static/style_table.css"/>
            </head>
            <body>
                <center>
                <table border="1" class="table_prob">
                    <thead>
                        <tr style="text-align: left;">
                        <th>№</th>
                        <th>Вопрос</th>
                        <th>Ответ</th>
                        <th>Вероятность</th>
                        <th>Время запроса</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table}
                    </tbody>
                    <script src="../../static/doubleClickRowTable.js"></script>
                </center>
            </body>
            '''
    for i, row in enumerate(data):
        str_table += "<tr><th>{}</th><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(i+1, row.question, row.answer, row.proba, row.created_on)
    return str_.format(table=str_table)
    
def get_table_link(data):
    str_table = ""
    str_ = '''<head>
                <meta charset="utf-8">
                <link rel="stylesheet" type="text/css" href="../../static/style_table.css"/>
            </head>
            <body>
                <center>
                <table border="1" class="table_prob">
                    <thead>
                        <tr style="text-align: left;">
                        <th>№</th>
                        <th>Вопрос</th>
                        <th>Ответ</th>
                        <th>Вероятность</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table}
                    </tbody>
                    <script src="../../static/doubleClickRowTable.js"></script>
                </center>
            </body>
            '''
    for i, row in enumerate(data):
        str_table += "<tr><th>{}</th><td>{}</td><td>{}</td><td>{}</td></tr>".format(i+1, row.question, row.answer, row.proba)
    return str_.format(table=str_table)

def get_list_pictures(proba=-1):
    base_scr = [
        '../static/pic/inactive1.svg',
        '../static/pic/inactive2.svg',
        '../static/pic/inactive3.svg',
        '../static/pic/inactive4.svg',
        '../static/pic/inactive5.svg',
        ]
    if proba == -1:
        return base_scr
    if proba <= 0.2:
        base_scr[0] = '../static/pic/active1.svg'
    elif proba <= 0.4:
        base_scr[1] = '../static/pic/active2.svg'
    elif proba <= 0.6:
        base_scr[2] = '../static/pic/active3.svg'
    elif proba <= 0.8:
        base_scr[3] = '../static/pic/active4.svg'
    else:
        base_scr[4] = '../static/pic/active5.svg'
    return base_scr

def predict_class(proba, treshold=0.5):
    if proba >= treshold:
        return 1
    return 0

def process_dict_from_proba(dict_data, update_db_proba=True, data_api=None):
    """
        Обработчик входного словаря. Расчет вероятности
    """
    
    comment = None
    #Проверка правильности формирования запроса
    if dict_data == {}:
        comment = "No found required keys: 'question', 'answer'."
    elif "question" not in dict_data.keys():
        comment = "No found required key: 'question."
    elif "answer" not in dict_data.keys():
        comment = "No found required key: 'answer'."
    
    dict_data["log"] = {"comment":comment}
    if comment != None:
        return

    #Проверка api ключа
    if data_api is None:
        data_api = db.session.query(ApiInformation).get(dict_data["key_api"])
        if data_api is None:
            dict_data["log"]["comment"] = "No correct api_key, or unauthorized user"
            return
        elif data_api.counts_proba_left == 0:
            dict_data["log"]["comment"] = "No available query probability"
            return

    question = dict_data["question"]
    answer = dict_data["answer"]
    if "treshold" not in dict_data.keys():
        dict_data["treshold"] = 0.5
    treshold = dict_data["treshold"]

    dict_data["log"]["comment"] = "OK"
    proba = []
    class_ = []
    #Определение максимального числа строк в запросе
    #question список, answer список 
    if isinstance(question,list) and isinstance(answer,list):
        max_len = len(question)
        type_ = 1
    #question строка, answer список
    elif not isinstance(question,list) and isinstance(answer,list):
        max_len = len(answer)
        type_ = 2
    #question список, answer строка
    elif isinstance(question,list) and not isinstance(answer,list):
        max_len = len(question)
        type_ = 3
    #question строка, answer строка
    else:
        max_len = 1
        type_ = 4
    
    if update_db_proba:
        len_seq = min(max_len, data_api.counts_proba_left)
    else:
        len_seq = max_len
    
    if type_ == 1:
        for i, q in enumerate(question[:len_seq]):
            proba.append(MODEL.predict(q, answer[i]))
            class_.append(predict_class(proba[-1], treshold=treshold))
    elif type_ == 2:
        for i, a in enumerate(answer[:len_seq]):
            proba.append(MODEL.predict(question, a))
            class_.append(predict_class(proba[-1], treshold=treshold))
    elif type_ == 3:
        for i, q in enumerate(question[:len_seq]):
            proba.append(MODEL.predict(q, answer))
            class_.append(predict_class(proba[-1], treshold=treshold))
    else:
        proba = MODEL.predict(question, answer)
        class_ = predict_class(proba, treshold=treshold)

    if len_seq != max_len: dict_data["log"]["comment"] = \
            "Some requests were processed. No available query probability"

    dict_data["proba"] = proba
    dict_data["class"] = class_
    
    if update_db_proba:
        #Запись изменений в базу данных
        data_api.counts_proba_left -= len_seq
        db.session.add(data_api)
        db.session.commit()

    dict_data["log"]["count_available_query"] = {"probabylity":data_api.counts_proba_left,
                                                 "link":data_api.counts_link_left,
                                                 "interpretation":data_api.counts_interpr_left
    }
    

def process_dict_from_link(dict_data, update_db_link=True):
    """
        Обработчик входного словаря. Расчет вероятности по ссылке на сайт
    """
    
    if dict_data == {} or ("link" not in dict_data.keys()):
        dict_data["log"] = {"comment":"No found required key: 'link'."}
        return
    dict_data["log"] = {}

    #Проверка api ключа
    data_api = db.session.query(ApiInformation).get(dict_data["key_api"])
    if data_api is None:
        dict_data["log"]["comment"] = "No correct api_key, or unauthorized user"
        return
    elif data_api.counts_link_left == 0:
        dict_data["log"]["comment"] = "No available query probability"
        return

    if "type_parser" not in dict_data.keys():
        dict_data["type_parser"] = "answers_mail.ru"
    
    if dict_data["type_parser"] == "answers_mail.ru":
        data_link = parce_data_from_link_answers_mail_ru(dict_data["link"])
        if data_link["code"] < 0:
            dict_data["log"]["comment"] = data_link["comment"]
            return

    if "treshold" not in dict_data.keys():
        dict_data["treshold"] = 0.5
    treshold = dict_data["treshold"]

    dict_data["question"] = data_link["question"]
    dict_data["answer"] = data_link["answer"]
    dict_data["treshold"] = treshold

    process_dict_from_proba(dict_data, update_db_proba=False, data_api=data_api)
    
    #Запись изменений в базу данных
    data_api.counts_link_left -= 1
    db.session.add(data_api)
    db.session.commit()

    dict_data["log"]["count_available_query"] = {"probabylity":data_api.counts_proba_left,
                                                 "link":data_api.counts_link_left,
                                                 "interpretation":data_api.counts_interpr_left
    }

def process_dict_from_interpretation(dict_data):
    """
        Обработчик входного словаря. Интерпретация
    """
    comment = None
    #Проверка правильности формирования запроса
    if dict_data == {}:
        comment = "No found required keys: 'question', 'answer'."
    elif "question" not in dict_data.keys():
        comment = "No found required key: 'question."
    elif "answer" not in dict_data.keys():
        comment = "No found required key: 'answer'."
    
    dict_data["log"] = {"comment":comment}
    if comment != None:
        return

    dict_data["log"] = {}
    #Проверка api ключа
    data_api = db.session.query(ApiInformation).get(dict_data["key_api"])
    if data_api is None:
        dict_data["log"]["comment"] = "No correct api_key, or unauthorized user"
        return
    elif data_api.counts_interpr_left == 0:
        dict_data["log"]["comment"] = "No available query interpretation"
        return

    neg, pos = interpretation_short(dict_data["question"], dict_data["answer"], dict_data["n_max_top"])

    for key, value in neg.items():
        neg[key] = round(value,3)
    for key, value in pos.items():
        pos[key] = round(value,3)

    dict_data["negative_contribution"] = neg
    dict_data["positive_contribution"] = pos

    #Запись изменений в базу данных
    data_api.counts_interpr_left -= 1
    db.session.add(data_api)
    db.session.commit()

    dict_data["log"]["count_available_query"] = {"probabylity":data_api.counts_proba_left,
                                                 "link":data_api.counts_link_left,
                                                 "interpretation":data_api.counts_interpr_left
    }


def preprocess_link_answers_mail_ru(link_to_site):
    """
        Обработчик входной ссылки на сайт Mail.ru
    """
    if link_to_site is None:
        return None
    elif link_to_site.isdigit():
        return 'https://otvet.mail.ru/question/'+link_to_site
    return link_to_site

def parce_data_from_link_answers_mail_ru(link_to_site):
    output = {}
    output["question"] = None
    output["answer"] = None
    link = preprocess_link_answers_mail_ru(link_to_site)
    if link is None:
        output["code"] = -3
        output["comment"] = ""
        return output
    data = get_question_answers(link)
    if isinstance(data, tuple):
        output["question"] = data[0]
        output["answer"] = data[1]
        if data[1] == []:
            output["code"] = -1
            output["comment"] = "For {} is no answers".format(link)
            return output
        output["code"] = 0
        output["comment"] = "Found question and answers"
    else:
        output["code"] = -2
        output["comment"] = "Url is incorrect format"
        return output
    return output
"""
Autorization
"""
@app_web.route("/guest/", methods=['GET', 'POST'])
def guest():
    user = db.session.query(User).filter(User.email == "guest@guest").first()
    login_user(user)
    return render_template("index.html")

@app_web.route("/autentification/", methods=["GET", "POST"])
def autentification():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = db.session.query(User).filter(User.email == email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect("/")
        return render_template("autentification.html", info="Неверные даннные по почте/паролю")
    return render_template("autentification.html", info="")

@app_web.route("/registration/", methods=['GET', 'POST'])
def registration():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        password_copy = request.form.get("password_copy")
        if password_copy != password:
            return render_template("registration.html", info="Пароли не совпадают")
        user = User(email=email,  password='password', last_id_group_query=0)
        user_db = db.session.query(User).filter(User.email == email).first()
        if user_db:
            return render_template("registration.html", info="Пользователь по этому электроному адресу уже зарегистрирован")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect("/")
    return render_template("registration.html", info="")

@app_web.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect('/')

"""
Main pages
"""
@app_web.route("/", methods=['GET', 'POST'])
@login_required
def index():
    return render_template("index.html")

@app_web.route("/q_a/", methods=['GET', 'POST'])
@login_required
def q_a():
    result = {}
    result["proba"] = ""
    result["smile"] = get_list_pictures()
    if request.method == "POST":
        result["question"] = request.form.get("question")
        result["answer"] = request.form.get("answer")
        result["proba"] = MODEL.predict(result["question"],result["answer"])
        result["smile"] = get_list_pictures(result["proba"])
        db.session.add(UserHistory(question=result["question"], answer=result["answer"], proba=result["proba"], users=current_user, id_group_query=0))
        db.session.commit()
    return render_template("index_question_answer.html", result=result)

@app_web.route("/link/", methods=['GET', 'POST'])
@login_required
def link():
    global LINK_COMMENT
    global FLAG_TABLE_LINK
    link_to_site = preprocess_link_answers_mail_ru(request.args.get("link_to_site"))
    data = parce_data_from_link_answers_mail_ru(link_to_site)
    if data["code"] == -3:
        return render_template("index_link.html")
    LINK_COMMENT = data["comment"]
    FLAG_TABLE_LINK = data["code"]

    if data["code"] < 0:
        return render_template("index_link.html")

    current_user.last_id_group_query+=1
    for answer in data["answer"]:
        proba = MODEL.predict(data["question"], answer)
        db.session.add(UserHistory(question=data["question"], answer=answer, proba=proba, users=current_user, id_group_query=current_user.last_id_group_query))

    db.session.add(current_user)
    db.session.commit()
    return render_template("index_link.html")

@app_web.route("/interpretation/", methods=['GET', 'POST'])
@login_required
def interpr():
    result = {}
    result["question"] = ""
    result["answer"] = ""
    if request.method == "POST":
        result["question"] = request.form.get("question")
        result["answer"] = request.form.get("answer")
        interpretation(result["question"], result["answer"])
    return render_template("index_interpretation.html", result=result)

@app_web.route("/service/", methods=['GET', 'POST'])
@login_required
def service():
    return render_template("index_service.html")

@app_web.route("/history/", methods=['GET', 'POST'])
@login_required 
def history():
    return render_template("index_history.html")

@app_web.route("/cabinet/", methods=['GET', 'POST'])
@login_required 
def cabinet():
    if request.method == "POST":
        api = ApiInformation(tarif="Тестовый", counts_proba_left=100, counts_link_left=25, counts_interpr_left=10, users=current_user)
        api.create_api_key(current_user.email)
        db.session.add(api)
        db.session.commit()
        return render_template("cabinet.html", info="")
        # email = request.form.get("email")
    if current_user.email == "guest@guest":
        return render_template("cabinet_guest.html")
    return render_template("cabinet.html", info="")

@app_web.route("/render_cabinet_table/", methods=['GET'])
def render_cabinet_table():
    data_key = db.session.query(ApiInformation).filter(ApiInformation.user_id == current_user.id).all()
    if not data_key:
        return render_template("empty.html", text="Нет информации по токенам")
    return render_template_string(get_simple_table(data_key))

"""
Catch Querry
"""
@app_web.route("/catch_query_interpretation/", methods=['GET', 'POST']) 
def catch_interpretation():
    if request.method == "POST":
        data = request.get_json()
        interpretation(data["question"], data["answer"])
    res = make_response("ok")
    return res

@app_web.route("/get_proba/", methods=['POST']) 
def catch_proba():
    data = request.get_json()
    process_dict_from_proba(data)
    return jsonify(data)

@app_web.route("/get_link/", methods=['POST']) 
def catch_link():
    data = request.get_json()
    process_dict_from_link(data)
    return jsonify(data)

@app_web.route("/get_interpretation/", methods=['POST']) 
def get_interpretation():
    data = request.get_json()
    process_dict_from_interpretation(data)
    return jsonify(data)

@app_web.route("/get_user_api_status/", methods=['POST']) 
def query_left():
    data = request.get_json()
    data_api = db.session.query(ApiInformation).get(data["key_api"])
    data["tarif"] = data_api.tarif
    data["counts_proba_left"] = data_api.counts_proba_left
    data["counts_link_left"] = data_api.counts_link_left
    data["counts_interpr_left"] = data_api.counts_interpr_left
    return jsonify(data)

"""
Other Querry
"""
@app_web.route("/output_frame_interpretation/", methods=['GET', 'POST']) 
def frame_interpretation():
    result = {}
    result["question"] = ""
    result["answer"] = ""
    if request.method == "POST":
        result = request.get_json()
    return render_template("form_interpretation.html", result=result)

@app_web.route("/single_plot/", methods=['GET']) 
def single_plot():
    return render_template("single_plot.html")

@app_web.route("/table_top/", methods=['GET']) 
def table_top():
    global TABLE_INTERP_TOP
    return TABLE_INTERP_TOP.get_html(table_id="table_top", class_table="table_top")

@app_web.route("/form_interpretation/", methods=['GET', 'POST']) 
def form_interpretation():
    return render_template("single_plot.html")

@app_web.route("/table_proba/", methods=['GET', 'POST']) 
def table_proba():
    data_hist = db.session.query(UserHistory).filter(UserHistory.user_id == current_user.id, UserHistory.id_group_query == current_user.last_id_group_query).all()
    global FLAG_TABLE_LINK
    if FLAG_TABLE_LINK < 0 or data_hist is None:
        return render_template("empty.html", text = LINK_COMMENT)
    return render_template_string(get_table_link(data_hist))
    
@app_web.route("/table_history/<int:size>/", methods=['GET', 'POST']) 
def table_history(size):
    data_hist = db.session.query(UserHistory).filter(UserHistory.user_id == current_user.id).order_by(db.desc(UserHistory.id)).limit(size).all()
    if not data_hist:
        return render_template("empty.html", text = "Ещё нет истории запросов")
    return render_template_string(get_table_history(data_hist))

@app_web.route("/table_interpretation/", methods=['GET', 'POST']) 
def table_interpretation():
    global TABLE_INTERP
    return TABLE_INTERP.get_html(table_id="table_interp")