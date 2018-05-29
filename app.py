from flask import Flask, session, redirect, url_for, request, render_template, jsonify
from flask_pymongo import PyMongo
import uuid
import requests
import json
from random import randint,random
from datetime import datetime,timedelta
import hashlib
from services import data
from geopy.distance import great_circle
import operator
#from twilio.rest import Client

app = Flask(__name__)
app.secret_key = "super secret key"


app.config['MONGO_DBNAME'] = 'kickback'
app.config['MONGO_URI'] = 'mongodb://kickback:kickback@ds161315.mlab.com:61315/kickback'
ALGORITHM = 'sha512'

mongo = PyMongo(app)

cap1APIkey = '5cf258920f26cc6357f2cb48701059ab'


def date_diff(date1, date2):
    return abs((date1 - date2).days)

# @app.route('/loadMongo')
# def load_mongo():
#     customerID = '5b04388a322fa06b677939e0'
#     url = 'http://api.reimaginebanking.com/accounts/{}/purchases?key={}'.format(customerID, cap1APIkey)
#     response = requests.get(url).json()
#     for res in response:
#         mongo.db.purchases.insert_one(res)
#     return 'yo'

# @app.route('/loadMerchantsMongo')
# def load_mongo_merchants():
#     customerID = '5b04388a322fa06b677939e0'
#     url = 'http://api.reimaginebanking.com/merchants?key={}'.format(cap1APIkey)
#     response = requests.get(url).json()
#     uniq_merchants = {}
#     for res in response:
#         if "creation_date" in res and res["creation_date"] == "2018-05-24" and not res["name"] in uniq_merchants:
#             uniq_merchants[res["name"]] = True
#             mongo.db.merchants.insert_one(res)
#     return 'yo'

@app.route('/')
def show_index():
    context = {}
    if 'logname' not in session:
        context['loggedin'] = 0
    return render_template("index.html", **context)


@app.route('/dashboard')
def show_dashboard():
    context = {}
    if 'logname' not in session:
        return redirect(url_for('show_signin'))
    return render_template("dashboard.html", **context)


@app.route('/explore')
def show_explore():
    context = {}
    if 'logname' not in session:
        return redirect(url_for('show_signin', link='explore'))
    return render_template("explore.html", **context)


@app.route('/api/discounts')
def get_discounts():
    current_lat = request.args.get('lat')
    current_lng = request.args.get('lng')
    items = []
    for key1 in data.discounts_by_category:
        for element in data.discounts_by_category[key1]:
            # return jsonify(element['deal'])
            if 'longitude' not in element['deal']['merchant']:
                if 'latitude' not in element['deal']['merchant']:
                    break
            item = {}
            item['name'] = element['deal']['merchant']['name']
            item['description'] = element['deal']['short_title']
            item['longitude'] = element['deal']['merchant']['longitude']
            item['latitude'] = element['deal']['merchant']['latitude']
            distance = great_circle((item['latitude'], item['longitude']), (current_lat, current_lng)).miles
            if distance < 250:
                item['distance'] = distance
                items.append(item)

    return jsonify(sorted(items, key=lambda item: item['distance']))


@app.route('/api/allDiscounts')
def get_all_discounts():
    items = []
    for key1 in data.discounts_by_category:
        for element in data.discounts_by_category[key1]:

            item = {}
            item['name'] = element['deal']['merchant']['name']
            item['description'] = element['deal']['short_title']
            item['category'] = element['deal']['category_slug']
            item['short_title'] = element['deal']['short_title']

            try:
                item['longitude'] = element['deal']['merchant']['longitude']
            except Exception:
                item['longitude'] = None
            try:
                item['latitude'] = element['deal']['merchant']['latitude']
            except Exception:
                item['latitude'] = None

            items.append(item)

    return jsonify(items)


@app.route('/signin/', methods=['GET', 'POST'])
def show_signin():
    if request.method == 'GET':
        context = {}
        return render_template('signin.html', **context)
    # post request
    if request.method == 'POST':
        username = request.form['username']
        pwd_to_check = request.form['password']
        # check if password matches

        res = mongo.db.users.find_one({"username": username})
        if res is not None:
            db_string = res['password']
            if check_pwd(db_string, pwd_to_check):
                session['logname'] = username
                session['fullname'] = res['fullname']
                if request.args.get('link') == 'explore':
                    return redirect(url_for('show_explore'))
                return redirect(url_for('show_dashboard'))
        context = {}
        return render_template('signin.html', **context)


