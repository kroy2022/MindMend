from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    if request.method == 'POST':
        income = float(request.form.get('income'))
        expenses = float(request.form.get('expenses'))
        savings = float(request.form.get('savings'))
        tax_rate = float(request.form.get('tax_rate'))

        net_income = income - (expenses*12)
        tax_amount = net_income * tax_rate
        final_savings = net_income - tax_amount
        if final_savings > savings: 
            return f"You are ahead of schedule! You save {final_savings - savings} more than your goal!"
        else:
            return f"You currently save {savings - final_savings} less than your goal."

    return render_template('info.html')


if __name__ == '__main__':
    app.run(debug=True)
 