from src.utils.Token import AccesToken, RefreshToken


def create_access_and_refresh_token(user, save=True):
    a = AccesToken(user)
    r = RefreshToken(user)
    if save:
        a.save_to_user()
        r.save_to_user()
    return a, r