from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.models import Users, Markets, Buys
from datetime import datetime, date
from flask import render_template, flash, redirect, request, url_for, session
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit

import sqlalchemy as sa

@app.route("/")


@app.route('/index')
@login_required
def index():
    # Selección de lista
    market_id = request.args.get('market_id', type=int)
    if market_id:
        session['selected_market_id'] = market_id
    else:
        market_id = session.get('selected_market_id')

    # Listado de listas del usuario
    markets = (
        Markets.query
        .filter_by(user_id=current_user.id)
        .order_by(Markets.date.desc())
        .all()
    )

    # Lista seleccionada y sus items
    selected_market = Markets.query.get(market_id) if market_id else None
    items = selected_market.items if selected_market else []

    # Cálculo de subtotales y total general en servidor
    items_data = []
    for item in items:
        items_data.append({
            'id': item.buy_id,
            'item_name': item.item_name,
            'qty': item.qty,
            'price': item.price,
            'expire': item.expire,
            'subtotal': item.qty * item.price
        })
    grand_total = sum(d['subtotal'] for d in items_data)

    return render_template(
        'index.html',
        markets=markets,
        selected_market=selected_market,
        items_data=items_data,
        grand_total=grand_total,
        current_date=date.today().isoformat()
    )


@app.route('/add_market', methods=['POST'])
@login_required
def add_market():
    name = request.form.get('market_name')
    date_str = request.form.get('market_date')
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('Invalid date format', 'danger')
        return redirect(url_for('index'))

    new_market = Markets(name=name, date=date_obj, user_id=current_user.id)
    db.session.add(new_market)
    db.session.commit()
    flash('List created!', 'success')
    return redirect(url_for('index', market_id=new_market.market_id))


@app.route('/edit_market/<int:market_id>', methods=['POST'])
@login_required
def edit_market(market_id):
    market = Markets.query.get_or_404(market_id)
    if market.user_id != current_user.id:
        abort(403)
    name = request.form.get('market_name')
    date_str = request.form.get('market_date')
    try:
        market.date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date', 'danger')
        return redirect(url_for('index', market_id=market_id))
    market.name = name
    db.session.commit()
    flash('List updated!', 'success')
    return redirect(url_for('index', market_id=market_id))

@app.route('/delete_market/<int:market_id>', methods=['POST'])
@login_required
def delete_market(market_id):
    market = Markets.query.get_or_404(market_id)
    if market.user_id != current_user.id:
        abort(403)
    db.session.delete(market)
    db.session.commit()
    flash('List deleted!', 'warning')
    return redirect(url_for('index'))


@app.route('/add_item', methods=['POST'])
@login_required
def add_item():
    market = Markets.query.get(session.get('selected_market_id'))
    if not market:
        flash('Select a list first', 'warning')
        return redirect(url_for('index'))

    name = request.form.get('item_name')
    qty = request.form.get('qty', type=int)
    price = request.form.get('price', type=float)
    expire_date = None
    if request.form.get('is_perishable'):
        exp_str = request.form.get('expire')
        try:
            expire_date = datetime.strptime(exp_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Invalid expiration date', 'danger')
            return redirect(url_for('index', market_id=market.market_id))

    if not name or qty < 1 or price < 0:
        flash('Invalid input', 'danger')
        return redirect(url_for('index', market_id=market.market_id))

    new_item = Buys(
        item_name=name,
        qty=qty,
        price=price,
        expire=expire_date,
        market=market,
        buyer=current_user
    )
    db.session.add(new_item)
    db.session.commit()
    flash('Item added!', 'success')
    return redirect(url_for('index', market_id=market.market_id))


@app.route('/edit_item/<int:item_id>', methods=['POST'])
@login_required
def edit_item(item_id):
    item = Buys.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    name = request.form.get('item_name')
    qty = request.form.get('qty', type=int)
    price = request.form.get('price', type=float)
    expire_date = None
    if request.form.get('is_perishable'):
        exp_str = request.form.get('expire')
        try:
            expire_date = datetime.strptime(exp_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Invalid expiration date', 'danger')
            return redirect(url_for('index', market_id=item.market_id))

    if not name or qty < 1 or price < 0:
        flash('Invalid input', 'danger')
        return redirect(url_for('index', market_id=item.market_id))

    item.item_name = name
    item.qty = qty
    item.price = price
    item.expire = expire_date
    db.session.commit()
    flash('Item updated!', 'success')
    return redirect(url_for('index', market_id=item.market_id))

@app.route('/delete_item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Buys.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    market_id = item.market_id
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted!', 'warning')
    return redirect(url_for('index', market_id=market_id))


@app.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("index"))

    # LLama la funcion de login
    form = LoginForm()
    # Valida la informacion proporcionada por el usuario
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(Users).where(Users.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")

            return redirect(url_for("login"))

        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")

        if not next_page or urlsplit(next_page).netloc != "":
            next_page = url_for("index")

        return redirect(next_page)

    return render_template("login.html", title="Sign In", form=form)


@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    
    if current_user.is_authenticated:
        
        return redirect(url_for("index"))

    form = RegistrationForm()
    if form.validate_on_submit():

        user = Users(name=form.name.data, username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")

        return redirect(url_for("login"))
    
    return render_template("register.html", title="Register", form=form)