@app.route('/signout/')
def show_signout():
    session.clear()
    return redirect(url_for('show_index'))


@app.route('/signup/', methods=['GET', 'POST'])
def show_signup():
    if 'logname' in session:
        return redirect(url_for('show_index'))

    # get request
    if request.method == 'GET':
        context = {}
        return render_template('signup.html', **context)
    # post request
    if request.method == 'POST':
        fullname = request.form['fullname']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # generate password hash
        salt = uuid.uuid4().hex
        password_hash = hash_pwd(salt, password)
        pwd_db_string = "$".join([ALGORITHM, salt, password_hash])
        # insert new record
        mongo.db.users.insert_one({"username": username, "fullname": fullname, "email": email, "password": pwd_db_string, "date": datetime.utcnow()})
        session['logname'] = username
        session['fullname'] = fullname
        return redirect(url_for('show_dashboard'))
    return render_template("index.html", **context)


def get_merchant_categories(merchant_id, id):
    customerID = '5b043889322fa06b677939de'
    url = 'http://api.reimaginebanking.com/merchants/{}?key={}'.format(merchant_id, cap1APIkey)
    merchant = mongo.db.merchants.find_one({"_id": merchant_id})
    return merchant['category'] if "category" in merchant else []


def get_rec_payments():
    # use Kelley's (default) customerID
    customerID = '5b04388a322fa06b677939e0'
    # Truncate payments to 600 most recent sorted by purchase date
    response = list(mongo.db.purchases.find({"payer_id": customerID}))[:600]
    recent_payments = response[:600]
    recent_payments.sort(key=lambda p: p["purchase_date"])
    # Build dict of most frequently occurring purchases
    frequencies = {}
    for payment in recent_payments:
        if payment["merchant_id"] in frequencies:
            frequencies[payment["merchant_id"]]["freq"] += 1
            if "occ2" not in frequencies[payment["merchant_id"]]:
                frequencies[payment["merchant_id"]]["occ2"] = datetime.strptime(payment["purchase_date"], '%Y-%m-%d')
        else:
            categories = get_merchant_categories(payment["merchant_id"], payment["description"])
            frequencies[payment["merchant_id"]] = {
                "freq": 1,
                "occ1": datetime.strptime(payment["purchase_date"], '%Y-%m-%d'),
                "name": payment["description"],
                "merchant_id": payment["merchant_id"],
                "categories": categories
            }
    # Truncate to those with high frequency and close together, sort by frequency
    truncated_frequencies = {key: frequencies[key] for key in frequencies if frequencies[key]["freq"] >= 8 and date_diff(frequencies[key]["occ1"], frequencies[key]["occ2"]) < 14}
    sorted_results = list(truncated_frequencies.values())
    sorted_results.sort(key=lambda p: -p["freq"])
    return sorted_results

@app.route('/api/getRecurringPayments')
def get_rec_payments_route():
    rec_payments = get_rec_payments()
    return jsonify(rec_payments)

@app.route('/api/getMerchants')
def get_merchants():
    customerID = '5b04388a322fa06b677939e0'
    url = 'http://api.reimaginebanking.com/merchants?key={}'.format(cap1APIkey)
    # Request all payments in account
    merchants = list(mongo.db.merchants.find())
    return merchants

def get_payments_by_merchant(merchant_id):
    customerID = '5b04388a322fa06b677939e0'
    url = 'http://api.reimaginebanking.com/merchants/{}/accounts/{}/purchases?key={}'.format(merchant_id, customerID, cap1APIkey)
    # Request all payments in account
    payments = list(mongo.db.purchases.find({"payer_id": customerID, "merchant_id": merchant_id}))
    return payments

@app.route('/api/getCategories')
def get_categories():
    customerID = '5b04388a322fa06b677939e0'
    merchants = list(mongo.db.merchants.find())
    merchant_categories = {}
    for merchant in merchants:
        if not merchant["name"] in merchant_categories:
            if "category" in merchant:
                merchant_categories[merchant["name"]] = merchant["category"]
                if len(merchant["category"]) == 0:
                    merchant_categories[merchant["name"]].append("miscellaneous")
            else:
                merchant_categories[merchant["name"]] = ["miscellaneous"]

    response = list(mongo.db.purchases.find({"payer_id": customerID}))
    sum = 0
    categories = {}
    for payment in response:
        sum += payment["amount"]
        if merchant_categories[payment["description"]][0] in categories:
            categories[merchant_categories[payment["description"]][0]]["sum"] += payment["amount"]
        else:
            categories[merchant_categories[payment["description"]][0]] = {
                "name": merchant_categories[payment["description"]][0],
                "sum": payment["amount"]
            }
    res = list(categories.values())
    res.sort(key=lambda x: -x["sum"])
    return jsonify(res)

