# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json

class CryptoPredictionMarket(gl.Contract):
    predictions: TreeMap[str, str]
    scores: TreeMap[str, str]
    resolved: bool
    crypto: str
    target_date: str
    start_price: str
    final_price: str
    direction: str

    def __init__(self, crypto: str, target_date: str, start_price: str):
        self.crypto = crypto
        self.target_date = target_date
        self.start_price = start_price
        self.predictions = TreeMap()
        self.scores = TreeMap()
        self.resolved = False
        self.final_price = ""
        self.direction = ""

    @gl.public.write
    def make_prediction(self, player: str, prediction: str) -> str:
        if self.resolved:
            raise Exception("Market already resolved!")
        if prediction not in ["UP", "DOWN"]:
            raise Exception("Must be UP or DOWN!")
        if player in self.predictions:
            raise Exception("Already predicted!")
        self.predictions[player] = prediction
        return (
            player + " predicted " + self.crypto
            + " will go " + prediction
            + " from $" + self.start_price
        )

    @gl.public.write
    def resolve_market(self) -> str:
        if self.resolved:
            raise Exception("Already resolved!")

        crypto = self.crypto
        start_price = self.start_price
        target_date = self.target_date

        coin_id = "bitcoin" if crypto == "BTC" else "ethereum"
        price_url = (
            "https://api.coingecko.com/api/v3/coins/"
            + coin_id
            + "/history?date="
            + target_date
            + "&localization=false"
        )

        def get_direction():
            web_data = gl.nondet.web.render(
                price_url, mode="text"
            )
            result = gl.nondet.exec_prompt(
                "From this CoinGecko price data for "
                + crypto + " on " + target_date
                + ", the starting price was $" + start_price
                + ". Find the current price and determine "
                + "if it went UP or DOWN. "
                + "Reply ONLY with this exact JSON: "
                + '{"final_price": "50000", "direction": "UP"}'
                + " . Data: " + str(web_data)[:2000],
                response_format="json"
            )
            return json.dumps(result, sort_keys=True)

        raw = gl.eq_principle.strict_eq(get_direction)
        result = json.loads(raw)

        self.final_price = str(result["final_price"])
        self.direction = str(result["direction"])

        correct = 0
        wrong = 0
        for player in self.predictions:
            pred = self.predictions[player]
            if pred == self.direction:
                self.scores[player] = "WIN-10pts"
                correct += 1
            else:
                self.scores[player] = "LOSS-0pts"
                wrong += 1

        self.resolved = True
        return (
            "Resolved! " + crypto + " went "
            + self.direction + " to $" + self.final_price
            + ". Winners: " + str(correct)
            + " Losers: " + str(wrong)
        )

    @gl.public.view
    def get_my_result(self, player: str) -> str:
        if not self.resolved:
            return "Not resolved yet"
        if player not in self.scores:
            return "Player not found"
        return self.scores[player]

    @gl.public.view
    def get_market_info(self) -> str:
        return (
            "Crypto: " + self.crypto
            + " | Start: $" + self.start_price
            + " | Date: " + self.target_date
            + " | Resolved: " + str(self.resolved)
            + " | Players: " + str(len(self.predictions))
        )
