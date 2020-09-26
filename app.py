#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request, Response,
    flash,
    redirect,
    url_for,
    jsonify
)
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
import config
from flask_moment import Moment
from datetime import datetime
from models import (
  db,
  app,
  Venue,
  Artist,
  Show
)

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app.config.from_object("config")
moment = Moment(app)
db.init_app(app)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  """parse date and format it"""
  date = dateutil.parser.parse(value)
  if format == 'full':
      format = "EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format = "EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
  """return: default home page"""
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  """list the venues and number of shows aggregated by city 
  return: venues page"""
    
  cities = Venue.query.distinct(Venue.city, Venue.state).all()
  data = []
  for row in cities:
      city_venues = []
      venues_list = Venue.query.filter(
          Venue.city == row.city, Venue.state == row.state).all()
      for venue in venues_list:
          city_venues.append({
              "id": venue.id,
              "name": venue.name,
              "num_upcoming_shows": len(venue.shows)
          })

      data.append({
          "city": row.city,
          "state": row.state,
          "venues": city_venues
      })

  return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    """search on artists with partial string search. Ensure it is case-insensitive.
    seach for Hop should return "The Musical Hop".
    search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    return: search_venues page"""

    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()

    for venue in venues:
        venue.num_upcoming_shows = len(
            list(filter(lambda s: s.start_time >= datetime.today(), venue.shows)))

    response = {
        "count": len(venues),
        "data": venues
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    
    venue = Venue.query.get(venue_id)
    for show in venue.shows:
        show.artist_name = show.artist.name
        show.artist_image_link = show.artist.image_link
    venue.past_shows = Venue.query.join(Show).filter(
                        Show.venue_id == venue_id,
                        Show.start_time < datetime.now()).all()
    venue.upcoming_shows = Venue.query.join(Show).filter(
                            Show.venue_id == venue_id,
                            Show.start_time >= datetime.now()).all()
    venue.past_shows_count = len(venue.past_shows)
    venue.upcoming_shows_count = len(venue.upcoming_shows)

    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  # create VenueForm and return new_venue page
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    """insert form data as a new Venue record in the db, instead
    on successful db insert, flash success
    on unsuccessful db insert, flash an error instead."""

    try:
        data = request.form.to_dict()
        data["genres"] = ",".join(request.form.getlist("genres"))
        venue = Venue(**data)
        db.session.add(venue)
        db.session.commit()

    except:
        db.session.rollback()
        flash('An error occurred. Venue ' +
              data["name"] + ' could not be listed.')
        print(sys.exc_info())
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    """param venue_id: id of the venue
    use SQLAlchemy ORM to delete a record. 
    Handle cases where the session commit could fail.
    return: None"""

    try:
        venue = Venue.query.get(venue_id)
        venue.delete()
        db.session.commit()

    except:
        db.session.rollback()
        flash('An error occurred. Venue ' +
              data["name"] + ' could not be deleted.')
        print(sys.exc_info())
    else:
        flash('Venue ' + request.form['name'] + ' was successfully deleted!')
    finally:
        db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
  """get a list of all artists from database
  render artists page"""
  artists_list = Artist.query.order_by('id').all()
  data = []
  for artist in artists_list:
      data.append({
          "id": artist.id,
          "name": artist.name
      })
  return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    """search on artists with partial string search. Ensure it is case-insensitive.
    seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    search for "band" should return "The Wild Sax Band"."""
    
    search_term = request.form.get('search_term', '')
    artists = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()

    for artist in artists:
        artist.num_upcoming_shows = len(
            list(filter(lambda s: s.start_time >= datetime.today(), artist.shows)))

    response = {
        "count": len(artists),
        "data": artists
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    """param artist_id: int
    shows the artist page with the given artist_id
    render show_artist page
    """
    artist = Artist.query.get(artist_id)
    artist.past_shows = Artist.query.join(Show).filter(
                            Show.artist_id == artist_id,
                            Show.start_time < datetime.now()).all()
    artist.upcoming_shows = Artist.query.join(Show).filter(
                            Show.artist_id == artist_id,
                            Show.start_time >= datetime.now()).all()
    artist.past_shows_count = len(artist.past_shows)
    artist.upcoming_shows_count = len(artist.upcoming_shows)

    return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    """retrieve artist from database by <artist_id> and
    populate form with fields from artist with ID <artist_id>
    param: artist_id
    return: edit_artist page"""
    
    artist = Artist.query.get(artist_id)
    form = ArtistForm(**artist.__dict__)

    # TODO: 
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    """take values from the form submitted, and update existing
    artist record with ID <artist_id> using the new attributes
    param: artist_id
    return: show_artist page"""

    try:
        data = request.form.to_dict()
        data["genres"] = ",".join(request.form.getlist("genres"))
        artist = Artist.query.get(artist_id)
        for key, value in data.items():
            artist[key] = value

        db.session.commit()

    except:
        db.session.rollback()
        flash('An error occurred. Artist ' +
              data["name"] + ' could not be edited.')
        print(sys.exc_info())
    else:
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    """retrieve venue from database by <venue_id> and
    populate form with fields from artist with ID <venue_id>
    param: artist_id
    return: edit_venue page"""

    venue = Venue.query.get(venue_id)
    form = VenueForm(**venue.__dict__)

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    """take values from the form submitted, and update existing
    venue record with ID <venue_id> using the new attributes
    param: venue_id
    return: show_venue page"""

    try:
        data = request.form.to_dict()
        data["genres"] = ",".join(request.form.getlist("genres"))
        venue = Venue.query.get(venue_id)
        for key, value in data.items():
            venue[key] = value

        db.session.commit()

    except:
        db.session.rollback()
        flash('An error occurred. Venue ' +
              data["name"] + ' could not be edited.')
        print(sys.exc_info())
    else:
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  """create ArtistForm and return new_artist page"""
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    """called upon submitting the new artist listing form
    insert form data as a new Artist record in the db
    on successful db insert, flash success
    on unsuccessful db insert, flash an error instead.
    return: home page"""
    
    try:
        data = request.form.to_dict()
        data["genres"] = ",".join(request.form.getlist("genres"))
        artist = Artist(**data)
        
        db.session.add(artist)
        db.session.commit()

    except:
        db.session.rollback()
        flash('An error occurred. Artist ' +
              data["name"] + ' could not be listed.')
        print(sys.exc_info())
    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    finally:
        db.session.close()

    
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows

    shows_list = Show.query.order_by('venue_id').all()
    data = []
    for show in shows_list:
        artist = Artist.query.get(show.artist_id)
        venue = Venue.query.get(show.venue_id)
        print(show.start_time, type(show.start_time))
        data.append({
            "venue_id": show.venue_id,
            "venue_name": venue.name,
            "artist_id": show.artist_id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(show.start_time)
        })
    
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    """called to create new shows in the db, upon submitting new show listing form
    on successful db insert, flash success
    on unsuccessful db insert, flash an error instead."""

    try:
        data = request.form.to_dict()
        show = Show(**data)
        db.session.add(show)
        db.session.commit()

    except:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
        print(sys.exc_info())
    else:
        flash('Show was successfully listed!')
    finally:
        db.session.close()
    
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
