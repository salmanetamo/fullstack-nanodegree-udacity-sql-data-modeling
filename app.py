# ---------------------------------------------------------------------------- #
# Imports
# ---------------------------------------------------------------------------- #
import sys

import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from config import SQLALCHEMY_DATABASE_URI
from forms import *
from models import Venue, Artist, Show, db

# ---------------------------------------------------------------------------- #
# App Config.
# ---------------------------------------------------------------------------- #


app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

# Database setup
db.init_app(app)
migrate = Migrate(app, db)

# ---------------------------------------------------------------------------- #
# Filters.
# ---------------------------------------------------------------------------- #
def format_datetime(value, format='medium'):
    # Added a small fix from StackOverflow to parse dates
    # https://stackoverflow.com/questions/63269150/typeerror-parser-must-be-a-string-or-character-stream-not-datetime

    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ---------------------------------------------------------------------------- #
# Controllers.
# ---------------------------------------------------------------------------- #
@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------
@app.route('/venues')
def venues():
    venues_grouped_by_cities = db.session.query(Venue.city, Venue.state).group_by('city', 'state')
    data = []

    for group in venues_grouped_by_cities:
        venues_data = []
        venues_in_city = db.session.query(Venue)\
            .filter(Venue.city == group.city)\
            .filter(Venue.state == group.state)
        for venue in venues_in_city:
            venue_data = extract_displayed_fields_from_venue_or_artist(venue)
            venues_data.append(venue_data)
        if len(venues_data) > 0:
            city_data = {
                'city': group.city,
                'state': group.state,
                'venues': venues_data
            }
            data.append(city_data)
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    matches = Venue.query.filter(Venue.name.ilike('%' + request.form.get("search_term", "") + '%')).all()
    venues_data = []
    for venue in matches:
        venue_data = extract_displayed_fields_from_venue_or_artist(venue)
        venues_data.append(venue_data)
    response = {
        'count': len(venues_data),
        'data': venues_data
    }
    return render_template(
        'pages/search_venues.html',
        results=response,
        search_term=request.form.get('search_term', '')
    )


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    data = get_venue_map(venue)

    return render_template('pages/show_venue.html', venue=data)


def get_venue_map(venue, include_shows=True):
    upcoming_shows = list(filter(lambda show: datetime.now() < show.start_time.replace(tzinfo=None), venue.shows))
    past_shows = list(filter(lambda show: datetime.now() >= show.start_time.replace(tzinfo=None), venue.shows))
    upcoming_shows_data = extract_show_data_for_venue(upcoming_shows)
    past_shows_data = extract_show_data_for_venue(past_shows)
    venue_map = {
        'id': venue.id,
        'name': venue.name,
        'genres': venue.genres,
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website_link,
        'facebook_link': venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description,
        'image_link': venue.image_link,
    }
    if include_shows:
        venue_map['past_shows'] = past_shows_data
        venue_map['past_shows_count'] = len(past_shows_data)
        venue_map['upcoming_shows'] = upcoming_shows_data
        venue_map['upcoming_shows_count'] = len(upcoming_shows_data)
    return venue_map

#  Create Venue
#  ----------------------------------------------------------------
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    data = None
    try:
        data = Venue(
            name=request.form['name'],
            city=request.form['city'],
            state=request.form['state'],
            address=request.form['address'],
            phone=request.form['phone'],
            image_link=request.form['image_link'],
            facebook_link=request.form['facebook_link'],
            website_link=request.form['website_link'],
            seeking_talent=request.form['seeking_talent'] == 'y',
            seeking_description=request.form['seeking_description'],
            genres=','.join(request.form.getlist('genres'))
        )
        db.session.add(data)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()

    return jsonify({'success': True})


def extract_displayed_fields_from_venue_or_artist(venue_or_artist):
    upcoming_shows = list(filter(lambda show: datetime.now() < show.start_time.replace(tzinfo=None), venue_or_artist.shows))
    return {
        'id': venue_or_artist.id,
        'name': venue_or_artist.name,
        'num_upcoming_shows': len(upcoming_shows),
    }


def extract_show_data_for_venue(shows_from_db):
    shows_data = []
    for show in shows_from_db:
        shows_data.append({
            'artist_id': show.artist.id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time
        })
    return shows_data

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists_from_db = Artist.query.all()
    data = []
    for artist in artists_from_db:
        data.append({
            'id': artist.id,
            'name': artist.name,
        })
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    matches = Artist.query.filter(Artist.name.ilike('%' + request.form.get("search_term", "") + '%')).all()
    artists_data = []
    for artist in matches:
        artist_data = extract_displayed_fields_from_venue_or_artist(artist)
        artists_data.append(artist_data)
    response = {
        'count': len(artists_data),
        'data': artists_data
    }
    return render_template(
        'pages/search_artists.html',
        results=response,
        search_term=request.form.get('search_term', '')
    )


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    data = get_artist_map(artist)

    return render_template('pages/show_artist.html', artist=data)


