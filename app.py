from flask import Flask, render_template, request, jsonify, session
import sqlite3
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Ensure you set a secret key
DATABASE = 'casino.db'


# Database setup
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE,
                            balance INTEGER DEFAULT 1000
                        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            game TEXT,
                            result TEXT,
                            amount INTEGER,
                            FOREIGN KEY(user_id) REFERENCES users(id)
                        )''')


def create_deck():
    """Creates a standard deck of cards."""
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']
    suits = ['hearts', 'diamonds', 'clubs', 'spades']
    return [{'rank': rank, 'suit': suit} for rank in ranks for suit in suits]


def calculate_hand_value(hand):
    """Calculates the value of a Blackjack hand."""
    value = 0
    aces = 0
    for card in hand:
        if card['rank'].isdigit():
            value += int(card['rank'])
        elif card['rank'] in ['jack', 'queen', 'king']:
            value += 10
        else:  # Ace
            aces += 1

    # Add aces as 11 first, then adjust if needed
    for _ in range(aces):
        if value + 11 > 21:
            value += 1
        else:
            value += 11

    return value


def is_soft_hand(hand):
    """Check if the hand is a soft hand (contains an Ace valued as 11)."""
    return any(card['rank'] == 'ace' for card in hand) and calculate_hand_value(hand) <= 17


roulette_numbers = {
    0: "green",
    1: "red", 2: "black", 3: "red", 4: "black", 5: "red", 6: "black",
    7: "red", 8: "black", 9: "red", 10: "black", 11: "black", 12: "red",
    13: "black", 14: "red", 15: "black", 16: "red", 17: "black", 18: "red",
    19: "red", 20: "black", 21: "red", 22: "black", 23: "red", 24: "black",
    25: "red", 26: "black", 27: "red", 28: "black", 29: "black", 30: "red",
    31: "black", 32: "red", 33: "black", 34: "red", 35: "black", 36: "red"
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/blackjack', methods=['GET', 'POST'])
def blackjack():
    if request.method == 'POST':
        action = request.json.get('action', None)
        session = request.json.get('session', None)

        if not session or action == 'new_game':
            deck = create_deck()
            random.shuffle(deck)
            player_hand = [deck.pop(), deck.pop()]
            dealer_hand = [deck.pop(), deck.pop()]
            session = {'deck': deck, 'player_hand': player_hand, 'dealer_hand': dealer_hand}

        else:
            deck = session['deck']
            player_hand = session['player_hand']
            dealer_hand = session['dealer_hand']

        if action == 'hit':
            player_hand.append(deck.pop())
            if calculate_hand_value(player_hand) > 21:
                return jsonify({'result': 'bust', 'session': session, 'player_hand': player_hand, 'dealer_hand': dealer_hand})

        if action == 'stand':
            while calculate_hand_value(dealer_hand) < 17 or (is_soft_hand(dealer_hand) and calculate_hand_value(dealer_hand) == 17):
                dealer_hand.append(deck.pop())

            player_total = calculate_hand_value(player_hand)
            dealer_total = calculate_hand_value(dealer_hand)

            if dealer_total > 21 or player_total > dealer_total:
                return jsonify({'result': 'win', 'session': session, 'player_hand': player_hand, 'dealer_hand': dealer_hand})
            elif player_total < dealer_total:
                return jsonify({'result': 'lose', 'session': session, 'player_hand': player_hand, 'dealer_hand': dealer_hand})
            else:
                return jsonify({'result': 'push', 'session': session, 'player_hand': player_hand, 'dealer_hand': dealer_hand})

        return jsonify({'session': session, 'player_hand': player_hand, 'dealer_hand': dealer_hand})

    return render_template('blackjack.html')


@app.route('/refresh_game', methods=['POST'])
def refresh_game():
    """Resets the game state by reshuffling the deck and dealing new cards."""
    deck = create_deck()
    random.shuffle(deck)
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    session = {'deck': deck, 'player_hand': player_hand, 'dealer_hand': dealer_hand}
    return jsonify({'session': session, 'player_hand': player_hand, 'dealer_hand': dealer_hand})


@app.route("/roulette")
def roulette():
    return render_template("roulette.html")

@app.route("/roulette/spin", methods=["POST"])
def spin():
    # Spin the wheel
    winning_number = random.choice(list(roulette_numbers.keys()))
    color = roulette_numbers[winning_number]

    # Process the player's bet
    bet_type = request.json.get("bet_type")
    bet_value = request.json.get("bet_value")

    result = {
        "winning_number": winning_number,
        "color": color,
        "won": False,
        "message": "You lost!"
    }

    # Check if the player won
    if bet_type == "number" and int(bet_value) == winning_number:
        result["won"] = True
        result["message"] = f"You won! The number was {winning_number}."
    elif bet_type == "color" and bet_value.lower() == color:
        result["won"] = True
        result["message"] = f"You won! The color was {color}."

    return jsonify(result)


@app.route('/slots', methods=['GET', 'POST'])
def slots():
    if request.method == 'POST':
        symbols = ['🍒', '🔔', '7️⃣', '⭐', '🍋']
        result = [random.choice(symbols) for _ in range(3)]
        if len(set(result)) == 1:
            payout = 100
            game_result = "win"
        else:
            payout = 0
            game_result = "lose"
        return jsonify({'result': game_result, 'symbols': result, 'payout': payout})
    return render_template('slots.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
