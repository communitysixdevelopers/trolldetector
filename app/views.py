# -*- coding: utf-8 -*-
from flask import request, render_template, make_response, jsonify, redirect, render_template_string

from app import app_web, MODEL, interpretation,\
    TABLE_INTERP_TOP, TABLE_INTERP, db, ApiInformation, User, UserHistory, login_required, login_user, current_user, logout_user

from .utils import get_list_pictures, preprocess_link_answers_mail_ru, parce_data_from_link_answers_mail_ru,\
    get_simple_table, get_table_link, get_table_history, process_dict_from_proba, process_dict_from_link, process_dict_from_interpretation

from datetime import datetime

FLAG_TABLE_LINK = -3
LINK_COMMENT = ""

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

@app_web.route('/logout_reg/')
@login_required
def logout_reg():
    logout_user()
    return redirect('/registration/')

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
    if data_hist is None:
        return render_template("empty.html", text="")
    if FLAG_TABLE_LINK < 0:
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