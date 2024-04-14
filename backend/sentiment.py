from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax

# Initialize the tokenizer and model
MODEL = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSequenceClassification.from_pretrained(MODEL)

def analyze_sentiment(text):
   """
   Analyze the sentiment of the given text using RoBERTa model.
   
   Args:
   text (str): The text to analyze.

   Returns:
   float: A float value containing the dominant sentiment from the input text.
   """
   # Encode the text
   encoded_input = tokenizer(text, return_tensors='pt')

   # Get output from the model
   output = model(**encoded_input)

   # Extract logits and apply softmax
   logits = output.logits
   probabilities = softmax(logits.detach().numpy()[0])

   # Prepare the scores dictionary
   scores_dict = {
      'negative': probabilities[0],
      'neutral': probabilities[1],
      'positive': probabilities[2]
   }

   dominant_sentiment = max(scores_dict, key=scores_dict.get)
   return dominant_sentiment