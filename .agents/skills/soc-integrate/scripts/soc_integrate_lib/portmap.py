"""Exact and ordered template port mappings."""
import re

CAPTURE_REFERENCE = re.compile('\\$(\\d+)')


class PortMap:
    """Exact instance keys, legacy module keys, then ordered template rules."""
    def __init__(self, data=None):
        data = data or {}
        self.data = data if any(k in data for k in ('mappings', 'templates', 'domains', 'annotations', 'instances', 'synchronizers', 'interfaces', 'bus_interfaces')) else {'mappings': data}
        self.mappings = self.data.get('mappings', {})
        self.rules = []
        self.exact = {}
        for key, value in self.mappings.items():
            if key.startswith(('regex:', 'glob:')) or any(c in key for c in '*?()\\'):
                kind, pattern = key.split(':', 1) if key.startswith(('regex:', 'glob:')) else ('regex' if any(c in key for c in '()\\') else 'glob', key)
                self.rules.append((kind, pattern, value))
            else:
                self.exact[key] = value
        for rule in self.data.get('templates', []):
            kind = 'regex' if 'regex' in rule else 'glob'
            self.rules.append((kind, rule[kind], rule.get('value')))

        self.compiled = []
        for kind, pattern, value in self.rules:
            regex = ''.join('(.*)' if c == '*' else '(.)' if c == '?' else re.escape(c) for c in pattern) if kind == 'glob' else pattern
            try:
                self.compiled.append((re.compile(regex), pattern, value))
            except re.error as exc:
                raise ValueError(f'template {pattern!r}: invalid regex: {exc}') from None

    def lookup(self, instance, module, port):
        for key in (f'{instance}.{port}', f'{module}.{port}'):
            if key in self.exact:
                return True, self.exact[key]
        key = f'{instance}.{port}'
        for regex, pattern, value in self.compiled:
            match = regex.fullmatch(key)
            if match:
                def replace(text):
                    def capture(group):
                        number = int(group[1])
                        if number > len(match.groups()):
                            raise ValueError(f'template {pattern!r}: missing capture ${number}')
                        return match[number] or ''
                    return CAPTURE_REFERENCE.sub(capture, text)
                if isinstance(value, str):
                    value = replace(value)
                elif isinstance(value, dict):
                    value = {k: replace(v) if isinstance(v, str) else v for k, v in value.items()}
                return True, value
        return False, None
