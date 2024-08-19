# BUCKET MENU
### CS50 Final Projetct 
#### Video Demo:  [YouTube Video For The Project](https://www.youtube.com/watch?v=oWKbEwkCoUc)
#### Description:

**Menu Journal** is a web app built with **Flask** designed to be a personal journal for restaurants, bars, cafes, and any other place that serves food and drinks. With this app, you can save all the restaurants you want to visit, categorize and rate the ones you have already visited, create comments, and add photos to remember the best dishes and drinks from your favorite places. It’s your quick-access journal to keep track of the places you like and an easy way to view the restaurants you want to visit.

### Main Features of Menu Journal:

- Add Restaurants using the restaurant's Instagram user:

   The place is added automatically by fetching information from the social media page. The data stored using this method includes:

  - Name
  - Profile Picture
  - Bio
  - Address
  - City

- Add Restaurants manually:

   In this scenario, you can manually input the restaurant's information. The fields in this case are:

  - Name
  - Profile Picture (accepts JPG and HEIC files)
  - Address
  - City

- **Edit or Delete a restaurant:** It’s possible to update a restaurant's data using an Instagram user, regardless of whether the place was added via Instagram or manually.

- **Manage your entries:** Every time a restaurant is added, an *entry* related to it is also created. In this entry, you can mark whether you have *visited or not visited* the restaurant, *favorite* it, or *unfavorite* it, and give it a *rating between 1 and 5*.

- **Create Comments about the restaurants:** Each comment allows you to add text and an image.

- **Delete Comments**

- **Create Tags:** You can add your own tags to organize all the places, and categorize each restaurant the way you want, multiple tags can be assigned or removed to a restaurant.

- **Filter through Tags:** On the Entries page is possible to filter restaurants usings the tags you've created.

- **Delete Tags**

- **The app homepage is the My List page:** It displays a list of places marked as *not visited*, so when you open the app, you can quickly look for new places you may want to go to.

#### Files:

**app.py** is the main project file. It handles the routes and interactions with the database. The SQL module from the CS50 library gives access to the database. It is also responsible for validating any information from the templates, preventing misinformation in the database, and redirecting or guiding the user along the correct path.

**helpers.py** contains functions called in **app.py** to prepare data before saving it in the database. Its main tasks include:

- Naming, saving, removing, and validating image files
  - The PIL library validates image formats and saves them as JPG.
- Instagram scraping
  - Using the requests library

The **templates folder** contains all the *HTML* files for this project. The libraries used in these files are Bootstrap, JQuery, and HTMX.