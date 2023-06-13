# Import the dependencies.
from flask import Flask, jsonify
import datetime as dt
import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, inspect


#################################################
# Database Setup
#################################################


# reflect an existing database into a new model
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

Base = automap_base()
Base.prepare(engine, reflect=True)
Base

# reflect the tables
Base

# View all of the classes that automap found
inspector = inspect(engine)
inspector.get_table_names()

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

columns = inspector.get_columns('measurement')
for c in columns:
    print(c['name'], c['type'])

columns = inspector.get_columns('station')
for c in columns:
    print(c['name'], c['type'])

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

@app.route("/")
def home():
    return (
        f"Welcome to the Climate Analysis API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;<br/>"
    )


#################################################
# Flask Routes
#################################################

# PRECIPITATION ROUTE
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    
    one_year_ago = (pd.to_datetime(most_recent_date) - pd.DateOffset(years=1)).strftime('%Y-%m-%d')
    
    results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()
    
    session.close()
    
    precipitation_data = {date: prcp for date, prcp in results}
    
    return jsonify(precipitation_data)

# STATONS ROUTE
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    results = session.query(Station.station).all()
    
    session.close()

    stations_list = list(np.ravel(results))
    
    return jsonify(stations_list)

# TOBS ROUTE
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    
    last_data_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_data_date = dt.datetime.strptime(last_data_date[0], "%Y-%m-%d")
    one_year_ago = last_data_date - dt.timedelta(days=365)

    results = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.date >= one_year_ago).\
        filter(Measurement.station == 'USC00519281').all()
    
    session.close()
    
    tobs_list = [{"date": date, "tobs": tobs} for date, tobs in results]
    
    return jsonify(tobs_list)

# START AND END ROUTES
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end=None):
    session = Session(engine)
    
    if not end:
        results = session.query(func.min(Measurement.tobs),
                                func.avg(Measurement.tobs),
                                func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).all()
    else:
        results = session.query(func.min(Measurement.tobs),
                                func.avg(Measurement.tobs),
                                func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).\
            filter(Measurement.date <= end).all()
    
    session.close()
    
    temperature_stats = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }
    
    return jsonify(temperature_stats)

if __name__ == "__main__":
    app.run(debug=True)
