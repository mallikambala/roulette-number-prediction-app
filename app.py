import os
import random
from flask import Flask, request, render_template, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "malli_predictor_secure_key")

class NumberPredictor:
    def __init__(self, mode="Normal", last_dozen=None):
        self.mode = mode
        self.last_dozen = last_dozen
        self.past_spins = [] 

    def get_dozen(self, number):
        if number == 0:
            return 0
        elif 1 <= number <= 12: return 1
        elif 13 <= number <= 24: return 2
        elif 25 <= number <= 36: return 3
        raise ValueError("Invalid roulette number")

    def get_recommended_dozens(self, dozen):
        if dozen is None: return None
        if self.mode == "Normal":
            return [1, 2] if dozen == 1 else [2, 3] if dozen == 2 else [3, 1]
        else:  # Recovery Mode
            return [1, 3] if dozen == 1 else [2, 1] if dozen == 2 else [3, 2]

    def _generate_predictions(self, target_dozens):
        if not target_dozens: return None
            
        d1, d2 = target_dozens[0], target_dozens[1]
        remaining_dozen = list({1, 2, 3} - {d1, d2})[0]
        
        dozen_ranges = {
            1: list(range(1, 13)), 2: list(range(13, 25)), 3: list(range(25, 37))
        }
        
        seed_val = "seed_" + "_".join(str(n) for n in self.past_spins)
        random.seed(seed_val)
        pick1 = random.sample(dozen_ranges[d1], 7)
        pick2 = random.sample(dozen_ranges[d2], 7)
        pick3 = random.sample(dozen_ranges[remaining_dozen], 3)
        
        random.seed()
        return sorted(pick1 + pick2 + pick3)

    def process_number(self, number):
        self.past_spins.append(number)
        dozen = self.get_dozen(number)
        
        if self.last_dozen is None:
            self.last_dozen = 1 if dozen == 0 else dozen
            rec_dozens = self.get_recommended_dozens(self.last_dozen)
            return {
                "number": number,
                "dozen": dozen,
                "predicted_numbers": self._generate_predictions(rec_dozens),
                "next_bet": rec_dozens,
                "next_mode": self.mode
            }
        rec_dozens = self.get_recommended_dozens(self.last_dozen)
        if dozen != 0 and (dozen in rec_dozens):
            if self.last_dozen == dozen:
                self.mode = "Normal"
            self.last_dozen = dozen
        else:
            self.mode = "Recovery" if self.mode == "Normal" else "Normal"
            self.last_dozen = 1 if dozen == 0 else dozen
        
        next_rec_dozens = self.get_recommended_dozens(self.last_dozen)
        return {
            "number": number,
            "dozen": dozen,
            "predicted_numbers": self._generate_predictions(next_rec_dozens),
            "next_bet": next_rec_dozens,
            "next_mode": self.mode
        }

roulette_numbers = [
    {"num": 0, "color": "green"}, {"num": 1, "color": "red"}, {"num": 2, "color": "black"}, 
    {"num": 3, "color": "red"}, {"num": 4, "color": "black"}, {"num": 5, "color": "red"}, 
    {"num": 6, "color": "black"}, {"num": 7, "color": "red"}, {"num": 8, "color": "black"}, 
    {"num": 9, "color": "red"}, {"num": 10, "color": "black"}, {"num": 11, "color": "black"}, 
    {"num": 12, "color": "red"}, {"num": 13, "color": "black"}, {"num": 14, "color": "red"}, 
    {"num": 15, "color": "black"}, {"num": 16, "color": "red"}, {"num": 17, "color": "black"}, 
    {"num": 18, "color": "red"}, {"num": 19, "color": "red"}, {"num": 20, "color": "black"}, 
    {"num": 21, "color": "red"}, {"num": 22, "color": "black"}, {"num": 23, "color": "red"}, 
    {"num": 24, "color": "black"}, {"num": 25, "color": "red"}, {"num": 26, "color": "black"}, 
    {"num": 27, "color": "red"}, {"num": 28, "color": "black"}, {"num": 29, "color": "black"}, 
    {"num": 30, "color": "red"}, {"num": 31, "color": "black"}, {"num": 32, "color": "red"}, 
    {"num": 33, "color": "black"}, {"num": 34, "color": "red"}, {"num": 35, "color": "black"}, 
    {"num": 36, "color": "red"}
]

@app.route("/process_click", methods=["POST"])
def process_click():
    numbers = session.get("numbers", [])
    action = request.form.get("action")
    
    if action == "spin":
        numbers.append(int(request.form["number"]))
    elif action == "undo" and numbers:
        numbers.pop()
    elif action == "reset":
        numbers = []
    elif action == "recalc":
        # --- NEW: Deletes the past spins, keeps this round as the new Round 1 ---
        start_row = int(request.form.get("start_row", 0))
        if 0 < start_row <= len(numbers):
            numbers = numbers[start_row-1:]
    
    session["numbers"] = numbers
    
    engine = NumberPredictor()
    history = [engine.process_number(num) for num in numbers]
    
    return {"history": history}

@app.route("/")
def index():
    numbers = session.get("numbers", [])
    engine = NumberPredictor()
    history = [engine.process_number(num) for num in numbers]
    return render_template("index.html", initial_history=history, roulette_numbers=roulette_numbers)

if __name__ == "__main__":
    app.run(debug=True)
