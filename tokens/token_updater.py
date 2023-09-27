def update_reset_password_token(db, user_id:int, token:str):
    user = get_user(user_id, db)
    user.reset_password_token = token
    db.commit()
    db.refresh(user)
    return user