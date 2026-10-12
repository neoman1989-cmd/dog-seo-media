"""JPY 3000 hard local ceiling; unknown rates, baseline or usage halt live work."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import json
from pathlib import Path
import uuid
from zoneinfo import ZoneInfo

LIMIT = Decimal('3000')


def amount(value):
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError('Invalid cost') from None
    if not result.is_finite() or result < 0: raise ValueError('Unknown or invalid cost')
    return result


def month(now):
    return now.astimezone(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m')


class Budget:
    def __init__(self, config_path, now=None):
        self.config = json.loads(Path(config_path).read_text())
        self.now = now or datetime.now(timezone.utc)

    def reserve(self, state, model, messages, max_tokens):
        c = self.config
        current = month(self.now)
        observed = datetime.fromisoformat(c['observed_at'])
        expires = datetime.fromisoformat(c['rates_valid_until'])
        if observed.tzinfo is None or expires.tzinfo is None:
            raise ValueError('Budget timestamps require timezone')
        if c['month_jst'] != current or month(observed) != current or not 0 <= (self.now-observed).total_seconds() <= 86400 or expires < self.now:
            raise ValueError('Stale spending baseline or pricing')
        if c.get('exclusive_project') is not True:
            raise ValueError('Dedicated project with no other spend is required')
        rates = c['models'][model]
        input_rate, output_rate, fx = (amount(rates['input_usd_per_million']), amount(rates['output_usd_per_million']), amount(c['usd_jpy_upper_bound']))
        if min(input_rate, output_rate, fx) <= 0: raise ValueError('Unknown pricing or exchange rate')
        # UTF-8 bytes bound content tokens conservatively; reserve extra protocol overhead.
        upper_input = len(json.dumps(messages,ensure_ascii=False).encode('utf-8')) + 4096
        estimate = ((Decimal(upper_input)*input_rate + Decimal(max_tokens)*output_rate) / 1000000 * fx).quantize(Decimal('.01'), rounding=ROUND_CEILING)
        spent = amount(c['month_spend_jpy_upper_bound'])
        for request in state.data['requests'].values():
            if request['month'] == current:
                if request['status'] == 'unknown': raise ValueError('Unreconciled API usage; live generation stopped')
                spent += amount(request['reserved_jpy'])
        # Never release reservations, even on success: conservative upper-bound accounting.
        if spent + estimate > LIMIT: raise ValueError('Monthly OpenAI budget would exceed JPY 3000')
        request_id = uuid.uuid4().hex
        state.data['requests'][request_id] = {'month':current,'reserved_jpy':str(estimate),'status':'unknown','input_upper':upper_input,'max_tokens':max_tokens}
        state.save()
        return request_id

    def confirm(self, state, request_id, result):
        reservation = state.data['requests'][request_id]
        usage = result.get('usage', {})
        prompt, completion = usage.get('prompt_tokens'), usage.get('completion_tokens')
        if type(prompt) is not int or type(completion) is not int or not 0 <= prompt <= reservation['input_upper'] or not 0 <= completion <= reservation['max_tokens']:
            raise ValueError('Usage missing or outside estimate; stopped for reconciliation')
        reservation['status'] = 'confirmed'
        reservation['usage'] = {'prompt_tokens':prompt,'completion_tokens':completion}
        state.save()
