from cs50 import SQL
from flask import Flask, render_template, request, redirect
from helpers import instagram_scrapper, save_image, delete_image
import json
from datetime import datetime


app = Flask(__name__)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")


@app.route("/")
def index():
    places_not_gone = db.execute(
        "SELECT * FROM restaurants WHERE id IN (SELECT restaurant_id FROM entries WHERE gone = ?) ORDER BY id DESC",
        0,
    )
    # Replace the None fields for a hyphen(-), for a better vizualization on the template
    for place in places_not_gone:
        for key in place.keys():
            if place[key] is None:
                place[key] = "-"
    return render_template("index.html", places_not_gone=places_not_gone)


# View and update for the restaurant's data
@app.route("/restaurant/<int:id>", methods=["GET", "POST"])
def restaurant(id):
    restaurant = db.execute("SELECT * FROM restaurants WHERE id = ?", id)
    if restaurant:
        # Get the dictionary inside the list
        restaurant = restaurant[0]
        if request.method == "POST":
            restaurant_name = request.form.get("name")
            # name is a required field in database
            if restaurant_name:
                profile_picture = request.files["profile_picture"]
                # verify if there's a new image file to update
                if profile_picture.filename != "":
                    image_path = save_image(profile_picture)
                    # save_image returns None if theres some error
                    if image_path is not None:
                        if restaurant["profile_pic"]:
                            # delete the old image from static folder
                            delete_image(restaurant["profile_pic"])
                        db.execute(
                            "UPDATE restaurants SET name = ?, address = ?, city = ?, profile_pic = ? WHERE id = ?",
                            restaurant_name,
                            request.form.get("address") or None, # If the field is empty, None will be placed instead
                            request.form.get("city") or None,
                            image_path,
                            id,
                        )
                    else:
                        # Error in case the image file updated is invalid
                        return render_template("restaurant.html", restaurant=restaurant, error="File not valid")
                else:
                    # Update without a new image
                    db.execute(
                        "UPDATE restaurants SET name = ?, address = ?, city = ? WHERE id = ?",
                        restaurant_name,
                        request.form.get("address") or None,
                        request.form.get("city") or None,
                        id,
                    )
            else:
                # Error when the validation of name fails on front-end
                return render_template("restaurant.html", restaurant=restaurant, error="Restaurant must have a name")
            
            return redirect(f"/restaurant/{id}")

        else:
            # Replace the None fields for empty(""), for a better vizualization on the template
            for key in restaurant.keys():
                if restaurant[key] is None:
                    restaurant[key] = ""
            return render_template("restaurant.html", restaurant=restaurant)

    else:
        # error when user try to force an access to a invalid restaurant
        return render_template("layout.html", error="Restaurant does not exist")

