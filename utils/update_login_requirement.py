from turtle import update


target = '},{"key":"background-colors"'
to = '},{"key":"need-login","value":"true"},{"key":"background-colors"'

def update_login_requirment(t: str) -> str:
    result = t.replace(target, to)
    return result

if __name__ == "__main__":
    update_login_requirment()