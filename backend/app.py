from flask import Flask, request, jsonify, render_template, url_for
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect 
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
from sentiment import analyze_sentiment
from keys import GOOGLE_KEY, GOOGLE_SEARCH_ID, ADMIN_USERNAME, ADMIN_PASSWORD, ids
import requests

app = Flask(__name__)
CORS(app)
csrf = CSRFProtect(app)

# Setup WebDriver
global_url = ""
global_following = [] # stores followed accounts
global_users = {} # global_users[user] = global_tweets
tweet_ids = []
driver = webdriver.Chrome()

@app.route('/twitter/info', methods=["POST"])
@csrf.exempt
def get_twitter_info():
    try:
      global_url = request.form.get("link")
      split_url = global_url.split("/")
      username = split_url[-1]
      users = login_to_twitter(global_url)


      # print("FOR LOOP")
      # for user in global_following[1:4]:
      #    print(user)
      #    tweet = get_last_tweet(user)
      #    new_user = extract_tweet_text(tweet)
      #    global_users[f"User {count}"] = new_user
      #    count += 1

      # for user in global_users.values():
      #    print(user)

      driver.quit()

      return jsonify({
         "status": "valid",
         "users": users
      })
    
    except Exception as e:
        return jsonify({
            "status": "Invalid",
            "error": str(e)
        })

# Function to log in to Twitter
def login_to_twitter(url):
#    global_username = username
#    # Navigate to the Twitter login page
#    global_url = f'https://twitter.com/{username}'
#    sleep(2)
   
   driver.get(url)
   sleep(2)
   # Enter username
   username_input = driver.find_element(By.NAME, "text")
   username_input.send_keys(ADMIN_USERNAME)
   username_input.send_keys(Keys.RETURN)
   sleep(2)
   
   # Enter password
   password_input = driver.find_element(By.NAME, "password")
   password_input.send_keys(ADMIN_PASSWORD)
   password_input.send_keys(Keys.RETURN)
   sleep(2)

   following_url = url + "/following"

   driver.get(following_url)
   sleep(2)  # Allow page to load

   body = driver.find_element(By.TAG_NAME, 'body')
   body_text = body.text
   body_lines = body_text.split("\n")
   sleep(2)  # Allow page to load

   for line in body_lines:
      if line[0] == '@':
         global_following.append(line.replace('@', ''))

   users = []
   for i in range(1, len(global_following)):
      tweet = get_last_tweet(global_following[i])
      new_user = extract_tweet_text(tweet)
      new_user['id'] = ids[i-1]
      users.append(new_user)
   
   return users

def get_url(username):
   return f"https://twitter.com/{username}"

def extract_tweet_text(tweet_array):
   user = {}
   if tweet_array[0] == 'Pinned':
      user['real_name'] = tweet_array[1]
      user['username'] = tweet_array[2]
      tweet_text = " ".join(tweet_array[5:])
      user['tweet'] = tweet_text
      user['sentiment'] = analyze_sentiment(tweet_text)
   else:
      user['real_name'] = tweet_array[0]
      user['username'] = tweet_array[1]
      tweet_text = " ".join(tweet_array[4:])
      user['tweet'] = tweet_text
      user['sentiment'] = analyze_sentiment(tweet_text)
   
   return user

def get_last_tweet(username):
   follow_url = get_url(username)
   driver.get(follow_url)
   # Wait for the tweets to load on the page
   WebDriverWait(driver, 4).until(
      EC.presence_of_all_elements_located((By.XPATH, '//article[@data-testid="tweet"]'))
   )

   tweets = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')

   # Loop through the tweets and get the text, stopping after the fifth tweet
   tweet_text = tweets[0].text
   tweet_text = tweet_text.split('\n')
   tweet = tweet_text
   #maybe delete this
   for t in tweet:
      t = t[:-1]

   return tweet


@app.route('/get/resources', methods=["POST"])
@csrf.exempt
def get_resources():
   tweet = request.form.get("tweet")
   search_query = "How can i help someone going through this: " + tweet

   url = 'https://www.googleapis.com/customsearch/v1'
   params = {
      "key": GOOGLE_KEY,
      "cx": GOOGLE_SEARCH_ID,
      "q": search_query
   }

   response = requests.get(url, params=params)
   results = response.json()["items"]
   print(results)
   res = []
   for i in range(3):
      res.append(results[i]["link"])
      print(results[i])

   return jsonify({
      "status": "valid",
      "results": res
   })