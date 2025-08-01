target = '"domDataset":[{"'
to = '"domDataset":[{"key":"need-login","value":"true"},{"'

def update_login_requirment(t: str) -> str:
    result = t.replace(target, to)
    return result

if __name__ == "__main__":
    update_login_requirment()