def get_artist_map(artist, include_shows=True):
    upcoming_shows = list(filter(lambda show: datetime.now() < show.start_time.replace(tzinfo=None), artist.shows))
    upcoming_shows_data = extract_show_data_for_artist(upcoming_shows)
    past_shows = list(filter(lambda show: datetime.now() >= show.start_time.replace(tzinfo=None), artist.shows))
    past_shows_data = extract_show_data_for_artist(past_shows)
    artist_map = {
        'id': artist.id,
        'name': artist.name,
        'genres': artist.genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
    }
    if include_shows:
        artist_map['past_shows'] = past_shows_data
        artist_map['past_shows_count'] = len(past_shows_data)
        artist_map['upcoming_shows'] = upcoming_shows_data
        artist_map['upcoming_shows_count'] = len(upcoming_shows_data)
    return artist_map


def extract_show_data_for_artist(shows_from_db):
    shows_data = []
    for show in shows_from_db:
        shows_data.append({
            'venue_id': show.venue.id,
            'venue_name': show.venue.name,
            'venue_image_link': show.artist.image_link,
            'start_time': show.start_time
        })
    return shows_data


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist_from_db = Artist.query.get(artist_id)
    artist = get_artist_map(artist_from_db, False)

    form = ArtistForm()
    form.name.data = artist['name']
    form.genres.data = artist['genres']
    form.city.data = artist['city']
    form.state.data = artist['state']
    form.phone.data = artist['phone']
    form.website_link.data = artist['website']
    form.facebook_link.data = artist['facebook_link']
    form.seeking_venue.data = artist['seeking_venue']
    form.seeking_description.data = artist['seeking_description']
    form.image_link.data = artist['image_link']

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.get(artist_id)
    error = False
    data = None
    try:
        artist.name = request.form['name']
        artist.city = request.form['city']
        artist.state = request.form['state']
        artist.phone = request.form['phone']
        artist.image_link = request.form['image_link']
        artist.facebook_link = request.form['facebook_link']
        artist.website = request.form['website_link']
        artist.seeking_venue = request.form['seeking_venue'] == 'y'
        artist.seeking_description = request.form['seeking_description']
        artist.genres = ','.join(request.form.getlist('genres'))
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    else:
        flash('Artist ' + request.form['name'] + ' was successfully updated!')

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue_from_db = Venue.query.get(venue_id)
    venue = get_venue_map(venue_from_db, False)

    form = VenueForm()
    form.name.data = venue['name']
    form.genres.data = venue['genres']
    form.address.data = venue['address']
    form.city.data = venue['city']
    form.state.data = venue['state']
    form.phone.data = venue['phone']
    form.website_link.data = venue['website']
    form.facebook_link.data = venue['facebook_link']
    form.seeking_talent.data = venue['seeking_talent']
    form.seeking_description.data = venue['seeking_description']
    form.image_link.data = venue['image_link']

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    data = None
    try:
        venue = Venue.query.get(venue_id)
        venue.name = request.form['name']
        venue.city = request.form['city']
        venue.state = request.form['state']
        venue.address = request.form['address']
        venue.phone = request.form['phone']
        venue.image_link = request.form['image_link']
        venue.facebook_link = request.form['facebook_link']
        venue.website_link = request.form['website_link']
        venue.seeking_talent = request.form['seeking_talent'] == 'y'
        venue.seeking_description = request.form['seeking_description']
        venue.genres = ','.join(request.form.getlist('genres'))
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    else:
        flash('Venue ' + request.form['name'] + ' was successfully updated!')

    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    data = None
    try:
        data = Artist(
            name=request.form['name'],
            city=request.form['city'],
            state=request.form['state'],
            phone=request.form['phone'],
            image_link=request.form['image_link'],
            facebook_link=request.form['facebook_link'],
            website=request.form['website_link'],
            seeking_venue=request.form['seeking_venue'] == 'y',
            seeking_description=request.form['seeking_description'],
            genres=','.join(request.form.getlist('genres'))
        )
        db.session.add(data)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------
@app.route('/shows')
def shows():
    shows_from_db = Show.query.all()
    data = []
    for show in shows_from_db:
        data.append({
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': show.start_time,
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    data = None
    try:
        data = Show(start_time=request.form['start_time'])
        venue = Venue.query.get(request.form['venue_id'])
        artist = Artist.query.get(request.form['artist_id'])
        data.venue = venue
        data.artist = artist
        db.session.add(data)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Show could not be listed.')
    else:
        flash('Show was successfully listed!')

    return render_template('pages/home.html')


# ---------------------------------------------------------------------------- #
# Error Handling.
# ---------------------------------------------------------------------------- #
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ---------------------------------------------------------------------------- #
# Launch.
# ---------------------------------------------------------------------------- #
# Default port:
if __name__ == '__main__':
    app.run()