# update restaraunt's data using the instagram user
@app.route("/update_instagram/<int:id>", methods=["POST"])
def update_instagram(id):
    restaurant = db.execute("SELECT * FROM restaurants WHERE id = ?", id)
    if restaurant:
        # Get the dictionary inside the list
        restaurant = restaurant[0]
        restaurant_user = request.form.get("restaurant_user")
        # restaraute instagram user is a required field in database
        if restaurant_user:
            restaurant_user_id = db.execute(
                "SELECT id FROM restaurants WHERE instagram_user = ?", restaurant_user
            )
            # verify if the instagram_user is alredy in use by another restaurant or if the instagram_user belongs to the resutarant being updated
            # instagram_user is unique row in database
            if not restaurant_user_id or restaurant_user_id[0]["id"] == id:
                restaurant_data = instagram_scrapper(restaurant_user)
                
                # instagram_scrapper retunrs None if theres some error while trying to get the data
                if restaurant_data is not None:
                    # delete
                    delete_image(restaurant["profile_pic"])
                    try:
                        # convert json into python dictionary
                        business_address = json.loads(
                            restaurant_data["business_address_json"]
                        )
                    # typerror may occur if the data scrapped is None
                    except TypeError:
                        business_address = {"street_address": None, "city_name": None}
                    
                    db.execute(
                        "UPDATE restaurants SET name = ?, address = ?, city = ?, bio = ?, profile_pic = ?, instagram_user = ? WHERE id = ?",
                        restaurant_data["full_name"],
                        business_address["street_address"],
                        business_address["city_name"],
                        restaurant_data["biography"],
                        restaurant_data["image_path"],
                        restaurant_user,
                        id,
                    )
                else:
                    # error if the user can't be found on instagram, prepare the data to be showed again
                    for key in restaurant.keys():
                        if restaurant[key] is None:
                            restaurant[key] = ""
                    return render_template("restaurant.html", restaurant=restaurant, error="User can't be found")
            else:
                # error if instagram user already exist on instagram
                for key in restaurant.keys():
                        if restaurant[key] is None:
                            restaurant[key] = ""
                return render_template("restaurant.html", restaurant=restaurant, error="User already exist")
        else:
            # instagram_user can't be null in database
            for key in restaurant.keys():
                if restaurant[key] is None:
                    restaurant[key] = ""
            return render_template("restaurant.html", restaurant=restaurant, error="You must insert a user")
    else:
        # error when user try to force an access to a invalid restaurant
        return render_template("layout.html", error="Restaurant does not exist")
    return redirect(f"/restaurant/{id}")


@app.route("/entries")
def entries():
    # get the data necessary from entries and restarant, also gets the comments 
    # collate nocase = insensitive-case
    entries = db.execute(
        """SELECT restaurants.name, restaurants.profile_pic, entries.id, entries.grade, 
                         entries.gone, entries.favourite, entries.restaurant_id, COUNT(comments.entrie_id) AS number_comments FROM restaurants JOIN entries 
                         ON (restaurants.id = entries.restaurant_id) LEFT JOIN comments on (entries.id = comments.entrie_id) GROUP BY entries.id ORDER BY restaurants.name COLLATE NOCASE"""
    )
    
    tags = db.execute("SELECT * FROM tags ORDER BY name COLLATE NOCASE")

    return render_template("entries.html", entries=entries, tags=tags)

# route called asynchronous inside entries.html
@app.route("/filter")
def tag_filter():
    # get the info through url the ids from the tags
    q = request.args.get("q")
    if q:
        q = list(q.split(","))
        # filter only the entries that have all the tags 
        entries_id = db.execute("SELECT entrie_id FROM categories WHERE tag_id IN (?) GROUP BY entrie_id HAVING COUNT(DISTINCT tag_id) = ?", q, len(q))
        # tranforms the list of dicts in a list
        entries_id = [item['entrie_id'] for item in entries_id]
        
        # get the same data as /entries
        # collate nocase = insensitive-case
        entries = db.execute(
        """SELECT restaurants.name, restaurants.profile_pic, entries.id, entries.grade, 
                         entries.gone, entries.favourite, entries.restaurant_id, COUNT(comments.entrie_id) AS number_comments FROM restaurants JOIN entries 
                         ON (restaurants.id = entries.restaurant_id) LEFT JOIN comments on (entries.id = comments.entrie_id) WHERE entries.id IN (?) GROUP BY entries.id ORDER BY restaurants.name COLLATE NOCASE""", entries_id
    )
        return render_template("filter.html", entries=entries)
    
    # if theres no aruments in th url, just shows all entries without filter
    entries = db.execute(
        """SELECT restaurants.name, restaurants.profile_pic, entries.id, entries.grade, 
                         entries.gone, entries.favourite, entries.restaurant_id, COUNT(comments.entrie_id) AS number_comments FROM restaurants JOIN entries 
                         ON (restaurants.id = entries.restaurant_id) LEFT JOIN comments on (entries.id = comments.entrie_id) GROUP BY entries.id ORDER BY restaurants.name COLLATE NOCASE"""
    )
    
    return render_template("filter.html", entries=entries)
    

