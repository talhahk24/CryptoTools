
class Strategies:
    def RSI(self, data):
        if data:
            signal = "HOLD"
        else:
            signal = "NO_DATA"
        return signal