@app.route('/api/savings')
def get_savings():
    rec_payments = get_rec_payments()
    with open('data/full_data_new.json') as f:
        deals = json.load(f)
    total_savings = []
    total_savings_amt = 0
    total_deals = []
    breakdown = []
    for rec_payment in rec_payments:
        idx = 0
        categories = rec_payment["categories"]
        category = categories[0] if len(categories) > 0 else "miscellaneous"
        payments_by_merchant = get_payments_by_merchant(rec_payment["merchant_id"])
        savings = 0
        top_deals = []
        for payment in payments_by_merchant:
            best_cost = payment["amount"]
            best_deal = {}
            if len(category) > 0 and category in deals:
                for deal in deals[category]:
                    estimate = deal["deal_estimate"]
                    if estimate["type"] == 'P':
                        discount = estimate["amt"] / 100
                        if deal["merchant"] == "Panera Bread":
                            discount = 0
                        if payment["amount"] * (1 - discount) < best_cost and payment["amount"] * (1 - discount) > 0.6 * payment["amount"]:
                            best_cost = payment["amount"] * (1 - discount)
                            best_deal = deal
                    elif estimate["type"] == 'PO':
                        discount = float(randint(0, int(estimate["amt"] * 2.0 / 3.0))) / 100.0
                        if deal["merchant"] == "Panera Bread":
                            discount = 0
                        if payment["amount"] * (1 - discount) < best_cost and payment["amount"] * (1 - discount) > 0.6 * payment["amount"]:
                            best_cost = payment["amount"] * (1 - discount)
                            best_deal = deal
                    elif estimate["type"] == 'R' or estimate["type"] == 'C':
                        if estimate["amt"] == 0:
                            prob = random()
                        elif estimate["amt"] < best_cost and estimate["amt"] > 0.4 * payment["amount"]:
                            best_cost = estimate["amt"]
                            best_deal = deal
                if best_cost < payment["amount"]:
                    savings += payment["amount"] - best_cost
                    top_deals.append(best_deal)
                    if idx < 4:
                        breakdown_data = {
                            "name": payment["description"],
                            "category": category,
                            "money_spent": payment["amount"],
                            "potential_savings": payment["amount"] - best_cost
                        }
                        breakdown.append(breakdown_data)
            idx += 1
        total_savings.append({"amount": savings,"category": category})
        total_savings_amt += savings
        for d in top_deals:
            dup = False
            for td in total_deals:
                if "link" in d and "link" in td:
                    if d["link"] == td["link"]:
                        dup = True
                else:
                    if d["merchant"] == td["merchant"] and d["description"] == td["description"]:
                        dup = True
            if not dup:
                total_deals.append(d)

    response_data = {
        "breakdown": breakdown,
        "savings_amt": total_savings_amt,
        "savings": total_savings,
        "deals": total_deals,
    }
    return jsonify(response_data)

@app.route('/api/totalPurchases')
def total_purchases():
    customerID = '5b04388a322fa06b677939e0'
    response = list(mongo.db.purchases.find({"payer_id": customerID}))
    sum = 0
    for payment in response:
        sum += payment["amount"]
    return str(sum)


@app.route('/api/getPurchases')
def get_purchases():
    return list(mongo.db.purchases.find({"payer_id": customerID}))


@app.route('/api/getNearbyStore')
#Get JSON response of stores through a Yelp API search of query term near the lat/long values
#URL sample: http://127.0.0.1:5000/api/getNearbyStore?lat=38&long=-77&query=starbucks """
def get_nearby_store():
    response = requests.get(
        "https://api.yelp.com/v3/businesses/search",
        params = {
        'term': request.args.get('query'),
        'latitude': request.args.get('lat'),
        'longitude': request.args.get('long')
        },
        headers = {"Authorization": 'Bearer '  + data.API_KEY,},
        )
    return jsonify(response.json())