# async method to update gone field to 1
@app.route("/gone/<int:id>", methods=["POST"])
def gone(id):
    db.execute("UPDATE entries SET gone = ? WHERE id = ?", 1, id)
    # returns the html for /not_gone
    response = f"""<button type="button" class="btn btn-success" hx-post="/not_gone/{id}" hx-swap="outerHTML">Gone</button>"""
    return response

# async method to update gone field to 0
@app.route("/not_gone/<int:id>", methods=["POST"])
def not_gone(id):
    db.execute("UPDATE entries SET gone = ? WHERE id = ?", 0, id)
    # returns the html for /gone
    response = f"""<button type="button" class="btn btn-secondary" hx-post="/gone/{id}" hx-swap="outerHTML">Not Gone</button>"""
    return response

# async method to update favourite field to 1
@app.route("/favourite/<int:id>", methods=["POST"])
def favourite(id):
    db.execute("UPDATE entries SET favourite = ? WHERE id = ?", 1, id)
    # returns the html for /unfavourite
    response = f"""<input type="image" src="/static/star-solid.svg" width="40px" alt="favourite star" hx-post="/unfavourite/{id}" hx-swap="outerHTML" hx-trigger="click">"""
    return response

# async method to update favourite field to 0
@app.route("/unfavourite/<int:id>", methods=["POST"])
def unfavourite(id):
    db.execute("UPDATE entries SET favourite = ? WHERE id = ?", 0, id)
    # returns the html for /favourite
    response = f"""<input type="image" src="/static/star-regular-2.svg" width="40px" alt="not favourite star" hx-post="/favourite/{id}" hx-swap="outerHTML" hx-trigger="click">"""
    return response

# async method to change the grade
@app.route("/define_grade/<int:id>", methods=["POST"])
def define_grade(id):
    if request.form.get("grade-select"):
        grade = int(request.form.get("grade-select"))
        if grade > 0 and grade < 6:
            db.execute("UPDATE entries SET grade = ? WHERE ID = ?", grade, id)
    return ""


def create_entry(restaurant_id):
    db.execute(
        "INSERT INTO entries (restaurant_id, gone, favourite) VALUES(?, ?, ?)",
        restaurant_id,
        0,
        0,
    )

# route to create a restaurant
@app.route("/add_restaurant", methods=["GET", "POST"])
def add_restaurant():
    if request.method == "POST":
        # a restaraut can be created using instagram user or manually
        radio_add_selector = request.form["restaurant-add"]
        # restaurant validation process if instagram is selected
        if radio_add_selector == "instagram":
            restaurant_user = request.form.get("restaurant_user")
            if restaurant_user:
                # verifies if not instagram_user in the database
                if not db.execute(
                    "SELECT id FROM restaurants WHERE instagram_user = ?",
                    restaurant_user,
                ):
                    restaurant_data = instagram_scrapper(restaurant_user)
                    # instagram_crapper returns None if some error occur
                    if restaurant_data is not None:
                        try:
                            # convert json into python dictionary
                            business_address = json.loads(
                                restaurant_data["business_address_json"]
                            )
                        # typeerror may happen if field is None 
                        except TypeError:
                            business_address = {"street_address": None, "city_name": None}
                            
                        restaurant_id = db.execute(
                            "INSERT INTO restaurants (name, address, city, bio, profile_pic, instagram_user) VALUES( ?, ?, ?, ?, ?, ?)",
                            restaurant_data["full_name"],
                            business_address["street_address"],
                            business_address["city_name"],
                            restaurant_data["biography"],
                            restaurant_data["image_path"],
                            restaurant_user,
                        )
                        # every time a restaurant is created a entrie is also created with it
                        create_entry(restaurant_id)

                        return redirect("/")
                    
                    else:
                        return render_template("add_restaurant.html", error="User can't be found")
                else:
                    return render_template("add_restaurant.html", error="User already exist")
            else:
                # error occurs if front-end validation fails
                return render_template("add_restaurant.html", error="You must insert a user")

        # restaurant validation process if manual is selected
        elif radio_add_selector == "manual":
            restaurant_name = request.form.get("name")
            # restaurant name is a required field
            if not restaurant_name:
                return render_template("add_restaurant.html", error="Restaurant must have a name")

            profile_picture = request.files["profile_picture"]
            if profile_picture.filename != "":
                image_path = save_image(profile_picture)
                # save_image returns None if some error happen when saving the image
                if image_path is None:
                    return render_template("add_restaurant.html", error="File not valid")
            else:
                image_path = None

            restaurant_id = db.execute(
                "INSERT INTO restaurants (name, address, city, profile_pic) VALUES(?, ?, ?, ?)",
                restaurant_name,
                request.form.get("address") or None, #return None if the field is empty
                request.form.get("city") or None,
                image_path,
            )

            # every time a restaurant is created a entrie is also created with it
            create_entry(restaurant_id)

            return redirect("/")

        else:
            # error if radio_add_selector gets a invalid value
            return render_template("add_restaurant.html", error="You have to add a restaurant by instagram or manually")

    else:
        return render_template("add_restaurant.html")


