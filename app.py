# ==========================================
# USER PROFILE
# ==========================================

@app.route("/profile", methods=["GET", "POST"])
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()

    # Get current user
    user = conn.execute(
        "SELECT * FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()

    if request.method == "POST":

        action = request.form.get("action")

        # ==========================================
        # UPDATE NAME
        # ==========================================

        if action == "update_name":

            name = request.form["name"].strip()

            if not name:
                conn.close()
                return "Name cannot be empty!"

            conn.execute(
                """
                UPDATE users
                SET name = ?
                WHERE id = ?
                """,
                (name, user_id)
            )

            conn.commit()

            # Update session name also
            session["user_name"] = name

            conn.close()

            return redirect(url_for("profile"))

        # ==========================================
        # CHANGE PASSWORD
        # ==========================================

        if action == "change_password":

            current_password = request.form["current_password"]
            new_password = request.form["new_password"]
            confirm_password = request.form["confirm_password"]

            # Check current password
            if not check_password_hash(
                user["password"],
                current_password
            ):
                conn.close()
                return "Current password is incorrect!"

            # Check new password
            if len(new_password) < 6:
                conn.close()
                return "New password must contain at least 6 characters!"

            # Check password match
            if new_password != confirm_password:
                conn.close()
                return "New password and confirm password do not match!"

            # Hash new password
            hashed_password = generate_password_hash(
                new_password
            )

            conn.execute(
                """
                UPDATE users
                SET password = ?
                WHERE id = ?
                """,
                (hashed_password, user_id)
            )

            conn.commit()
            conn.close()

            return redirect(url_for("profile"))

    conn.close()

    return render_template(
        "profile.html",
        user=user
    )
