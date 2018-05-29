# Kickback

What is Kickback?
<br>
<br>
Kickback reviews your purchase behavior and transaction history, figures out what you like to buy, and makes spending cheaper with personalized discounts developed with our custom recommendation engine.

Our main feature lies in our web application's dashboard. Through this, a user can identify how much money they have saved by utilizing our discount engine, analyzing where their money goes each month, viewing their favorite merchants / places to shop, pursuing recommended discounts, and much more. We also provide an exploration tab that shows users different discounts based on their location.

#### The Landing Page

<img src="https://preview.ibb.co/crAgRT/Screen_Shot_2018_05_25_at_3_51_13_AM.png">

<img src="https://preview.ibb.co/cHY1RT/Screen_Shot_2018_05_25_at_3_51_33_AM.png">

#### The Dashboard

<img src="https://preview.ibb.co/grUY6T/Screen_Shot_2018_05_25_at_3_48_26_AM.png">

#### The Explore Page

<img src="https://preview.ibb.co/iiAbt8/Screen_Shot_2018_05_25_at_3_50_08_AM.png">

### How It Works
Kickback works by using a four-stage algorithmic pipeline to accurately identify store discounts most relevant to your daily routine.

In the first stage, Kickback reads in your transaction history through the Capital One Nessie API. Using this data, our algorithm analyzes which merchants you spend most of your money and time at and consequently predicts how you will spend in the future.

In the second stage, our application uses the Visa Developer API to categorize all transactions into distinct sets such as fast food restaurants, fashion, lifestyle, etc.

In the third stage, Kickback uses data scraped from multiple discount aggregation sites and attempts to find discounts that will provide the most cash back for a user while allowing the user to still maintain their normal spending habits.

Lastly, the algorithm filters our discount recommendations to provide the most cost-saving strategy to the user.

All of this is provided to the client using a RESTful server architecture.

### Problems We Ran Into
- Not being able to use real credit card data
- No openly accessible training data for our recommendation engine
- Learning new technologies in a short timespan

### Things We Learned
We learned a lot about dealing with various APIs and how to integrate them together to create a professional web application. As we approached our project with a data-driven mindset, we came to realize that data is not very clean or standardized on the web, and learned many good practices when it comes to dealing with the disparity between data sources.

### Technologies Used
- Frontend: [Bulma](https://bulma.io/)
- Backend: [Flask](http://flask.pocoo.org/)
- Hosting: [AWS](https://aws.amazon.com/)
- Database: [MongoDb](https://www.mongodb.com/), [mLab](https://mlab.com/home)

### Setup:
- Clone the repository
- Enter the project directory
- Create a python3 virtual environment: python3 -m venv env
- Enter the virtual environment: source env/bin/activate
- Upgrade pip: pip install --upgrade pip
- Download requirments: pip install -r requirements.txt
- Run the application: bin/kickbackrun
- Navigate to the application at http://localhost:8000/