# delete restaraunt inside restaurant.html
@app.route("/delete_restaurant/<int:id>", methods=["POST"])
def delete_restaurant(id):
    restaurant = db.execute("SELECT * FROM restaurants WHERE id = ?", id)
    # make sure if restaurant id really exists in database
    if restaurant:
        entrie_id = db.execute("SELECT id FROM entries WHERE restaurant_id = ?", id)[0]['id']
        delete_image(restaurant[0]["profile_pic"])
        # must delete the comments, categories, and entrie before the restaurat
        db.execute("DELETE FROM comments WHERE entrie_id = ?", entrie_id)
        db.execute("DELETE FROM categories WHERE entrie_id = ?", entrie_id)
        db.execute("DELETE FROM entries WHERE restaurant_id = ?", id)
        db.execute("DELETE FROM restaurants WHERE id = ?", id)
        return redirect("/")
    else:
        return render_template("layout.html", error="Restaurant does not exist")

# shows comments for a restaurant
@app.route("/entrie/<int:id>/comments")
def comments(id):
    if db.execute("SELECT id FROM entries WHERE id = ?", id):
        comments = db.execute("SELECT id, comment, comment_image, STRFTIME('%d/%m/%Y', datetime) AS date FROM comments WHERE entrie_id = ? ORDER BY datetime DESC", id)
        restaurant_data = db.execute("SELECT name, profile_pic FROM restaurants WHERE id = (SELECT restaurant_id FROM entries WHERE id = ?)", id)[0]
        return render_template("comments.html", comments=comments, id=id, restaurant_data=restaurant_data)
    # error if restaurant does not exist in database
    return render_template("layout.html", error="Restaurant does not exist")

# create comments
@app.route("/entrie/<int:id>/add_comment", methods=["GET", "POST"])
def add_comment(id):
    if db.execute("SELECT id FROM entries WHERE id = ?", id):
        if request.method == "POST":
            comment_text = request.form.get("comment_text")
            # error if validation on front-end fails
            if not comment_text:
                return render_template("add_comment.html", id=id, error="Comment must have text")
                        
            comment_picture = request.files["comment_picture"]
            if comment_picture.filename != "":
                image_path = save_image(comment_picture)
                # save_image returns None if theres some error
                if image_path is None:
                    return render_template("add_comment.html", id=id, error="File not valid")
            else:
                image_path = None
                
            db.execute("INSERT INTO comments (comment, comment_image, datetime, entrie_id) VALUES(?, ?, ?, ?)", comment_text, image_path, datetime.now(), id)
            
            return redirect(f"/entrie/{id}/comments")
            
            
        else:
            return render_template("add_comment.html", id=id)
    
    # error if tries to create a comment for a restaurant not in database
    return render_template("layout.html", error="Restaurant does not exist")