# Loads simulated data into the Capital One Nessie API
# @app.route('/api/loadPayments')
# def load_payments():
#     customerID = '5b04388a322fa06b677939e0'
#     url = 'http://api.reimaginebanking.com/accounts/{}/purchases?key={}'.format(customerID, cap1APIkey)
#     merchants = list(mongo.db.merchants.find())
#     d = datetime.strptime("2018-05-24", '%Y-%m-%d')
#     for i in range(180):
#         d = d - timedelta(days=1)
#         num_purchases = randint(0,5)
#         probs = {
#             "chipotle": {
#                 "data": 0.1,
#                 "id": "5b06eef1f0cec56abfa4095e",
#                 "description": "Chipotle Mexican Grill"
#             },
#             "starbucks": {
#             "data": 0.3,
#             "id": "5b06eeeff0cec56abfa40928",
#             "description": "Starbucks"
#             },
#             "kroger": {
#                 "data": 0.35,
#                 "id": "5b06eeeff0cec56abfa40900",
#                 "description": "Kroger"
#             },
#             "gap": {
#                 "data": 0.45,
#                 "id": "5b06eeeff0cec56abfa4091f",
#                 "description": "Gap"
#             },
#             "verizon": {
#                 "data": 0.5,
#                 "id": "5b06eeeff0cec56abfa40927",
#                 "description": "Verizon Wireless"
#             }
#         }
#         for j in range(num_purchases):
#             prob = random()
#             post_data = {
#                 "medium": "balance",
#                 "purchase_date": d.strftime('%Y-%m-%d'),
#                 "status": "pending"
#             }
#             pick = ""
#             if prob < probs["chipotle"]["data"]:
#                 pick = "chipotle"
#             elif prob < probs["starbucks"]["data"]:
#                 pick = "starbucks"
#             elif prob < probs["kroger"]["data"]:
#                 pick = "kroger"
#             elif prob < probs["gap"]["data"]:
#                 pick = "gap"
#             elif prob < probs["verizon"]["data"]:
#                 pick = "verizon"
#             else:
#                 rand_merchant = merchants[randint(0,len(merchants)-1)]
#                 post_data["merchant_id"] = rand_merchant["_id"]
#                 post_data["description"] = rand_merchant["name"]
#                 print("picking random merchant: " + rand_merchant["name"]);
#             if len(pick) > 0:
#                 print("picking {}".format(pick))
#                 post_data["merchant_id"] = probs[pick]["id"]
#                 post_data["description"] = probs[pick]["description"]
#             amount = randint(0,10)
#             merchant_id = post_data["merchant_id"]
#             categories = []
#             for m in merchants:
#                 if merchant_id == m["_id"]:
#                     categories = m["category"]
#             category = " ".join(categories)
#             if "grocery" in category.lower():
#                 amount = randint(0,150)
#             elif "clothing" in category.lower() or "retail" in category.lower():
#                 amount = randint(50,200)
#             else:
#                 amount = randint(0,30)
#             post_data["amount"] = amount
#             response = requests.post(
#             	url,
#             	data=json.dumps(post_data),
#             	headers={'content-type':'application/json'},
#             	)
#             if response.status_code == 201:
#                 print("Payment added")
#     return "payments done..."

# UTILS


def check_pwd(db_string, password):
    """Check if the password matches the db_string."""
    arr = db_string.split('$', 2)
    assert len(arr) == 3
    assert ALGORITHM == arr[0]
    salt = arr[1]
    pwd_hash = arr[2]
    return hash_pwd(salt, password) == pwd_hash


def hash_pwd(salt, password):
    """Create only the hash, not the whole db_string."""
    hash_obj = hashlib.new(ALGORITHM)
    password_salted = salt + password
    hash_obj.update(password_salted.encode('utf-8'))
    password_hash = hash_obj.hexdigest()
    return password_hash


@app.errorhandler(404)
def page_not_found(e):
    context = {}
    if 'logname' not in session:
        context['loggedin'] = 0
    return render_template('404.html'), 404


@app.route('/about')
def about():
    context = {}
    if 'logname' not in session:
        context['loggedin'] = 0
    return render_template("about.html")


def twilio(text):
    # Your Account SID from twilio.com/console
    account_sid = "AC7ed438a23b72fb52b3c5a4a0ba26f468"
    # Your Auth Token from twilio.com/console
    auth_token = "06ef832c1561a0ca4b0c30ab8fdbdd72"

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        to="+13018327995",
        from_="+15172101902",
        body=text)

    print(message.sid)


if __name__ == '__main__':
    app.run()
