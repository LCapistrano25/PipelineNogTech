import re

def format_cpf(cpf):
    cpf = re.sub(r'\D', '', str(cpf))

    if len(cpf) != 11:
        return None

    return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'