@app.route("/delete_comment/<int:id>", methods=["POST"])
def delete_comment(id):
    comment = db.execute("SELECT comment_image, entrie_id FROM comments WHERE id = ?", id)
    # confirms ir comment exists in db
    if comment:
        comment = comment[0]
        delete_image(comment['comment_image'])
        db.execute("DELETE FROM comments WHERE id = ?", id)
        return redirect(f"/entrie/{comment['entrie_id']}/comments")
    else:
        return render_template("layout.html", error="Comment does not exist")
    
# create and view tags
@app.route("/tags", methods=["GET", "POST"])
def tags():
    if request.method == "POST":
        tag_name = request.form.get("tag_name")
        # tag_name is a required field
        if tag_name:
            db.execute("INSERT INTO tags (name) VALUES (?)", tag_name)
            return redirect("/tags")
            
        else:
            # collate nocase = insensitive-case
            tags = db.execute("SELECT * from tags ORDER BY name COLLATE NOCASE")
            error = "Tag must have a name"
            # error if front-end validation fails
            return render_template("tags.html", tags=tags, error=error)
        
    else: 
        tags = db.execute("SELECT * from tags ORDER BY name COLLATE NOCASE")
        return render_template("tags.html", tags=tags)
    
@app.route("/delete_tags", methods=["POST"])
def delete_tags():
    tags_ids = request.form.getlist("tag_button")
    # must delete categories (associative entity between restaurant and tag) befoere delete tags
    db.execute("DELETE FROM categories WHERE tag_id IN (?)", tags_ids)
    db.execute("DELETE FROM tags WHERE id IN (?)", tags_ids)        
    return redirect("/tags")

# associate restaurant with tags
@app.route("/entrie/<int:id>/tags", methods=["GET", "POST"])
def categories(id):
    restaurant_id = db.execute("SELECT restaurant_id FROM entries WHERE id = ?", id)
    # ensure restaurant exists in database
    if restaurant_id:
        restaurant_id = restaurant_id[0]['restaurant_id']
        
        if request.method == "POST":
            tags_ids_selected = request.form.getlist("tag_button")
            # ensure the tags selecte really exists in database
            tags_ids_selected = db.execute("SELECT id from tags WHERE id IN (?)", tags_ids_selected)
            # tags that the entrie has on database through categories table
            tags_ids_categories = db.execute("SELECT tag_id FROM categories WHERE entrie_id = ?", id)
            
            # creates a set with the list of dctionaries returned from database
            tags_ids_selected_set = set(item['id'] for item in tags_ids_selected)
            tags_ids_categories_set = set(item['tag_id'] for item in tags_ids_categories)
            
            # creates a intersection betweend the sets selected on front-end and the tags from the entrie
            intersection = tags_ids_selected_set.intersection(tags_ids_categories_set)
            
            # the operation (-) selected tags and the intersection returns the categories that will be created
            insert = tags_ids_selected_set - intersection
            # the operation (-) existing tags and the intersection returns the categories that will be deleted
            remove = tags_ids_categories_set - intersection
            
            for i in insert:
                db.execute("INSERT INTO categories (entrie_id, tag_id) VALUES (?, ?)", id, i)
            
            for i in remove:
                db.execute("DELETE FROM categories WHERE entrie_id = ? AND tag_id = ?", id, i)
            
            
            
            
            return redirect(f"/entrie/{id}/tags")
    
        else:
            restaurant_data = db.execute("SELECT name, profile_pic FROM restaurants WHERE id = ?", restaurant_id)[0]
            tags = db.execute("SELECT * FROM tags ORDER BY name COLLATE NOCASE")
            categories = db.execute("SELECT tag_id FROM categories WHERE entrie_id = ?", id)
            categories = set(item['tag_id'] for item in categories)
            return render_template("categories.html", tags=tags, categories=categories, restaurant_data=restaurant_data, id=id)
            
    return render_template("layout.html", error="Restaurant does not exist")